"""The Mayor: a satirical role-playing chatbot game set in the made-up Pogi City.

Screens follow the team's Figma lo-fi wireframes: title, main game, envelope offer,
debate/speech event, end of day, and game over.

Run with:  streamlit run app.py
"""

import json
import os
from datetime import datetime

import streamlit as st

from mayor import config as C
from mayor import engine as E
from mayor import ui
from mayor.brain import ScriptedBrain, make_brain
from mayor.cast import EVENTS, VISITORS, get_card
from mayor.defenses import clean_input, kuya_boy_callout
from mayor.llm import PROVIDERS, LLMError

st.set_page_config(page_title="The Mayor of Pogi City", page_icon="🏛️", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown(ui.CSS, unsafe_allow_html=True)

QUICK_LINES = {
    "accept_help": "Sige, aasikasuhin ko 'yan. Walang kapalit.",
    "refuse": "Hindi pwede 'yan. Ayoko ng ganyang usapan dito sa opisina ko.",
    "threaten": "Alam mo ba kung sino kausap mo? Isang tawag ko lang, sarado ang negosyo mo.",
    "vague": "Alam mo, pinag-aaralan pa namin 'yan. Lahat ng bagay may tamang panahon.",
    "haggle_plain": "Kulang pa 'yan. Ano pa ang kaya mong ibigay?",
}
SPEECH_ANGLES = {
    "Promise": "Pangako ko sa inyo: ",
    "Deny": "Hindi totoo 'yan. Fake news 'yan. ",
    "Blame rival": "Ang tanong, nasaan si Konsehal Tanyag nung kailangan ninyo siya? ",
    "Make a joke": "Alam niyo, mas mabilis pa ang Wi-Fi sa munisipyo kaysa sa paratang na 'yan. ",
    "Sagot-pulitiko": "Magandang tanong 'yan. Ang mahalaga, sama-sama tayo para sa kinabukasan ng Pogi. ",
}
EVENT_BANNERS = {
    "typhoon": "Typhoon warning: Bagyong Kulot is flooding Brgy. Lubog. Your response today changes Approval.",
    "fiesta": "Pista ng Pogi tonight! Give a speech at the plaza. The crowd reacts live.",
    "scandal": "A video of a brown envelope on your desk went viral. Face the press.",
    "ribbon": "You're opening the barangay basketball league tonight. Short speech lang.",
    "debate": "Election debate at the city plaza. Answer each question with a speech. The crowd reacts live.",
}
TOMORROW = {
    3: "Bagyong Kulot is coming. Lubog will flood.", 5: "Pista ng Pogi: you're giving a speech.",
    7: "Something big tomorrow. Depends how suspicious people are.", 9: "Election debate against Konsehal Tanyag.",
    10: "Your last day. Ms. Reyes will be there.",
}


def html(s: str, where=st):
    # Strip indentation and blank lines so Markdown never turns our HTML into a code block.
    where.markdown("\n".join(line.strip() for line in s.splitlines() if line.strip()), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Settings and brain
# ---------------------------------------------------------------------------

def secret(name: str) -> str | None:
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:  # no secrets.toml at all
        pass
    return os.environ.get(name)


def available_providers() -> list:
    return ["Offline demo"] + [p for p in PROVIDERS if secret(PROVIDERS[p]["secret"])]


def default_provider() -> str:
    return available_providers()[1] if len(available_providers()) > 1 else "Offline demo"


def provider_models(provider: str) -> list:
    if provider == "Custom":
        return [m.strip() for m in (secret("LLM_MODEL") or "").split(",") if m.strip()]
    return PROVIDERS.get(provider, {}).get("models", [])


def settings() -> dict:
    s = st.session_state.setdefault("settings", {})
    s.setdefault("provider", default_provider())
    models = provider_models(s["provider"])
    if s.get("model") not in models:
        s["model"] = models[0] if models else None
    s.setdefault("temperature", 0.8)
    s.setdefault("debug", False)
    return s


def get_brain():
    s = settings()
    provider = s["provider"]
    if provider == "Offline demo":
        return ScriptedBrain()
    key = secret(PROVIDERS[provider]["secret"])
    base_url = secret("LLM_BASE_URL") if provider == "Custom" else None
    return make_brain(provider, key, s["model"], s["temperature"], base_url=base_url)


def call(fn, *args, fallback=None):
    """Run an LLM call; on failure fall back to the offline brain and say so."""
    try:
        return fn(*args)
    except LLMError as e:
        st.session_state.llm_error = str(e)
        if fallback:
            return fallback(*args)
        raise


@st.dialog("Settings")
def settings_dialog():
    s = settings()
    opts = available_providers()
    provider = st.selectbox("AI model provider", opts, index=opts.index(s["provider"]) if s["provider"] in opts else 0,
                            help="A provider appears once its API key is in .streamlit/secrets.toml")
    models = provider_models(provider)
    model = st.selectbox("Model", models, index=models.index(s["model"]) if s.get("model") in models else 0) if models else None
    temp = st.slider("Visitor creativity (temperature)", 0.0, 1.2, float(s["temperature"]), 0.1,
                     help="The judge always runs at temperature 0.")
    debug = st.toggle("Demo mode: show who the auditor is", value=s["debug"])
    if provider == "Offline demo":
        st.caption("Offline demo uses scripted visitors. No API key needed, handy as a backup.")
    if st.button("Save", type="primary"):
        s.update(provider=provider, model=model, temperature=temp, debug=debug)
        st.rerun()


# ---------------------------------------------------------------------------
# Game actions
# ---------------------------------------------------------------------------

def game() -> E.GameState:
    return st.session_state.game


def reset_game():
    for k in ("game", "last_result", "headline", "attacks", "llm_error", "crowd", "reactions", "pending", "toasts"):
        st.session_state.pop(k, None)


def new_game(name: str, female: bool):
    reset_game()
    st.session_state.game = E.new_game(name or "Pogi", "female" if female else "male")
    st.session_state.screen = "game"


def visitor_opening():
    g = game()
    card = get_card(g.current_id())
    brain, offline = get_brain(), ScriptedBrain()
    text, left = call(brain.opening, g, card, fallback=offline.opening)
    g.transcript.append({"role": "visitor", "text": text})
    g.visitor_left = left
    st.session_state.crowd = None
    st.session_state.reactions = []


def send_mayor_message(raw: str):
    g = game()
    if E.visit_over(g):
        return
    f = clean_input(raw)
    if not f.text:
        return
    g.transcript.append({"role": "mayor", "text": f.text})
    g.mayor_turns += 1
    if f.flagged:
        g.transcript.append({"role": "kuya", "text": kuya_boy_callout(f.reasons)})
        st.session_state.attacks = st.session_state.get("attacks", 0) + 1
    card = get_card(g.current_id())
    brain, offline = get_brain(), ScriptedBrain()
    text, left = call(brain.reply, g, card, fallback=offline.reply)
    g.transcript.append({"role": "visitor", "text": text})
    if left:
        g.visitor_left = True
    if card.kind == "speech":
        v = call(brain.judge_speech, g, card, fallback=offline.judge_speech) or {}
        try:
            score = max(-15, min(15, int(v.get("crowd_score", 0))))
        except (TypeError, ValueError):
            score = 0
        st.session_state.crowd = score
        quote = f.text[:48] + ("…" if len(f.text) > 48 else "")
        mood = "Crowd cheers at" if score >= 5 else "Murmurs at" if score >= 0 else "Boos at"
        st.session_state.setdefault("reactions", []).append(f"{mood} “{quote}”")
        st.session_state.reactions.append(text.split(".")[0][:90])


def finish_visit():
    """Judge the visit, apply the stats, and move on to the next visitor (or the night)."""
    g = game()
    cid = g.current_id()
    card = get_card(cid)
    brain, offline = get_brain(), ScriptedBrain()
    if card.kind == "speech":
        score = st.session_state.get("crowd")
        if score is None:
            v = call(brain.judge_speech, g, card, fallback=offline.judge_speech) or {}
            score = v.get("crowd_score", 0)
        mayor = [m["text"] for m in g.transcript if m["role"] == "mayor"]
        quote = max(mayor, key=len)[:100] if mayor else ""
        mood = "won the crowd" if score >= 4 else "got polite applause" if score >= 0 else "got booed"
        note = f"The mayor {mood} at the {card.role.split(',')[0].lower()}" + (f": “{quote}”" if quote else ".")
        result = E.apply_speech(g, cid, score, note, quote)
    else:
        v = call(brain.judge, g, card, fallback=offline.judge)
        result = E.apply_outcome(g, cid, v)
    st.session_state.last_result = result
    toasts = []
    if result["d_wealth"]:
        toasts.append(f"💰 {'+' if result['d_wealth'] > 0 else '−'}₱{abs(result['d_wealth']):,}")
    if result["d_approval"]:
        toasts.append(f"👍 Approval {result['d_approval']:+d}")
    if result["d_suspicion"]:
        toasts.append(f"🔎 Suspicion {result['d_suspicion']:+d}")
    st.session_state.toasts = toasts
    if g.phase != "ended":
        E.next_visitor(g)
        if g.phase == "visit":
            visitor_opening()
        else:
            st.session_state.headline = None


def start_next_day():
    g = game()
    E.end_day(g, st.session_state.headline or "ANOTHER DAY AT POGI CITY HALL")
    st.session_state.headline = None
    st.session_state.last_result = None


# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------

@st.dialog("How to play")
def how_to_play():
    st.markdown(
        "You're the new mayor of **Pogi City**. You have **10 araw** to stash **₱1,000,000** in your offshore "
        "account.\n\n"
        "- Every day, visitors walk into your office. Talk to them in English, Filipino or Taglish, or use the "
        "quick buttons.\n"
        "- **Approval** at 0 means the city riots. **Suspicion** at 100 means arrest.\n"
        "- One contractor might be an **undercover auditor**. Take their envelope and it's over. Listen for "
        "people who ask about receipts and 'the records'.\n"
        "- Ms. Reyes from Radyo Pogi airs anything shady you say. Kuya Boy can keep the office quiet, for a price.\n"
        "- Typhoons, fiestas, scandals and an election debate will test your speeches.\n\n"
        "_Everything is fiction and satire. No real politicians, parties or places._")


@st.dialog("Take the oath")
def new_term_dialog():
    name = st.text_input("Your name, Mayor", placeholder="e.g. Kiko, Pogi, Ganda, Maria", max_chars=20)
    title = st.radio("Visitors call you", ["Sir / Tito", "Ma'am / Tita"], horizontal=True)
    if st.button("🎖️ Take the oath of office", type="primary", use_container_width=True):
        new_game(name, title.startswith("Ma"))
        st.rerun()


@st.dialog("Envelope offer")
def envelope_dialog(cid: str):
    g = game()
    card = get_card(cid)
    bg, _ = ui.colors(cid)
    html(f"<div style='display:flex;gap:.7rem;align-items:center'><div class='av' style='width:48px;height:48px;"
         f"background:{bg};font-size:26px'>{card.emoji}</div><div><b style='font-size:1.1rem'>{ui.esc(card.name)}</b>"
         f"<div class='muted'>{ui.esc(card.goal.split('.')[0])}</div></div></div>")
    offer = card.opening_offer or card.max_bribe // 2
    html(f"<div class='box' style='display:flex;justify-content:space-between;align-items:center;margin:.6rem 0'>"
         f"<span>Their offer</span><b style='font-family:Anton;font-size:2rem'>₱{offer:,}</b></div>")
    lo, hi = offer, card.max_bribe
    counter = st.slider("Your counter-offer", min_value=lo, max_value=max(hi, lo + 5000), step=5000,
                        value=min(hi, int(offer * 1.6 // 5000 * 5000)), format="₱%d")

    def risk(amount):
        sus = E.bribe_suspicion(amount) + card.effects.get("deal", {}).get("suspicion", 0)
        app = card.effects.get("deal", {}).get("approval", 0)
        return sus, app
    sus, app = risk(counter)
    level = "low" if sus <= 4 else "medium" if sus <= 10 else "high"
    reporter = any(c == "ms_reyes" for c in g.lineup[g.slot + 1:])
    heads = "<div class='muted' style='margin-top:.3rem'>Heads up: Ms. Reyes from Radyo Pogi is waiting outside.</div>" if reporter else ""
    html(f"<div class='box'><div class='h'>Risk if you accept ₱{counter:,}</div>"
         f"<div class='srow'><div class='row'><span>Suspicion</span><b>+{sus} ({level})</b></div>{ui.bar(sus * 4, '#ea7a1f')}</div>"
         f"<div class='srow'><div class='row'><span>Approval</span><b>{app:+d}</b></div>{ui.bar(abs(app) * 6, '#0038a8')}</div>{heads}</div>")
    c1, c2, c3 = st.columns(3)
    if c1.button("Refuse", use_container_width=True):
        st.session_state.pending = "Hindi ko tatanggapin 'yan. Ibalik mo 'yang sobre."
        st.rerun()
    if c2.button(f"Counter ₱{counter:,}", use_container_width=True):
        st.session_state.pending = f"Kulang 'yan. Gawin mong ₱{counter:,} at pag-uusapan natin."
        st.rerun()
    if c3.button(f"Accept ₱{offer:,}", type="primary", use_container_width=True):
        st.session_state.pending = f"Sige, tanggap ko ang ₱{offer:,}. Basta tahimik lang tayo."
        st.rerun()
    st.caption("The judge sets the final numbers after the conversation ends.")


# ---------------------------------------------------------------------------
# Screens
# ---------------------------------------------------------------------------

def title_screen():
    g = st.session_state.get("game")
    html("<div class='banderitas'></div><div class='ttl-top'><span>v1.0 · Pogi City Hall</span>"
         "<span>Language: EN / Taglish</span></div>")
    left, mid, right = st.columns([1, 1.5, 1], gap="large")
    html(ui.title_art_left(), left)
    with mid:
        html(ui.title_center())
        _, bcol, _ = st.columns([1, 2, 1])
        if bcol.button("New term", type="primary", use_container_width=True):
            new_term_dialog()
        live = g is not None and g.phase != "ended"
        if bcol.button(f"Continue (Araw {g.day})" if live else "Continue", use_container_width=True, disabled=not live):
            st.session_state.screen = "game"
            st.rerun()
        if bcol.button("How to play", use_container_width=True):
            how_to_play()
        if bcol.button("Settings", use_container_width=True):
            settings_dialog()
    html(ui.title_art_right([(c, get_card(c)) for c in ["lola_rosing", "don_ramon", "ms_reyes", "engr_santos", "kuya_boy", "carlo"]]), right)
    html("<div class='foot'>Fictional satire set in the Philippines. No real politicians, parties or places.</div>")


def banner_for(g) -> tuple[str, str, bool]:
    cid = g.current_id()
    event = next((c for c in g.lineup if c in EVENTS), None)
    if cid in EVENTS:
        return "Random event", ui.esc(EVENT_BANNERS.get(cid, "")), True
    for line in g.briefing:
        if line.startswith("📻"):
            return "Radyo Pogi", ui.esc(line.lstrip("📻 ")), True
    hint = next((l for l in g.briefing if "canteen" in l or "Integrity Commission" in l or "dike" in l), None)
    if hint:
        return "Kuya Boy", ui.esc(hint.replace('Kuya Boy: ', '').strip('"')), True
    if event:
        return "Tonight", ui.esc(EVENT_BANNERS.get(event, "")), False
    return "Kuya Boy", f"Boss, good morning. Araw {g.day} na. {len([c for c in g.lineup if c in VISITORS])} visitors today.", False


def show_toasts():
    for t in st.session_state.pop("toasts", []) or []:
        st.toast(t)


def game_screen(g):
    cid = g.current_id()
    card = get_card(cid)
    is_event = cid in EVENTS
    pending = st.session_state.pop("pending", None)
    if pending:
        with st.spinner(f"{card.name} is thinking..."):
            send_mayor_message(pending)
    show_toasts()
    html(ui.topbar(g))
    label, text, hot = banner_for(g)
    html(ui.banner(label, text, hot))

    left, mid, right = st.columns([1, 2.4, 1.05], gap="medium")
    html(ui.visitors_today(g, get_card, EVENTS), left)
    html(ui.memory_notes(g), left)

    turns = E.turns_allowed(cid)
    with mid:
        html(ui.scene(card, cid, is_event))
        html(ui.nameplate(card, is_event, g.slot, len(g.lineup), g.mayor_turns, turns))
        html(ui.dialogue(g.transcript, card))
        if st.session_state.get("llm_error"):
            st.warning(f"The AI didn't answer, so the offline script stood in. ({st.session_state.llm_error[:140]})")
            st.session_state.llm_error = None
        over = E.visit_over(g)
        if over:
            st.info(f"🚪 {card.name} has left your office." if g.visitor_left else
                    "⏰ Time's up. Kuya Boy is showing them out.")
        else:
            cols = st.columns(5)
            briber = card.max_bribe > 0
            if cols[0].button("Accept", use_container_width=True):
                if briber:
                    envelope_dialog(cid)
                elif card.ask:
                    st.session_state.pending = f"Sige, eto na ang ₱{card.ask:,}. Basta tahimik ka, ha?"
                    st.rerun()
                else:
                    st.session_state.pending = QUICK_LINES["accept_help"]
                    st.rerun()
            if cols[1].button("Haggle", use_container_width=True):
                if briber:
                    envelope_dialog(cid)
                else:
                    st.session_state.pending = ("Masyadong mahal 'yan. Kalahati na lang." if card.ask
                                                else QUICK_LINES["haggle_plain"])
                    st.rerun()
            for col, (lbl, key) in zip(cols[2:], [("Refuse", "refuse"), ("Threaten", "threaten"), ("Sagot-pulitiko", "vague")]):
                if col.button(lbl, use_container_width=True):
                    st.session_state.pending = QUICK_LINES[key]
                    st.rerun()
            with st.form("say", clear_on_submit=True, border=False):
                c1, c2 = st.columns([5, 1])
                said = c1.text_input("say", placeholder="Type what you say... (English, Filipino or Taglish)",
                                     label_visibility="collapsed", max_chars=C.MAX_INPUT_CHARS + 200)
                if c2.form_submit_button("Send", type="primary", use_container_width=True) and said.strip():
                    st.session_state.pending = said
                    st.rerun()
        with st.expander(f"Full conversation ({len([m for m in g.transcript if m['role'] != 'kuya'])} messages)"):
            html(ui.history(g.transcript, card, g.mayor_name))

    with right:
        html(ui.paper_mini(g.headlines[-1][1] if g.headlines else None))
        r = st.session_state.get("last_result")
        html(ui.last_deal(r if r and r["day"] == g.day else None))
        st.write("")
        last = g.slot + 1 >= len(g.lineup)
        if st.button("Next visitor", type="primary" if not last else "secondary", use_container_width=True,
                     disabled=last):
            with st.spinner("Kuya Boy is writing it all down..."):
                finish_visit()
            st.rerun()
        if st.button("End day", type="primary" if last else "secondary", use_container_width=True, disabled=not last):
            with st.spinner("Closing the office..."):
                finish_visit()
            st.rerun()
        if settings()["debug"]:
            st.caption(f"Demo mode · auditor: {get_card(g.auditor_id).name if g.auditor_id else 'nobody'} · "
                       f"attacks caught: {st.session_state.get('attacks', 0)}")


def rival_line(g) -> str:
    if g.flags["carlo_contracts"]:
        return f"Ask the Mayor about his pamangkin's {g.flags['carlo_contracts']} contracts!"
    if g.flags["rival_funded"]:
        return "Ang mayor na 'to, puro pangako. Ako, may plano. (And a very generous sponsor.)"
    if g.flags["fake_dike"]:
        return "Nasaan ang dike sa Lubog, Mayor? Nasa litrato lang?"
    return "Tatlong taon na ang health center sa Lubog. Karatula pa rin lang!"


def speech_screen(g):
    cid = g.current_id()
    card = get_card(cid)
    pending = st.session_state.pop("pending", None)
    if pending:
        with st.spinner("The crowd is reacting..."):
            send_mayor_message(pending)
    show_toasts()
    if st.session_state.pop("clear_speech", False):
        st.session_state.speech = ""
    html(ui.topbar(g))
    html(ui.banner("Random event", ui.esc(EVENT_BANNERS.get(cid, "")), True))
    left, mid, right = st.columns([1, 2.4, 1.05], gap="medium")
    if cid == "debate":
        html(ui.rival_card(g.flags["rival_funded"], rival_line(g)), left)
    else:
        html(ui.crowd_card(card), left)

    with mid:
        html(ui.scene(card, cid, True))
        question = next((m["text"] for m in reversed(g.transcript) if m["role"] == "visitor"), card.sample_line)
        html(ui.question_box(card, question, g.mayor_turns + 1, card.speech_turns))
        kuya = next((m for m in reversed(g.transcript) if m["role"] == "kuya"), None)
        if kuya and g.transcript[-2:] and kuya in g.transcript[-2:]:
            st.warning(f"🧔 Kuya Boy: {kuya['text']}")
        if E.visit_over(g):
            st.success("🎤 The crowd has heard enough. Kuya Boy is pulling you off stage.")
        else:
            st.caption("Quick angle:")
            cols = st.columns(len(SPEECH_ANGLES))
            for col, (lbl, start) in zip(cols, SPEECH_ANGLES.items()):
                if col.button(lbl, use_container_width=True):
                    st.session_state.speech = start
                    st.rerun()
            text = st.text_area("speech", key="speech", height=150, label_visibility="collapsed",
                                placeholder="Write your speech... (English, Filipino or Taglish)")
            words = len(text.split())
            c1, c2 = st.columns([3, 1])
            c1.caption(f"{words} / 120 words · {E.turns_allowed(cid) - g.mayor_turns} answer(s) left")
            if c2.button("Deliver speech", type="primary", use_container_width=True, disabled=words == 0):
                st.session_state.pending = " ".join(text.split()[:120])
                st.session_state.clear_speech = True
                st.rerun()

    score = st.session_state.get("crowd")
    with right:
        html(ui.crowd_meter(score))
        html(ui.live_reactions(st.session_state.get("reactions", [])))
        html(ui.if_ended_now(score if score is None else score + (C.RIVAL_FUNDED_DEBATE_PENALTY
                                                                   if cid == "debate" and g.flags["rival_funded"] else 0)))
        last = g.slot + 1 >= len(g.lineup)
        if st.button("End day" if last else "Next visitor", type="primary", use_container_width=True,
                     disabled=not E.visit_over(g) and g.mayor_turns == 0):
            with st.spinner("Counting the applause..."):
                finish_visit()
            st.rerun()


def end_of_day_screen(g):
    show_toasts()
    if not st.session_state.get("headline"):
        brain, offline = get_brain(), ScriptedBrain()
        with st.spinner("Ang Pahayagan ng Pogi is going to print..."):
            st.session_state.headline = call(brain.headline, g, fallback=offline.headline)
    today = [r for r in g.log if r["day"] == g.day]
    big = max(today, key=lambda r: abs(r["d_wealth"]) / 10000 + abs(r["d_approval"]) + abs(r["d_suspicion"]), default=None)
    emoji = get_card(big["visitor"]).emoji if big else "🏛️"
    html(f"<div class='banderitas'></div><div class='daytitle'><div class='av'>{ui.esc(ui.initials(g.mayor_name))}</div>"
         f"<div><b>END OF ARAW {g.day}</b><span class='muted'>{C.TERM_DAYS - g.day} day(s) left in your term</span></div></div>")
    left, right = st.columns([1.45, 1], gap="large")
    html(ui.end_of_day_paper(g.day, st.session_state.headline, [r["memory_note"] for r in today], emoji), left)
    with right:
        html(ui.todays_visitors(today, get_card))
        html(ui.your_stats(g.day_start, g))
        html(ui.tomorrow(TOMORROW.get(g.day + 1, "A normal day. Probably.") if g.day < C.TERM_DAYS
                         else "Your term ends tonight. Let's see how history remembers you."))
        c1, c2 = st.columns(2)
        if c1.button("Main menu", use_container_width=True):
            st.session_state.screen = "title"
            st.rerun()
        label = "Finish term" if g.day >= C.TERM_DAYS else f"Start Araw {g.day + 1}"
        if c2.button(label, type="primary", use_container_width=True):
            start_next_day()
            st.rerun()


def game_over_screen(g):
    show_toasts()
    title, won, headline = E.ENDINGS[g.ending]
    if won and not st.session_state.get("celebrated"):
        st.session_state.celebrated = True
        st.balloons()
    left, right = st.columns([2.3, 1], gap="large")
    with left:
        html(ui.game_over_head(g, title, won))
        html(ui.stat_boxes(g, g.day))
        html(f"<div class='paper-mini' style='margin-bottom:.6rem'><div class='mast'>Ang Pahayagan ng Pogi · Special edition</div>"
             f"<div class='head'>{ui.esc(headline)}</div></div>")
        html(ui.key_moments(g.log))
        st.caption(f"Score: {E.score(g):,} (wealth ÷ 1,000 + approval × 10 − suspicion × 5). The auditor this run was "
                   f"{get_card(g.auditor_id).name if g.auditor_id else 'nobody. You were paranoid for nothing'}.")
        _, c1, c2, _ = st.columns([1, 1, 1, 1])
        if c1.button("Main menu", use_container_width=True):
            st.session_state.screen = "title"
            st.rerun()
        if c2.button("Play again", type="primary", use_container_width=True):
            new_term_dialog()
    html(ui.all_endings(g.ending), right)


# ---------------------------------------------------------------------------

def sidebar():
    g = st.session_state.get("game")
    with st.sidebar:
        st.markdown("## 🏛️ Pogi City Hall")
        s = settings()
        st.caption(f"AI: {s['provider']}" + (f" · {s['model']}" if s["provider"] != "Offline demo" else ""))
        if st.button("⚙️ Settings", use_container_width=True):
            settings_dialog()
        if st.button("🏠 Main menu", use_container_width=True):
            st.session_state.screen = "title"
            st.rerun()
        if g:
            log = {"exported": datetime.now().isoformat(timespec="seconds"), "state": g.to_dict()}
            st.download_button("⬇️ Export chat history", json.dumps(log, ensure_ascii=False, indent=2),
                               file_name=f"the-mayor-araw{g.day}.json", mime="application/json",
                               use_container_width=True)


def main():
    sidebar()
    g = st.session_state.get("game")
    if not g or st.session_state.get("screen", "title") == "title":
        title_screen()
        return
    if g.phase == "briefing":
        E.begin_visit(g)
        with st.spinner("Someone's knocking..."):
            visitor_opening()
    if g.phase == "ended":
        game_over_screen(g)
    elif g.phase == "night":
        end_of_day_screen(g)
    elif get_card(g.current_id()).kind == "speech":
        speech_screen(g)
    else:
        game_screen(g)


main()
