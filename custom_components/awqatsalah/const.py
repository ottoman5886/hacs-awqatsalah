"""Konstanten für AwqatSalah Integration."""

DOMAIN = "awqatsalah"
CONF_API_URL = "api_url"
CONF_CITY_ID = "city_id"
CONF_COUNTRY_ID = "country_id"
CONF_STATE_ID = "state_id"
CONF_CITY_NAME = "city_name"
CONF_LANGUAGE = "language"

# Flexible Auth – zwei optionale Header-Paare
CONF_HEADER1_NAME  = "header1_name"
CONF_HEADER1_VALUE = "header1_value"
CONF_HEADER2_NAME  = "header2_name"
CONF_HEADER2_VALUE = "header2_value"

# Legacy – damit bestehende Config Entries nicht brechen
CONF_API_KEY = "api_key"

DEFAULT_API_URL = "https://awqatsalah.onrender.com"
DEFAULT_SCAN_INTERVAL = 86400  # 1x täglich

# Sensor Keys
SENSOR_IMSAK = "imsak"
SENSOR_SABAH = "sabah"
SENSOR_GUNES = "gunes"
SENSOR_OGLE = "ogle"
SENSOR_IKINDI = "ikindi"
SENSOR_AKSAM = "aksam"
SENSOR_YATSI = "yatsi"
SENSOR_ASTRONOMICAL_SUNRISE = "astronomical_sunrise"
SENSOR_ASTRONOMICAL_SUNSET = "astronomical_sunset"
SENSOR_QIBLA_TIME = "qibla_time"
SENSOR_HIJRI_DATE_SHORT = "hijri_date_short"
SENSOR_HIJRI_DATE_LONG = "hijri_date_long"
SENSOR_GREGORIAN_DATE_LONG = "gregorian_date_long"
SENSOR_MOON_URL = "moon_url"

# DailyContent Sensor Keys
SENSOR_VERSE = "verse"
SENSOR_VERSE_SOURCE = "verse_source"
SENSOR_HADITH = "hadith"
SENSOR_HADITH_SOURCE = "hadith_source"
SENSOR_PRAY = "pray"
SENSOR_PRAY_SOURCE = "pray_source"

# Eid Sensor Keys
SENSOR_EID_AL_FITR_DATE = "eid_al_fitr_date"
SENSOR_EID_AL_FITR_TIME = "eid_al_fitr_time"
SENSOR_EID_AL_FITR_HIJRI = "eid_al_fitr_hijri"
SENSOR_EID_AL_ADHA_DATE = "eid_al_adha_date"
SENSOR_EID_AL_ADHA_TIME = "eid_al_adha_time"
SENSOR_EID_AL_ADHA_HIJRI = "eid_al_adha_hijri"

# Sensor Gruppen
PRAYER_SENSORS = [
    SENSOR_IMSAK,
    SENSOR_SABAH,
    SENSOR_GUNES,
    SENSOR_OGLE,
    SENSOR_IKINDI,
    SENSOR_AKSAM,
    SENSOR_YATSI,
    SENSOR_ASTRONOMICAL_SUNRISE,
    SENSOR_ASTRONOMICAL_SUNSET,
    SENSOR_QIBLA_TIME,
    SENSOR_HIJRI_DATE_SHORT,
    SENSOR_HIJRI_DATE_LONG,
    SENSOR_GREGORIAN_DATE_LONG,
    SENSOR_MOON_URL,
]

DAILY_CONTENT_SENSORS = [
    SENSOR_VERSE,
    SENSOR_VERSE_SOURCE,
    SENSOR_HADITH,
    SENSOR_HADITH_SOURCE,
    SENSOR_PRAY,
    SENSOR_PRAY_SOURCE,
]

EID_SENSORS = [
    SENSOR_EID_AL_FITR_DATE,
    SENSOR_EID_AL_FITR_TIME,
    SENSOR_EID_AL_FITR_HIJRI,
    SENSOR_EID_AL_ADHA_DATE,
    SENSOR_EID_AL_ADHA_TIME,
    SENSOR_EID_AL_ADHA_HIJRI,
]

SENSORS = PRAYER_SENSORS + DAILY_CONTENT_SENSORS + EID_SENSORS

# Sprachen
LANGUAGES = {
    "tr": "Türkçe",
    "de": "Deutsch",
    "en": "English",
    "ar": "العربية",
}

