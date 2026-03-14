# AwqatSalah – Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Home Assistant Integration für Diyanet Gebetszeiten via [AwqatSalah API](https://github.com/ottoman5886/AwqatSalah).

## Features

- 🕌 27 Sensoren (Gebetszeiten, Hijri Datum, DailyContent, Eid)
- 🌍 Mehrsprachig (Türkisch, Deutsch, Englisch, Arabisch)
- 🔍 Stadt-Suche über Land → Region → Stadt
- 💾 Restart-resistenter Cache (HA Storage)
- 📅 Automatischer Jahres- und Monats-Refresh
- 🌙 Mondphase Sensor

---

## Installation

### Via HACS (empfohlen)

1. HACS → Integrationen → ⋮ → **Custom Repositories**
2. URL: `https://github.com/ottoman5886/hacs-awqatsalah`
3. Kategorie: **Integration**
4. **Add** → **Download**
5. Home Assistant neu starten

### Manuell

Ordner `custom_components/awqatsalah` in `/config/custom_components/` kopieren → HA neu starten.

---

## Einrichtung

1. **Einstellungen** → **Geräte & Dienste** → **Integration hinzufügen**
2. Nach **AwqatSalah** suchen
3. API Key eingeben (von deiner AwqatSalah API Instanz)
4. Land → Region → Stadt auswählen
5. Sprache auswählen

---

## Sensoren

### Gebetszeiten

| Sensor | Türkisch | Deutsch | Englisch |
|--------|----------|---------|----------|
| `sensor.imsak` | İmsak | Imsak | Imsak |
| `sensor.sabah` | Sabah | Morgengebet | Fajr |
| `sensor.gunes` | Güneş | Sonnenaufgang | Sunrise |
| `sensor.ogle` | Öğle | Mittagsgebet | Dhuhr |
| `sensor.ikindi` | İkindi | Nachmittagsgebet | Asr |
| `sensor.aksam` | Akşam | Abendgebet | Maghrib |
| `sensor.yatsi` | Yatsı | Nachtgebet | Isha |

> **Sabah** wird automatisch berechnet: Güneş − 60 Minuten

### Zusätzliche Zeiten

| Sensor | Beschreibung |
|--------|--------------|
| `sensor.astronomical_sunrise` | Astronomischer Sonnenaufgang |
| `sensor.astronomical_sunset` | Astronomischer Sonnenuntergang |
| `sensor.qibla_time` | Kibla Zeit |

### Datum

| Sensor | Beschreibung | Beispiel |
|--------|--------------|---------|
| `sensor.hijri_date_short` | Hijri Datum (kurz) | 23.9.1447 |
| `sensor.hijri_date_long` | Hijri Datum (lang) | 23 Ramazan 1447 |
| `sensor.gregorian_date_long` | Gregorianisches Datum | 13 Mart 2026 Cuma |
| `sensor.moon_url` | Mondphase Bild URL | https://... |

### Täglicher Inhalt (DailyContent)

| Sensor | Beschreibung |
|--------|--------------|
| `sensor.verse` | Tagesvers (Koran) |
| `sensor.verse_source` | Quellenangabe Vers |
| `sensor.hadith` | Tageshadith |
| `sensor.hadith_source` | Quellenangabe Hadith |
| `sensor.pray` | Tagesgebet |
| `sensor.pray_source` | Quellenangabe Gebet |

### Feiertage (Eid)

| Sensor | Beschreibung |
|--------|--------------|
| `sensor.eid_al_fitr_date` | Zuckerfest Datum |
| `sensor.eid_al_fitr_time` | Zuckerfest Uhrzeit |
| `sensor.eid_al_fitr_hijri` | Zuckerfest Hijri Datum |
| `sensor.eid_al_adha_date` | Opferfest Datum |
| `sensor.eid_al_adha_time` | Opferfest Uhrzeit |
| `sensor.eid_al_adha_hijri` | Opferfest Hijri Datum |

---

## Cache Strategie

```
HA Start:
  1. HA Storage laden (restart-resistent)
  2. Jahres-Cache vorhanden? → direkt nutzen
  3. API aufrufen:
     - Yearly verfügbar → ganzes Jahr cachen
     - Yearly nicht verfügbar → Monthly cachen
  4. Monatswechsel → automatisch neuen Monat laden
  5. Jahreswechsel → automatisch neues Jahr laden

DailyContent → täglich neu von API
Eid → jährlich neu von API
```

---

## Voraussetzungen

- Home Assistant 2026.2.0+
- HACS installiert
- Eigene [AwqatSalah API](https://github.com/ottoman5886/AwqatSalah) Instanz
- API Key

---

## Bekannte Einschränkungen

- Diyanet DateRange API: max. 10 Anfragen/Monat pro Stadt
- Bei Limit-Erreichen automatischer Fallback auf Monthly Daten

---

## Lizenz

MIT License
