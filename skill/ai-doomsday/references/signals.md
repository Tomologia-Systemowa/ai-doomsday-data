# Signals, thresholds, scale and triggers

Max points in [brackets]; they must match `scripts/config.py`. Update cadence in
parentheses. Record status in report.json as `green`/`yellow`/`red`, and for qualitative
signals as `q0`/`q25`/`q50`/`q75`/`q100`. "bp" = basis points (Polish report: "pb").

## Contents
- Counting rules
- A. Debt [300]
- B. Capex and cash flows [150]
- C. Demand and adoption [150]
- D. Hardware [150]
- E. Macro [100]
- F. Power and infrastructure [50]
- G. Token prices and open-weight models [100]
- Scale, triggers

## Counting rules
One event, one signal. A discrete event – a deal, default, downgrade, regulatory change,
project delay, price-list change, model release – raises the status of one signal only: its
primary signal below. Other signals whose definitions mention it record it in `note`
without a status change. Measured series (yields, spreads, CDS levels, rental rates,
prices, reported capex and FCF, index readings) are not events: each reading counts in its
own signal, even when the same news moved several of them. Triggers and
`heavy_credit_event` follow the primary signal.
    credit events listed in A8 (downgrades, defaults, failed refinancing, margin calls,
      redemption limits, ABS/CMBS tranche marks, down rounds, tenant force majeure or
      payment deferral claims)                                          → A8
    securitizations, SPVs, sale-leasebacks, private-credit deals, ABS rules and
      exemptions                                                        → A6
    capex guidance changes                                              → B1
    server depreciation period changes                                  → D4
    data-center project delays and cancellations without a payment claim → F1
    Fed decisions and statements                                        → E3
    frontier model price-list changes                                   → G2
    open-weight model releases                                          → G4
An event that fits none of these counts in the signal whose definition names it most
directly; say which in `note`.

