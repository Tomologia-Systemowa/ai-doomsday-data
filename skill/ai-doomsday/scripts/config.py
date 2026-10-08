"""AI Doomsday constants: budgets, signals, bands, statuses.

When changing max points or signal names, update references/signals.md too
(both places must agree).
"""

SCHEMA_VERSION = "1.2"
TZ = "Europe/Warsaw"
DISCLAIMER = "To nie jest porada inwestycyjna."
DISCLAIMER_EN = "This is not investment advice."

BUDGETS = {"A": 300, "B": 150, "C": 150, "D": 150, "E": 100, "F": 50, "G": 100}

CATEGORY_NAMES = {
    "A": ("Dług", "Debt"),
    "B": ("Capex i przepływy", "Capex and cash flows"),
    "C": ("Popyt i adopcja", "Demand and adoption"),
    "D": ("Sprzęt", "Hardware"),
    "E": ("Makro", "Macro"),
    "F": ("Energia i infrastruktura", "Power and infrastructure"),
    "G": ("Ceny tokenów i modele open-weight", "Token prices and open-weight models"),
}

# id -> (Polish name, English name, base max points)
SIGNALS = {
    "A1": ("Rentowność 10Y USA", "US 10Y Treasury yield", 50),
    "A2": ("Premia AI w spreadach IG", "AI premium in IG spreads", 40),
    "A3": ("Spread obligacji śmieciowych", "High-yield spread", 40),
    "A4": ("Udział długu w finansowaniu capeksu hiperskalerów", "Debt share of hyperscaler capex funding", 30),
    "A5": ("CDS sektora AI", "AI sector CDS", 35),
    "A6": ("Sekurytyzacja i private credit centrów danych", "Data center securitization and private credit", 30),
    "A7": ("Premia neocloudów", "Neocloud funding premium", 35),
    "A8": ("Zdarzenia kredytowe", "Credit events", 40),
    "B1": ("Prognozy capeksu hiperskalerów", "Hyperscaler capex guidance", 50),
    "B2": ("Kursy hiperskalerów vs S&P 500", "Hyperscaler stocks vs S&P 500", 30),
    "B3": ("FCF wielkiej czwórki jako % capeksu", "Big Four FCF as % of capex", 70),
    "C1": ("Ramp AI Index", "Ramp AI Index", 50),
    "C2": ("Census BTOS: adopcja AI", "Census BTOS: AI adoption", 25),
    "C3": ("Przychody laboratoriów i wzrost chmur", "Lab revenue and cloud growth", 35),
    "C4": ("Zwrot z wdrożeń vs adopcja", "Deployment ROI vs adoption", 40),
    "D1": ("Stawki wynajmu GPU", "GPU rental rates", 45),
    "D2": ("Ceny DRAM", "DRAM prices", 30),
    "D3": ("Zapasy i capex producentów pamięci", "Memory makers' inventories and capex", 20),
    "D4": ("Wartość rezydualna GPU", "GPU residual value", 30),
    "D5": ("Wąskie gardła produkcji", "Production bottlenecks", 25),
    "E1": ("ISM PMI przemysłu", "ISM Manufacturing PMI", 25),
    "E2": ("Krzywa 10Y–2Y", "10Y–2Y yield curve", 25),
    "E3": ("Polityka Fed", "Fed policy", 50),
    "F1": ("Energia i infrastruktura centrów danych", "Data center power and infrastructure", 50),
    "G1": ("Efektywna cena tokena", "Effective token price", 25),
    "G2": ("Cenniki czołowych modeli", "Frontier model pricing", 25),
    "G3": ("Udział modeli open-weight", "Open-weight model share", 20),
    "G4": ("Luka jakości open-weight vs zamknięte", "Open-weight vs closed quality gap", 30),
}

# Signals whose raw values are never published in the repo (ICE BofA licence).
DEFAULT_RESTRICTED = {"A2", "A3"}

STATUS_SHARE = {
    "green": 0.0, "yellow": 0.5, "red": 1.0,
    "q0": 0.0, "q25": 0.25, "q50": 0.5, "q75": 0.75, "q100": 1.0,
    "skipped": None,
}
STATUS_EMOJI = {
    "green": "🟢", "yellow": "🟡", "red": "🔴", "skipped": "⚪",
    "q0": "q0", "q25": "q25", "q50": "q50", "q75": "q75", "q100": "q100",
}

# (from, to, Polish, English)
BANDS = [
    (0, 200, "Zdrowy boom", "Healthy boom"),
    (201, 400, "Przegrzanie", "Overheating"),
    (401, 600, "Pęknięcia", "Cracks"),
    (601, 800, "Korekta", "Correction"),
    (801, 1000, "Krach", "Crash"),
]
BAND_BOUNDARIES = [200, 400, 600, 800]
NEAR_BOUNDARY = 15

TRIGGER_FLOOR_SHARE = 0.7      # trigger: category >= 70% of budget
HEAVY_CREDIT_FLOOR_A = 210     # heavy credit event: A >= 210
STALE_DAYS = 90
UNCONFIRMED_SHARE = 0.5       # single-source reading: half of the gap to its status
UNCONFIRMED_MAX_DAYS = 14     # ...and only while it is at most 14 days old
REVIEW_SCORE = 601            # calibration review: score at or above this...
REVIEW_DAYS = 90              # ...for this many days, or a signal at REVIEW_SHARE+ that long
REVIEW_SHARE = 0.75           # red, q75, q100

# Correlated measured series: readings of the same underlying price of risk. When signals
# of a group rise together for one reason (declared in report.json "correlated_moves"),
# the member with the largest rise counts in full; for the others only CORRELATED_SHARE of
# their rise in that move counts (their level before the move counts in full), for as
# long as they keep the status they had in it.
CORRELATION_GROUPS = {
    "credit_spreads": ("A2", "A3", "A5", "A7"),
}
CORRELATION_GROUP_NAMES = {"credit_spreads": ("spready kredytowe", "credit spreads")}
CORRELATED_SHARE = 0.5        # other members: 50% of their rise in the joint move
CORRELATED_WINDOW_DAYS = 14   # "together": each status change at most 14 days old

# State file state/historia-progow.json: readings kept per series for trend and relative
# thresholds. Series in STATE_NO_LEVEL come from licensed sources and are stored as % change
# and direction only (the data repo is public).
STATE_FILE = "state/historia-progow.json"
STATE_SERIES = {"A4": 5, "C1": 3, "C2": 3, "D1": 3, "D3": 4, "D4": 2, "G3": 7, "G4": 1}
STATE_NO_LEVEL = {"D1"}

EVENT_TYPES = {"credit_light", "credit_heavy", "rating", "fed_hike", "fed_cut", "infra",
               "financing", "threshold_cross", "trigger", "pricing", "model_release"}
SEVERITIES = {"info", "light", "medium", "heavy", "trigger"}


def band_for(score):
    for lo, hi, pl, en in BANDS:
        if score <= hi:
            return pl, en
    return BANDS[-1][2], BANDS[-1][3]


def near_boundary(score):
    return any(abs(score - b) <= NEAR_BOUNDARY for b in BAND_BOUNDARIES)


def daily_filename(iso_date):
    y, m, d = iso_date.split("-")
    return f"history-{d}-{m}-{y}.json"

# Report text fields stored in the daily file (Polish field + _en).
SUMMARY_MAX_WORDS = {"full": 150, "short": 80}
WEEKLY_WORDS = (400, 700)
FRIDAY = 4  # date.weekday()
