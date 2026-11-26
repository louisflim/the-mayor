"""Game state and rules. Pure Python, no Streamlit and no LLM, so it can be unit-tested.

The LLM never touches the numbers. The judge reports facts (who paid whom, what was
agreed), and apply_outcome() turns those facts into stat changes.
"""

import random
from dataclasses import dataclass, field, asdict

from . import config as C
from .cast import VISITORS, EVENTS, EVENT_INTRO, get_card

OUTCOMES = {"deal", "paid", "helped", "refused", "threatened", "stalled"}


@dataclass
class GameState:
    mayor_name: str = "Pogi"
    gender: str = "male"                 # "male" | "female": only changes Tito/Tita, Sir/Ma'am
    seed: int = 0
    day: int = 1
    wealth: int = C.START_WEALTH
    approval: int = C.START_APPROVAL
    suspicion: int = C.START_SUSPICION
    auditor_id: str | None = None        # decided once per run by the code, never by the LLM
    lineup: list = field(default_factory=list)
    slot: int = 0
    transcript: list = field(default_factory=list)   # [{"role": "visitor"|"mayor"|"system", "text": ...}]
    mayor_turns: int = 0
    visitor_left: bool = False
    memory: dict = field(default_factory=dict)        # visitor id -> list of notes
    relationship: dict = field(default_factory=dict)  # visitor id -> -2..+2
    visits: dict = field(default_factory=dict)        # visitor id -> times seen
    lineups: dict = field(default_factory=dict)       # day -> lineup, for history
    day_notes: list = field(default_factory=list)
    headlines: list = field(default_factory=list)     # [(day, headline)]
    pending_stories: list = field(default_factory=list)
    briefing: list = field(default_factory=list)
    flags: dict = field(default_factory=lambda: {
        "fake_dike": False, "rival_funded": False, "hush_day": 0, "carlo_contracts": 0,
    })
    log: list = field(default_factory=list)           # every visit result, for export
    phase: str = "briefing"                           # briefing | visit | night | ended
    ending: str | None = None
    jepoy_live: bool = False
    event_plan: dict = field(default_factory=dict)    # day -> event id, drawn fresh for every game
    day_start: dict = field(default_factory=dict)     # stats at the start of today, for the end-of-day page

    # ---- convenience -------------------------------------------------
    @property
    def uncle_aunt(self) -> str:
        return "Tita" if self.gender == "female" else "Tito"

    @property
    def sir_maam(self) -> str:
        return "Ma'am" if self.gender == "female" else "Sir"

    def rng(self, salt: str = "") -> random.Random:
        return random.Random(f"{self.seed}-{self.day}-{self.slot}-{salt}")

    def current_id(self) -> str | None:
        return self.lineup[self.slot] if self.slot < len(self.lineup) else None

    def is_undercover(self, card_id: str | None) -> bool:
        return card_id is not None and card_id == self.auditor_id

    def to_dict(self) -> dict:
        return asdict(self)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# Setup and schedule
# ---------------------------------------------------------------------------

def new_game(mayor_name: str, gender: str = "male", seed: int | None = None) -> GameState:
    seed = random.randrange(1_000_000) if seed is None else seed
    st = GameState(mayor_name=(mayor_name.strip() or "Pogi")[:30], gender=gender, seed=seed)
    roll = random.Random(seed).random()
    # The auditor is usually Engr. Santos, sometimes Boss Erning, sometimes nobody,
    # so learning one name doesn't solve the game.
    st.auditor_id = "engr_santos" if roll < 0.5 else "boss_erning" if roll < 0.8 else None
    st.relationship = {k: 0 for k in VISITORS}
    st.event_plan = make_event_plan(seed)
    start_day(st)
    return st


def make_event_plan(seed: int) -> dict:
    """Draw this game's events: one random pool event per window, then the debate near the end."""
    rng = random.Random(f"{seed}-events")
    picks = rng.sample(C.EVENT_POOL, len(C.EVENT_SLOTS))
    plan = {rng.randint(lo, hi): ev for (lo, hi), ev in zip(C.EVENT_SLOTS, picks)}
    plan[rng.choice(C.DEBATE_DAYS)] = "debate"
    return plan


def planned_event(st: GameState, day: int) -> str | None:
    return getattr(st, "event_plan", {}).get(day)