Correlated series. A2, A3, A5 and A7 are different readings of one price of credit risk
(group `credit_spreads`). When two or more of them reach a higher status within 14 days of
each other for one cause, declare a joint move in report.json `correlated_moves` with that
cause. The script then counts the member with the largest rise in full; for the others
their level before the move counts in full and their rise in it at 50% (🟡→🔴 on 40 points:
20 + 10 = 30). This holds for as long as each keeps the status it had in the move; a member whose status changes
leaves it, and the move ends below two members. Signals of the group that move for
different reasons (e.g. A7 on one neocloud's refinancing, A3 on the broad market) are not
a joint move and count in full. Joint or not, report the A2/A3 reading as sector or
systemic stress (interpretation under A).

## A. Debt [300]
A1. US 10Y yield (market close; confirm with FRED DGS10; daily) [50]
    🟢 < 4.5% | 🟡 4.5–5.25% | 🔴 > 5.25%
A2. AI premium: spread of AI companies' debt minus the spread of the whole investment-grade
    bond market (news: Goldman, ICE; reference: FRED BAMLC0A0CM) [40]
    🟢 < 20 bp | 🟡 20–50 bp | 🔴 > 50 bp
A3. High-yield spread (FRED: BAMLH0A0HYM2, daily) [40]
    🟢 < 3.5% | 🟡 3.5–5% | 🔴 > 5%
A4. Debt share of hyperscaler capex funding (quarterly) [30]
    🟢 < 20% | 🟡 20–40%, or > 40% but at most 5 pp above its average of the previous 4
    quarters | 🔴 > 40% and more than 5 pp above that average
    The relative part keeps a share that has settled at a new, higher level from staying
    🔴 for good. With fewer than 4 previous quarters in "HISTORIA DO PROGÓW", use > 40% = 🔴
    and set `preliminary: true`.
    Off-balance-sheet structures (SPVs or sale-leasebacks of GPUs or data centers, e.g.
    Amazon's ~USD 8bn GPU SPV reported by the FT on 2 Oct 2026) are debt-like funding that
    the reported debt share does not capture. Note them in `note` with amount, date and
    status (explored / closed); they don't change the debt share or the A4 status – under
    the counting rules such a deal counts in A6.
A5. AI sector CDS: number of large AI issuers (hyperscalers, Oracle, neoclouds) with a
    record 5-year CDS in the last month (news) [35]
    🟢 0 | 🟡 1–2 | 🔴 3+ or CDS doubling within 3 months
A6. Data-center securitization and private credit: data-center ABS/CMBS issuance volume,
    their spreads vs other ABS, changes in standards (regulation, ratings), share of risk
    retained by sponsors in new deals (reference: ~30% in 2026), scope of regulatory
    exemptions (e.g. the SEC position of 29 Jul 2026 exempting some data-center
    securitizations from ABS rules), SPV structures financing GPUs alone (e.g. Amazon's
    USD 8bn SPV of 2 Oct 2026; see also A4, D4) [30]
    🟢 stable spreads, no loosening of standards, sponsor risk retention ≥ 25% |
    🟡 fast volume growth (> 30% y/y), loosening standards, or risk retention down to
       10–25% |
    🔴 widening data-center ABS/CMBS spreads, risk retention < 10%, or regulatory exemptions
       extended to securitizations of GPUs alone or other fast-depreciating assets
    A regulatory exemption covering data-center securitizations in general counts as
    loosening standards (🟡). 🔴 requires one of these, confirmed by a reading: data-center
    ABS/CMBS spreads widening vs other ABS over at least two readings; actual risk retention
    below 10% in closed deals; or an exemption applied to a closed securitization of GPUs
    alone or other fast-depreciating assets. Deals that are only being explored or
    negotiated stay 🟡 and go into `note`.
    A status based on an event (a regulatory change or exemption, loosening of standards,
    risk retention in a closed deal, an exemption applied to a closed deal) holds for 90
    days from the event; give its date in `note`. After that the signal falls back to what
    its measured readings (spreads, issuance volume, risk retention in recent deals)
    support, unless a new event confirms the status.
A7. Neocloud premium: cost of neocloud debt and GPU-backed loans (company filings, CDS,
    news on financing terms) minus the investment-grade yield (10Y + IG spread) [35]
    🟢 < 200 bp | 🟡 200–500 bp | 🔴 > 500 bp
    Use only readings no older than 90 days.
A8. Credit events (news from the last 30 days) [40]
    🟢 none
    🟡 LIGHT: postponed or withdrawn IPO or issue, provided valuation and access to funding
       did not fall at the same time (e.g. a new round at a higher valuation); a single
       postponed bond issue; a tenant invoking force majeure or asking to defer payments
       on a debt-financed data-center project
    🔴 HEAVY: downgrade of an AI company to speculative grade; failed refinancing or
       emergency issue by a neocloud; default on a GPU-backed loan, an Nvidia guarantee
       being called, or a margin call on a loan secured by GPUs or lab equity; redemption
       limits at a private credit fund or BDC exposed to AI or data centers; downgrade,
       default, or a mark clearly below par on a data-center ABS/CMBS tranche; an AI lab
       round or IPO at a clearly lower valuation; such a force majeure or deferral claim
       once the landlord accepts it, payments are actually withheld, or the project's debt
       is marked down or downgraded
    Heavy event: set `heavy_credit_event: true` (the script lifts category A to at least
    210) and run a full report.
Interpretation: high AI premium (A2) with a low junk spread (A3) = sector stress; both
rising = systemic stress.

## B. Capex and cash flows [150]
B1. Capex guidance of Alphabet, Microsoft, Amazon, Meta, Oracle (quarterly; between
    earnings only material news) [50]
    🟢 rising or unchanged | 🟡 growth paused at 2+ companies | 🔴 guidance cut by a major
    hyperscaler (not when the cut is purely an accounting change)
B2. Hyperscaler stocks vs S&P 500 (e.g. MAGS ETF vs S&P 500) [30]
    🟢 outperforming YTD | 🟡 underperforming by 0–10 pp | 🔴 underperforming by > 10 pp
B3. Combined free cash flow (FCF) of Alphabet, Microsoft, Amazon and Meta as % of their
    combined capex (quarterly, from filings; state which capex definition each company
    uses) [70]
    🟢 > 25% | 🟡 0–25% | 🔴 < 0 (combined negative)

## C. Demand and adoption [150]
C1. Ramp AI Index: % of businesses paying, spend per employee (median, top 10%, top 1%)
    (monthly/weekly) [50]
    Median: 🟢 rising | 🟡 flat 2+ months | 🔴 falling 2+ months
C2. Census BTOS: % of firms using AI (biweekly) [25]
    🟢 rising | 🟡 flat 2+ readings | 🔴 falling 2+ readings
C3. Lab revenue (run-rate) and cloud growth (news, quarterly) [35] – qualitative
C4. Deployment ROI vs adoption (quarterly or on new surveys): share of firms reporting a
    measurable AI impact on EBIT and share abandoning most AI initiatives [40]
    🟢 ROI rising, abandonment falling | 🟡 stable or mixed | 🔴 ROI falling and
    abandonment rising

## D. Hardware [150]
D1. H100/B200 GPU rental rates: spot/on-demand and 1-year+ contracts (weekly; e.g. Ornn
    OCPI, Silicon Data) [45]
    🟢 rising | 🟡 flat 2+ months, or spot down ≥ 15% in a month with stable contracts (early
    warning: smaller providers dumping capacity) | 🔴 contracts down 3 months in a row, or
    spot and contracts falling together
D2. DRAM prices: contract and spot (TrendForce, weekly) [30]
    Contract: 🟢 rising | 🟡 flat | 🔴 falling
D3. Memory makers' inventories (DIO) and capex (quarterly) [20]
    🟢 inventories stable or falling | 🟡 rising 2 quarters in a row | 🔴 rising 3+
    quarters in a row
    Count consecutive quarterly increases in DIO for the same company. If makers disagree,
    use the one with the most quarters of history and say so in `note`; don't mix different
    makers in one series.
D4. GPU residual value: used H100 and A100 prices (Compute Exchange, Hashrate Index,
    ServerBuyback) and changes to server depreciation periods in hyperscaler filings [30]
    🟢 prices stable or rising | 🟡 down 15–30% in a quarter | 🔴 down > 30% in a quarter,
    or a hyperscaler shortens its depreciation period
    Valuations of installed GPUs in SPV or sale-leaseback deals (e.g. Amazon's GPU SPV) are
    market readings of residual value: once such a deal closes, record the implied value
    per GPU (or as % of purchase cost) with GPU model, date and source, and use it as a
    reading for D4: compare it with the market price of the same GPU model in the previous
    quarter and apply the thresholds to that change. The deal itself counts in A6 (counting
    rules). Deals only being explored go into `note`.
D5. Production bottlenecks (on TSMC and memory makers' earnings): CoWoS packaging
    capacity, DRAM wafer allocation to HBM [25]
    🟢 bottleneck persists (shortage continues) | 🟡 bottleneck easing with stable demand |
    🔴 bottleneck easing with weakening demand (oversupply risk)

## E. Macro [100]
E1. ISM Manufacturing PMI incl. prices index (1st business day of the month) [25]
    🟢 rising and > 50 | 🟡 falling but > 50 | 🔴 < 50
E2. 10Y–2Y curve (market close; confirm with FRED T10Y2Y) [25]. ALWAYS classify the move
    from the 2Y and 10Y changes over the last week and month:
    - steepening via falling 2Y (market expects cuts) = easing,
    - steepening via rising 10Y (term premium, inflation) = tightening financial
      conditions,
    - flattening or inversion via rising 2Y = tightening monetary policy,
    - flattening via falling 10Y = slowdown expectations.
    🟢 easing | 🟡 mixed | 🔴 tightening
    Don't treat every widening of the spread as positive.
E3. Fed policy: decisions, statements, market expectations for upcoming meetings (CME
    FedWatch, Kalshi), futures reaction after decisions [50]
    🟢 cuts or expected cuts | 🟡 rates on hold with no expected hikes | 🔴 a hike in the
    last 3 months, or the market pricing a hike at > 50%

## F. Power and infrastructure [50]
F1. Delayed/abandoned data-center projects, interconnection wait times for large loads
    (PJM, ERCOT), PJM auctions, cost and scale of behind-the-meter power, local opposition
    [50] – qualitative

## G. Token prices and open-weight models [100]
G1. Effective usage-weighted token price: Ramp AI Index, Silicon Data LLM Token
    Expenditure Index or similar (weekly/monthly) [25] – status per G INTERPRETATION:
    healthy adoption 🟢 | revenue pressure 🟡 | warning sign 🔴
G2. Frontier model price lists (OpenAI, Anthropic, Google, xAI): increases, cuts, end of
    promotional pricing, limit changes [25]
    🟢 stable or rising | 🟡 a cut at one major provider, or cuts only on cheaper models |
    🔴 cuts of ≥ 30% on frontier models at two or more major providers within a quarter
    (price war)
G3. Open-weight (incl. Chinese) model share of traffic: OpenRouter (weekly); share of
    businesses using open-source models in the Ramp AI Index (monthly) [20]
    Ramp: 🟢 < 10% | 🟡 10–20%, or > 20% but at most 3 pp above its average of the previous
    6 months | 🔴 > 20% and more than 3 pp above that average
    With fewer than 6 previous months in "HISTORIA DO PROGÓW", use > 20% = 🔴 and set
    `preliminary: true`.
G4. Quality gap between the best open-weight and best closed model: Artificial Analysis
    Intelligence Index (points and %), Epoch AI estimates (lag in months) (on new
    releases; at least weekly) [30]
    🟢 > 10% of index and > 9 months | 🟡 5–10% or 3–9 months | 🔴 < 5% or < 3 months
    Use the latest Artificial Analysis index version and state its number. Never compare
    across versions; on a version change say so and compare within one version only.
    Use each model's score at its highest available setting (e.g. max reasoning effort)
    and state the setting. Also report the gap vs the best closed model not made by
    Anthropic.
G INTERPRETATION – always together with C1:
- "Total spend" means the Ramp median spend per employee (C1). Moves of the top 10% /
  top 1% go into `note` only and do not change the G1 status.
- falling prices + rising total spend = healthy adoption,
- falling prices + flat spend = revenue pressure on providers,
- falling prices + falling spend = warning sign.
A rising open-weight share in developer traffic is a moderate signal; the same trend in
enterprise data (Ramp, surveys) is a strong signal.

## AI Doomsday scale (0–1000)
The score measures how much stress the signals show, not an event or its timing: a high
score means conditions in which a correction is more likely, not that one is happening or
when it will come. Bubbles can stay under high stress for years. Never present a band as a
forecast. Band names in the Polish report (the script also writes `band_en`), each with
its typical picture:
    0–200  Niskie napięcie (Low stress): easy financing, rising capex, hardware shortage
  201–400  Umiarkowane napięcie (Moderate stress): rising debt and cost of money, cracks in
           weaker links
  401–600  Podwyższone napięcie (Elevated stress): refinancing problems, downgrades,
           weakening bond demand, price pressure on labs
  601–800  Wysokie napięcie (High stress): first capex cuts, falling GPU rates and DRAM
           prices, failed rounds/IPOs, price war
  801–1000 Skrajne napięcie (Extreme stress): mass capex cuts, failures of leveraged
           players, hardware glut
Until 2026-10-06 the bands were called Zdrowy boom / Przegrzanie / Pęknięcia / Korekta /
Krach; the ranges did not change, so a different name for the same range is not a band
change.
A score within 15 points of a band boundary is "na granicy" (the script flags it).

## Triggers
Each lifts its category to at least 70% of its budget and forces a full report. In
report.json add each as `{"name": "<Polish>", "name_en": "<English>", "category": "X"}`.
- capex guidance cut by a major hyperscaler – 🔴 in B1 (B),
- Big Four combined FCF negative – 🔴 in B3 (B),
- GPU spot and contract rates falling together, or contracts down 3 months in a row –
  🔴 in D1 (D),
- a hyperscaler shortening its server depreciation period (D),
- Fed hike while 10Y > 5.25% (E),
- price war on frontier models – 🔴 in G2 (G),
- an open-weight model matching or beating the best closed model in the Artificial
  Analysis Intelligence Index (G).
Heavy credit events: see A8.
