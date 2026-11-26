"""HTML/CSS building blocks for the Streamlit UI, laid out after the team's Figma lo-fi screens
(title, main game, envelope offer, debate, end of day, game over).

Every piece of player or model text goes through esc() before it lands in HTML.

The hi-fi look from the Figma game screen lives in ui_hifi.py and is hooked in at the very bottom."""

import html
import re

from . import config as C

PORTRAIT_COLORS = {
    "don_ramon": ("#f6d365", "#c79a2b"), "lola_rosing": ("#ffd1dc", "#e58fa8"),
    "ms_reyes": ("#c3e8ff", "#5aa9e6"), "engr_santos": ("#ffe0a3", "#e0a030"),
    "kuya_boy": ("#d9e4c8", "#8aa66b"), "boss_erning": ("#ffc9a3", "#e07b39"),
    "kap_luz": ("#e3d4ff", "#9b7be0"), "atty_villaflor": ("#d6d6e7", "#6a6a8e"),
    "sir_jepoy": ("#ffb3f0", "#d455b8"), "nanay_merly": ("#cde7e1", "#5fa596"),
    "vm_ging": ("#ffe8b3", "#e0b23c"), "carlo": ("#b8f0d0", "#3fbf7f"),
    "typhoon": ("#b8d4e8", "#3d6f94"), "fiesta": ("#ffd6a5", "#ff8c42"),
    "scandal": ("#ffb3b3", "#c8102e"), "ribbon": ("#ffd8b3", "#e8812e"),
    "debate": ("#cfd8ff", "#3a4fbf"),
}