def _ramon_days(st: GameState) -> set:
    """Don Ramon comes back on two random days, so his bribe-and-rival arc lands differently every game."""
    return set(random.Random(f"{st.seed}-ramon").sample(range(3, 9), 2))


def _seen_recently(st: GameState, cid: str, days: int) -> bool:
    return any(cid in st.lineups.get(d, []) for d in range(st.day - days, st.day))


def build_lineup(st: GameState) -> list:
    rng = st.rng("lineup")
    day = st.day
    want: list = []

    def add(cid):
        if cid not in want:
            want.append(cid)

    if day == 1:
        for cid in rng.sample(C.DAY1_POOL, C.VISITORS_PER_DAY):
            add(cid)
    if day in _ramon_days(st):
        add("don_ramon")
    if day == 10 or (day >= 3 and not _seen_recently(st, "ms_reyes", 2)):
        add("ms_reyes")
    if (st.suspicion >= C.VILLAFLOR_SUSPICION_TRIGGER and day >= VISITORS["atty_villaflor"].min_day
            and st.visits.get("atty_villaflor", 0) < VISITORS["atty_villaflor"].max_visits
            and not _seen_recently(st, "atty_villaflor", 1)):
        add("atty_villaflor")
    if day == 2:
        add(rng.choice(["engr_santos", "boss_erning"]))

    def eligible(relax: bool):
        out = []
        for cid, card in VISITORS.items():
            if cid in want or card.weight == 0 or card.min_day > day:
                continue
            if not relax and st.visits.get(cid, 0) >= card.max_visits:
                continue
            if not relax and _seen_recently(st, cid, 1):
                continue
            out.append(cid)
        return out

    while len(want) < C.VISITORS_PER_DAY:
        pool = eligible(False) or eligible(True)
        if not pool:
            break
        weights = [VISITORS[c].weight for c in pool]
        add(rng.choices(pool, weights=weights)[0])

    want = want[: C.VISITORS_PER_DAY]
    if day != 1:
        rng.shuffle(want)

    event = planned_event(st, day)
    if (event and event != "debate" and day >= 4 and st.suspicion >= C.SCANDAL_THRESHOLD
            and not st.flags.get("scandal_done")):
        event = "scandal"          # a high-Suspicion mayor gets the viral video instead of a friendlier event
        st.flags["scandal_done"] = True
    if event:
        want.append(event)
    return want


def start_day(st: GameState) -> None:
    st.day_start = {"wealth": st.wealth, "approval": st.approval, "suspicion": st.suspicion}
    st.lineup = build_lineup(st)
    st.lineups[st.day] = list(st.lineup)
    st.slot = 0
    st.day_notes = []
    st.transcript = []
    st.mayor_turns = 0
    st.visitor_left = False
    st.phase = "briefing"
    st.briefing = morning_briefing(st)
    st.jepoy_live = st.rng("jepoy").random() < 0.35
    check_instant_ending(st)   # a morning story can push Suspicion to 100


def morning_briefing(st: GameState) -> list:
    """Kuya Boy's morning lines. Morning stories are applied here, so they hit the stats."""
    lines = []
    if st.headlines:
        lines.append(f"📰 Yesterday's Pogi Daily Balita: **{st.headlines[-1][1]}**")
    for story in st.pending_stories:
        st.suspicion = clamp(st.suspicion + C.ON_RECORD_SUSPICION, 0, 100)
        st.approval = clamp(st.approval + C.ON_RECORD_APPROVAL, 0, 100)
        lines.append(f"📻 Radyo Pogi aired this morning: \"{story}\" (Approval and Suspicion took a hit.)")
    st.pending_stories = []

    names = [get_card(c).name for c in st.lineup if c in VISITORS]
    lines.append(f"Kuya Boy: \"Boss, good morning. Day {st.day} of {C.TERM_DAYS}. "
                 f"Schedule today: {', '.join(names)}.\"")

    event = next((c for c in st.lineup if c in EVENTS), None)
    if event == "typhoon":
        lines.append("Kuya Boy: \"Boss, Bagyong Kulot is here. Lubog is flooding. Ma'am Nora from disaster office "
                     "will see you after the visitors.\"")
        if st.flags["fake_dike"]:
            st.approval = clamp(st.approval + C.FAKE_DIKE_TYPHOON_APPROVAL, 0, 100)
            lines.append("Kuya Boy: \"Boss... the dike in Lubog? The one we paid for? Wala pala talaga. "
                         "Nasa social media na yung picture ng baha.\" (Approval fell.)")
    elif event == "fiesta":
        lines.append("Kuya Boy: \"Fiesta tonight, Boss! You're giving a speech at the plaza. Wag masyadong mahaba.\"")
    elif event == "scandal":
        lines.append("Kuya Boy: \"Boss... may video. Yung brown envelope sa desk mo. Trending na. "
                     "Press briefing after the visitors.\"")
    elif event == "ribbon":
        lines.append("Kuya Boy: \"Boss, you're opening the barangay basketball league tonight. Short speech lang.\"")
    elif event == "debate":
        extra = " At Boss, balita ko pinopondohan siya ni Don Ramon." if st.flags["rival_funded"] else ""
        lines.append(f"Kuya Boy: \"Debate tonight vs Konsehal Bong Tanyag. Tatlong tanong.{extra}\"")
    elif event in EVENT_INTRO:
        lines.append(EVENT_INTRO[event])

    if st.auditor_id in st.lineup and st.rng("hint").random() < 0.5:
        lines.append("Kuya Boy: \"Boss, may narinig ako sa canteen. May bagong mukha daw na umiikot sa "
                     "mga contractor. Masyadong maraming tanong. Ingat lang.\"")
    if "atty_villaflor" in st.lineup:
        lines.append("Kuya Boy: \"Boss... yung taga-Integrity Commission, nandito ulit. Ayusin mo sagot mo.\"")
    return lines