# API Felder → Sensor Mapping (Gebetszeiten)
API_FIELD_MAP = {
    SENSOR_IMSAK: "fajr",
    SENSOR_GUNES: "sunrise",
    SENSOR_OGLE: "dhuhr",
    SENSOR_IKINDI: "asr",
    SENSOR_AKSAM: "maghrib",
    SENSOR_YATSI: "isha",
    SENSOR_ASTRONOMICAL_SUNRISE: "astronomicalSunrise",
    SENSOR_ASTRONOMICAL_SUNSET: "astronomicalSunset",
    SENSOR_QIBLA_TIME: "qiblaTime",
    SENSOR_HIJRI_DATE_SHORT: "hijriDateShort",
    SENSOR_HIJRI_DATE_LONG: "hijriDateLong",
    SENSOR_GREGORIAN_DATE_LONG: "gregorianDateLong",
    SENSOR_MOON_URL: "shapeMoonUrl",
}

# DailyContent API Felder → Sensor Mapping
DAILY_CONTENT_FIELD_MAP = {
    SENSOR_VERSE: "verse",
    SENSOR_VERSE_SOURCE: "verseSource",
    SENSOR_HADITH: "hadith",
    SENSOR_HADITH_SOURCE: "hadithSource",
    SENSOR_PRAY: "pray",
    SENSOR_PRAY_SOURCE: "praySource",
}

