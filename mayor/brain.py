"""The two 'brains' that can drive visitors, the judge and headlines.

LLMBrain uses a real model. ScriptedBrain is an offline stand-in so the game runs
with no API key (useful for testing and as the demo backup if the Wi-Fi dies).
"""

import json
import random
import re

from . import prompts
from .cast import Card, AUDITOR_TELLS, card_text
from .defenses import wrap_mayor, check_reply
from .engine import GameState
from .llm import LLMClient, LLMError

LEAVES_TAG = "[LEAVES]"


def transcript_text(transcript: list, visitor_name: str) -> str:
    lines = []
    for m in transcript:
        if m["role"] == "mayor":
            lines.append(f"MAYOR: {m['text']}")
        elif m["role"] == "visitor":
            lines.append(f"{visitor_name.upper()}: {m['text']}")
    return "\n".join(lines)


def parse_verdict(text: str) -> dict | None:
    """Pull the JSON out of <verdict> tags (or the last {...} block). None if unparseable."""
    m = re.search(r"<verdict>\s*(\{.*?\})\s*</verdict>", text, re.S)
    blob = m.group(1) if m else None
    if blob is None:
        found = re.findall(r"\{[^{}]*\}", text, re.S)
        blob = found[-1] if found else None
    if blob is None:
        return None
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def split_leaves(reply: str) -> tuple[str, bool]:
    left = LEAVES_TAG.lower() in reply.lower()
    clean = re.sub(r"\[\s*leaves\s*\]", "", reply, flags=re.I).strip()
    return clean, left


class LLMBrain:
    name = "llm"

    def __init__(self, client: LLMClient):
        self.client = client

    def _card(self, st: GameState, card: Card) -> str:
        return card_text(card, undercover=st.is_undercover(card.id), mayor_name=st.mayor_name,
                         uncle_aunt=st.uncle_aunt, sir_maam=st.sir_maam)

    def _system(self, st: GameState, card: Card) -> str:
        memory = "\n".join(st.memory.get(card.id, [])) or "This is your first meeting with this mayor."
        return prompts.VISITOR_SYSTEM.format(card=self._card(st, card), memory=memory, day=st.day)

    def _messages(self, st: GameState, card: Card) -> list:
        msgs = []
        for m in st.transcript:
            if m["role"] == "visitor":
                msgs.append({"role": "assistant", "content": m["text"]})
            elif m["role"] == "mayor":
                msgs.append({"role": "user", "content": wrap_mayor(m["text"], card.name)})
        return msgs

    def opening(self, st: GameState, card: Card) -> tuple[str, bool]:
        msgs = [{"role": "user", "content": wrap_mayor(
            "[The mayor looks up as you walk into the office.]", card.name)}]
        reply = self.client.chat(self._system(st, card), msgs)
        return self._finish(st, card, reply)

    def reply(self, st: GameState, card: Card) -> tuple[str, bool]:
        msgs = self._messages(st, card)
        if msgs and msgs[0]["role"] == "assistant":
            msgs.insert(0, {"role": "user", "content": wrap_mayor("[The mayor looks up.]", card.name)})
        reply = self.client.chat(self._system(st, card), msgs)
        return self._finish(st, card, reply)

    def _finish(self, st, card, reply):
        text, left = split_leaves(reply)
        text, blocked = check_reply(text, undercover=st.is_undercover(card.id))
        return text, left

    def judge(self, st: GameState, card: Card) -> dict | None:
        # The judge sees the card WITHOUT the undercover overlay. The code, not the judge,
        # decides whether taking money was an arrest.
        visitor = card_text(card, undercover=False, mayor_name=st.mayor_name,
                            uncle_aunt=st.uncle_aunt, sir_maam=st.sir_maam)
        system = prompts.JUDGE_SYSTEM.format(visitor=visitor,
                                             transcript=transcript_text(st.transcript, card.name))
        out = self.client.chat(system, [{"role": "user", "content": "Report the verdict."}],
                               temperature=0, max_tokens=600)
        return parse_verdict(out)

    def judge_speech(self, st: GameState, card: Card) -> dict | None:
        system = prompts.SPEECH_JUDGE_SYSTEM.format(
            event=f"{card.role}. {card.goal}", transcript=transcript_text(st.transcript, card.name))
        out = self.client.chat(system, [{"role": "user", "content": "Score the crowd reaction."}],
                               temperature=0, max_tokens=500)
        return parse_verdict(out)

    def headline(self, st: GameState) -> str:
        notes = "\n".join(st.day_notes) or "A quiet day at city hall."
        out = self.client.chat(prompts.HEADLINE_SYSTEM.format(notes=notes),
                               [{"role": "user", "content": "Write the headline."}],
                               temperature=0.9, max_tokens=60)
        line = out.strip().splitlines()[0].strip(' "*#')
        return line.upper()[:120]