# ---------------------------------------------------------------------------
# Visits
# ---------------------------------------------------------------------------

def begin_visit(st: GameState) -> None:
    cid = st.current_id()
    st.transcript = []
    st.mayor_turns = 0
    st.visitor_left = False
    st.phase = "visit"
    if cid in VISITORS:
        st.visits[cid] = st.visits.get(cid, 0) + 1


def turns_allowed(card_id: str) -> int:
    card = get_card(card_id)
    return card.speech_turns if card.kind == "speech" else C.MAX_MAYOR_TURNS


def visit_over(st: GameState) -> bool:
    cid = st.current_id()
    return cid is not None and (st.visitor_left or st.mayor_turns >= turns_allowed(cid))


def bribe_suspicion(amount: int) -> int:
    if amount <= 0:
        return 0
    for upper, sus in C.BRIBE_SUSPICION:
        if amount <= upper:
            return sus
    return C.BRIBE_SUSPICION[-1][1]


def normalise_verdict(raw: dict | None) -> dict:
    """Validate the judge's JSON. Anything malformed falls back to a harmless 'stalled'."""
    raw = raw if isinstance(raw, dict) else {}

    def as_int(v):
        try:
            return max(0, int(float(str(v).replace(",", "").replace("₱", ""))))
        except (TypeError, ValueError):
            return 0

    out = {
        "outcome": raw.get("outcome") if raw.get("outcome") in OUTCOMES else "stalled",
        "amount_received": as_int(raw.get("amount_received", 0)),
        "amount_paid": as_int(raw.get("amount_paid", 0)),
        "mayor_offered_bribe": raw.get("mayor_offered_bribe") is True,
        "on_record": raw.get("on_record") is True,
        "tone": raw.get("tone") if raw.get("tone") in {"honest", "vague", "threatening"} else "vague",
        "promised": str(raw.get("promised", ""))[:80],
        "memory_note": str(raw.get("memory_note", "")).strip()[:300],
        "quote": str(raw.get("quote", "")).strip()[:200],
    }
    return out


