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
    CONF_API_KEY,
    CONF_API_URL,
    CONF_CITY_ID,
    CONF_COUNTRY_ID,
    CONF_STATE_ID,
    CONF_CITY_NAME,
    CONF_LANGUAGE,
    DEFAULT_API_URL,
    LANGUAGES,
)

_LOGGER = logging.getLogger(__name__)


class AwqatSalahConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config Flow Handler."""

    VERSION = 1

    def __init__(self):
        self._api_key = None
        self._api_url = None
        self._language = "de"
        self._country_id = None
        self._country_name = None
        self._state_id = None
        self._state_name = None
        self._countries = []
        self._states = []
        self._cities = []

    async def async_step_user(self, user_input=None):
        """Schritt 1: API Key + URL + Sprache."""
        errors = {}

        if user_input is not None:
            self._api_key = user_input[CONF_API_KEY]
            self._api_url = user_input.get(CONF_API_URL, DEFAULT_API_URL).rstrip("/")
            self._language = user_input.get(CONF_LANGUAGE, "de")

            if await self._test_api():
                self._countries = await self._fetch_countries()
                if self._countries:
                    return await self.async_step_country()
                errors["base"] = "cannot_fetch_countries"
            else:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): str,
                vol.Optional(CONF_API_URL, default=DEFAULT_API_URL): str,
                vol.Required(CONF_LANGUAGE, default="de"): SelectSelector(
                    SelectSelectorConfig(
                        options=[{"value": k, "label": v} for k, v in LANGUAGES.items()],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
            errors=errors,
        )

    async def async_step_country(self, user_input=None):
        """Schritt 2: Land auswählen."""
        errors = {}
        # Name → ID Mapping
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

    async def async_step_state(self, user_input=None):
        """Schritt 3: Region auswählen."""
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

    async def async_step_city(self, user_input=None):
        """Schritt 4: Stadt auswählen."""
        errors = {}
        city_map = {c["name"]: c["id"] for c in self._cities}

        if user_input is not None:
            city_name = user_input[CONF_CITY_ID]
            city_id = city_map.get(city_name)

            if city_id:
                return self.async_create_entry(
                    title=city_name,
                    data={
                        CONF_API_KEY: self._api_key,
                        CONF_API_URL: self._api_url,
                        CONF_COUNTRY_ID: self._country_id,
                        CONF_STATE_ID: self._state_id,
                        CONF_CITY_ID: city_id,
                        CONF_CITY_NAME: city_name,
                        CONF_LANGUAGE: self._language,
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

    async def _test_api(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._api_url}/health",
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    return response.status == 200
        except Exception as ex:
            _LOGGER.error("[AwqatSalah] API Test fehlgeschlagen: %s", ex)
            return False

    async def _fetch_countries(self) -> list:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._api_url}/api/v2/Place/Countries",
                    headers={"X-API-Key": self._api_key},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", [])
        except Exception as ex:
            _LOGGER.error("[AwqatSalah] Länder laden fehlgeschlagen: %s", ex)
        return []

    async def _fetch_states(self, country_id: int) -> list:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._api_url}/api/v2/Place/States/{country_id}",
                    headers={"X-API-Key": self._api_key},
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
                    headers={"X-API-Key": self._api_key},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", [])
        except Exception as ex:
            _LOGGER.error("[AwqatSalah] Städte laden fehlgeschlagen: %s", ex)
        return []
