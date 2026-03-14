"""Coordinator für AwqatSalah Integration."""
import logging
import aiohttp
from datetime import datetime, timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_API_URL,
    CONF_CITY_ID,
    DEFAULT_SCAN_INTERVAL,
    API_FIELD_MAP,
    DAILY_CONTENT_FIELD_MAP,
    EID_FIELD_MAP,
    SENSOR_SABAH,
)

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = "awqatsalah_cache"
STORAGE_KEY_DAILY = "awqatsalah_daily_content"
STORAGE_KEY_EID = "awqatsalah_eid"


class AwqatSalahCoordinator(DataUpdateCoordinator):
    """Koordiniert die Gebetszeiten Daten."""

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        """Initialisierung."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.config = config
        self.api_key = config[CONF_API_KEY]
        self.api_url = config[CONF_API_URL]
        self.city_id = config[CONF_CITY_ID]
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._store_daily = Store(hass, STORAGE_VERSION, STORAGE_KEY_DAILY)
        self._store_eid = Store(hass, STORAGE_VERSION, STORAGE_KEY_EID)
        self._cached_data: dict = {}
        self._cached_daily: dict = {}
        self._cached_eid: dict = {}

    async def _async_update_data(self) -> dict:
        """Daten aktualisieren – täglich aufgerufen."""
        today = datetime.now().strftime("%d.%m.%Y")

        # Cache laden
        await self._load_cache()
        await self._load_daily_cache()
        await self._load_eid_cache()

        # Monats-Refresh prüfen
        await self.async_check_and_refresh_month()

        # Gebetszeiten
        prayer_data = self._get_today_from_cache(today)
        if not prayer_data:
            _LOGGER.info("[AwqatSalah] Cache leer, lade Gebetszeiten von API")
            await self._fetch_and_cache()
            prayer_data = self._get_today_from_cache(today)

        if not prayer_data:
            raise UpdateFailed("Keine Gebetszeiten für heute verfügbar")

        # DailyContent
        daily_content = await self._get_daily_content(today)

        # Eid
        eid_data = await self._get_eid_data()

        # Alles zusammenführen
        result = prayer_data.copy()
        if daily_content:
            result.update(daily_content)
        if eid_data:
            result.update(eid_data)

        return result

    def _get_today_from_cache(self, today: str) -> dict | None:
        """Heutigen Tag aus Cache holen."""
        entries = self._cached_data.get("entries", [])
        for entry in entries:
            if entry.get("gregorianDateShort") == today:
                return self._process_entry(entry)
        return None

    def _process_entry(self, entry: dict) -> dict:
        """Eintrag verarbeiten und Sabah berechnen."""
        result = {}

        for sensor, api_field in API_FIELD_MAP.items():
            result[sensor] = entry.get(api_field, "")

        # Sabah = Güneş - 60 Minuten
        gunes = entry.get("sunrise", "")
        if gunes:
            try:
                h, m = map(int, gunes.split(":"))
                total = h * 60 + m - 60
                result[SENSOR_SABAH] = f"{total // 60:02d}:{total % 60:02d}"
            except Exception:
                result[SENSOR_SABAH] = ""

        result["hijriDateLong"] = entry.get("hijriDateLong", "")
        result["gregorianDateShort"] = entry.get("gregorianDateShort", "")

        return result

    async def _get_daily_content(self, today: str) -> dict | None:
        """DailyContent holen – täglich neu."""
        cached_date = self._cached_daily.get("date")
        if cached_date == today and self._cached_daily.get("data"):
            _LOGGER.debug("[AwqatSalah] DailyContent Cache-Treffer")
            return self._cached_daily["data"]

        # Neu laden
        _LOGGER.info("[AwqatSalah] Lade DailyContent von API")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/api/DailyContent",
                    headers={"X-API-Key": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        raw = data.get("data", {})
                        result = {}
                        for sensor, api_field in DAILY_CONTENT_FIELD_MAP.items():
                            result[sensor] = raw.get(api_field, "")

                        self._cached_daily = {"date": today, "data": result}
                        await self._store_daily.async_save(self._cached_daily)
                        return result
        except Exception as ex:
            _LOGGER.warning("[AwqatSalah] DailyContent Fehler: %s", ex)

        return self._cached_daily.get("data")

    async def _get_eid_data(self) -> dict | None:
        """Eid Daten holen – jährlich neu."""
        cached_year = self._cached_eid.get("year")
        if cached_year == datetime.now().year and self._cached_eid.get("data"):
            _LOGGER.debug("[AwqatSalah] Eid Cache-Treffer")
            return self._cached_eid["data"]

        # Neu laden
        _LOGGER.info("[AwqatSalah] Lade Eid Daten von API")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/api/AwqatSalah/Eid/{self.city_id}",
                    headers={"X-API-Key": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        raw = data.get("data", {})
                        result = {}
                        for sensor, api_field in EID_FIELD_MAP.items():
                            result[sensor] = raw.get(api_field, "")

                        self._cached_eid = {"year": datetime.now().year, "data": result}
                        await self._store_eid.async_save(self._cached_eid)
                        return result
        except Exception as ex:
            _LOGGER.warning("[AwqatSalah] Eid Fehler: %s", ex)

        return self._cached_eid.get("data")

    async def _fetch_and_cache(self) -> None:
        """Daten von API laden und cachen."""
        yearly = await self._fetch_yearly()
        if yearly:
            _LOGGER.info("[AwqatSalah] Jahres-Daten geladen: %d Einträge", len(yearly))
            self._cached_data = {
                "type": "yearly",
                "year": datetime.now().year,
                "entries": yearly,
                "fetched_at": datetime.now().isoformat(),
            }
            await self._save_cache()
            return

        monthly = await self._fetch_monthly()
        if monthly:
            _LOGGER.info("[AwqatSalah] Monats-Daten geladen: %d Einträge", len(monthly))
            existing = self._cached_data.get("entries", [])
            existing_dates = {e.get("gregorianDateShort") for e in existing}
            for entry in monthly:
                if entry.get("gregorianDateShort") not in existing_dates:
                    existing.append(entry)
            self._cached_data = {
                "type": "monthly",
                "year": datetime.now().year,
                "month": datetime.now().month,
                "entries": existing,
                "fetched_at": datetime.now().isoformat(),
            }
            await self._save_cache()
            return

        _LOGGER.error("[AwqatSalah] Keine Daten von API verfügbar")

    async def _fetch_yearly(self) -> list | None:
        """Jahres-Daten von API laden."""
        year = datetime.now().year
        url = f"{self.api_url}/api/AwqatSalah/Yearly"
        payload = {
            "cityId": self.city_id,
            "startDate": f"{year}-01-01T00:00:00Z",
            "endDate": f"{year}-12-31T00:00:00Z",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers={"X-API-Key": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        entries = data.get("data", [])
                        if entries and len(entries) > 31:
                            return entries
                    _LOGGER.warning("[AwqatSalah] Yearly fehlgeschlagen: %s", response.status)
                    return None
        except Exception as ex:
            _LOGGER.warning("[AwqatSalah] Yearly Fehler: %s", ex)
            return None

    async def _fetch_monthly(self) -> list | None:
        """Monats-Daten von API laden."""
        url = f"{self.api_url}/api/AwqatSalah/Monthly/{self.city_id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers={"X-API-Key": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", [])
                    _LOGGER.warning("[AwqatSalah] Monthly fehlgeschlagen: %s", response.status)
                    return None
        except Exception as ex:
            _LOGGER.warning("[AwqatSalah] Monthly Fehler: %s", ex)
            return None

    async def _load_cache(self) -> None:
        """Gebetszeiten Cache laden."""
        if self._cached_data:
            return
        data = await self._store.async_load()
        if data:
            cached_year = data.get("year")
            if cached_year and cached_year != datetime.now().year:
                _LOGGER.info("[AwqatSalah] Jahreswechsel erkannt, Cache wird erneuert")
                self._cached_data = {}
                return
            self._cached_data = data
            _LOGGER.info("[AwqatSalah] Cache geladen: %d Einträge", len(data.get("entries", [])))

    async def _load_daily_cache(self) -> None:
        """DailyContent Cache laden."""
        if self._cached_daily:
            return
        data = await self._store_daily.async_load()
        if data:
            self._cached_daily = data

    async def _load_eid_cache(self) -> None:
        """Eid Cache laden."""
        if self._cached_eid:
            return
        data = await self._store_eid.async_load()
        if data:
            self._cached_eid = data

    async def _save_cache(self) -> None:
        """Cache speichern."""
        await self._store.async_save(self._cached_data)
        _LOGGER.info("[AwqatSalah] Cache gespeichert")

    async def async_check_and_refresh_month(self) -> None:
        """Prüfen ob neuer Monat benötigt wird."""
        if self._cached_data.get("type") == "monthly":
            cached_month = self._cached_data.get("month")
            if cached_month and cached_month != datetime.now().month:
                _LOGGER.info("[AwqatSalah] Neuer Monat erkannt, lade neue Daten")
                self._cached_data = {}
                await self._fetch_and_cache()
