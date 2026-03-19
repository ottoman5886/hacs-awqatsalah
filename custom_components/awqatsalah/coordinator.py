"""Coordinator für AwqatSalah Integration."""
import calendar
import logging
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
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
    """Header aus Config zusammenbauen."""
    headers = {}
    for name_key, value_key in [
        (CONF_HEADER1_NAME, CONF_HEADER1_VALUE),
        (CONF_HEADER2_NAME, CONF_HEADER2_VALUE),
    ]:
        name  = (config.get(name_key)  or "").strip()
        value = (config.get(value_key) or "").strip()
        if name and value:
            headers[name] = value

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
        self.api_url = config[CONF_API_URL].rstrip("/")
        self.city_id = config[CONF_CITY_ID]
        self._headers = _build_headers(config)
        self._session = async_get_clientsession(hass)

        self._store       = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._store_daily = Store(hass, STORAGE_VERSION, STORAGE_KEY_DAILY)
        self._store_eid   = Store(hass, STORAGE_VERSION, STORAGE_KEY_EID)

        self._cached_data:  dict = {}
        self._cached_daily: dict = {}
        self._cached_eid:   dict = {}

        self._midnight_unsub = None

    # ── Refresh Logik ────────────────────────────────────────────────────────

    def async_setup_midnight_refresh(self) -> None:
        """Erster Versuch nach Mitternacht (01:05 Uhr wegen UTC/CET Offset der API)."""
        self._midnight_unsub = async_track_time_change(
            self.hass,
            self._async_midnight_refresh,
            hour=1, minute=5, second=0,
        )
        _LOGGER.debug("[AwqatSalah] Midnight-Refresh für 01:05 Uhr registriert")

    def async_unsubscribe_midnight(self) -> None:
        if self._midnight_unsub:
            self._midnight_unsub()
            self._midnight_unsub = None

    @callback
    def _async_midnight_refresh(self, _now: datetime) -> None:
        """Cache wird nicht mehr gelöscht, nur das Update wird getriggert."""
        _LOGGER.debug("[AwqatSalah] 01:05 Uhr erreicht. Starte täglichen Refresh-Zyklus.")
        self.hass.async_create_task(self.async_refresh())

    # ── Hauptupdate ──────────────────────────────────────────────────────────

    async def _async_update_data(self) -> dict:
        today = datetime.now().strftime("%d.%m.%Y")

        # Caches laden falls nötig
        await self._load_cache()
        await self._load_daily_cache()
        await self._load_eid_cache()

        # Monatspflege
        await self.async_check_and_refresh_month()
        await self._async_prefetch_next_month_if_needed()

        # Gebetszeiten holen
        prayer_data = self._get_today_from_cache(today)
        if not prayer_data:
            await self._fetch_and_cache()
            prayer_data = self._get_today_from_cache(today)

        if not prayer_data:
            raise UpdateFailed("Keine Gebetszeiten für heute verfügbar")

        # Daily Content und Eid Daten laden (mit intelligenter Cache-Logik)
        daily_content = await self._get_daily_content(today)
        eid_data      = await self._get_eid_data()

        result = prayer_data.copy()
        if daily_content:
            result.update(daily_content)
        if eid_data:
            result.update(eid_data)

        return result

    # ── API & Content Logik ──────────────────────────────────────────────────

    async def _get_daily_content(self, today: str) -> dict | None:
        """Holt Daily Content. Zeigt alte Daten, bis neue valide Daten da sind."""
        # Falls wir für HEUTE schon erfolgreich geladen haben, nutze das
        if self._cached_daily.get("date") == today and self._cached_daily.get("data"):
            return self._cached_daily["data"]

        try:
            async with self._session.get(
                f"{self.api_url}/api/DailyContent",
                headers=self._headers,
                timeout=40,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    raw = data.get("data", {})
                    result = {s: raw.get(f) for s, f in DAILY_CONTENT_FIELD_MAP.items()}
                    
                    # Validierung: Nur speichern, wenn echter Inhalt vorhanden ist
                    if any(str(v).strip() for v in result.values() if v):
                        self._cached_daily = {"date": today, "data": result}
                        await self._store_daily.async_save(self._cached_daily)
                        _LOGGER.info("[AwqatSalah] Daily Content für %s erfolgreich aktualisiert", today)
                        return result
                    
                    _LOGGER.info("[AwqatSalah] API hat noch keinen neuen Content. Nutze vorhandenen Cache.")
                else:
                    _LOGGER.warning("[AwqatSalah] Daily Content HTTP %s", response.status)

        except Exception as ex:
            _LOGGER.error("[AwqatSalah] Fehler beim Daily Content Update: %s", ex)

        # Im Fehlerfall oder bei leerer API: Zeige alten Content weiter an.
        # Da 'date' ungleich 'today' bleibt, wird beim nächsten Scan automatisch ein Retry versucht.
        return self._cached_daily.get("data")

    async def _get_eid_data(self) -> dict | None:
        """Eid Daten mit 30-Tage-Refresh Logik."""
        now = datetime.now()
        year = now.year
        
        # Prüfen, ob Refresh nötig: Jahr gewechselt, Cache leer oder > 30 Tage alt
        last_fetched_str = self._cached_eid.get("fetched_at", "2000-01-01T00:00:00")
        try:
            last_fetched = datetime.fromisoformat(last_fetched_str)
        except ValueError:
            last_fetched = datetime(2000, 1, 1)

        needs_refresh = (
            self._cached_eid.get("year") != year or 
            (now - last_fetched) > timedelta(days=30) or
            not self._cached_eid.get("data")
        )

        if not needs_refresh:
            return self._cached_eid.get("data")

        try:
            async with self._session.get(
                f"{self.api_url}/api/AwqatSalah/Eid/{self.city_id}",
                headers=self._headers,
                timeout=20,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    raw = data.get("data", {})
                    result = {s: raw.get(f) for s, f in EID_FIELD_MAP.items()}
                    
                    if any(result.values()):
                        self._cached_eid = {
                            "year": year, 
                            "data": result,
                            "fetched_at": now.isoformat()
                        }
                        await self._store_eid.async_save(self._cached_eid)
                        _LOGGER.debug("[AwqatSalah] Eid Daten für das Jahr %s aktualisiert", year)
                        return result
        except Exception as ex:
            _LOGGER.debug("[AwqatSalah] Eid Update fehlgeschlagen (nutze Cache): %s", ex)
            
        return self._cached_eid.get("data")

    async def _fetch_and_cache(self) -> None:
        """Lädt Jahres- oder Monatsdaten."""
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
            self._cached_data = {
                "type": "monthly", "year": datetime.now().year,
                "month": datetime.now().month, "entries": monthly,
                "fetched_at": datetime.now().isoformat(),
            }
            await self._save_cache()

    async def _fetch_yearly(self) -> list | None:
        year = datetime.now().year
        payload = {
            "cityId": self.city_id,
            "startDate": f"{year}-01-01T00:00:00Z",
            "endDate":   f"{year}-12-31T00:00:00Z",
        }
        try:
            async with self._session.post(
                f"{self.api_url}/api/AwqatSalah/Yearly",
                json=payload, headers=self._headers, timeout=40,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    entries = data.get("data", [])
                    if entries and len(entries) > 31:
                        return entries
        except Exception:
            return None

    async def _fetch_monthly_for(self, month: int, year: int) -> list | None:
        try:
            async with self._session.get(
                f"{self.api_url}/api/AwqatSalah/Monthly/{self.city_id}",
                headers=self._headers,
                params={"month": month, "year": year},
                timeout=20,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
        except Exception:
            return None

    async def _fetch_monthly(self) -> list | None:
        return await self._fetch_monthly_for(datetime.now().month, datetime.now().year)

    # ── Hilfsfunktionen ──────────────────────────────────────────────────────

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
                result[SENSOR_SABAH] = f"{max(0, total // 60):02d}:{total % 60:02d}"
            except Exception:
                result[SENSOR_SABAH] = ""

        result["hijriDateLong"]       = entry.get("hijriDateLong", "")
        result["gregorianDateShort"]  = entry.get("gregorianDateShort", "")
        return result

    async def async_check_and_refresh_month(self) -> None:
        if self._cached_data.get("type") == "monthly":
            if self._cached_data.get("month") != datetime.now().month:
                self._cached_data = {}
                await self._fetch_and_cache()

    async def _async_prefetch_next_month_if_needed(self) -> None:
        now = datetime.now()
        last_day = calendar.monthrange(now.year, now.month)[1]
        if now.day < last_day - 1:
            return

        next_month = now.month + 1 if now.month < 12 else 1
        next_year  = now.year if now.month < 12 else now.year + 1
        
        next_month_str = f".{next_month:02d}.{next_year}"
        entries = self._cached_data.get("entries", [])
        if any(next_month_str in e.get("gregorianDateShort", "") for e in entries):
            return

        monthly = await self._fetch_monthly_for(next_month, next_year)
        if monthly:
            existing_dates = {e.get("gregorianDateShort") for e in entries}
            for entry in monthly:
                if entry.get("gregorianDateShort") not in existing_dates:
                    entries.append(entry)
            self._cached_data["entries"] = entries
            await self._save_cache()

    async def _load_cache(self) -> None:
        if not self._cached_data:
            data = await self._store.async_load()
            if data and data.get("year") == datetime.now().year:
                self._cached_data = data

    async def _load_daily_cache(self) -> None:
        if not self._cached_daily:
            self._cached_daily = await self._store_daily.async_load() or {}

    async def _load_eid_cache(self) -> None:
        if not self._cached_eid:
            self._cached_eid = await self._store_eid.async_load() or {}

    async def _save_cache(self) -> None:
        await self._store.async_save(self._cached_data)
