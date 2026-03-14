"""Sensoren für AwqatSalah Integration."""
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_CITY_NAME,
    CONF_LANGUAGE,
    SENSORS,
    SENSOR_NAMES,
)
from .coordinator import AwqatSalahCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Sensoren einrichten."""
    coordinator: AwqatSalahCoordinator = hass.data[DOMAIN][entry.entry_id]
    language = entry.data.get(CONF_LANGUAGE, "de")
    city_name = entry.data.get(CONF_CITY_NAME, "")

    entities = [
        AwqatSalahSensor(coordinator, sensor_key, language, city_name, entry.entry_id)
        for sensor_key in SENSORS
    ]

    async_add_entities(entities, True)


class AwqatSalahSensor(CoordinatorEntity, SensorEntity):
    """Gebetszeit Sensor."""

    def __init__(
        self,
        coordinator: AwqatSalahCoordinator,
        sensor_key: str,
        language: str,
        city_name: str,
        entry_id: str,
    ) -> None:
        """Initialisierung."""
        super().__init__(coordinator)
        self._sensor_key = sensor_key
        self._language = language
        self._city_name = city_name
        self._entry_id = entry_id

    @property
    def unique_id(self) -> str:
        """Eindeutige ID."""
        return f"{DOMAIN}_{self._entry_id}_{self._sensor_key}"

    @property
    def name(self) -> str:
        """Sensor Name in gewählter Sprache."""
        names = SENSOR_NAMES.get(self._language, SENSOR_NAMES["de"])
        sensor_name = names.get(self._sensor_key, self._sensor_key)
        return f"{sensor_name} ({self._city_name})"

    @property
    def state(self) -> str:
        """Aktueller Wert."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._sensor_key, "")

    @property
    def extra_state_attributes(self) -> dict:
        """Zusätzliche Attribute."""
        if self.coordinator.data is None:
            return {}
        return {
            "hijri_date": self.coordinator.data.get("hijriDateLong", ""),
            "gregorian_date": self.coordinator.data.get("gregorianDateShort", ""),
            "city": self._city_name,
            "language": self._language,
        }

    @property
    def icon(self) -> str:
        """Icon pro Gebetszeit."""
        icons = {
            "imsak": "mdi:weather-night",
            "sabah": "mdi:weather-sunset-up",
            "gunes": "mdi:white-balance-sunny",
            "ogle": "mdi:weather-sunny",
            "ikindi": "mdi:weather-sunny-alert",
            "aksam": "mdi:weather-sunset-down",
            "yatsi": "mdi:weather-night",
        }
        return icons.get(self._sensor_key, "mdi:clock")

    @property
    def device_info(self) -> dict:
        """Geräteinformationen."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": f"AwqatSalah - {self._city_name}",
            "manufacturer": "Diyanet",
            "model": "Gebetszeiten API",
            "sw_version": "1.0.0",
        }