# Eid API Felder → Sensor Mapping
EID_FIELD_MAP = {
    SENSOR_EID_AL_FITR_DATE: "eidAlFitrDate",
    SENSOR_EID_AL_FITR_TIME: "eidAlFitrTime",
    SENSOR_EID_AL_FITR_HIJRI: "eidAlFitrHijri",
    SENSOR_EID_AL_ADHA_DATE: "eidAlAdhaDate",
    SENSOR_EID_AL_ADHA_TIME: "eidAlAdhaTime",
    SENSOR_EID_AL_ADHA_HIJRI: "eidAlAdhaHijri",
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
        SENSOR_ASTRONOMICAL_SUNRISE: "Astronomik Gün Doğumu",
        SENSOR_ASTRONOMICAL_SUNSET: "Astronomik Gün Batımı",
        SENSOR_QIBLA_TIME: "Kıble Vakti",
        SENSOR_HIJRI_DATE_SHORT: "Hicri Tarih (Kısa)",
        SENSOR_HIJRI_DATE_LONG: "Hicri Tarih (Uzun)",
        SENSOR_GREGORIAN_DATE_LONG: "Miladi Tarih",
        SENSOR_MOON_URL: "Ay Şekli",
        SENSOR_VERSE: "Günün Ayeti",
        SENSOR_VERSE_SOURCE: "Ayet Kaynağı",
        SENSOR_HADITH: "Günün Hadisi",
        SENSOR_HADITH_SOURCE: "Hadis Kaynağı",
        SENSOR_PRAY: "Günün Duası",
        SENSOR_PRAY_SOURCE: "Dua Kaynağı",
        SENSOR_EID_AL_FITR_DATE: "Ramazan Bayramı Tarihi",
        SENSOR_EID_AL_FITR_TIME: "Ramazan Bayramı Saati",
        SENSOR_EID_AL_FITR_HIJRI: "Ramazan Bayramı Hicri",
        SENSOR_EID_AL_ADHA_DATE: "Kurban Bayramı Tarihi",
        SENSOR_EID_AL_ADHA_TIME: "Kurban Bayramı Saati",
        SENSOR_EID_AL_ADHA_HIJRI: "Kurban Bayramı Hicri",
    },
    "de": {
        SENSOR_IMSAK: "Imsak",
        SENSOR_SABAH: "Morgengebet",
        SENSOR_GUNES: "Sonnenaufgang",
        SENSOR_OGLE: "Mittagsgebet",
        SENSOR_IKINDI: "Nachmittagsgebet",
        SENSOR_AKSAM: "Abendgebet",
        SENSOR_YATSI: "Nachtgebet",
        SENSOR_ASTRONOMICAL_SUNRISE: "Astronomischer Sonnenaufgang",
        SENSOR_ASTRONOMICAL_SUNSET: "Astronomischer Sonnenuntergang",
        SENSOR_QIBLA_TIME: "Kibla Zeit",
        SENSOR_HIJRI_DATE_SHORT: "Hijri Datum (Kurz)",
        SENSOR_HIJRI_DATE_LONG: "Hijri Datum (Lang)",
        SENSOR_GREGORIAN_DATE_LONG: "Gregorianisches Datum",
        SENSOR_MOON_URL: "Mondphase",
        SENSOR_VERSE: "Tagesvers",
        SENSOR_VERSE_SOURCE: "Vers Quelle",
        SENSOR_HADITH: "Tageshadith",
        SENSOR_HADITH_SOURCE: "Hadith Quelle",
        SENSOR_PRAY: "Tagesgebet",
        SENSOR_PRAY_SOURCE: "Gebet Quelle",
        SENSOR_EID_AL_FITR_DATE: "Zuckerfest Datum",
        SENSOR_EID_AL_FITR_TIME: "Zuckerfest Uhrzeit",
        SENSOR_EID_AL_FITR_HIJRI: "Zuckerfest Hijri",
        SENSOR_EID_AL_ADHA_DATE: "Opferfest Datum",
        SENSOR_EID_AL_ADHA_TIME: "Opferfest Uhrzeit",
        SENSOR_EID_AL_ADHA_HIJRI: "Opferfest Hijri",
    },
    "en": {
        SENSOR_IMSAK: "Imsak",
        SENSOR_SABAH: "Fajr",
        SENSOR_GUNES: "Sunrise",
        SENSOR_OGLE: "Dhuhr",
        SENSOR_IKINDI: "Asr",
        SENSOR_AKSAM: "Maghrib",
        SENSOR_YATSI: "Isha",
        SENSOR_ASTRONOMICAL_SUNRISE: "Astronomical Sunrise",
        SENSOR_ASTRONOMICAL_SUNSET: "Astronomical Sunset",
        SENSOR_QIBLA_TIME: "Qibla Time",
        SENSOR_HIJRI_DATE_SHORT: "Hijri Date (Short)",
        SENSOR_HIJRI_DATE_LONG: "Hijri Date (Long)",
        SENSOR_GREGORIAN_DATE_LONG: "Gregorian Date",
        SENSOR_MOON_URL: "Moon Phase",
        SENSOR_VERSE: "Daily Verse",
        SENSOR_VERSE_SOURCE: "Verse Source",
        SENSOR_HADITH: "Daily Hadith",
        SENSOR_HADITH_SOURCE: "Hadith Source",
        SENSOR_PRAY: "Daily Prayer",
        SENSOR_PRAY_SOURCE: "Prayer Source",
        SENSOR_EID_AL_FITR_DATE: "Eid Al-Fitr Date",
        SENSOR_EID_AL_FITR_TIME: "Eid Al-Fitr Time",
        SENSOR_EID_AL_FITR_HIJRI: "Eid Al-Fitr Hijri",
        SENSOR_EID_AL_ADHA_DATE: "Eid Al-Adha Date",
        SENSOR_EID_AL_ADHA_TIME: "Eid Al-Adha Time",
        SENSOR_EID_AL_ADHA_HIJRI: "Eid Al-Adha Hijri",
    },
    "ar": {
        SENSOR_IMSAK: "الإمساك",
        SENSOR_SABAH: "الفجر",
        SENSOR_GUNES: "الشروق",
        SENSOR_OGLE: "الظهر",
        SENSOR_IKINDI: "العصر",
        SENSOR_AKSAM: "المغرب",
        SENSOR_YATSI: "العشاء",
        SENSOR_ASTRONOMICAL_SUNRISE: "الشروق الفلكي",
        SENSOR_ASTRONOMICAL_SUNSET: "الغروب الفلكي",
        SENSOR_QIBLA_TIME: "وقت القبلة",
        SENSOR_HIJRI_DATE_SHORT: "التاريخ الهجري (مختصر)",
        SENSOR_HIJRI_DATE_LONG: "التاريخ الهجري (كامل)",
        SENSOR_GREGORIAN_DATE_LONG: "التاريخ الميلادي",
        SENSOR_MOON_URL: "شكل القمر",
        SENSOR_VERSE: "آية اليوم",
        SENSOR_VERSE_SOURCE: "مصدر الآية",
        SENSOR_HADITH: "حديث اليوم",
        SENSOR_HADITH_SOURCE: "مصدر الحديث",
        SENSOR_PRAY: "دعاء اليوم",
        SENSOR_PRAY_SOURCE: "مصدر الدعاء",
        SENSOR_EID_AL_FITR_DATE: "تاريخ عيد الفطر",
        SENSOR_EID_AL_FITR_TIME: "وقت عيد الفطر",
        SENSOR_EID_AL_FITR_HIJRI: "عيد الفطر هجري",
        SENSOR_EID_AL_ADHA_DATE: "تاريخ عيد الأضحى",
        SENSOR_EID_AL_ADHA_TIME: "وقت عيد الأضحى",
        SENSOR_EID_AL_ADHA_HIJRI: "عيد الأضحى هجري",
    },
}
