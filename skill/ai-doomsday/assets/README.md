# ai-doomsday-data

Dane skali **AI Doomsday** (0–1000) – ocena ryzyka pęknięcia bańki inwestycyjnej w AI.
Aktualizowane automatycznie po każdym raporcie.
Repozytorium: {{REPO_URL}}

*AI Doomsday scale data (0–1000) – an assessment of AI investment bubble risk, updated after
every report. Every text field has an English counterpart with the `_en` suffix.*

**To nie jest porada inwestycyjna. / This is not investment advice.**

## Pliki / Files

| Plik | Opis | Adres raw |
|---|---|---|
| `data/latest.json` | Ostatni raport (nadpisywany) | {{RAW_BASE}}/data/latest.json |
| `data/scale.json` | Przedziały skali i budżety kategorii | {{RAW_BASE}}/data/scale.json |
| `data/history/index.json` | Spis plików dziennych z wynikiem (do wykresu) | {{RAW_BASE}}/data/history/index.json |
| `data/history/history-DD-MM-RRRR.json` | Jeden plik na dzień: wynik, zdarzenia i pełny tekst raportu | `{{RAW_BASE}}/data/history/<file z index.json>` |
| `data/history.json` | Przestarzały, nieaktualizowany (jeśli jeszcze istnieje) | – |

Kolejność chronologiczną wyznacza pole `date` w `index.json`, nie nazwa pliku
(format DD-MM-RRRR nie sortuje się alfabetycznie).

## Wspólne zasady

- `schema_version`: `"1.2"` (1.1 = bez bloku `report`; pliki starszych wersji mogą
  współistnieć z nowszymi).
- Każde pole tekstowe ma odpowiednik `*_en` (angielski): `headline`, `summary`,
  `curve_comment`, `weekly_analysis`, `title`, `name`, `note`, `band`, `reason`,
  `comment`, `disclaimer`; lista `triggers` ma odpowiednik `triggers_en`. Starsze pliki mogą
  nie mieć pól `_en` – wtedy użyj pola polskiego.
- Daty: `RRRR-MM-DD`; `updated_at`: ISO 8601 ze strefą Europa/Warszawa.
- Przedziały (`band` / `band_en`) opisują poziom napięcia w sygnałach, nie zdarzenie ani
  jego termin: Niskie napięcie / Low stress (0–200), Umiarkowane napięcie / Moderate stress
  (201–400), Podwyższone napięcie / Elevated stress (401–600), Wysokie napięcie / High
  stress (601–800), Skrajne napięcie / Extreme stress (801–1000). Do 2026-10-06 te same
  zakresy nazywały się Zdrowy boom / Przegrzanie / Pęknięcia / Korekta / Krach; starsze
  pliki historii zachowują dawne nazwy, więc przedział porównuj po zakresie (`score`),
  nie po nazwie.

Katalog `state/` (`state/historia-progow.json`) to roboczy stan skilla – krótkie serie
odczytów do progów trendowych. Nie jest przeznaczony do wyświetlania; dla danych
licencjonowanych zawiera tylko zmianę procentową i kierunek, bez poziomów.

## data/latest.json

| Pole | Opis |
|---|---|
| `date`, `report_type` | Data raportu; `full` albo `short` |
| `score`, `band`, `band_en` | Wynik 0–1000 i przedział |
| `change_vs_previous` | Zmiana względem poprzedniego wpisu (`null`, jeśli brak) |
| `headline`, `headline_en` | Najważniejsza zmiana, 1 zdanie |
| `summary`, `summary_en` | Podsumowanie raportu |
| `report_file` | Ścieżka pliku dziennego z pełnym tekstem raportu (względem `data/`) |
| `triggers[]`, `triggers_en[]` | Nazwy aktywnych wyzwalaczy |
| `heavy_credit_event` | Czy wystąpiło ciężkie zdarzenie kredytowe |
| `skipped_signals[]` | Sygnały pominięte (brak odczytu lub starszy niż 90 dni) |
| `correlated_moves[]` | Wspólne ruchy skorelowanych sygnałów (grupa `credit_spreads`: A2, A3, A5, A7): `{group, signals: {id: {status, from}}, since, reason, reason_en, discount_points}`. Członek z największym wzrostem liczy się w pełni; u pozostałych poziom sprzed ruchu liczy się w pełni, a wzrost w nim w 50% |
| `adjustments[]` | Korekty kategorii do progu minimalnego: `{category, points, floor, reason, reason_en}`. `score` = suma `points` sygnałów + suma `adjustments[].points` |
| `signals[]` | Sygnały A1–G4 (niżej) |
| `calendar[]` | `{date, title, title_en}` – najbliższe 2 tygodnie |
| `disclaimer`, `disclaimer_en` | Zastrzeżenie |