SCENES = {   # backdrop behind the character, by visitor or event
    "typhoon": "🌧️🌊🏚️", "fiesta": "🎆🎉🎶", "scandal": "📸📹📱", "ribbon": "🏀🏟️📣", "debate": "🎤🏛️👥",
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Playfair+Display:wght@700;900&family=Poppins:wght@400;500;600;700&display=swap');
:root{ --red:#c8102e; --blue:#0038a8; --gold:#fcd116; --ink:#221a12; --paper:#fbf4e4; --muted:#7a6a58;
  --card:#ffffff; --line:#e6d8bf; --soft:#f6efe2; }
html, body, [data-testid="stAppViewContainer"], .stMarkdown, button, input, textarea{font-family:'Poppins',sans-serif;}
[data-testid="stAppViewContainer"]{
  background: radial-gradient(circle at 15% 0%, rgba(252,209,22,.16), transparent 40%),
              radial-gradient(circle at 95% 5%, rgba(200,16,46,.08), transparent 35%), #f5ecda;}
[data-testid="stHeader"]{background:transparent;}
.block-container{padding-top:1.4rem; max-width:1380px;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#4a2a19,#2e1a10);}
[data-testid="stSidebar"] *{color:#f8ecd8 !important;}
[data-testid="stSidebar"] [data-baseweb="select"] *{color:#221a12 !important;}
[data-testid="stBottom"], [data-testid="stBottom"]>div, [data-testid="stBottomBlockContainer"]{background:transparent !important;}
div[data-testid="stVerticalBlock"]{gap:.6rem;}

.box{background:var(--card); border:1.5px solid var(--line); border-radius:12px; padding:.75rem .9rem;
  box-shadow:0 3px 0 rgba(107,62,38,.12);}
.box.dark{border-color:#3a2c20;}
.h{font-size:.72rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; color:var(--ink); margin-bottom:.45rem;}
.muted{color:var(--muted); font-size:.8rem;}
.tag{display:inline-block; font-size:.62rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase;
  padding:.12rem .45rem; border:1.5px solid #3a2c20; border-radius:5px; background:#fff; color:#3a2c20; white-space:nowrap;}
.tag.now{background:var(--blue); border-color:var(--blue); color:#fff;}
.tag.deal{background:#e3f6e8; border-color:#15703a; color:#15703a;}
.tag.bad{background:#fde2e6; border-color:#9b0d23; color:#9b0d23;}
.tag.gold{background:#fff3c4; border-color:#a07800; color:#7a5d00;}
.av{width:36px; height:36px; border-radius:50%; display:grid; place-items:center; font-size:19px; flex:none;
  border:2px dashed #bba98c; background:var(--soft);}

/* banderitas */
.banderitas{height:18px; margin:-.5rem 0 .5rem;
  background: conic-gradient(from 135deg at 50% 0, var(--red) 0 90deg, transparent 0) 0 0/36px 18px,
   conic-gradient(from 135deg at 50% 0, var(--blue) 0 90deg, transparent 0) 12px 0/36px 18px,
   conic-gradient(from 135deg at 50% 0, var(--gold) 0 90deg, transparent 0) 24px 0/36px 18px;}

/* top bar */
.topbar{display:grid; grid-template-columns:auto 1fr auto; gap:1rem; align-items:center; margin-bottom:.6rem;}
.mayor{display:flex; gap:.6rem; align-items:center; background:#fff; border:1.5px solid #3a2c20; border-radius:10px; padding:.45rem .8rem .45rem .5rem;}
.mayor .av{width:40px; height:40px; font-weight:700; font-size:.85rem; border-style:solid; border-color:#3a2c20; background:#fff3c4;}
.mayor b{display:block; font-size:.9rem; letter-spacing:.02em;} .mayor span{font-size:.72rem; color:var(--muted);}
.araw{justify-self:center; background:#fff; border:1.5px solid #3a2c20; border-radius:10px; padding:.35rem 1.4rem .5rem; text-align:center;}
.araw b{font-family:'Anton',sans-serif; font-size:1.35rem; letter-spacing:.06em;}
.dots{display:flex; gap:4px; justify-content:center; margin-top:.2rem;}
.dots i{width:16px; height:6px; border-radius:3px; background:#e3d8c4;}
.dots i.done{background:#3a2c20;} .dots i.now{background:var(--red);}
.stats{display:flex; gap:.6rem;}
.stat{background:#fff; border:1.5px solid #3a2c20; border-radius:10px; padding:.4rem .7rem .5rem; width:190px;}
.stat .row{display:flex; justify-content:space-between; font-size:.64rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase;}
.stat .row em{font-style:normal; letter-spacing:0; font-size:.72rem;}
.bar{height:7px; border-radius:99px; background:#ece3d2; overflow:hidden; margin-top:.35rem;}
.bar>span{display:block; height:100%; border-radius:99px;}
@media (max-width:1000px){ .topbar{grid-template-columns:1fr;} .araw{justify-self:start;} .stats{flex-wrap:wrap;} .stat{width:auto; flex:1;} }

.banner{display:flex; gap:.7rem; align-items:center; background:#fff; border:1.5px solid #3a2c20; border-radius:10px;
  padding:.55rem .8rem; margin-bottom:.7rem; font-size:.9rem;}
.banner.hot{background:#fff6f6; border-color:var(--red);}

/* left column */
.vlist .v{display:flex; gap:.55rem; align-items:center; padding:.35rem 0; border-bottom:1px dashed #eadfcb;}
.vlist .v:last-child{border-bottom:none;}
.vlist .v .nm{flex:1; line-height:1.15;} .vlist .v .nm b{font-size:.85rem;} .vlist .v .nm div{font-size:.7rem; color:var(--muted);}
.vlist .v.done{opacity:.55;}
.notes p{font-size:.8rem; margin:0 0 .45rem; line-height:1.35;}

/* center */
.scene{position:relative; height:250px; border-radius:12px; border:1.5px solid var(--line); overflow:hidden;
  background:linear-gradient(180deg,#fdf6e8 0%, #f2e4c8 62%, #8a5a3c 62%, #6b3e26 100%);}
.scene .wall{position:absolute; inset:0 0 38% 0; display:flex; justify-content:space-between; padding:.8rem 1.2rem; font-size:1.5rem; opacity:.55;}
.scene .flag{position:absolute; top:14px; right:18px; width:54px; height:32px; border:1px solid #c9b89a;
  background:linear-gradient(#0038a8 50%, #c8102e 50%);}
.scene .flag:before{content:""; position:absolute; left:0; top:0; border-left:28px solid #fff; border-top:16px solid transparent; border-bottom:16px solid transparent;}
.scene .seal{position:absolute; top:12px; left:18px; width:46px; height:46px; border-radius:50%; background:#fcd116;
  border:3px solid #c79a2b; display:grid; place-items:center; font-size:.5rem; font-weight:800; color:#6b4d12; text-align:center; line-height:1;}
.scene .char{position:absolute; left:50%; bottom:22px; transform:translateX(-50%); width:150px; height:150px; border-radius:50%;
  display:grid; place-items:center; font-size:96px; border:5px solid #fff; box-shadow:0 0 0 3px var(--ring,#ccc), 0 10px 22px rgba(0,0,0,.25);
  animation:walkin .5s ease-out;}
.scene .desk{position:absolute; left:8%; right:8%; bottom:0; height:30px; background:#4a2a19; border-radius:6px 6px 0 0;}
.scene .desk:after{content:"MAYOR"; position:absolute; left:50%; top:6px; transform:translateX(-50%); background:linear-gradient(#d9b35b,#a77c27);
  color:#2b1d07; font-size:.6rem; font-weight:800; letter-spacing:.2em; padding:.1rem .6rem; border-radius:3px;}
.scene.event{background:linear-gradient(180deg,#1b2a5e 0%, #34478f 60%, #6b3e26 60%, #4a2a19 100%);}
.scene.event .wall{opacity:.9; font-size:2rem;}
@keyframes walkin{from{transform:translateX(-80%) scale(.85); opacity:0} to{transform:translateX(-50%); opacity:1}}
.plate{display:flex; justify-content:center; margin:-1.05rem 0 .4rem; position:relative; z-index:2;}
.plate div{background:#fff; border:1.5px solid #3a2c20; border-radius:8px; padding:.3rem .9rem; font-size:.75rem; color:var(--muted);}
.plate b{color:var(--ink); letter-spacing:.06em; text-transform:uppercase; font-size:.82rem; margin-right:.35rem;}
.dialogue{background:#fff; border:2px solid #3a2c20; border-radius:12px; padding:.75rem 1rem; min-height:92px; animation:pop .25s ease-out;}
.dialogue .said{font-size:.8rem; color:var(--muted); margin-bottom:.35rem;}
.dialogue .line{font-size:1.12rem; font-weight:600; line-height:1.4;}
.dialogue .kuya{margin-top:.5rem; background:#fff7cc; border:1.5px dashed #e0b400; border-radius:8px; padding:.35rem .6rem; font-size:.82rem; color:#5a4500;}
@keyframes pop{from{transform:translateY(6px); opacity:0} to{transform:none; opacity:1}}
.act{font-style:italic; color:#8a7a66; font-weight:400;}
.log .m{font-size:.85rem; margin:.25rem 0; line-height:1.35;} .log .m b{font-size:.7rem; letter-spacing:.06em; text-transform:uppercase; color:var(--muted);}

/* right column */
.paper-mini{background:var(--paper); border:1.5px solid #3a2c20; border-radius:10px; padding:.7rem .85rem;}
.paper-mini .mast{font-size:.66rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; border-bottom:2px solid var(--ink); padding-bottom:.3rem;}
.paper-mini .head{font-family:'Anton',sans-serif; font-size:1.3rem; line-height:1.08; text-transform:uppercase; margin-top:.3rem;}
.deal b{display:block; font-size:.9rem; margin:.3rem 0 .15rem;} .deal div{font-size:.75rem; color:var(--muted);}

/* buttons */
button[data-testid^="stBaseButton"]{border-radius:9px !important; font-weight:600 !important;}
button[data-testid="stBaseButton-secondary"], button[data-testid="stBaseButton-secondaryFormSubmit"]{border:1.5px solid #3a2c20 !important; background:#fff !important; color:#3a2c20 !important;}
button[data-testid="stBaseButton-secondary"]:hover{background:#fff6dd !important;}
button[data-testid="stBaseButton-primary"], button[data-testid="stBaseButton-primaryFormSubmit"]{background:#2b2b2b !important; border:1.5px solid #2b2b2b !important; color:#fff !important;}
button[data-testid="stBaseButton-primary"]:hover{background:var(--red) !important; border-color:var(--red) !important;}
button:disabled{opacity:.45;}
[data-testid="stForm"]{border:none; padding:0;}

/* title */
.ttl-top{display:flex; justify-content:space-between; font-size:.75rem; color:var(--muted); margin-bottom:.5rem;}
.art{background:#fff; border:1.5px dashed #bba98c; border-radius:14px; height:330px; display:flex; flex-direction:column;
  align-items:center; justify-content:center; gap:.4rem; text-align:center; padding:1rem;}
.art .big{font-size:110px; line-height:1;}
.art .grid{display:grid; grid-template-columns:repeat(3,1fr); gap:.5rem; font-size:44px;}
.art .grid span{width:64px; height:64px; border-radius:50%; display:grid; place-items:center; border:2px solid #fff; box-shadow:0 0 0 2px #e6d8bf;}
.logo{background:linear-gradient(160deg,#0038a8,#0b2a6f); border-radius:14px; height:150px; display:grid; place-items:center; overflow:hidden;}
.logo svg{height:140px;}
.title{font-family:'Anton',sans-serif; font-size:4.2rem; text-align:center; letter-spacing:.04em; line-height:1; margin:.6rem 0 .2rem; color:var(--ink);}
.title span{color:var(--red);}
.sub{text-align:center; color:var(--muted); margin-bottom:.8rem;}
.foot{text-align:center; color:var(--muted); font-size:.75rem; margin-top:1.2rem;}

/* newspaper (end of day) */
.paper{background:#fff; color:#111; border:1px solid #ddd; border-radius:2px; padding:1rem 1.15rem 1.2rem;
  box-shadow:0 3px 14px rgba(0,0,0,.08); max-width:100%; overflow:hidden;}
.paper .strip{display:grid; grid-template-columns:auto 1fr; gap:.8rem; align-items:center;
  border-bottom:7px solid #ffd900; padding-bottom:.35rem;}
.paper .paper-city{font-size:.65rem; line-height:1.05; font-weight:500; white-space:nowrap;}
.paper .paper-city strong{display:block; color:#f00000; font-family:Arial,sans-serif; font-size:2rem;
  line-height:.9; font-weight:1000; letter-spacing:-.08em;}
.paper .paper-brand{font-family:Arial Black,Arial,sans-serif; font-size:clamp(2rem,5vw,4rem);
  line-height:.9; font-weight:1000; letter-spacing:-.075em; text-align:right; white-space:nowrap;}
.paper .head{font-family:Arial Black,Arial,sans-serif; color:#f00000; font-size:clamp(2rem,5vw,3.8rem);
  line-height:.95; font-weight:1000; letter-spacing:-.045em; text-transform:uppercase; text-align:center;
  margin:.45rem 0 .35rem; overflow-wrap:anywhere;}
.paper .subhead{font-family:Arial Black,Arial,sans-serif; font-size:1.65rem; line-height:1.05;
  font-weight:1000; text-align:center; margin:0 0 .55rem;}
.paper .lead-grid{display:grid; grid-template-columns:1.65fr 1fr; gap:.55rem; align-items:start;}
.paper .photo{min-height:190px; border:0; display:grid; place-items:center; font-size:clamp(4rem,9vw,6rem);
  border-radius:0; background:#555; color:#fff; filter:none;}
.paper .lead{font-family:Arial,sans-serif; font-size:.96rem; line-height:1.42; text-align:justify;
  overflow-wrap:anywhere;}
.paper .body-copy{font-family:Arial,sans-serif; font-size:.98rem; line-height:1.48; text-align:justify;
  margin:.6rem .2rem 0; overflow-wrap:anywhere;}
.paper .edition{font-size:.68rem; color:#555; text-align:right; margin-top:.55rem;}
@media(max-width:560px){.paper{padding:.75rem}.paper .lead-grid{grid-template-columns:1fr 1fr;gap:.45rem}
  .paper .photo{min-height:150px}.paper .lead,.paper .body-copy{font-size:.86rem}
  .paper .paper-city strong{font-size:1.55rem}.paper .subhead{font-size:1.3rem}}
.daytitle{display:flex; gap:.8rem; align-items:center; margin-bottom:.7rem;}
.daytitle .av{width:52px; height:52px; font-weight:700; border-style:solid; border-color:#3a2c20; background:#fff3c4;}
.daytitle b{font-family:'Anton',sans-serif; font-size:2rem; letter-spacing:.04em; display:block; line-height:1;}
.srow{margin:.45rem 0;} .srow .row{display:flex; justify-content:space-between; font-size:.8rem;}

/* game over */
.over{text-align:center;}
.over .big{font-family:'Anton',sans-serif; font-size:4rem; letter-spacing:.04em; line-height:1; margin:.4rem 0;}
.over .big.win{color:#15703a;} .over .big.lose{color:var(--red);}
.over .why{color:var(--muted); margin-bottom:.8rem;}
.endart{height:210px; border:1.5px dashed #bba98c; border-radius:12px; display:grid; place-items:center; font-size:96px; background:#fff;}
.sbox{display:grid; grid-template-columns:repeat(4,1fr); gap:.6rem; margin:.8rem 0;}
.sbox div{background:#fff; border:1.5px solid #3a2c20; border-radius:10px; padding:.45rem; text-align:center;}
.sbox small{display:block; font-size:.62rem; letter-spacing:.1em; text-transform:uppercase; color:var(--muted);}
.sbox b{font-family:'Anton',sans-serif; font-size:1.4rem;}
.endcard{background:#fff; border:1.5px solid var(--line); border-radius:12px; padding:.55rem .7rem; margin-bottom:.55rem; opacity:.65;}
.endcard.this{border:2.5px solid #3a2c20; opacity:1; box-shadow:0 3px 0 rgba(0,0,0,.15);}
.endcard .pic{height:60px; border-radius:8px; background:var(--soft); display:grid; place-items:center; font-size:34px;}
.endcard b{display:block; font-size:.85rem; margin-top:.3rem;} .endcard div.d{font-size:.72rem; color:var(--muted);}

/* debate */
.meter{display:flex; gap:4px; margin:.3rem 0;} .meter i{flex:1; height:16px; border-radius:4px; background:#ece3d2;}
.meter i.on{background:#3a2c20;}
.meter-lbl{display:flex; justify-content:space-between; font-size:.68rem; color:var(--muted);}
.reactions p{font-size:.8rem; margin:.25rem 0;}
.question{background:#fff; border:2px solid #3a2c20; border-radius:12px; padding:.65rem .9rem;}
.question .line{font-size:1.08rem; font-weight:600; margin-top:.35rem;}
</style>
"""

CITY_HALL_SVG = """<svg viewBox="0 0 330 200" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
<rect x="0" y="185" width="330" height="15" fill="#0b1f4d"/><rect x="40" y="95" width="250" height="90" fill="#f5ecd9"/>
<polygon points="30,98 165,40 300,98" fill="#fff6e3"/><polygon points="55,92 165,50 275,92" fill="#e9dcc1"/>
<circle cx="165" cy="76" r="11" fill="#fcd116"/><g fill="#d6c6a6"><rect x="58" y="100" width="12" height="85"/>
<rect x="92" y="100" width="12" height="85"/><rect x="126" y="100" width="12" height="85"/><rect x="192" y="100" width="12" height="85"/>
<rect x="226" y="100" width="12" height="85"/><rect x="260" y="100" width="12" height="85"/></g>
<rect x="148" y="135" width="34" height="50" fill="#6b3e26"/><rect x="40" y="180" width="250" height="6" fill="#d6c6a6"/>
<line x1="165" y1="40" x2="165" y2="6" stroke="#ddd" stroke-width="2"/><rect x="166" y="6" width="34" height="10" fill="#0038a8"/>
<rect x="166" y="16" width="34" height="10" fill="#c8102e"/><polygon points="166,6 180,16 166,26" fill="#fff"/>
<text x="165" y="128" font-family="Anton,sans-serif" font-size="11" text-anchor="middle" fill="#6b3e26">POGI CITY HALL</text></svg>"""


# ---------------------------------------------------------------------------

def esc(text) -> str:
    return html.escape(str(text or ""), quote=True)


def fmt_dialogue(text: str) -> str:
    """Escape, keep line breaks, and render [stage directions] in italics."""
    safe = esc(text).replace("\n", "<br>")
    return re.sub(r"\[([^\]]{1,120})\]", r"<span class='act'>[\1]</span>", safe)


def colors(card_id: str):
    return PORTRAIT_COLORS.get(card_id, ("#eee", "#bbb"))


def initials(name: str) -> str:
    parts = [p for p in re.split(r"\s+", name.replace(".", "")) if p and p[0].isalpha()]
    return (parts[0][0] + (parts[1][0] if len(parts) > 1 else "")).upper() if parts else "?"


def bar(pct: float, color: str) -> str:
    return f"<div class='bar'><span style='width:{max(0, min(100, pct)):.0f}%;background:{color}'></span></div>"


def peso_short(n: int) -> str:
    return f"₱{n / 1_000_000:.2f}M".replace(".00M", "M") if n >= 1_000_000 else f"₱{n // 1000}K" if n >= 1000 else f"₱{n}"


def suspicion_color(s: int) -> str:
    return "#2e9e5b" if s < 25 else "#d4a800" if s < 50 else "#ea7a1f" if s < 75 else "#c8102e"


def suspicion_words(s: int) -> str:
    return ("Kalmado. Nobody's looking." if s < 25 else "May bulung-bulungan." if s < 50
            else "Mainit. The press is circling." if s < 75 else "Delikado. They're building a case.")


# ---------------------------------------------------------------------------
# Main game pieces

def topbar(g) -> str:
    dots = "".join(f"<i class='{'done' if d < g.day else 'now' if d == g.day else ''}'></i>"
                   for d in range(1, C.TERM_DAYS + 1))
    return f"""<div class='banderitas'></div>
<div class='topbar'>
<div class='mayor'><div class='av'>{esc(initials(g.mayor_name))}</div><div><b>MAYOR {esc(g.mayor_name.upper())}</b><span>Pogi City Hall</span></div></div>
<div class='araw'><b>ARAW {g.day} / {C.TERM_DAYS}</b><div class='dots'>{dots}</div></div>
<div class='stats'>
<div class='stat'><div class='row'><span>💰 Yaman</span><em>{peso_short(g.wealth)} / ₱1M</em></div>{bar(g.wealth / C.TARGET_WEALTH * 100, 'linear-gradient(90deg,#fcd116,#e0a800)')}</div>
<div class='stat'><div class='row'><span>👍 Approval</span><em>{g.approval} / 100</em></div>{bar(g.approval, '#0038a8')}</div>
<div class='stat'><div class='row'><span>🔎 Suspicion</span><em>{g.suspicion} / 100</em></div>{bar(g.suspicion, suspicion_color(g.suspicion))}</div>
</div></div>"""


def banner(label: str, text: str, hot: bool = False) -> str:
    return f"<div class='banner {'hot' if hot else ''}'><span class='tag {'bad' if hot else ''}'>{esc(label)}</span><span>{text}</span></div>"


def visitors_today(g, get_card, events) -> str:
    rows = []
    for i, cid in enumerate(g.lineup):
        c = get_card(cid)
        met = g.visits.get(cid, 0) > (1 if i >= g.slot else 0) or i < g.slot
        hidden = c.hidden_name and i > g.slot and not met
        name = c.hidden_name if hidden else (c.role if cid in events else c.name)
        sub = "Contractor?" if hidden else (c.name if cid in events else c.role.split(",")[0])
        if i < g.slot or (i == g.slot and g.phase in ("night", "ended")):
            tag, cls = "Done", "v done"
            res = next((r for r in reversed(g.log) if r["visitor"] == cid and r["day"] == g.day), None)
            if res:
                tag = {"deal": "Deal", "paid": "Paid", "helped": "Helped", "refused": "Refused", "threatened": "Threat",
                       "stalled": "Stalled", "speech": "Spoke", "caught": "Caught"}.get(res["outcome"], "Done")
        elif i == g.slot:
            tag, cls = "Now", "v"
        elif i == g.slot + 1:
            tag, cls = "Next", "v"
        else:
            tag, cls = ("Hidden" if hidden else "Later"), "v"
        bg, _ = colors(cid)
        face = "?" if hidden else c.emoji
        tcls = "now" if tag == "Now" else "deal" if tag in ("Deal", "Helped", "Paid") else "bad" if tag in ("Refused", "Threat", "Caught") else ""
        rows.append(f"<div class='{cls}'><div class='av' style='background:{bg}'>{face}</div>"
                    f"<div class='nm'><b>{esc(name)}</b><div>{esc(sub)}</div></div><span class='tag {tcls}'>{tag}</span></div>")
    return f"<div class='box'><div class='h'>Visitors today</div><div class='vlist'>{''.join(rows)}</div></div>"


def memory_notes(g) -> str:
    notes = [r for r in g.log][-6:]
    if not notes:
        body = "<p class='muted'>Nothing yet. Everything you say is remembered.</p>"
    else:
        body = "".join(f"<p><b>Araw {r['day']}:</b> {esc(r['memory_note'])}</p>" for r in notes)
    return f"<div class='box notes'><div class='h'>Memory notes</div>{body}</div>"


def scene(card, cid: str, is_event: bool) -> str:
    bg, ring = colors(cid)
    wall = SCENES.get(cid, "🪴🖼️🕰️")
    parts = re.findall(r".\ufe0f?", wall)   # keep emoji variation selectors attached
    left, right = "".join(parts[:len(parts) // 2]), "".join(parts[len(parts) // 2:])
    return f"""<div class='scene {'event' if is_event else ''}'>
<div class='seal'>LUNGSOD<br>NG POGI</div><div class='flag'></div>
<div class='wall'><span>{left}</span><span>{right}</span></div>
<div class='char' style='background:radial-gradient(circle at 35% 30%, #fff, {bg} 62%); --ring:{ring}'>{card.emoji}</div>
<div class='desk'></div></div>"""


def nameplate(card, is_event: bool, slot: int, total: int, msg: int, turns: int) -> str:
    name = card.role if is_event else card.name
    sub = card.name if is_event else card.role.split(",")[0]
    return (f"<div class='plate'><div><b>{esc(name)}</b>{esc(sub)} · Visitor {slot + 1} of {total} · "
            f"Message {min(msg + 1, turns)} of ~{turns}</div></div>")


def dialogue(transcript, card) -> str:
    last_v = next((m for m in reversed(transcript) if m["role"] == "visitor"), None)
    last_m = None
    kuya = None
    for m in reversed(transcript):
        if m["role"] == "mayor":
            last_m = m
            break
        if m["role"] == "kuya":
            kuya = m
    said = f"<div class='said'>You said: “{fmt_dialogue(last_m['text'])}”</div>" if last_m else ""
    line = f"<div class='line'>“{fmt_dialogue(last_v['text'])}”</div>" if last_v else "<div class='line muted'>...</div>"
    kb = f"<div class='kuya'>🧔 <b>Kuya Boy, whispering:</b> {fmt_dialogue(kuya['text'])}</div>" if kuya else ""
    return f"<div class='dialogue'>{said}{line}{kb}</div>"


def history(transcript, card, mayor_name: str) -> str:
    rows = []
    for m in transcript:
        who = {"mayor": f"Mayor {mayor_name}", "visitor": card.name, "kuya": "Kuya Boy"}.get(m["role"], "")
        rows.append(f"<div class='m'><b>{esc(who)}</b><br>{fmt_dialogue(m['text'])}</div>")
    return f"<div class='log'>{''.join(rows)}</div>"


def paper_mini(headline: str | None) -> str:
    head = esc(headline) if headline else "BAGONG MAYOR, NANUMPA NA"
    return (f"<div class='paper-mini'><div class='mast'>Ang Pahayagan ng Pogi</div>"
            f"<div class='muted' style='margin-top:.3rem'>Yesterday's headline</div><div class='head'>{head}</div></div>")


def last_deal(r: dict | None) -> str:
    if not r:
        return ("<div class='box deal'><span class='tag'>Last visitor: none yet</span>"
                "<b>First visitor of the day</b><div>Results appear here after each visitor.</div></div>")
    label = {"deal": "Last visitor: deal", "paid": "Last visitor: you paid", "helped": "Last visitor: helped",
             "refused": "Last visitor: refused", "threatened": "Last visitor: threatened",
             "stalled": "Last visitor: stalled", "speech": "Last event", "caught": "Caught!"}.get(r["outcome"], "Last visitor")
    cls = "deal" if r["outcome"] in ("deal", "helped", "paid") else "bad" if r["outcome"] in ("refused", "threatened", "caught") else ""

    def d(label, v, money=False):
        if not v:
            return f"{label} 0"
        return f"{label} {'+' if v > 0 else '−'}{'₱' if money else ''}{abs(v):,}"
    extra = "".join(f"<div>• {esc(n)}</div>" for n in r["notes"])
    return (f"<div class='box deal'><span class='tag {cls}'>{label}</span><b>{esc(r['memory_note'])}</b>"
            f"<div>{d('Yaman', r['d_wealth'], True)} · {d('Approval', r['d_approval'])} · {d('Suspicion', r['d_suspicion'])}</div>{extra}</div>")


# ---------------------------------------------------------------------------
# Title

def title_art_left() -> str:
    return ("<div class='art'><div class='big'>🧑‍💼</div><b>Mayor of Pogi City</b>"
            "<div class='muted'>Fresh barong, fresh oath,<br>very flexible principles.</div></div>")


def title_art_right(cards) -> str:
    faces = "".join(f"<span style='background:{colors(cid)[0]}'>{'❓' if c.hidden_name else c.emoji}</span>" for cid, c in cards)
    return (f"<div class='art'><div class='grid'>{faces}</div><b>Today's visitors</b>"
            "<div class='muted'>Lola, Don Ramon, the reporter,<br>and someone who isn't who they say.</div></div>")


def title_center() -> str:
    return (f"<div class='logo'>{CITY_HALL_SVG}</div><div class='title'>THE <span>MAYOR</span></div>"
            "<div class='sub'>Run Pogi City for 10 days. Get rich. Don't get caught.</div>")


# ---------------------------------------------------------------------------
# End of day

def end_of_day_paper(day: int, headline: str, story: list, emoji: str) -> str:
    # Build the article only from the day's recorded memory notes.
    notes = [esc(str(note)) for note in story if note]
    fallback = "City hall was quiet today. Suspiciously quiet."
    lead = notes[0] if notes else fallback
    body = " ".join(notes[1:]) if len(notes) > 1 else "The mayor’s decisions today will shape what happens next in Pogi City."
    subhead = f"ARAW {day}: ANG MGA PANGYAYARI SA POGI CITY"
    return f"""<article class='paper'>
<div class='strip'>
  <div class='paper-city'>Lungsod ng<strong>POGI</strong></div>
  <div class='paper-brand'>Sonstar</div>
</div>
<div class='head'>{esc(headline)}</div>
<div class='subhead'>{subhead}</div>
<div class='lead-grid'>
  <div class='photo' aria-label='Newspaper photo'>{esc(emoji)}</div>
  <div class='lead'><b>POGI CITY</b> — {lead}</div>
</div>
<div class='body-copy'>{body}</div>
<div class='edition'>ANG PAHAYAGAN NG POGI · ARAW {day} EDITION</div>
</article>"""


def todays_visitors(results, get_card) -> str:
    rows = []
    for r in results:
        c = get_card(r["visitor"])
        bg, _ = colors(r["visitor"])
        tag = {"deal": "Deal", "paid": "Paid", "helped": "Helped", "refused": "Refused", "threatened": "Threat",
               "stalled": "Stalled", "speech": "Spoke", "caught": "Caught"}.get(r["outcome"], r["outcome"])
        if r["visitor"] == "engr_santos" or r["visitor"] == "boss_erning":
            tag = tag if r["outcome"] != "refused" else "Not caught"
        cls = "deal" if r["outcome"] in ("deal", "helped", "paid") else "bad" if r["outcome"] in ("refused", "threatened", "caught") else ""
        w = r["d_wealth"]
        rows.append(f"<div class='v'><div class='av' style='background:{bg}'>{c.emoji}</div><div class='nm'><b>{esc(c.name if c.kind == 'visitor' else c.role)}</b>"
                    f"<div>{'+' if w > 0 else '−' if w < 0 else ''}₱{abs(w):,} · Approval {r['d_approval']:+d} · Suspicion {r['d_suspicion']:+d}</div></div>"
                    f"<span class='tag {cls}'>{tag}</span></div>")
    return f"<div class='box'><div class='h'>Today's visitors</div><div class='vlist'>{''.join(rows) or '<p class=muted>Nobody came.</p>'}</div></div>"


def your_stats(start: dict, g) -> str:
    def row(label, a, b, pct, color, money=False):
        f = (lambda x: peso_short(x)) if money else str
        return f"<div class='srow'><div class='row'><span>{label}</span><b>{f(a)} → {f(b)}</b></div>{bar(pct, color)}</div>"
    return ("<div class='box'><div class='h'>Your stats</div>" +
            row("Yaman", start.get("wealth", 0), g.wealth, g.wealth / C.TARGET_WEALTH * 100, "#e0a800", True) +
            row("Approval", start.get("approval", 0), g.approval, g.approval, "#0038a8") +
            row("Suspicion", start.get("suspicion", 0), g.suspicion, g.suspicion, suspicion_color(g.suspicion)) + "</div>")


def tomorrow(text: str) -> str:
    return f"<div class='box'><span class='tag gold'>Tomorrow</span> <span style='font-size:.85rem'>{esc(text)}</span></div>"


# ---------------------------------------------------------------------------
# Game over

ENDING_ART = {"arrested_caught": "🚔", "arrested": "🚔", "ousted": "🔥", "dynasty": "👑", "retired_rich": "🛥️",
              "good_mayor": "😇", "broke": "🪧"}
ENDING_WHY = {
    "arrested_caught": "You took the undercover auditor's money.",
    "arrested": "Suspicion hit 100. The Integrity Commission came with a warrant.",
    "ousted": "Approval hit 0. The city stormed the gates.",
    "dynasty": "₱1,000,000 and the city still loves you. Your pamangkin is running for vice.",
    "retired_rich": "₱1,000,000 in the account. Nobody likes you, but who's asking?",
    "good_mayor": "You barely took a centavo and the people adore you. This was not the assignment.",
    "broke": "You served out the term without the money or the love.",
}
ALL_ENDINGS = [("dynasty", "Dynasty", "₱1M and approval 70+"), ("retired_rich", "Retired rich", "Reach ₱1M by the end of Araw 10"),
               ("arrested", "Arrested", "Suspicion reaches 100, or you bribe the auditor"),
               ("ousted", "Voted out", "Approval drops to 0 and the city riots"),
               ("good_mayor", "Accidentally good", "Approval 80+ with almost no money"),
               ("broke", "Broke and forgotten", "Anything else")]


def game_over_head(g, title: str, won: bool) -> str:
    return (f"<div class='over'><span class='tag'>Game over · Araw {g.day}</span>"
            f"<div class='big {'win' if won else 'lose'}'>{esc(title.upper())}!</div>"
            f"<div class='why'>{esc(ENDING_WHY.get(g.ending, ''))}</div>"
            f"<div class='endart'>{ENDING_ART.get(g.ending, '🏛️')}</div></div>")


def stat_boxes(g, days_served: int) -> str:
    return (f"<div class='sbox'><div><small>Yaman</small><b>₱{g.wealth:,}</b></div><div><small>Approval</small><b>{g.approval}</b></div>"
            f"<div><small>Suspicion</small><b>{g.suspicion}</b></div><div><small>Days served</small><b>{days_served} / {C.TERM_DAYS}</b></div></div>")


def key_moments(log) -> str:
    top = sorted(log, key=lambda r: -(abs(r["d_wealth"]) / 10000 + abs(r["d_approval"]) + abs(r["d_suspicion"])))[:4]
    top.sort(key=lambda r: r["day"])
    rows = "".join(f"<p><b>Araw {r['day']}:</b> {esc(r['memory_note'])}</p>" for r in top) or "<p class='muted'>Nothing happened. Impressive.</p>"
    return f"<div class='box notes'><div class='h'>Key moments</div>{rows}</div>"


def all_endings(current: str) -> str:
    cur = "arrested" if current == "arrested_caught" else current
    cards = "".join(f"<div class='endcard {'this' if k == cur else ''}'><div class='pic'>{ENDING_ART[k]}</div><b>{esc(t)}</b>"
                    f"<div class='d'>{esc(d)}{' (This ending)' if k == cur else ''}</div></div>" for k, t, d in ALL_ENDINGS)
    return f"<div class='h'>All endings</div>{cards}"


# ---------------------------------------------------------------------------
# Debate / speech events

def rival_card(rival_funded: bool, rival_said: str) -> str:
    backed = "Backed by Don Ramon (you turned him down)." if rival_funded else "Running on a 'clean government' platform."
    return (f"<div class='box'><div class='h'>Your rival</div><div class='endart' style='height:150px;font-size:70px'>🕴️</div>"
            f"<b style='display:block;margin-top:.5rem'>Konsehal Bong Tanyag</b><div class='muted'>{backed}</div></div>"
            f"<div class='box'><span class='tag'>Rival said</span><div style='margin-top:.4rem;font-size:.85rem'>“{esc(rival_said)}”</div></div>")


def crowd_card(card) -> str:
    return (f"<div class='box'><div class='h'>The crowd</div><div class='endart' style='height:150px;font-size:70px'>👥</div>"
            f"<b style='display:block;margin-top:.5rem'>{esc(card.role)}</b><div class='muted'>Hosted by {esc(card.name)}</div></div>")


def question_box(card, question: str, n: int, total: int) -> str:
    label = "Moderator" if card.id == "debate" else card.name
    return (f"<div class='question'><span class='tag'>{esc(label)} · Question {min(n, total)} of {total}</span>"
            f"<div class='line'>“{fmt_dialogue(question)}”</div></div>")


def crowd_meter(score: int | None) -> str:
    level = 3 if score is None else 1 + round((max(-15, min(15, score)) + 15) / 30 * 4)
    cells = "".join(f"<i class='{'on' if i < level else ''}'></i>" for i in range(5))
    return (f"<div class='box'><div class='h'>Crowd reaction</div><div class='meter'>{cells}</div>"
            f"<div class='meter-lbl'><span>Boo</span><span>Murmur</span><span>Cheer</span></div></div>")


def live_reactions(items: list) -> str:
    rows = "".join(f"<p>• {fmt_dialogue(t)}</p>" for t in items[-6:]) or "<p class='muted'>The crowd is waiting...</p>"
    return f"<div class='box reactions' style='min-height:200px'><div class='h'>Live reactions</div>{rows}</div>"


def if_ended_now(score: int | None) -> str:
    v = "—" if score is None else f"Approval {score:+d}"
    return f"<div class='box'><div class='muted' style='font-size:.65rem;letter-spacing:.1em;text-transform:uppercase'>If it ended now</div><b style='font-size:1.3rem'>{v}</b></div>"


# ---------------------------------------------------------------------------
# Hi-fi theme hook. Keep this at the VERY BOTTOM: ui_hifi imports the helpers above (esc, colors, bar, ...)
# from this module, so they must already be defined when this import runs.

from . import ui_hifi as _hf  # noqa: E402

CSS = CSS + _hf.CSS
topbar, banner, visitors_today, memory_notes = _hf.topbar, _hf.banner, _hf.visitors_today, _hf.memory_notes
scene, nameplate, dialogue, paper_mini, last_deal = _hf.scene, _hf.nameplate, _hf.dialogue, _hf.paper_mini, _hf.last_deal
