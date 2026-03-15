"""Config Flow für AwqatSalah Integration."""
import logging
import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    DOMAIN,
    CONF_API_URL,
    CONF_CITY_ID,
    CONF_COUNTRY_ID,
    CONF_STATE_ID,
    CONF_CITY_NAME,
    CONF_LANGUAGE,
    CONF_HEADER1_NAME,
    CONF_HEADER1_VALUE,
    CONF_HEADER2_NAME,
    CONF_HEADER2_VALUE,
    DEFAULT_API_URL,
    LANGUAGES,
)

_LOGGER = logging.getLogger(__name__)


def _build_headers(data: dict) -> dict:
    """Aus den gespeicherten Name/Value-Paaren echte Request-Header bauen.

    Leere Namen oder Werte werden übersprungen.
    Beispiele:
      Self-hosted  → header1_name=X-API-Key, header1_value=abc123
      Diyanet JWT  → header1_name=Authorization, header1_value=Bearer <token>
                     (Token wird vom Coordinator dynamisch ersetzt)
    """
    headers = {}
    for name_key, value_key in [
        (CONF_HEADER1_NAME, CONF_HEADER1_VALUE),
        (CONF_HEADER2_NAME, CONF_HEADER2_VALUE),
    ]:
        name = (data.get(name_key) or "").strip()
        value = (data.get(value_key) or "").strip()
        if name and value:
            headers[name] = value
    return headers


class AwqatSalahConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config Flow Handler."""

    VERSION = 1

    def __init__(self):
        self._api_url = None
        self._language = "de"
        self._header1_name = ""
        self._header1_value = ""
        self._header2_name = ""
        self._header2_value = ""
        self._direct_city_id = None  # optional: skip country/state/city steps
        self._country_id = None
        self._country_name = None
        self._state_id = None
        self._state_name = None
        self._countries = []
        self._states = []
        self._cities = []

    # ── Schritt 1: API URL + Sprache + Header ────────────────────────────────

    async def async_step_user(self, user_input=None):
        """Schritt 1: Verbindung & Authentifizierung."""
        errors = {}

        if user_input is not None:
            self._api_url = user_input.get(CONF_API_URL, DEFAULT_API_URL).rstrip("/")
            self._language = user_input.get(CONF_LANGUAGE, "de")
            self._header1_name  = (user_input.get(CONF_HEADER1_NAME)  or "").strip()
            self._header1_value = (user_input.get(CONF_HEADER1_VALUE) or "").strip()
            self._header2_name  = (user_input.get(CONF_HEADER2_NAME)  or "").strip()
            self._header2_value = (user_input.get(CONF_HEADER2_VALUE) or "").strip()

            # Optionale direkte City ID
            raw_city = str(user_input.get(CONF_CITY_ID) or "").strip()
            self._direct_city_id = int(raw_city) if raw_city.isdigit() else None

            # Header1 Name + Value sind Pflicht
            if not self._header1_name or not self._header1_value:
                errors["base"] = "header1_required"
            elif self._direct_city_id:
                # City ID direkt angegeben → Dropdown überspringen
                return self.async_create_entry(
                    title=f"AwqatSalah – City {self._direct_city_id}",
                    data={
                        CONF_API_URL:       self._api_url,
                        CONF_LANGUAGE:      self._language,
                        CONF_HEADER1_NAME:  self._header1_name,
                        CONF_HEADER1_VALUE: self._header1_value,
                        CONF_HEADER2_NAME:  self._header2_name,
                        CONF_HEADER2_VALUE: self._header2_value,
                        CONF_COUNTRY_ID:    None,
                        CONF_STATE_ID:      None,
                        CONF_CITY_ID:       self._direct_city_id,
                        CONF_CITY_NAME:     f"City {self._direct_city_id}",
                    },
                )
            else:
                # Kein direkter City ID → Länder laden für Dropdown
                # Render.com braucht beim Aufwachen bis zu 90 Sek → langer Timeout + 1 Retry.
                self._countries = await self._fetch_countries()
                if self._countries:
                    return await self.async_step_country()
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Optional(CONF_API_URL, default=DEFAULT_API_URL): str,
                vol.Required(CONF_LANGUAGE, default="de"): SelectSelector(
                    SelectSelectorConfig(
                        options=[{"value": k, "label": v} for k, v in LANGUAGES.items()],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_HEADER1_NAME, default="X-API-Key"): str,
                vol.Required(CONF_HEADER1_VALUE): str,
                vol.Optional(CONF_HEADER2_NAME, default=""): str,
                vol.Optional(CONF_HEADER2_VALUE, default=""): str,
                vol.Optional(CONF_CITY_ID, default=""): str,
            }),
            errors=errors,
        )

    # ── Schritt 2: Land ──────────────────────────────────────────────────────

    async def async_step_country(self, user_input=None):
        errors = {}
        country_map = {c["name"]: c["id"] for c in self._countries}

        if user_input is not None:
            country_name = user_input[CONF_COUNTRY_ID]
            self._country_id = country_map.get(country_name)
            self._country_name = country_name
            if self._country_id:
                self._states = await self._fetch_states(self._country_id)
                if self._states:
                    return await self.async_step_state()
            errors["base"] = "cannot_fetch_states"

        return self.async_show_form(
            step_id="country",
            data_schema=vol.Schema({
                vol.Required(CONF_COUNTRY_ID): SelectSelector(
                    SelectSelectorConfig(
                        options=list(country_map.keys()),
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
            errors=errors,
        )

    # ── Schritt 3: Region ────────────────────────────────────────────────────

    async def async_step_state(self, user_input=None):
        errors = {}
        state_map = {s["name"]: s["id"] for s in self._states}

        if user_input is not None:
            state_name = user_input[CONF_STATE_ID]
            self._state_id = state_map.get(state_name)
            self._state_name = state_name
            if self._state_id:
                self._cities = await self._fetch_cities(self._state_id)
                if self._cities:
                    return await self.async_step_city()
            errors["base"] = "cannot_fetch_cities"

        return self.async_show_form(
            step_id="state",
            data_schema=vol.Schema({
                vol.Required(CONF_STATE_ID): SelectSelector(
                    SelectSelectorConfig(
                        options=list(state_map.keys()),
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
            errors=errors,
        )

    # ── Schritt 4: Stadt ─────────────────────────────────────────────────────

    async def async_step_city(self, user_input=None):
        errors = {}
        city_map = {c["name"]: c["id"] for c in self._cities}

        if user_input is not None:
            city_name = user_input[CONF_CITY_ID]
            city_id = city_map.get(city_name)
            if city_id:
                return self.async_create_entry(
                    title=city_name,
                    data={
                        CONF_API_URL:       self._api_url,
                        CONF_LANGUAGE:      self._language,
                        CONF_HEADER1_NAME:  self._header1_name,
                        CONF_HEADER1_VALUE: self._header1_value,
                        CONF_HEADER2_NAME:  self._header2_name,
                        CONF_HEADER2_VALUE: self._header2_value,
                        CONF_COUNTRY_ID:    self._country_id,
                        CONF_STATE_ID:      self._state_id,
                        CONF_CITY_ID:       city_id,
                        CONF_CITY_NAME:     city_name,
                    },
                )
            errors["base"] = "cannot_fetch_cities"

        return self.async_show_form(
            step_id="city",
            data_schema=vol.Schema({
                vol.Required(CONF_CITY_ID): SelectSelector(
                    SelectSelectorConfig(
                        options=list(city_map.keys()),
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
            errors=errors,
        )

    # ── API Hilfsmethoden ────────────────────────────────────────────────────

    def _get_headers(self) -> dict:
        """Aktuelle Header aus den eingegebenen Feldern zusammenbauen."""
        return _build_headers({
            CONF_HEADER1_NAME:  self._header1_name,
            CONF_HEADER1_VALUE: self._header1_value,
            CONF_HEADER2_NAME:  self._header2_name,
            CONF_HEADER2_VALUE: self._header2_value,
        })

    async def _test_api(self) -> bool:
        # Nicht mehr verwendet – _fetch_countries übernimmt die Verbindungsprüfung
        return True

    async def _fetch_countries(self) -> list:
        """Länder laden – mit langem Timeout für Render.com Aufwachzeit + 1 Retry."""
        for attempt in range(2):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self._api_url}/api/v2/Place/Countries",
                        headers=self._get_headers(),
                        timeout=aiohttp.ClientTimeout(total=90),
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data.get("data", [])
                        _LOGGER.warning(
                            "[AwqatSalah] Länder: HTTP %s (Versuch %d)",
                            response.status, attempt + 1,
                        )
            except Exception as ex:
                _LOGGER.warning(
                    "[AwqatSalah] Länder laden fehlgeschlagen (Versuch %d): %s",
                    attempt + 1, ex,
                )
        return []

    async def _fetch_states(self, country_id: int) -> list:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._api_url}/api/v2/Place/States/{country_id}",
                    headers=self._get_headers(),
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", [])
        except Exception as ex:
            _LOGGER.error("[AwqatSalah] Regionen laden fehlgeschlagen: %s", ex)
        return []

    async def _fetch_cities(self, state_id: int) -> list:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._api_url}/api/v2/Place/Cities/{state_id}",
                    headers=self._get_headers(),
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", [])
        except Exception as ex:
            _LOGGER.error("[AwqatSalah] Städte laden fehlgeschlagen: %s", ex)
        return []