Pola sygnału: `id`, `category` (A–G), `name`, `name_en`, `value` (`null` przy danych
licencjonowanych, np. ICE BofA, i płatnych indeksach), `unit`, `as_of`, `status`,
`points`, `max_points` (po redystrybucji punktów pominiętych sygnałów; suma = 1000),
`preliminary`, `source`, opcjonalnie `note`/`note_en`, `expires`, `conflict_of_interest`,
`unconfirmed` (`{status, as_of, source, note, note_en, added_points}` – odczyt z jednego
źródła wtórnego, wliczany w 50% różnicy statusów przez 14 dni; `points` już go zawiera),
`status_since` (data, od której sygnał ma obecny status), `status_prev` (status
poprzedni), `correlated` (`{group,
discount_points}` – rabat za wspólny ruch skorelowanych sygnałów; `points` już go
uwzględnia).

`status`: `green` | `yellow` | `red` | `skipped` | `q0` | `q25` | `q50` | `q75` | `q100`
(q* – ocena jakościowa, odsetek budżetu sygnału).

## data/history/index.json

```json
{"schema_version": "1.2", "updated_at": "...",
 "files": [{"date": "RRRR-MM-DD", "file": "history-DD-MM-RRRR.json",
            "kind": "full|short|baseline", "score": 368, "band": "Przegrzanie"}]}
```

## data/history/history-DD-MM-RRRR.json

```json
{"schema_version": "1.2", "date": "RRRR-MM-DD", "updated_at": "...",
 "entry": {"kind": "full|short|baseline", "score": 368, "band": "...", "band_en": "...",
           "categories": {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0, "G": 0},
           "headline": "...", "headline_en": "..."},
 "events": [{"date": "RRRR-MM-DD", "type": "...", "signal": "A8", "severity": "...",
             "title": "...", "title_en": "...", "source": "<url>", "expires": "RRRR-MM-DD"}],
 "report": {
   "summary": "...", "summary_en": "...",
   "curve_comment": "...", "curve_comment_en": "...",
   "category_comments": {"A": {"comment": "...", "comment_en": "..."}},
   "top_signals": ["B3", "G4", "E1"],
   "near_boundary": false,
   "weekly_analysis": null, "weekly_analysis_en": null,
   "adjustments": [],
   "signals": [],
   "calendar": []
 }}
```

- `entry` może być `null` (dzień ze zdarzeniami bez raportu).
- `report` – pełny tekst raportu z danego dnia. Brak w plikach zasianych z historii
  i utworzonych przed wersją 1.2. W raporcie krótkim `curve_comment` i
  `category_comments` mogą być `null`. `weekly_analysis` wypełniony tylko w piątki.
  `signals` i `calendar` mają ten sam format co w `latest.json` (stan z danego dnia).
- `type`: credit_light | credit_heavy | rating | fed_hike | fed_cut | infra | financing |
  threshold_cross | trigger | pricing | model_release.
- `severity`: info | light | medium | heavy | trigger.

## data/scale.json

Przedziały (`bands[]`: `min`, `max`, `band`, `band_en`) i kategorie
(`categories`: `name`, `name_en`, `budget`). Suma budżetów = 1000.