# ---------------------------------------------------------------------------
# Offline scripted brain
# ---------------------------------------------------------------------------

_AMOUNT_RE = re.compile(r"(?:₱|php|p)?\s*(\d[\d,\.]*)\s*(k|thousand|libo|m|million)?", re.I)

_KW = {
    "threat": ["ipapakulong", "kulong", "sisante", "fired", "ipapa-raid", "lagot ka", "threat", "mag-ingat ka",
               "humanda ka", "you'll regret", "ipapatanggal", "get out or"],
    "refuse": ["ayoko", "ayaw ko", "hindi pwede", "hindi ako", "no way", "refuse", "not interested", "labas",
               "umalis ka", "get out", "bawal", "no thanks", "hindi", " no", "no.", "no,"],
    "pay": ["raise", "babayaran", "bayaran kita", "here's", "heto", "eto na", "talent fee", "i'll pay", "ibibigay ko sa'yo",
            "bibigyan kita", "sweldo", "i will pay"],
    "help": ["tutulungan", "help", "i-fund", "fund", "ipapagawa", "gagawin natin", "sasagutin ko", "guarantee letter",
             "approve", "aprubado", "relief", "ipamigay", "distribute", "sige po lola", "pipirmahan ko", "appoint"],
    "accept": ["sige", "deal", "tanggap", "game", "okay", "ok", "call", "pwede", "akin na", "tara", "g na"],
    "haggle": ["dagdagan", "kulang", "taasan", "more", "gawin mong", "make it", "higher", "dagdag"],
}


def classify(text: str) -> str:
    t = f" {text.lower()} "
    for cat in ("threat", "haggle", "pay", "help", "refuse", "accept"):
        if any(k in t for k in _KW[cat]):
            return cat
    return "vague"


def parse_amount(text: str) -> int:
    best = 0
    for num, unit in _AMOUNT_RE.findall(text or ""):
        try:
            val = float(num.replace(",", ""))
        except ValueError:
            continue
        unit = (unit or "").lower()
        if unit in ("k", "thousand", "libo"):
            val *= 1_000
        elif unit in ("m", "million"):
            val *= 1_000_000
        if val >= 1000:
            best = max(best, int(val))
    return best


_REPLIES = {
    "accept_money": ["[ngumiti] Ayan! Sabi ko na nga ba, magkakasundo tayo, Mayor. Ako na bahala sa iba.",
                     "[inabot ang sobre] Salamat, Mayor. Tahimik lang tayo, ha?"],
    "accept_help": ["Salamat po, Mayor! Hindi ko po kayo makakalimutan. Ikukwento ko po sa lahat.",
                    "[napaluha] Maraming salamat po. Sana po tuloy-tuloy na."],
    "paid": ["[binilang ang pera] Ayos, Boss. Wala akong nakita, wala akong narinig.",
             "Grabe, Mayor! Solid! Glowing review 'to, promise."],
    "refuse": ["[tumigil sandali] Ganun po ba. Sayang, Mayor. Pag-isipan niyo pa po.",
               "Hmm. Hindi ko inasahan 'yan, Mayor. Pero sige po."],
    "refuse_final": ["Sige po, Mayor. Tandaan ko po 'to. [LEAVES]",
                     "Okay. Alam ko na kung saan ako lulugar. Paalam po. [LEAVES]"],
    "threat": ["[napaatras] Mayor, grabe naman po kayo. Aalis na po ako. [LEAVES]"],
    "haggle": ["[napakamot ng ulo] Ang galing niyo talaga makipag-usap, Mayor. Sige, dagdagan natin.",
               "Mayor naman... sige na nga. Para sa'yo."],
    "vague": ["Mayor, ano po ba talaga? Oo o hindi?", "[naghihintay] Hindi ko po masyadong gets, Mayor.",
              "Pwede po bang mas malinaw, Mayor?"],
}


PAYOUT_FIRST = {"kuya_boy", "sir_jepoy"}   # visitors where "sige" means the mayor pays