def apply_outcome(st: GameState, card_id: str, verdict: dict) -> dict:
    """Turn the judge's facts into stat changes. Returns a result dict for the UI."""
    card = get_card(card_id)
    v = normalise_verdict(verdict)
    received = min(v["amount_received"], card.max_bribe)
    paid = min(v["amount_paid"], card.max_payout, st.wealth)
    outcome = v["outcome"]

    # Money decides the outcome, not the label the judge picked.
    if received > 0:
        outcome = "deal"
    elif paid > 0:
        outcome = "paid"
    elif outcome == "deal":
        outcome = "helped"   # agreed to the favour but no money changed hands
    elif outcome == "paid":
        outcome = "stalled"  # promised to pay but never named an amount

    w0, a0, s0 = st.wealth, st.approval, st.suspicion
    notes = []
    if v["amount_received"] > card.max_bribe and card.max_bribe:
        notes.append(f"{card.name} only had ₱{card.max_bribe:,} to give, whatever was promised.")

    # Undercover auditor: taking the money ends the run.
    if st.is_undercover(card_id) and outcome == "deal":
        st.suspicion = 100
        st.ending = "arrested_caught"
        st.phase = "ended"
        note = v["memory_note"] or f"The mayor took ₱{received:,} from {card.name}."
        st.day_notes.append(note)
        result = _result(st, card_id, "caught", v, received, paid, w0, a0, s0,
                         [f"{card.name} was an undercover auditor. You're under arrest."])
        st.log.append(result)
        return result

    base = dict(C.BASE_EFFECTS[outcome])
    extras = card.effects.get(outcome, {})
    if outcome == "helped" and card.max_bribe > 0 and "helped" not in card.effects:
        extras = {"approval": card.effects.get("deal", {}).get("approval", 0)}  # the favour still hurts the city

    d_app = base["approval"] + extras.get("approval", 0)
    d_sus = base["suspicion"] + extras.get("suspicion", 0)
    d_rel = base["relationship"]

    if outcome == "deal":
        st.wealth += received
        d_sus += bribe_suspicion(received)
    if outcome == "paid":
        st.wealth -= paid

    # Visitor-specific rules
    if card_id == "kuya_boy" and outcome == "paid":
        if st.flags["hush_day"] != st.day:
            st.flags["hush_day"] = st.day
            d_sus += C.HUSH_SUSPICION
            notes.append("Kuya Boy will keep the office quiet.")
        else:
            notes.append("You already paid Kuya Boy today. He took it anyway.")
    if card_id == "sir_jepoy" and outcome == "paid" and st.jepoy_live:
        d_app = -6
        d_sus += 9
        notes.append("Sir Jepoy was streaming live the whole time. The payment is in the clip.")
    if card_id == "kap_luz" and outcome == "deal":
        st.flags["fake_dike"] = True
    if card_id == "carlo" and outcome == "deal":
        st.flags["carlo_contracts"] += 1
        notes.append(f"That's Carlo's contract number {st.flags['carlo_contracts']}.")
    if v["mayor_offered_bribe"]:
        if card_id == "atty_villaflor":
            d_sus += 35
            notes.append("Atty. Villaflor wrote down your offer.")
        elif card_id == "ms_reyes":
            v["on_record"] = True
            d_sus += C.BRIBE_OFFER_TO_PRESS
            notes.append("Ms. Reyes's recorder was running.")
    if card_id == "ms_reyes" and v["on_record"]:
        story = v["quote"] or v["memory_note"] or "The mayor dodged questions about the mangrove permit."
        st.pending_stories.append(story[:200])
        notes.append("That's going on air tomorrow morning.")

    st.approval = clamp(st.approval + d_app, 0, 100)
    st.suspicion = clamp(st.suspicion + d_sus, 0, 100)
    st.wealth = max(0, st.wealth)
    if card_id in st.relationship:
        st.relationship[card_id] = clamp(st.relationship[card_id] + d_rel, -2, 2)
        if card_id == "don_ramon" and st.relationship[card_id] <= -1 and outcome in ("refused", "threatened"):
            if not st.flags["rival_funded"]:
                notes.append("Don Ramon is now funding Konsehal Bong Tanyag.")
            st.flags["rival_funded"] = True

    memory_note = v["memory_note"] or f"Day {st.day}: the mayor's answer was '{outcome}'."
    st.memory.setdefault(card_id, []).append(f"Day {st.day}: {memory_note}")
    st.day_notes.append(f"{card.name}: {memory_note}")

    result = _result(st, card_id, outcome, v, received, paid, w0, a0, s0, notes)
    st.log.append(result)
    check_instant_ending(st)
    return result


