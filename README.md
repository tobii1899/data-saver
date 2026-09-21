# Options Chain Collector

Sammelt täglich nach US-Börsenschluss die aktuellen Optionsketten für:
**AAPL · GLD · NVDA · SPY · TSLA**

Läuft vollautomatisch via GitHub Actions — kostenlos, kein Server nötig.

---

## Ordnerstruktur

```
data/
  AAPL/
    2026-09-22.csv
    2026-09-23.csv
    ...
  GLD/
  NVDA/
  SPY/
  TSLA/
  index.json        ← Übersicht aller gesammelten Tage
```

Jede CSV enthält:

| Spalte | Bedeutung |
|---|---|
| `symbol` | Ticker |
| `snapshot_date` | Datum des Snapshots |
| `spot` | Kurs des Underlyings beim Snapshot |
| `expiry` | Verfallsdatum der Option |
| `right` | C = Call, P = Put |
| `strike` | Strike-Preis |
| `bid` / `ask` | Geld- / Briefkurs |
| `open_interest` | Offene Kontrakte — **das wichtigste für IV Walls** |
| `implied_vol` | Implizite Volatilität |
| `volume` | Tagesvolumen |

---

## Setup (einmalig, ~3 Minuten)

### 1. Repository auf GitHub erstellen

- github.com → **New repository**
- Name: `options-collector`
- **Private** (empfohlen — deine Daten bleiben bei dir)
- Ohne README erstellen (haben wir schon)

### 2. Diesen Code hochladen

```powershell
cd C:\Pfad\zu\options-collector
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/DEIN-USERNAME/options-collector.git
git push -u origin main
```

### 3. GitHub Actions aktivieren

- Auf GitHub: **Actions** Tab → "I understand my workflows, go ahead and enable them"

### 4. Ersten manuellen Run starten (Test)

- Actions → **Daily Option Chain Collector** → **Run workflow** → **Run workflow**
- Nach ~30 Sekunden siehst du die gesammelten CSVs im `data/` Ordner

Ab dann läuft es jeden Werktag um **21:00 UTC (= 16:00 ET)** automatisch.

---

## Lokal testen

```powershell
pip install yfinance pandas
python scripts/collect.py
```

---

## Nach 3-6 Monaten

Du hast dann echte historische Optionsketten und kannst damit den
iv-wall-quant Backtester mit echten Wall-Levels füttern statt modellierten.
