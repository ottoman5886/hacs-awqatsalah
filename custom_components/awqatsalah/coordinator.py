"""Coordinator für AwqatSalah Integration."""
import calendar
import logging
import aiohttp
from datetime import datetime, timedelta
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_API_URL,
    CONF_CITY_ID,
    CONF_API_KEY,           # Legacy-Support
    CONF_HEADER1_NAME,
    CONF_HEADER1_VALUE,
    CONF_HEADER2_NAME,
    CONF_HEADER2_VALUE,
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


def _build_headers(config: dict) -> dict:
    """Header aus Config zusammenbauen.

    Unterstützt sowohl neue (header1_name/value) als auch
    alte Config Entries (api_key) – damit bestehende Installationen
    nach dem Update ohne Neueinrichtung weiterlaufen.
    """
    headers = {}

    # Neue flexible Header
    for name_key, value_key in [
        (CONF_HEADER1_NAME, CONF_HEADER1_VALUE),
        (CONF_HEADER2_NAME, CONF_HEADER2_VALUE),
    ]:
        name  = (config.get(name_key)  or "").strip()
        value = (config.get(value_key) or "").strip()
        if name and value:
            headers[name] = value

    # Legacy: alter api_key Eintrag → automatisch als X-API-Key senden
    if not headers and config.get(CONF_API_KEY):
        headers["X-API-Key"] = config[CONF_API_KEY]

    return headers


