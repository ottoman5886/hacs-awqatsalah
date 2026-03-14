"""Konstanten für AwqatSalah Integration."""

DOMAIN = "awqatsalah"
CONF_API_KEY = "api_key"
CONF_API_URL = "api_url"
CONF_CITY_ID = "city_id"
CONF_COUNTRY_ID = "country_id"
CONF_STATE_ID = "state_id"
CONF_CITY_NAME = "city_name"
CONF_LANGUAGE = "language"

DEFAULT_API_URL = "https://awqatsalah.onrender.com"
DEFAULT_SCAN_INTERVAL = 86400  # 1x täglich

# Sensor Namen (intern)
SENSOR_IMSAK = "imsak"
SENSOR_SABAH = "sabah"
SENSOR_GUNES = "gunes"
SENSOR_OGLE = "ogle"
SENSOR_IKINDI = "ikindi"
SENSOR_AKSAM = "aksam"
SENSOR_YATSI = "yatsi"

SENSORS = [
    SENSOR_IMSAK,
    SENSOR_SABAH,
    SENSOR_GUNES,
    SENSOR_OGLE,
    SENSOR_IKINDI,
    SENSOR_AKSAM,
    SENSOR_YATSI,
]

# Sprachen
LANGUAGES = {
    "tr": "Türkçe",
    "de": "Deutsch",
    "en": "English",
    "ar": "العربية",
}

# API Felder → Sensor Mapping
API_FIELD_MAP = {
    SENSOR_IMSAK: "fajr",
    SENSOR_GUNES: "sunrise",
    SENSOR_OGLE: "dhuhr",
    SENSOR_IKINDI: "asr",
    SENSOR_AKSAM: "maghrib",
    SENSOR_YATSI: "isha",
}

# Sensor Namen pro Sprache
SENSOR_NAMES = {
    "tr": {
        SENSOR_IMSAK: "İmsak",
        SENSOR_SABAH: "Sabah",
        SENSOR_GUNES: "Güneş",
        SENSOR_OGLE: "Öğle",
        SENSOR_IKINDI: "İkindi",
        SENSOR_AKSAM: "Akşam",
        SENSOR_YATSI: "Yatsı",
    },
    "de": {
        SENSOR_IMSAK: "Imsak",
        SENSOR_SABAH: "Morgengebet",
        SENSOR_GUNES: "Sonnenaufgang",
        SENSOR_OGLE: "Mittagsgebet",
        SENSOR_IKINDI: "Nachmittagsgebet",
        SENSOR_AKSAM: "Abendgebet",
        SENSOR_YATSI: "Nachtgebet",
    },
    "en": {
        SENSOR_IMSAK: "Imsak",
        SENSOR_SABAH: "Fajr",
        SENSOR_GUNES: "Sunrise",
        SENSOR_OGLE: "Dhuhr",
        SENSOR_IKINDI: "Asr",
        SENSOR_AKSAM: "Maghrib",
        SENSOR_YATSI: "Isha",
    },
    "ar": {
        SENSOR_IMSAK: "الإمساك",
        SENSOR_SABAH: "الفجر",
        SENSOR_GUNES: "الشروق",
        SENSOR_OGLE: "الظهر",
        SENSOR_IKINDI: "العصر",
        SENSOR_AKSAM: "المغرب",
        SENSOR_YATSI: "العشاء",
    },
}
