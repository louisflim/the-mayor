"""Every tunable number in the game lives here, so balancing never touches game logic."""

TERM_DAYS = 10
TARGET_WEALTH = 1_000_000

START_WEALTH = 0
START_APPROVAL = 60
START_SUSPICION = 10

VISITORS_PER_DAY = 3
MAX_MAYOR_TURNS = 6          # mayor messages per visitor before they are shown out
MAX_INPUT_CHARS = 500        # input filter cap

# Events are drawn fresh for every game: one random pool event lands on a random day inside each window,
# and the debate always closes the term. (Scandal is not in the pool: it replaces an event when Suspicion is high.)
EVENT_POOL = ["typhoon", "fiesta", "ribbon", "brownout", "dengue", "jeepney", "graduation", "callin"]
EVENT_SLOTS = [(2, 3), (4, 5), (6, 7)]
DEBATE_DAYS = (8, 9)
# Day 1 draws its visitors from here instead of always being the same three
DAY1_POOL = ["don_ramon", "lola_rosing", "kuya_boy", "sir_jepoy", "nanay_merly", "kap_luz", "engr_santos", "boss_erning"]
SCANDAL_THRESHOLD = 60       # at this Suspicion the viral scandal replaces a planned event (once per game)

# Overnight drift
NIGHT_SUSPICION_DRIFT = -4   # the news cycle moves on
NIGHT_APPROVAL_PULL = 2      # approval moves this many points toward 50
APPROVAL_NEUTRAL = 50

# Suspicion from the size of a bribe the mayor takes: (upper bound inclusive, suspicion)
BRIBE_SUSPICION = [
    (30_000, 4),
    (100_000, 8),
    (float("inf"), 15),
]

# Base effects for each judge outcome, before the visitor card's own extras.
BASE_EFFECTS = {
    "deal":       {"approval": 0,  "suspicion": 0, "relationship": 1},   # suspicion comes from BRIBE_SUSPICION
    "helped":     {"approval": 0,  "suspicion": -3, "relationship": 1},
    "paid":       {"approval": 0,  "suspicion": 0, "relationship": 1},
    "refused":    {"approval": 0,  "suspicion": -2, "relationship": -1},
    "stalled":    {"approval": -1, "suspicion": 0, "relationship": 0},
    "threatened": {"approval": -3, "suspicion": 3, "relationship": -2},
}

ON_RECORD_SUSPICION = 10     # when Ms. Reyes's story runs the next morning
ON_RECORD_APPROVAL = -5
BRIBE_OFFER_TO_PRESS = 5     # extra suspicion for trying to buy the reporter

HUSH_MONEY = 50_000          # Kuya Boy's price
HUSH_SUSPICION = -10         # once per day

FAKE_DIKE_TYPHOON_APPROVAL = -8   # if you split Kap Luz's dike money and the typhoon comes
RIVAL_FUNDED_DEBATE_PENALTY = -4  # Don Ramon funded your rival

VILLAFLOR_SUSPICION_TRIGGER = 45  # the investigator starts showing up past this

CROWD_SCORE_RANGE = (-15, 15)

# Ending thresholds
DYNASTY_APPROVAL = 70
GOOD_MAYOR_MAX_WEALTH = 250_000
GOOD_MAYOR_APPROVAL = 80