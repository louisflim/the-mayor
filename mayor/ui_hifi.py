"""Hi-fi theme for The Mayor: chunky game-UI look from the Figma "Game Screen" mockup.

Plugs into ui.py (see the 6-line hook at the bottom of this file's docstring):

    # ---- at the very bottom of ui.py ----
    from . import ui_hifi as _hf
    CSS = CSS + _hf.CSS
    topbar, banner, visitors_today, memory_notes = _hf.topbar, _hf.banner, _hf.visitors_today, _hf.memory_notes
    scene, nameplate, dialogue, paper_mini, last_deal = _hf.scene, _hf.nameplate, _hf.dialogue, _hf.paper_mini, _hf.last_deal

Same function signatures as ui.py, so the app code does not change, except for widget keys (see KEYS).
Optional art: assets/office_bg.png (full background) and assets/chars/<card_id>.png (character art).
"""
import base64
from pathlib import Path

from . import config as C
from .ui import esc, fmt_dialogue, colors, initials, bar, peso_short, suspicion_color, PORTRAIT_COLORS

_FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "proximanova-black.otf"
_FONT_DATA = base64.b64encode(_FONT_PATH.read_bytes()).decode() if _FONT_PATH.is_file() else None
_REGULAR_FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "proximanova-regular.otf"
_REGULAR_FONT_DATA = base64.b64encode(_REGULAR_FONT_PATH.read_bytes()).decode() if _REGULAR_FONT_PATH.is_file() else None
_FONT_FACE = (
    '@font-face{font-family:"Proxima Nova Black";src:url("data:font/otf;base64,'
    + _FONT_DATA
    + '") format("opentype");font-style:normal;font-weight:900;font-display:swap}'
    if _FONT_DATA else ""
)
_REGULAR_FONT_FACE = (
    '@font-face{font-family:"Proxima Nova";src:url("data:font/otf;base64,'
    + _REGULAR_FONT_DATA
    + '") format("opentype");font-style:normal;font-weight:400;font-display:swap}'
    if _REGULAR_FONT_DATA else ""
)

PORTRAIT_COLORS.update({"brownout": ("#ffe9a8", "#c79a2b"), "dengue": ("#d6f0d0", "#4f9a45"), "jeepney": ("#ffd0a8", "#e07b39"),
                        "graduation": ("#d9d6ff", "#5b52c9"), "callin": ("#ffc6c6", "#d8222f")})

# Give your Streamlit widgets these keys, e.g. st.button("Accept", key="act_accept"), and they get the mockup colours.
KEYS = {  # key: (face, edge, text)
    "act_accept": ("#2fa84f", "#3b2417", "#fff"), "act_haggle": ("#ffcf1f", "#3b2417", "#3a2a00"),
    "act_refuse": ("#d8222f", "#3b2417", "#fff"), "act_threaten": ("#7b49c9", "#3b2417", "#fff"),
    "act_sagot": ("#14226b", "#3b2417", "#fff"), "send": ("#d8222f", "#3b2417", "#fff"),
    "next_visitor": ("#2fa84f", "#3b2417", "#fff"), "end_day": ("#14226b", "#3b2417", "#fff"),
}

_ROOT = Path(__file__).resolve().parent
_ASSET_DIRS = [_ROOT / "assets", _ROOT.parent / "assets", Path.cwd() / "assets"]


def _uri(rel: str, limit: int = 1_500_000):
    for d in _ASSET_DIRS:
        p = d / rel
        if p.is_file() and p.stat().st_size <= limit:
            return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()
    return None


_bg = _uri("office_bg.png")
_BG = (f"[data-testid='stAppViewContainer']{{background:url({_bg}) center top/cover fixed !important;"
       "image-rendering:pixelated}" if _bg else
       "[data-testid='stAppViewContainer']{background:"
       "radial-gradient(ellipse 28% 38% at 50% 42%,rgba(255,214,150,.38),transparent 70%),"
       "linear-gradient(180deg,#bba9ae 0%,#a99aa6 40%,#5a4c63 78%,#2b2233 100%) fixed !important}")

_KEYCSS = "".join(
    f".st-key-{k}{{--edge:{e}}}.st-key-{k} button[data-testid^='stBaseButton']{{background:{f} !important;color:{t} !important}}"
    f".st-key-{k} button p{{color:{t} !important}}" for k, (f, e, t) in KEYS.items())

CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Lilita+One&family=Nunito:wght@600;700;800&display=swap');
""" + _FONT_FACE + _REGULAR_FONT_FACE + """
:root{--navy:#14226b;--navy2:#0b1550;--gold:#ffcf1f;--cream:#fff6dc;--wood:#7a4a22;--ink:#3b2417;--sh:4px 5px 0 #3b2417;
--red:#d8222f;--green:#2fa84f;--purple:#7b49c9;--muted:#7d6a55}
html,body,.stMarkdown,button,input,textarea{font-family:'Nunito',sans-serif !important}
""" + _BG + """
/* Proxima Nova is reserved for the end-of-day newspaper only. The rest of the app uses Lilita One + Nunito. */
.paper,.paper *{font-family:'Proxima Nova',sans-serif !important}
.paper .paper-city strong,.paper .paper-brand,.paper .head,.paper .subhead{
  font-family:'Proxima Nova Black','Arial Black',Impact,sans-serif !important;
}
[data-testid="stHeader"]{background:transparent;pointer-events:none}
.block-container{max-width:100% !important;padding:.8rem 1.6rem 1rem 4.8rem !important}
[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"],#MainMenu,footer{display:none !important}
.box{background:var(--cream);border:4px solid var(--ink);border-radius:22px;padding:.8rem .95rem;box-shadow:var(--sh)}
.h{font-family:'Lilita One',sans-serif;font-size:1.05rem;letter-spacing:.04em;text-transform:none;color:var(--wood);margin-bottom:.4rem}
.bar{height:9px;border:2px solid var(--ink);border-radius:99px;background:#fff;overflow:hidden;margin-top:.25rem}
.bar>span{display:block;height:100%}

/* top bar */
.hf-top{display:grid;grid-template-columns:auto 1fr auto;gap:1rem;align-items:start;margin-bottom:.7rem}
.hf-mayor{display:flex;gap:.7rem;align-items:center;background:var(--cream);border:4px solid var(--ink);border-radius:99px;
padding:.4rem 1.4rem .4rem .45rem;box-shadow:var(--sh)}
.hf-mayor .av{width:52px;height:52px;border-radius:50%;border:4px solid var(--gold);background:#fff;display:grid;place-items:center;
font-family:'Lilita One','Arial Black',Impact,sans-serif;color:#9a9a9a;font-size:1.2rem;overflow:hidden;flex:none}
.hf-mayor .av img,.hf-av img{width:100%;height:100%;object-fit:cover;object-position:center top;image-rendering:pixelated;display:block}
.hf-mayor b{display:block;font-family:'Lilita One','Arial Black',Impact,sans-serif;font-weight:400;font-size:1.5rem;color:var(--navy);line-height:1;letter-spacing:.03em}
.hf-mayor span{font-size:.8rem;color:var(--muted);font-weight:700}
.hf-araw{justify-self:center;background:var(--navy);border:4px solid var(--gold);border-radius:20px;padding:.35rem 1.6rem .45rem;
text-align:center;box-shadow:var(--sh)}
.hf-araw b{font-family:'Lilita One','Arial Black',Impact,sans-serif;font-weight:400;font-size:1.6rem;color:var(--gold);letter-spacing:.04em;line-height:1.1}
.hf-dots{display:flex;gap:5px;justify-content:center;margin:.2rem 0 .3rem}
.hf-dots i{width:11px;height:11px;border-radius:50%;background:#5a64a8}
.hf-dots i.done,.hf-dots i.now{background:var(--gold)}
.hf-dots i.now{box-shadow:0 0 0 2px var(--navy),0 0 0 4px var(--gold)}
.hf-araw small{color:#fff;font-size:.72rem;font-weight:700}
.hf-stats{display:flex;gap:.7rem}
.hf-stat{display:flex;align-items:center;gap:.5rem;background:var(--cream);border:4px solid var(--ink);border-radius:99px;
padding:.3rem 1rem .3rem .3rem;width:215px;box-shadow:var(--sh)}
.hf-stat .ic{width:42px;height:42px;border-radius:50%;border:3px solid #fff;display:grid;place-items:center;color:#fff;
font-weight:800;font-size:1.15rem;flex:none}
.hf-stat .sb{flex:1}
.hf-stat .row{display:flex;justify-content:space-between;align-items:baseline;font-size:.75rem;font-weight:800;color:var(--ink)}
.hf-stat .row em{font-style:normal;font-size:.7rem}
@media(max-width:1100px){.hf-top{grid-template-columns:1fr}.hf-araw{justify-self:start}.hf-stats{flex-wrap:wrap}.hf-stat{width:auto;flex:1}}

/* event banner */
.hf-banner{display:flex;gap:.8rem;align-items:center;justify-content:center;background:var(--navy);border:4px solid var(--gold);
border-radius:14px;padding:.45rem 1rem;margin-bottom:.8rem;color:#fff;font-weight:700;box-shadow:var(--sh)}
.hf-banner.hot{background:var(--red)}
.hf-banner b{font-family:'Lilita One','Arial Black',Impact,sans-serif;font-weight:400;font-size:1.45rem;color:var(--gold);letter-spacing:.03em}

/* left column */
.hf-list .hd{background:var(--wood);color:var(--cream);font-family:'Lilita One','Arial Black',Impact,sans-serif;text-align:center;padding:.4rem;border-radius:12px;
letter-spacing:.05em;margin-bottom:.3rem}
.hf-row{display:flex;align-items:center;gap:.65rem;padding:.4rem .1rem}
.hf-av{width:46px;height:46px;border-radius:50%;border:4px solid #b9b2a6;background:#e9e3d6;display:grid;place-items:center;
font-family:'Lilita One','Arial Black',Impact,sans-serif;color:#9a9486;flex:none;overflow:hidden}
.hf-row.cur .hf-av{border-color:var(--gold);background:#fff;color:var(--navy)}
.hf-av.q{background:var(--navy2);border-color:#3b3b3b;color:var(--gold);font-size:1.4rem}
.hf-row .nm{flex:1;line-height:1.1}
.hf-row .nm b{font-family:'Lilita One','Arial Black',Impact,sans-serif;font-weight:400;font-size:1.05rem;color:var(--ink)}
.hf-row .nm div{font-size:.72rem;color:var(--muted);font-weight:700}
.hf-row.done .nm{opacity:.6}
.pill{font-family:'Lilita One','Arial Black',Impact,sans-serif;font-size:.72rem;letter-spacing:.05em;color:#fff;padding:.12rem .6rem;border-radius:99px;background:var(--navy)}
.pill.ok{background:var(--green)}.pill.now{background:var(--red)}.pill.bad{background:#8f121c}.pill.mys{background:var(--purple)}
.hf-foot{font-size:.78rem;color:var(--muted);font-weight:700;margin-top:.3rem;line-height:1.3}
.hf-note{background:#ffe566;border:3px solid #e0b800;border-radius:6px;padding:1.1rem 1rem .8rem;transform:rotate(-1.4deg);
box-shadow:var(--sh);position:relative;margin-top:.7rem}
.hf-note:before{content:"";position:absolute;top:-9px;left:50%;width:16px;height:16px;border-radius:50%;background:var(--red);
box-shadow:0 2px 0 rgba(0,0,0,.4)}
.hf-note h4{font-family:'Lilita One','Arial Black',Impact,sans-serif;font-weight:400;font-size:1.3rem;margin:0 0 .4rem;color:var(--ink)}
.hf-note p{font-size:.85rem;font-weight:700;margin:0 0 .4rem;line-height:1.3;color:var(--ink)}

/* centre */
.hf-stage{height:clamp(200px,32vh,340px);border-radius:36px;border:6px solid var(--ink);display:grid;place-items:center;overflow:hidden;
background:#d9d5ca;box-shadow:var(--sh)}
.hf-stage.event{background:radial-gradient(circle at 50% 35%,#4b5fb0,#1b2a5e)}
.hf-stage img{max-height:100%;max-width:100%;image-rendering:pixelated;filter:drop-shadow(0 12px 0 rgba(59,36,23,.2));animation:hfin .45s ease-out}
.hf-stage .face{width:150px;height:150px;border-radius:50%;display:grid;place-items:center;font-size:92px;border:6px solid #fff;
box-shadow:0 0 0 4px var(--ring,#ccc),0 12px 0 rgba(0,0,0,.18);animation:hfin .45s ease-out}
@keyframes hfin{from{transform:translateX(-40%) scale(.9);opacity:0}to{transform:none;opacity:1}}
@media(prefers-reduced-motion:reduce){.hf-stage .face{animation:none}}
.hf-plate{display:flex;justify-content:center;margin:-1.7rem 0 .6rem;position:relative;z-index:2}
.hf-plate div{background:var(--navy);border:4px solid var(--gold);border-radius:16px;padding:.25rem 1.6rem .35rem;text-align:center;
box-shadow:var(--sh)}
.hf-plate b{display:block;font-family:'Lilita One','Arial Black',Impact,sans-serif;font-weight:400;font-size:1.7rem;color:#fff;letter-spacing:.03em;line-height:1.1}
.hf-plate span{font-size:.8rem;color:var(--gold);font-weight:800}
.hf-say{background:var(--cream);border:4px solid var(--ink);border-radius:24px;padding:.9rem 1.3rem;min-height:110px;
box-shadow:var(--sh)}
.hf-say .said{font-size:.85rem;color:var(--muted);font-weight:700;margin-bottom:.4rem}
.hf-say .line{font-size:1.3rem;font-weight:800;line-height:1.35;color:var(--ink)}
.hf-say .kuya{margin-top:.6rem;background:#fff2a8;border:2px dashed #c9a000;border-radius:10px;padding:.4rem .7rem;font-size:.85rem;font-weight:700}
.act{font-style:italic;color:var(--muted);font-weight:600}

/* right column */
.hf-news{background:#f7f0e0;border:3px solid var(--ink);border-radius:8px;padding:.8rem 1rem;transform:rotate(1.6deg);
box-shadow:var(--sh)}
.hf-news .mast{font-family:'Lilita One','Arial Black',Impact,sans-serif;font-size:.85rem;border-bottom:2px solid var(--ink);padding-bottom:.25rem;letter-spacing:.04em}
.hf-news .head{font-family:'Lilita One','Arial Black',Impact,sans-serif;font-size:1.5rem;line-height:1.05;margin:.3rem 0;text-transform:uppercase;color:var(--ink)}
.hf-news small{color:var(--muted);font-weight:700;font-size:.72rem}
.paper .photo{overflow:hidden}
.paper .photo img{max-height:100%;max-width:100%;object-fit:contain;image-rendering:pixelated}
.hf-deal{background:#fffdf3;border:4px solid var(--green);border-radius:14px;padding:.6rem .9rem;transform:rotate(-3deg);
box-shadow:var(--sh);margin:.8rem 0 .8rem -.4rem}
.hf-deal.bad{border-color:var(--red)}.hf-deal.idle{border-color:#b9b2a6}
.hf-deal h5{font-family:'Lilita One','Arial Black',Impact,sans-serif;font-weight:400;font-size:1.4rem;margin:0;color:var(--green)}
.hf-deal.bad h5{color:var(--red)}.hf-deal.idle h5{color:var(--muted)}
.hf-deal b{display:block;font-size:.88rem;font-weight:800;color:var(--ink);margin:.1rem 0 .2rem}
.hf-deal .up,.hf-deal .dn{font-weight:800;font-size:.85rem}.hf-deal .up{color:#15703a}.hf-deal .dn{color:var(--red)}

/* buttons */
button[data-testid^="stBaseButton"]{font-family:'Lilita One',sans-serif !important;font-weight:400 !important;font-size:1.2rem !important;min-height:48px;
letter-spacing:.05em;text-transform:uppercase;border:4px solid var(--ink) !important;border-radius:16px !important;
box-shadow:0 5px 0 var(--ink) !important;transition:transform .08s,box-shadow .08s}
button[data-testid="stBaseButton-secondary"]{background:var(--cream) !important;color:var(--ink) !important}
button[data-testid="stBaseButton-primary"]{background:var(--navy) !important;color:#fff !important;--edge:var(--navy2)}
""" + _KEYCSS + """
[class*="st-key-act_"] button{white-space:nowrap;padding:.45rem .2rem !important}
.st-key-act_sagot button p{font-size:.8rem !important}
[data-baseweb="input"],[data-baseweb="textarea"]{background:var(--cream) !important;border:4px solid var(--ink) !important;border-radius:16px !important;box-shadow:0 4px 0 var(--ink)}
[data-baseweb="input"] input,[data-baseweb="textarea"] textarea{background:transparent !important;color:var(--ink) !important;font-weight:700}
button[data-testid^="stBaseButton"]:active{transform:translateY(3px);box-shadow:0 2px 0 var(--ink) !important}
button[data-testid^="stBaseButton"]:focus-visible{outline:3px solid var(--gold) !important;outline-offset:2px}
[data-testid="stChatInput"]{background:var(--cream) !important;border:3px solid var(--ink) !important;border-radius:16px !important}
[data-testid="stChatInputSubmitButton"]{background:var(--red) !important;color:#fff !important;border-radius:10px !important}

/* full conversation */
.hf-convo{margin-bottom:.6rem;padding:.7rem .9rem;min-height:0;max-height:clamp(150px,27vh,300px);overflow-y:auto;display:flex;flex-direction:column-reverse}
.cv-in{display:flex;flex-direction:column;gap:.55rem}
.cv{max-width:88%}
.cv small{display:block;font-size:.68rem;font-weight:800;color:var(--muted);letter-spacing:.05em;text-transform:uppercase;margin:0 .4rem .1rem}
.cv .b{border:3px solid var(--ink);border-radius:18px;padding:.45rem .85rem;font-weight:700;font-size:1.02rem;line-height:1.35;color:var(--ink)}
.cv.v .b{background:#fff;border-bottom-left-radius:4px}
.cv.m{align-self:flex-end;text-align:right}.cv.m .b{background:#ffe566;border-bottom-right-radius:4px;text-align:left}
.cv.k .b{background:#fff2a8;border-style:dashed;font-size:.88rem}

/* main menu */
.st-key-menu_card{margin-top:1.6rem;background:#1b2a6b;border:3px solid var(--gold);border-radius:30px;padding:1.5rem 1.9rem 1.3rem !important;box-shadow:0 9px 0 var(--ink);gap:.55rem !important}
.mm-eyebrow{color:var(--gold);font-weight:800;letter-spacing:.12em;font-size:.9rem}
.mm-the{font-family:'Lilita One','Arial Black',Impact,sans-serif;color:#fff;font-size:2.6rem;line-height:1;margin-top:.2rem}
.mm-mayor{white-space:nowrap;font-family:'Lilita One','Arial Black',Impact,sans-serif;color:var(--gold);font-size:clamp(4rem,7.2vw,7rem);line-height:.9;letter-spacing:.01em;margin:-.2rem 0 .5rem}
.mm-tag{color:#fff;font-weight:700;font-size:1.1rem;padding-bottom:.9rem;border-bottom:2px solid rgba(252,209,22,.35);margin-bottom:.5rem}
.mm-cap{text-align:center;color:#fff;font-weight:700;font-size:.85rem}
.mm-pill{display:inline-block;background:#fff4dc;border:4px solid var(--ink);border-radius:14px;padding:.4rem 1.4rem;
font-family:'Lilita One','Arial Black',Impact,sans-serif;font-size:1.4rem;color:var(--ink);box-shadow:0 4px 0 var(--ink);text-transform:uppercase}
.mm-cast{display:flex;justify-content:flex-end;gap:.35rem;margin-top:.9rem}
.mm-cast img{width:56px;height:56px;border-radius:50%;border:4px solid var(--gold);background:var(--cream);
object-fit:cover;object-position:center top;image-rendering:pixelated;box-shadow:var(--sh)}
.mm-bar{position:fixed;left:0;right:0;bottom:0;height:116px;background:#41383a;color:#fff6dc;display:flex;justify-content:space-between;
align-items:center;padding:0 3rem;font-weight:700;z-index:1}
.st-key-menu_continue button[data-testid^='stBaseButton']{background:#fcd116 !important;color:#3b2417 !important;min-height:58px;font-size:1.5rem !important}
.st-key-menu_continue button p{color:#3b2417 !important}
.st-key-menu_new button[data-testid^='stBaseButton']{background:#fff4dc !important;color:#1b2a6b !important;min-height:58px;font-size:1.5rem !important}
.st-key-menu_new button p{color:#1b2a6b !important}
[class*="st-key-menu_sm_"] button[data-testid^='stBaseButton']{background:transparent !important;color:#fff6dc !important;
border:1.5px solid rgba(255,246,220,.55) !important;box-shadow:none !important;min-height:44px;font-size:.9rem !important;border-radius:14px !important;letter-spacing:.02em;white-space:nowrap;padding:0 .2rem !important}
[class*="st-key-menu_sm_"] button p{color:#fff6dc !important}

/* settings gear, top-left of every in-game screen (the sidebar is no longer used) */
[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],[data-testid="collapsedControl"]{display:none !important}
.st-key-settings_btn{position:fixed;top:.8rem;left:.8rem;z-index:1000001;width:auto !important}
.st-key-settings_btn button[data-testid^='stBaseButton']{width:50px;min-height:50px;padding:0 !important;background:var(--cream) !important;
color:var(--ink) !important;font-size:1.5rem !important;border-radius:16px !important}
</style>"""


# ---------------------------------------------------------------------------

def topbar(g) -> str:
    dots = "".join(f"<i class='{'done' if d < g.day else 'now' if d == g.day else ''}'></i>"
                   for d in range(1, C.TERM_DAYS + 1))
    left = max(0, C.TERM_DAYS - g.day)
    mayor_art = _uri(f"chars/avatar_mayor_{'female' if g.gender == 'female' else 'male'}.png")
    mayor_av = f"<img src='{mayor_art}' alt=''>" if mayor_art else esc(initials(g.mayor_name))


    def stat(icon, color, label, val, vcolor, pct, fill):
        return (f"<div class='hf-stat'><div class='ic' style='background:{color}'>{icon}</div><div class='sb'>"
                f"<div class='row'><span>{label}</span><em style='color:{vcolor}'>{val}</em></div>{bar(pct, fill)}</div></div>")
    return (f"<div class='hf-top'><div class='hf-mayor'><div class='av'>{mayor_av}</div>"
            f"<div><b>MAYOR {esc(g.mayor_name.upper())}</b><span>Pogi City Hall · Philippines</span></div></div>"
            f"<div class='hf-araw'><b>ARAW {g.day} / {C.TERM_DAYS}</b><div class='hf-dots'>{dots}</div>"
            f"<small>{left} day{'s' if left != 1 else ''} left in your term</small></div>"
            f"<div class='hf-stats'>"
            + stat("₱", "#e0a800", "YAMAN", f"{peso_short(g.wealth)} / ₱1M", "#9a7400", g.wealth / C.TARGET_WEALTH * 100, "#ffcf1f")
            + stat("♥", "#2fa84f", "APPROVAL", g.approval, "#1a6f33", g.approval, "#2fa84f")
            + stat("🔍", "#d8222f", "SUSPICION", g.suspicion, "#8f121c", g.suspicion, suspicion_color(g.suspicion))
            + "</div></div>")


def banner(label: str, text: str, hot: bool = False) -> str:
    return f"<div class='hf-banner {'hot' if hot else ''}'><b>{esc(label)}</b><span>{text}</span></div>"


_DONE = {"deal": "Deal", "paid": "Paid", "helped": "Helped", "refused": "Refused", "threatened": "Threat",
         "stalled": "Stalled", "speech": "Spoke", "caught": "Caught"}
_BAD = ("Refused", "Threat", "Caught")


def visitors_today(g, get_card, events) -> str:
    rows = []
    for i, cid in enumerate(g.lineup):
        c = get_card(cid)
        met = g.visits.get(cid, 0) > (1 if i >= g.slot else 0) or i < g.slot
        hidden = bool(c.hidden_name) and i > g.slot and not met
        name = c.hidden_name if hidden else (c.role if cid in events else c.name)
        sub = "Contractor?" if hidden else (c.name if cid in events else c.role.split(",")[0])
        row, pill, cls = "", "Later", ""
        if i < g.slot or (i == g.slot and g.phase in ("night", "ended")):
            res = next((r for r in reversed(g.log) if r["visitor"] == cid and r["day"] == g.day), None)
            pill = _DONE.get(res["outcome"], "Done") if res else "Done"
            row, cls = "done", "bad" if pill in _BAD else "ok"
        elif i == g.slot:
            row, pill, cls = "cur", "Now", "now"
        elif i == g.slot + 1:
            pill = "Next"
        elif hidden:
            pill, cls = "???", "mys"
        art = _uri(f"chars/avatar_{cid}.png")
        av = ("<div class='hf-av q'>?</div>" if hidden else
              f"<div class='hf-av'><img src='{art}' alt=''></div>" if art else
              f"<div class='hf-av'>{esc(initials(c.name))}</div>")
        rows.append(f"<div class='hf-row {row}'>{av}<div class='nm'><b>{esc(name)}</b><div>{esc(sub)}</div></div>"
                    f"<span class='pill {cls}'>{pill}</span></div>")
    foot = ("<div class='hf-foot'>Someone today is undercover. Watch how they talk.</div>"
            if any(get_card(x).hidden_name for x in g.lineup) else "")
    return f"<div class='box hf-list'><div class='hd'>BISITA NGAYON</div>{''.join(rows)}{foot}</div>"


def memory_notes(g) -> str:
    notes = g.log[-5:]
    body = ("".join(f"<p>Day {r['day']}: {esc(r['memory_note'])}</p>" for r in notes)
            or "<p>Nothing yet. Everything you say is remembered.</p>")
    return f"<div class='hf-note'><h4>MEMORY NOTES</h4>{body}</div>"


def scene(card, cid: str, is_event: bool) -> str:
    bg, ring = colors(cid)
    img = _uri(f"chars/{cid}.png")
    inner = (f"<img src='{img}' alt=''>" if img else
             f"<div class='face' style='background:radial-gradient(circle at 35% 30%,#fff,{bg} 65%);--ring:{ring}'>{card.emoji}</div>")
    return f"<div class='hf-stage {'event' if is_event else ''}'>{inner}</div>"


def nameplate(card, is_event: bool, slot: int, total: int, msg: int, turns: int) -> str:
    name = card.role if is_event else card.name
    sub = card.name if is_event else card.role.split(",")[0]
    return (f"<div class='hf-plate'><div><b>{esc(name.upper())}</b><span>{esc(sub)} · Visitor {slot + 1} of {total} · "
            f"Message {min(msg + 1, turns)} of ~{turns}</span></div></div>")


def dialogue(transcript, card) -> str:
    """Full conversation as chat bubbles. column-reverse keeps the newest message in view."""
    rows = []
    for m in transcript:
        who, cls = (("You", "m") if m["role"] == "mayor" else ("Kuya Boy · whispering", "k") if m["role"] == "kuya"
                    else (card.name, "v"))
        rows.append(f"<div class='cv {cls}'><small>{esc(who)}</small><div class='b'>{fmt_dialogue(m['text'])}</div></div>")
    body = "".join(rows) or "<div class='cv v'><div class='b'>...</div></div>"
    return f"<div class='hf-say hf-convo'><div class='cv-in'>{body}</div></div>"


def paper_mini(headline: str | None) -> str:
    head = esc(headline) if headline else "BAGONG MAYOR, NANUMPA NA"
    return (f"<div class='hf-news'><div class='mast'>ANG PAHAYAGAN NG POGI</div><small>Yesterday's headline</small>"
            f"<div class='head'>{head}</div><small>The AI writes a new headline from what you did each day.</small></div>")


def end_of_day_paper(day: int, headline: str, story: list, emoji: str, cid: str | None = None) -> str:
    notes = [esc(str(note)) for note in story if note]
    fallback = "City hall was quiet today. Suspiciously quiet."
    lead = notes[0] if notes else fallback
    body = " ".join(notes[1:]) if len(notes) > 1 else "The mayor’s decisions today will shape what happens next in Pogi City."
    subhead = f"ARAW {day}: ANG MGA PANGYAYARI SA POGI CITY"
    art = _uri(f"chars/{cid}.png") if cid else None
    photo = f"<img src='{art}' alt=''>" if art else esc(emoji)
    return f"""<article class='paper'>
<div class='strip'>
  <div class='paper-city'>Lungsod ng<strong>POGI</strong></div>
  <div class='paper-brand'>Sonstar</div>
</div>
<div class='head'>{esc(headline)}</div>
<div class='subhead'>{subhead}</div>
<div class='lead-grid'>
  <div class='photo' aria-label='Newspaper photo'>{photo}</div>
  <div class='lead'><b>POGI CITY</b> — {lead}</div>
</div>
<div class='body-copy'>{body}</div>
<div class='edition'>ANG PAHAYAGAN NG POGI · ARAW {day} EDITION</div>
</article>"""


def todays_visitors(results, get_card) -> str:
    rows = []
    for r in results:
        cid = r["visitor"]
        c = get_card(cid)
        tag = _DONE.get(r["outcome"], r["outcome"])
        cls = "bad" if tag in _BAD else "ok" if r["outcome"] in ("deal", "helped", "paid", "speech") else ""
        if cid in ("engr_santos", "boss_erning") and r["outcome"] == "refused":
            tag, cls = "Not caught", "ok"
        w = r["d_wealth"]
        art = _uri(f"chars/avatar_{cid}.png")
        av = (f"<div class='hf-av'><img src='{art}' alt=''></div>" if art else
              f"<div class='hf-av'>{esc(initials(c.name))}</div>")
        name = c.name if c.kind == "visitor" else c.role
        detail = (f"{'+' if w > 0 else '−' if w < 0 else ''}₱{abs(w):,} · "
                  f"Approval {r['d_approval']:+d} · Suspicion {r['d_suspicion']:+d}")
        rows.append(f"<div class='hf-row'>{av}<div class='nm'><b>{esc(name)}</b><div>{esc(detail)}</div></div>"
                    f"<span class='pill {cls}'>{esc(tag)}</span></div>")
    empty = "<div class='hf-foot'>Nobody came.</div>"
    return f"<div class='box hf-list'><div class='hd'>TODAY'S VISITORS</div>{''.join(rows) or empty}</div>"


_HEAD = {"deal": "DEAL!", "paid": "PAID!", "helped": "HELPED!", "refused": "REFUSED!", "threatened": "THREAT!",
         "stalled": "STALLED", "speech": "SPEECH!", "caught": "CAUGHT!"}


def last_deal(r: dict | None) -> str:
    if not r:
        return ("<div class='hf-deal idle'><h5>NO VISITS YET</h5><b>First visitor of the day</b>"
                "<div class='muted'>Results appear here after each visitor.</div></div>")
    cls = "" if r["outcome"] in ("deal", "helped", "paid", "speech") else "bad" if r["outcome"] in ("refused", "threatened", "caught") else "idle"

    def d(v, label, money=False, up_good=True):
        if not v:
            return ""
        good = (v > 0) == up_good
        return f"<div class='{'up' if good else 'dn'}'>{'+' if v > 0 else '−'}{'₱' if money else ''}{abs(v):,} {label}</div>"
    lines = d(r["d_wealth"], "Yaman", True) + d(r["d_approval"], "Approval") + d(r["d_suspicion"], "Suspicion", False, False)
    extra = "".join(f"<div class='muted'>• {esc(n)}</div>" for n in r["notes"])
    return f"<div class='hf-deal {cls}'><h5>{_HEAD.get(r['outcome'], 'DONE')}</h5><b>{esc(r['memory_note'])}</b>{lines}{extra}</div>"


# ---------------------------------------------------------------------------
# Main menu

MENU_BG = "<style>[data-testid='stAppViewContainer']{background:#bba9ae !important}</style>"


def menu_header() -> str:
    return ("<div class='mm-eyebrow'>POGI CITY · PHILIPPINES</div><div class='mm-the'>THE</div><div class='mm-mayor'>MAYOR</div>"
            "<div class='mm-tag'>Your city. Your choices. Your consequences.</div>")


def welcome_pill() -> str:
    faces = "".join(f"<img src='{art}' alt=''>" for art in
                    (_uri(f"chars/avatar_{cid}.png") for cid in
                     ("don_ramon", "lola_rosing", "ms_reyes", "kuya_boy", "atty_villaflor")) if art)
    return (f"<div style='text-align:right;margin-top:.4rem'><span class='mm-pill'>Welcome to City Hall</span>"
            f"<div class='mm-cast'>{faces}</div></div>")


def menu_bar() -> str:
    return "<div class='mm-bar'><span>A political survival game</span><span>Serve the people. Survive your term.</span></div>"