def apply_speech(st: GameState, card_id: str, crowd_score, memory_note: str, quote: str = "") -> dict:
    card = get_card(card_id)
    try:
        score = int(crowd_score)
    except (TypeError, ValueError):
        score = 0
    score = clamp(score, *C.CROWD_SCORE_RANGE)
    if card_id == "debate" and st.flags["rival_funded"]:
        score += C.RIVAL_FUNDED_DEBATE_PENALTY
    a0, s0, w0 = st.approval, st.suspicion, st.wealth
    st.approval = clamp(st.approval + score, 0, 100)
    if card_id == "scandal" and score < 0:
        st.suspicion = clamp(st.suspicion + 5, 0, 100)
    note = (memory_note or f"The mayor spoke at the {card.role.lower()}.")[:300]
    st.day_notes.append(f"{card.role}: {note}")
    v = {"memory_note": note, "quote": quote, "crowd_score": score}
    reaction = ("Standing ovation!" if score >= 10 else "The crowd cheered." if score >= 4 else
                "Polite applause." if score >= 0 else "Some boos from the back." if score > -8 else
                "The crowd booed you off the stage.")
    result = _result(st, card_id, "speech", v, 0, 0, w0, a0, s0, [reaction])
    st.log.append(result)
    check_instant_ending(st)
    return result


def _result(st, card_id, outcome, v, received, paid, w0, a0, s0, notes) -> dict:
    return {
        "day": st.day, "visitor": card_id, "name": get_card(card_id).name, "outcome": outcome,
        "received": received, "paid": paid, "memory_note": v.get("memory_note", ""),
        "d_wealth": st.wealth - w0, "d_approval": st.approval - a0, "d_suspicion": st.suspicion - s0,
        "notes": notes, "transcript": list(st.transcript),
    }


def next_visitor(st: GameState) -> None:
    st.slot += 1
    st.transcript = []
    st.mayor_turns = 0
    st.visitor_left = False
    st.phase = "visit" if st.slot < len(st.lineup) else "night"
    if st.phase == "visit":
        begin_visit(st)


# ---------------------------------------------------------------------------
# Night and endings
# ---------------------------------------------------------------------------

def end_day(st: GameState, headline: str) -> None:
    st.headlines.append((st.day, headline))
    st.suspicion = clamp(st.suspicion + C.NIGHT_SUSPICION_DRIFT, 0, 100)
    if st.approval > C.APPROVAL_NEUTRAL:
        st.approval = max(C.APPROVAL_NEUTRAL, st.approval - C.NIGHT_APPROVAL_PULL)
    elif st.approval < C.APPROVAL_NEUTRAL and st.approval > 0:
        st.approval = min(C.APPROVAL_NEUTRAL, st.approval + C.NIGHT_APPROVAL_PULL)
    if st.day >= C.TERM_DAYS:
        st.ending = final_ending(st)
        st.phase = "ended"
        return
    st.day += 1
    start_day(st)


def check_instant_ending(st: GameState) -> None:
    if st.ending:
        return
    if st.suspicion >= 100:
        st.ending = "arrested"
    elif st.approval <= 0:
        st.ending = "ousted"
    if st.ending:
        st.phase = "ended"


def final_ending(st: GameState) -> str:
    if st.suspicion >= 100:
        return "arrested"
    if st.approval <= 0:
        return "ousted"
    if st.wealth >= C.TARGET_WEALTH and st.approval >= C.DYNASTY_APPROVAL:
        return "dynasty"
    if st.wealth >= C.TARGET_WEALTH:
        return "retired_rich"
    if st.wealth < C.GOOD_MAYOR_MAX_WEALTH and st.approval >= C.GOOD_MAYOR_APPROVAL:
        return "good_mayor"
    return "broke"


ENDINGS = {
    "arrested_caught": ("Arrested in an entrapment", False,
                        "MAYOR NABBED IN ENTRAPMENT; KUYA BOY TURNS STATE WITNESS"),
    "arrested": ("Arrested by the Integrity Commission", False,
                 "MAYOR ARRESTED AT CITY HALL; VICE MAYOR GING 'SHOCKED, SADDENED, READY'"),
    "ousted": ("Ousted by a rioting public", False,
               "POGI CITY HALL GATES STORMED; MAYOR FLEES IN TRICYCLE"),
    "dynasty": ("Dynasty", True, "LANDSLIDE! MAYOR RE-ELECTED, PAMANGKIN TO RUN FOR VICE"),
    "retired_rich": ("Retired rich", True, "EX-MAYOR SPOTTED ON YACHT; 'I SERVED WITH HONOR'"),
    "good_mayor": ("Accidentally a good mayor", False, "HONEST MAYOR CONFUSES EVERYONE"),
    "broke": ("Broke and forgotten", False, "OUTGOING MAYOR LEAVES WITH NOTHING BUT A TARPAULIN"),
}


def score(st: GameState) -> int:
    return int(st.wealth / 1000 + st.approval * 10 - st.suspicion * 5)