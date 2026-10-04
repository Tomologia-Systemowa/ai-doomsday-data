# ai-doomsday-data

Dane skali „AI Doomsday” (0–1000) – codzienny monitoring ryzyka pęknięcia bańki inwestycyjnej w AI. Pliki czyta strona osmanowski.net. **To nie jest porada inwestycyjna.**

## Pliki
- `data/latest.json` – ostatni raport (nadpisywany przy każdym przebiegu).
- `data/history.json` – historia wyników (`series`, tylko dopisywana) i zdarzeń (`events`) oraz stała definicja skali (`scale`).
- `state/` – pliki stanu analityka (tabela sygnałów, historia do progów, log raportów).

Adresy raw:
- https://raw.githubusercontent.com/theluckyprogrammer/ai-doomsday-data/main/data/latest.json
- https://raw.githubusercontent.com/theluckyprogrammer/ai-doomsday-data/main/data/history.json

## latest.json
`schema_version` ("1.1"; pola tekstowe mają odpowiedniki `_en`: headline, band, name, note, title, disclaimer), `date`, `report_type` (`full`|`short`), `score`, `band`, `change_vs_previous`, `headline`, `triggers[]`, `heavy_credit_event` (bool), `skipped_signals[]`, `signals[]`, `calendar[]` (`{date,title}`), `disclaimer`.

Element `signals[]`: `id` (A1–G4), `category` (A–G), `name`, `value` (null dla danych licencjonowanych: ICE BofA, płatne indeksy), `unit`, `as_of`, `status`, `points`, `max_points` (z uwzględnieniem redystrybucji), `preliminary`, `source`, opcjonalnie `note`, `expires`, `conflict_of_interest`.

`status`: `green` | `yellow` | `red` | `skipped` | `q0` | `q25` | `q50` | `q75` | `q100` (q = ocena jakościowa, % budżetu sygnału).

## history.json
- `updated_at` – ISO 8601 ze strefą (+01:00/+02:00).
- `scale` – `bands` (przedziały) i `categories` (A–G z budżetami: 300/150/150/150/100/50/100).
- `series[]` – `{date, kind: full|short|baseline, score, band, categories{A..G}, headline}`.
- `events[]` – `{date, type, signal, severity, title, source, expires}`; `type`: credit_light, credit_heavy, rating, fed_hike, fed_cut, infra, financing, threshold_cross, trigger, pricing, model_release; `severity`: info, light, medium, heavy, trigger.
