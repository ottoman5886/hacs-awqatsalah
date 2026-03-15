"""Sensoren für AwqatSalah Integration."""
import logging
from datetime import datetime, timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_CITY_NAME,
    CONF_LANGUAGE,
    PRAYER_SENSORS,
    DAILY_CONTENT_SENSORS,
    EID_SENSORS,
    SENSOR_NAMES,
    SENSOR_MOON_URL,
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

    entities = []

    # Gebetszeiten Sensoren
    for sensor_key in PRAYER_SENSORS:
        if sensor_key == SENSOR_MOON_URL:
            entities.append(AwqatSalahImageSensor(coordinator, sensor_key, language, city_name, entry.entry_id))
        else:
            entities.append(AwqatSalahSensor(coordinator, sensor_key, language, city_name, entry.entry_id))

    # DailyContent Sensoren
    for sensor_key in DAILY_CONTENT_SENSORS:
        entities.append(AwqatSalahSensor(coordinator, sensor_key, language, city_name, entry.entry_id))

    # Eid Sensoren
    for sensor_key in EID_SENSORS:
        entities.append(AwqatSalahSensor(coordinator, sensor_key, language, city_name, entry.entry_id))

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
        return f"{DOMAIN}_{self._entry_id}_{self._sensor_key}"

    @property
    def name(self) -> str:
        names = SENSOR_NAMES.get(self._language, SENSOR_NAMES["de"])
        sensor_name = names.get(self._sensor_key, self._sensor_key)
        return f"{sensor_name} ({self._city_name})"

    @property
    def state(self) -> str:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._sensor_key, "")

    @property
    def extra_state_attributes(self) -> dict:
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
        icons = {
            "imsak": "mdi:weather-night",
            "sabah": "mdi:weather-sunset-up",
            "gunes": "mdi:white-balance-sunny",
            "ogle": "mdi:weather-sunny",
            "ikindi": "mdi:weather-sunny-alert",
            "aksam": "mdi:weather-sunset-down",
            "yatsi": "mdi:weather-night",
            "astronomical_sunrise": "mdi:weather-sunset-up",
            "astronomical_sunset": "mdi:weather-sunset-down",
            "qibla_time": "mdi:compass",
            "hijri_date_short": "mdi:calendar-month",
            "hijri_date_long": "mdi:calendar-month",
            "gregorian_date_long": "mdi:calendar",
            "verse": "mdi:book-open-variant",
            "verse_source": "mdi:book-open-variant",
            "hadith": "mdi:book-open-page-variant",
            "hadith_source": "mdi:book-open-page-variant",
            "pray": "mdi:hands-pray",
            "pray_source": "mdi:hands-pray",
            "eid_al_fitr_date": "mdi:star-crescent",
            "eid_al_fitr_time": "mdi:star-crescent",
            "eid_al_fitr_hijri": "mdi:star-crescent",
            "eid_al_adha_date": "mdi:star-crescent",
            "eid_al_adha_time": "mdi:star-crescent",
            "eid_al_adha_hijri": "mdi:star-crescent",
        }
        return icons.get(self._sensor_key, "mdi:clock")

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=f"AwqatSalah - {self._city_name}",
            manufacturer="Diyanet İşleri Başkanlığı",
            model="Gebetszeiten API",
            sw_version="1.1.0",
            entry_type="service",
        )


class AwqatSalahImageSensor(AwqatSalahSensor):
    """Mond Bild Sensor."""

    @property
    def state(self) -> str:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._sensor_key, "")

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        attrs["entity_picture"] = self.coordinator.data.get(self._sensor_key, "") if self.coordinator.data else ""
        return attrs

    @property
    def icon(self) -> str:
        return "mdi:moon-waxing-crescent"