class ScriptedBrain:
    """Keyword-driven stand-in. Not smart, but it plays every rule of the game."""
    name = "scripted"

    def _rng(self, st: GameState):
        return random.Random(f"{st.seed}-{st.day}-{st.slot}-{len(st.transcript)}")

    def opening(self, st: GameState, card: Card) -> tuple[str, bool]:
        line = card.sample_line.replace("{uncle_aunt}", st.uncle_aunt)
        if st.memory.get(card.id):
            line = "Mayor, ako ulit. Naaalala niyo pa po ba last time? " + line
        return line, False

    def reply(self, st: GameState, card: Card) -> tuple[str, bool]:
        rng = self._rng(st)
        last = next((m["text"] for m in reversed(st.transcript) if m["role"] == "mayor"), "")
        cat = classify(last)
        refusals = sum(1 for m in st.transcript if m["role"] == "mayor" and classify(m["text"]) == "refuse")

        if card.kind == "speech":
            return self._speech_reply(st, card, last, rng)

        tell = ""
        if st.is_undercover(card.id) and rng.random() < 0.6:
            tell = " " + rng.choice([
                "Para lang po malinaw sa records namin, magkano po exactly?",
                "Cash po ba o check? Kanino po ipapangalan ang resibo?",
                "For the records lang po, paano po ipo-process yung pera?",
            ])

        if cat == "threat":
            return rng.choice(_REPLIES["threat"]).replace(" [LEAVES]", ""), True
        if cat == "refuse":
            if refusals >= 2 or card.max_bribe == 0:
                text = rng.choice(_REPLIES["refuse_final"])
                return text.replace(" [LEAVES]", ""), True
            return rng.choice(_REPLIES["refuse"]) + tell, False
        if cat == "pay" and card.max_payout:
            return rng.choice(_REPLIES["paid"]), True
        if cat == "haggle" and card.max_bribe:
            haggles = sum(1 for m in st.transcript if m["role"] == "mayor" and classify(m["text"]) == "haggle")
            if haggles >= 2:   # they've met your price
                return rng.choice(_REPLIES["accept_money"]), True
            return rng.choice(_REPLIES["haggle"]) + tell, False
        if cat == "accept" and card.id in PAYOUT_FIRST:
            return rng.choice(_REPLIES["paid"]), True
        if cat in ("accept", "help", "pay"):
            if card.max_bribe:
                return rng.choice(_REPLIES["accept_money"]), True
            return rng.choice(_REPLIES["accept_help"]), True
        return rng.choice(_REPLIES["vague"]) + tell, False

    def _speech_reply(self, st, card, last, rng):
        if card.id == "debate":
            qs = ["Second question: ano po ang plano ninyo sa baha sa Brgy. Lubog?",
                  "Final question: bakit kayo dapat iboto ulit ng Pogi City?"]
            n = st.mayor_turns
            if n <= len(qs):
                return f"[Konsehal Tanyag smirks.] {qs[n - 1]}", False
            return "Thank you, Mayor. Ang crowd na ang huhusga. [LEAVES]".replace(" [LEAVES]", ""), True
        if card.id == "scandal" and st.mayor_turns < 2:
            return "Mayor, follow-up po: kanino po galing yung brown envelope sa video?", False
        return "[the crowd murmurs] Palakpakan natin ang ating Mayor!", True

    def judge(self, st: GameState, card: Card) -> dict:
        mayor_lines = [m["text"] for m in st.transcript if m["role"] == "mayor"]
        cats = [classify(t) for t in mayor_lines]
        decisive = next((c for c in reversed(cats) if c != "vague"), "vague")
        amount = max([parse_amount(t) for t in mayor_lines] + [0])
        all_text = " ".join(mayor_lines).lower()
        v = {"outcome": "stalled", "amount_received": 0, "amount_paid": 0, "mayor_offered_bribe": False,
             "on_record": False, "tone": "vague", "promised": "", "quote": mayor_lines[-1] if mayor_lines else ""}
        if decisive == "threat":
            v.update(outcome="threatened", tone="threatening")
        elif decisive == "refuse":
            v.update(outcome="refused", tone="honest")
        elif decisive in ("accept", "haggle", "help", "pay"):
            if card.max_bribe and decisive in ("accept", "haggle"):
                default = card.max_bribe // 2 if decisive == "accept" else int(card.max_bribe * 0.8)
                v.update(outcome="deal", amount_received=amount or default)
            elif card.max_payout and (decisive == "pay" or (decisive == "accept" and card.id in PAYOUT_FIRST)):
                v.update(outcome="paid", amount_paid=amount or card.max_payout)
            else:
                v.update(outcome="helped", tone="honest")
        offer_words = ["sobre", "envelope", "pera", "bayad", "bribe", "magkano gusto mo", "may pang-kape"]
        if card.id in ("ms_reyes", "atty_villaflor") and any(w in all_text for w in offer_words + ["₱"]):
            v["mayor_offered_bribe"] = any(w in all_text for w in ["bibigyan kita", "sa'yo na", "for you", "take this",
                                                                    "bayaran kita", "ito sa'yo", "magkano gusto mo"])
        if card.id == "ms_reyes":
            v["on_record"] = v["mayor_offered_bribe"] or any(
                w in all_text for w in ["sobre", "envelope", "deal", "commission", "porsyento", "cut", "bribe"])
        name = card.name
        verb = {"deal": f"took ₱{v['amount_received']:,} from {name}",
                "paid": f"paid {name} ₱{v['amount_paid']:,}",
                "helped": f"agreed to help {name}", "refused": f"turned {name} down",
                "threatened": f"threatened {name}", "stalled": f"gave {name} a sagot-pulitiko"}[v["outcome"]]
        quote = f" and said \"{v['quote'][:80]}\"" if v["quote"] else ""
        v["memory_note"] = f"The mayor {verb}{quote}."
        return v

    def judge_speech(self, st: GameState, card: Card) -> dict:
        text = " ".join(m["text"] for m in st.transcript if m["role"] == "mayor").lower()
        good = ["salamat", "tulong", "pangako", "baha", "health", "trabaho", "para sa inyo", "pamilya", "kabataan",
                "dike", "ospital", "sorry", "patawad", "transparent", "imbestigasyon", "investigate", "mahal ko"]
        bad = ["wala akong pakialam", "pake", "tanga", "ninakaw", "kinuha ko", "bribe", "sobre", "fake news", "shut up",
               "manahimik", "ako ang batas"]
        score = 2 * sum(w in text for w in good) - 4 * sum(w in text for w in bad)
        score += 1 if 40 <= len(text) <= 600 else -2
        score = max(-15, min(15, score))
        mayor_lines = [m["text"] for m in st.transcript if m["role"] == "mayor"]
        quote = max(mayor_lines, key=len)[:120] if mayor_lines else ""
        mood = "won the crowd over" if score > 3 else "got polite applause" if score >= 0 else "got booed"
        return {"crowd_score": score, "memory_note": f"The mayor {mood} at the {card.role.lower()}.",
                "quote": quote}

    def headline(self, st: GameState) -> str:
        last = st.log[-len(st.lineup):] if st.log else []
        worst = max(last, key=lambda r: abs(r["d_suspicion"]) + abs(r["d_approval"]) + r["received"] / 20000,
                    default=None)
        if not worst:
            return "QUIET DAY AT POGI CITY HALL; MAYOR SEEN EATING PANSIT"
        name = worst["name"].upper()
        return {
            "deal": f"{name} LEAVES CITY HALL SMILING; SOURCES CITE 'MERIENDA'",
            "paid": f"MAYOR'S WALLET LIGHTER AFTER MEETING WITH {name}",
            "helped": f"MAYOR HELPS {name}; CITY HALL STAFF IN SHOCK",
            "refused": f"MAYOR SAYS NO TO {name}; TSISMIS SPREADS",
            "threatened": f"{name} STORMS OUT OF MAYOR'S OFFICE",
            "stalled": f"MAYOR DODGES {name} WITH CLASSIC SAGOT-PULITIKO",
            "speech": f"MAYOR'S SPEECH AT {worst['name'].upper()} GETS PEOPLE TALKING",
            "caught": "MAYOR NABBED IN ENTRAPMENT",
        }.get(worst["outcome"], "ANOTHER DAY AT POGI CITY HALL")


def make_brain(provider: str | None, api_key: str | None, model: str | None, temperature: float,
               base_url: str | None = None):
    if not provider or provider == "Offline demo" or not api_key or not model:
        return ScriptedBrain()
    return LLMBrain(LLMClient(provider=provider, api_key=api_key, model=model, temperature=temperature,
                              base_url=base_url))


__all__ = ["LLMBrain", "ScriptedBrain", "make_brain", "parse_verdict", "transcript_text", "LLMError",
           "AUDITOR_TELLS"]
