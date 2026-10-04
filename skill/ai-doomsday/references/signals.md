# Signals, thresholds, scale and triggers

Max points in [brackets]; they must match `scripts/config.py`. Update cadence in
parentheses. Record status in report.json as `green`/`yellow`/`red`, and for qualitative
signals as `q0`/`q25`/`q50`/`q75`/`q100`. "bp" = basis points (Polish report: "pb").

## Contents
- A. Debt [300]
- B. Capex and cash flows [150]
- C. Demand and adoption [150]
- D. Hardware [150]
- E. Macro [100]
- F. Power and infrastructure [50]
- G. Token prices and open-weight models [100]
- Scale, triggers

## A. Debt [300]
A1. US 10Y yield (market close; confirm with FRED DGS10; daily) [50]
    🟢 < 4.5% | 🟡 4.5–5.25% | 🔴 > 5.25%
A2. AI premium: spread of AI companies' debt minus the spread of the whole investment-grade
    bond market (news: Goldman, ICE; reference: FRED BAMLC0A0CM) [40]
    🟢 < 20 bp | 🟡 20–50 bp | 🔴 > 50 bp
A3. High-yield spread (FRED: BAMLH0A0HYM2, daily) [40]
    🟢 < 3.5% | 🟡 3.5–5% | 🔴 > 5%
A4. Debt share of hyperscaler capex funding (quarterly) [30]
    🟢 < 20% | 🟡 20–40% | 🔴 > 40%
A5. AI sector CDS: number of large AI issuers (hyperscalers, Oracle, neoclouds) with a
    record 5-year CDS in the last month (news) [35]
    🟢 0 | 🟡 1–2 | 🔴 3+ or CDS doubling within 3 months
A6. Data-center securitization and private credit: data-center ABS/CMBS issuance volume,
    their spreads vs other ABS, changes in standards (regulation, ratings), share of risk
    retained by sponsors in new deals (reference: ~30% in 2026), scope of regulatory
    exemptions (e.g. the SEC position of 29 Jul 2026 exempting some data-center
    securitizations from ABS rules), SPV structures financing GPUs alone (e.g. Amazon's
    USD 8bn SPV of 2 Oct 2026) [30]
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
A7. Neocloud premium: cost of neocloud debt and GPU-backed loans (company filings, CDS,
    news on financing terms) minus the investment-grade yield (10Y + IG spread) [35]
    🟢 < 200 bp | 🟡 200–500 bp | 🔴 > 500 bp
    Use only readings no older than 90 days.
A8. Credit events (news from the last 30 days) [40]
    🟢 none
    🟡 LIGHT: postponed or withdrawn IPO or issue, provided valuation and access to funding
       did not fall at the same time (e.g. a new round at a higher valuation); a single
       postponed bond issue
    🔴 HEAVY: downgrade of an AI company to speculative grade; failed refinancing or
       emergency issue by a neocloud; default on a GPU-backed loan, an Nvidia guarantee
       being called, or a margin call on a loan secured by GPUs or lab equity; redemption
       limits at a private credit fund or BDC exposed to AI or data centers; downgrade,
       default, or a mark clearly below par on a data-center ABS/CMBS tranche; an AI lab
       round or IPO at a clearly lower valuation
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
    Ramp: 🟢 < 10% | 🟡 10–20% | 🔴 > 20%
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
Band names in the Polish report (the script also writes `band_en`):
    0–200  Zdrowy boom (Healthy boom): easy financing, rising capex, hardware shortage
  201–400  Przegrzanie (Overheating): rising debt and cost of money, cracks in weaker links
  401–600  Pęknięcia (Cracks): refinancing problems, downgrades, weakening bond demand,
           price pressure on labs
  601–800  Korekta (Correction): first capex cuts, falling GPU rates and DRAM prices,
           failed rounds/IPOs, price war
  801–1000 Krach (Crash): mass capex cuts, failures of leveraged players, hardware glut
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