class AwqatSalahCoordinator(DataUpdateCoordinator):
    """Koordiniert die Gebetszeiten Daten."""

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.config = config
        self.api_url = config[CONF_API_URL]
        self.city_id = config[CONF_CITY_ID]
        self._headers = _build_headers(config)

        self._store       = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._store_daily = Store(hass, STORAGE_VERSION, STORAGE_KEY_DAILY)
        self._store_eid   = Store(hass, STORAGE_VERSION, STORAGE_KEY_EID)

        self._cached_data:  dict = {}
        self._cached_daily: dict = {}
        self._cached_eid:   dict = {}

        self._midnight_unsub = None

    # ── Feature 7: Midnight Refresh ──────────────────────────────────────────

    def async_setup_midnight_refresh(self) -> None:
        """00:01 Uhr Refresh registrieren."""
        self._midnight_unsub = async_track_time_change(
            self.hass,
            self._async_midnight_refresh,
            hour=0, minute=1, second=0,
        )
        _LOGGER.debug("[AwqatSalah] Midnight-Refresh um 00:01 registriert")

    def async_unsubscribe_midnight(self) -> None:
        if self._midnight_unsub:
            self._midnight_unsub()
            self._midnight_unsub = None

    @callback
    def _async_midnight_refresh(self, _now: datetime) -> None:
        _LOGGER.debug("[AwqatSalah] Midnight-Refresh ausgelöst")
        self.hass.async_create_task(self.async_refresh())

    # ── Hauptupdate ───────────────────────────────────────────────────────────

    async def _async_update_data(self) -> dict:
        today = datetime.now().strftime("%d.%m.%Y")

        await self._load_cache()
        await self._load_daily_cache()
        await self._load_eid_cache()

        await self.async_check_and_refresh_month()

        # Feature 4: Predictive Prefetch
        await self._async_prefetch_next_month_if_needed()

        prayer_data = self._get_today_from_cache(today)
        if not prayer_data:
            _LOGGER.info("[AwqatSalah] Cache leer, lade Gebetszeiten von API")
            await self._fetch_and_cache()
            prayer_data = self._get_today_from_cache(today)

        if not prayer_data:
            raise UpdateFailed("Keine Gebetszeiten für heute verfügbar")

        daily_content = await self._get_daily_content(today)
        eid_data      = await self._get_eid_data()

        result = prayer_data.copy()
        if daily_content:
            result.update(daily_content)
        if eid_data:
            result.update(eid_data)

        return result

    # ── Feature 4: Predictive Prefetch ───────────────────────────────────────

    async def _async_prefetch_next_month_if_needed(self) -> None:
        now = datetime.now()
        last_day = calendar.monthrange(now.year, now.month)[1]
        if now.day < last_day - 1:
            return

        next_month = now.month + 1 if now.month < 12 else 1
        next_year  = now.year if now.month < 12 else now.year + 1

        next_month_str = f".{next_month:02d}.{next_year}"
        already_cached = any(
            next_month_str in e.get("gregorianDateShort", "")
            for e in self._cached_data.get("entries", [])
        )
        if already_cached:
            return

        _LOGGER.info("[AwqatSalah] Predictive Prefetch: lade %02d/%d", next_month, next_year)
        monthly = await self._fetch_monthly_for(next_month, next_year)
        if monthly:
            existing       = self._cached_data.get("entries", [])
            existing_dates = {e.get("gregorianDateShort") for e in existing}
            for entry in monthly:
                if entry.get("gregorianDateShort") not in existing_dates:
                    existing.append(entry)
            self._cached_data["entries"] = existing
            await self._save_cache()

    # ── Cache & API ───────────────────────────────────────────────────────────

    def _get_today_from_cache(self, today: str) -> dict | None:
        for entry in self._cached_data.get("entries", []):
            if entry.get("gregorianDateShort") == today:
                return self._process_entry(entry)
        return None

    def _process_entry(self, entry: dict) -> dict:
        result = {}
        for sensor, api_field in API_FIELD_MAP.items():
            result[sensor] = entry.get(api_field, "")

        gunes = entry.get("sunrise", "")
        if gunes:
            try:
                h, m = map(int, gunes.split(":"))
                total = h * 60 + m - 60
                result[SENSOR_SABAH] = f"{total // 60:02d}:{total % 60:02d}"
            except Exception:
                result[SENSOR_SABAH] = ""

        result["hijriDateLong"]       = entry.get("hijriDateLong", "")
        result["gregorianDateShort"]  = entry.get("gregorianDateShort", "")
        return result

    async def _get_daily_content(self, today: str) -> dict | None:
        if self._cached_daily.get("date") == today and self._cached_daily.get("data"):
            return self._cached_daily["data"]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/api/DailyContent",
                    headers=self._headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        data   = await response.json()
                        raw    = data.get("data", {})
                        result = {s: raw.get(f) for s, f in DAILY_CONTENT_FIELD_MAP.items()}
                        self._cached_daily = {"date": today, "data": result}
                        await self._store_daily.async_save(self._cached_daily)
                        return result
        except Exception as ex:
            _LOGGER.warning("[AwqatSalah] DailyContent Fehler: %s", ex)
        return self._cached_daily.get("data")

    async def _get_eid_data(self) -> dict | None:
        if self._cached_eid.get("year") == datetime.now().year and self._cached_eid.get("data"):
            return self._cached_eid["data"]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/api/AwqatSalah/Eid/{self.city_id}",
                    headers=self._headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        data   = await response.json()
                        raw    = data.get("data", {})
                        result = {s: raw.get(f) for s, f in EID_FIELD_MAP.items()}
                        self._cached_eid = {"year": datetime.now().year, "data": result}
                        await self._store_eid.async_save(self._cached_eid)
                        return result
        except Exception as ex:
            _LOGGER.warning("[AwqatSalah] Eid Fehler: %s", ex)
        return self._cached_eid.get("data")

    async def _fetch_and_cache(self) -> None:
        yearly = await self._fetch_yearly()
        if yearly:
            self._cached_data = {
                "type": "yearly", "year": datetime.now().year,
                "entries": yearly, "fetched_at": datetime.now().isoformat(),
            }
            await self._save_cache()
            return

        monthly = await self._fetch_monthly()
        if monthly:
            existing       = self._cached_data.get("entries", [])
            existing_dates = {e.get("gregorianDateShort") for e in existing}
            for entry in monthly:
                if entry.get("gregorianDateShort") not in existing_dates:
                    existing.append(entry)
            self._cached_data = {
                "type": "monthly", "year": datetime.now().year,
                "month": datetime.now().month, "entries": existing,
                "fetched_at": datetime.now().isoformat(),
            }
            await self._save_cache()
            return

        _LOGGER.error("[AwqatSalah] Keine Daten von API verfügbar")

    async def _fetch_yearly(self) -> list | None:
        year = datetime.now().year
        payload = {
            "cityId": self.city_id,
            "startDate": f"{year}-01-01T00:00:00Z",
            "endDate":   f"{year}-12-31T00:00:00Z",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/api/AwqatSalah/Yearly",
                    json=payload,
                    headers=self._headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status == 200:
                        data    = await response.json()
                        entries = data.get("data", [])
                        if entries and len(entries) > 31:
                            return entries
        except Exception as ex:
            _LOGGER.warning("[AwqatSalah] Yearly Fehler: %s", ex)
        return None

    async def _fetch_monthly(self) -> list | None:
        return await self._fetch_monthly_for(datetime.now().month, datetime.now().year)

    async def _fetch_monthly_for(self, month: int, year: int) -> list | None:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/api/AwqatSalah/Monthly/{self.city_id}",
                    headers=self._headers,
                    params={"month": month, "year": year},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", [])
        except Exception as ex:
            _LOGGER.warning("[AwqatSalah] Monthly Fehler: %s", ex)
        return None

    async def _load_cache(self) -> None:
        if self._cached_data:
            return
        data = await self._store.async_load()
        if data:
            if data.get("year") and data["year"] != datetime.now().year:
                _LOGGER.info("[AwqatSalah] Jahreswechsel erkannt, Cache erneuern")
                return
            self._cached_data = data

    async def _load_daily_cache(self) -> None:
        if self._cached_daily:
            return
        data = await self._store_daily.async_load()
        if data:
            self._cached_daily = data

    async def _load_eid_cache(self) -> None:
        if self._cached_eid:
            return
        data = await self._store_eid.async_load()
        if data:
            self._cached_eid = data

    async def _save_cache(self) -> None:
        await self._store.async_save(self._cached_data)

    async def async_check_and_refresh_month(self) -> None:
        if self._cached_data.get("type") == "monthly":
            if self._cached_data.get("month") != datetime.now().month:
                _LOGGER.info("[AwqatSalah] Neuer Monat, lade neue Daten")
                self._cached_data = {}
                await self._fetch_and_cache()
