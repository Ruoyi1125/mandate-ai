"""
Persistent canvas background + transparent CSS overlay.

Uses the same-origin iframe trick: a height=1 st.components.v1.html injects
a <canvas> into window.parent.document so the animation lives beneath
Streamlit's own layout across ALL pages/steps.

KEY: body MUST stay transparent — canvas has z-index:-200 and an opaque
body background would completely cover it. The html element background
provides the dark fallback colour (below the canvas).
"""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

# ── Canvas animation injected into the PARENT document ─────────────────────
_BG_JS = r"""
<script>
(function(){
  try {
    const P = window.parent;
    const D = P.document;

    // Already running — just refresh mouse binding if needed
    if (D.getElementById('mandate-bg-canvas')) return;

    const C = D.createElement('canvas');
    C.id = 'mandate-bg-canvas';
    Object.assign(C.style, {
      position:'fixed', top:'0', left:'0',
      width:'100vw', height:'100vh',
      zIndex:'-200', pointerEvents:'none', display:'block',
    });
    D.body.insertBefore(C, D.body.firstChild);

    // CRITICAL: body must be transparent so canvas shows through
    // html element background sits BELOW canvas (z-index stack)
    D.body.style.background    = 'transparent';
    D.documentElement.style.background = '#040810';

    const ctx = C.getContext('2d');
    let W, H, T = 0;
    // Smooth mouse target — starts at center
    let mx = 0.5, my = 0.5;
    let smx = 0.5, smy = 0.5;

    function resize() {
      W = C.width  = P.innerWidth;
      H = C.height = P.innerHeight;
    }
    resize();
    P.addEventListener('resize', resize);

    // Mouse tracking on parent document
    D.addEventListener('mousemove', function(e) {
      mx = e.clientX / P.innerWidth;
      my = e.clientY / P.innerHeight;
    });

    /* ── Stars ── */
    const STARS = Array.from({length: 130}, () => ({
      x: Math.random(), y: Math.random(),
      r: Math.random() * .9 + .15,
      ph: Math.random() * 6.283,
      sp: Math.random() * .3 + .08,
    }));

    /* ── Left wave ── dense organic terrain, reacts to mouse Y ── */
    function drawLeft(t) {
      const boost = 1 + smy * .45; // mouse Y increases amplitude
      for (let L = 0; L < 12; L++) {
        const alpha = .028 + L * .01;
        ctx.beginPath();
        ctx.strokeStyle = 'rgba(255,255,255,' + alpha + ')';
        ctx.lineWidth = 1;
        const cx = W * .10 + L * 15 + smx * 18; // subtle X shift with mouse
        const y0 = H * .18, span = H * .62;
        for (let i = 0; i <= 200; i++) {
          const p  = i / 200;
          const y  = y0 + p * span;
          const en = Math.sin(p * Math.PI);
          const amp = (18 + L * 9) * en * boost;
          const x = cx
            + Math.sin(p * 20 + t * .52 + L * .88) * amp * .55
            + Math.sin(p * 8  + t * .26 + L * .45) * amp * .35
            + Math.cos(p * 4.5 + t * .14)           * amp * .1;
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.stroke();
      }
      const g = ctx.createRadialGradient(W*.18, H*.5, 0, W*.18, H*.5, W*.24);
      g.addColorStop(0, 'rgba(100,150,220,.055)');
      g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = g; ctx.fillRect(0, 0, W * .42, H);
    }

    /* ── Right wave ── flowing silk threads, reacts to mouse X ── */
    function drawRight(t) {
      const shift = (smx - .5) * 40; // mouse X shifts threads horizontally
      for (let i = 0; i < 20; i++) {
        const a = .024 + Math.abs(Math.sin(i * .38)) * .024;
        ctx.beginPath();
        ctx.strokeStyle = 'rgba(255,255,255,' + a + ')';
        ctx.lineWidth = .7;
        const bx = W * .62 + i * 21 + shift;
        const yo = H * (-.07 + i * .065);
        for (let j = 0; j <= 160; j++) {
          const p = j / 160;
          const x = bx
            + Math.sin(p * Math.PI * 3   + t * .36 + i * .66) * (22 + i * 3.5)
            + Math.cos(p * Math.PI * 1.3 + t * .18)            * 11;
          const y = yo + p * H * 1.15;
          j === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.stroke();
      }
      const g = ctx.createRadialGradient(W*.84, H*.32, 0, W*.84, H*.32, W*.2);
      g.addColorStop(0, 'rgba(130,180,255,.055)');
      g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = g; ctx.fillRect(W * .56, 0, W * .44, H);
    }

    /* ── Nebula ── follows mouse with a breathing pulse ── */
    function drawNebula(t) {
      const pulse = .22 + .06 * Math.sin(t * .42);
      // Nebula follows mouse (constrained to center region)
      const nx = W * (.28 + smx * .44);
      const ny = H * (.18 + smy * .62);
      const g = ctx.createRadialGradient(nx, ny, 0, nx, ny, 300);
      g.addColorStop(0,   'rgba(65,105,190,' + pulse + ')');
      g.addColorStop(.45, 'rgba(38,65,135,.028)');
      g.addColorStop(1,   'rgba(0,0,0,0)');
      ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    }

    function frame() {
      // Smooth mouse interpolation — .10 = snappy but not jarring
      smx += (mx - smx) * .10;
      smy += (my - smy) * .10;

      ctx.clearRect(0, 0, W, H);
      ctx.fillStyle = '#040810'; ctx.fillRect(0, 0, W, H);

      STARS.forEach(s => {
        const b = .22 + .32 * Math.sin(T * s.sp + s.ph);
        ctx.beginPath();
        ctx.arc(s.x*W, s.y*H, s.r, 0, 6.283);
        ctx.fillStyle = 'rgba(255,255,255,' + b + ')';
        ctx.fill();
      });

      drawNebula(T);
      drawLeft(T);
      drawRight(T);
      T += .006;
      requestAnimationFrame(frame);
    }
    frame();

  } catch(e) { console.warn('MANDATE bg:', e); }
})();
</script>
"""

# ── CSS: make all Streamlit containers transparent so canvas shows through ──
GLASS_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300&family=Inter:wght@200;300;400;500&family=JetBrains+Mono:wght@400;500&display=swap');

/* html element bg = viewport canvas = below canvas element = safe dark fallback */
html { background: #040810 !important; min-height: 100vh !important; }

/* body MUST be transparent — an opaque body covers z-index:-200 canvas */
body {
  background: transparent !important;
  background-color: transparent !important;
  color: rgba(232,228,220,.95) !important;
  -webkit-font-smoothing: antialiased;
}

/* All Streamlit containers transparent */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
[data-testid="stMain"],
[data-testid="stBottom"],
[data-testid="stBottomBlockContainer"],
[data-testid="stHeader"],
section[data-testid="stMain"] > div {
  background: transparent !important;
  background-color: transparent !important;
}

/* Hide Streamlit chrome */
header[data-testid="stHeader"], #MainMenu, footer,
[data-testid="stDecoration"], .stDecoration {
  display: none !important;
}

/* ── Page enter animation ─────────────────────────────────────────── */
@keyframes pageIn {
  from { opacity: 0; transform: translateY(18px); }
  to   { opacity: 1; transform: translateY(0); }
}
.block-container > div {
  animation: pageIn .6s cubic-bezier(.22,1,.36,1) both;
}

/* ── Staggered item reveal ────────────────────────────────────────── */
@keyframes revealItem {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Block container sizing */
.block-container {
  padding-top: 1rem !important;
  padding-bottom: 6rem !important;
  max-width: 1240px !important;
  padding-left: 2rem !important;
  padding-right: 2rem !important;
}

/* ── Typography ──────────────────────────────────────────────────── */
h1,h2,h3 { color: rgba(232,228,220,.95) !important; }

/* ── Ghost inputs ────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
  background: rgba(255,255,255,.035) !important;
  border: 1px solid rgba(232,228,220,.16) !important;
  border-radius: 6px !important;
  color: rgba(232,228,220,.92) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: .9rem !important;
  font-weight: 300 !important;
  caret-color: rgba(232,228,220,.7);
  transition: border-color .3s, box-shadow .3s, background .3s !important;
}
.stTextInput > div > div > input:hover,
.stTextArea > div > div > textarea:hover {
  border-color: rgba(140,180,240,.35) !important;
  background: rgba(255,255,255,.05) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: rgba(140,180,240,.6) !important;
  box-shadow: 0 0 0 2px rgba(140,180,240,.12), 0 0 24px rgba(140,180,240,.1) !important;
  background: rgba(255,255,255,.06) !important;
}

/* Mobile / Safari: force text colour & fix autofill white-on-white */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
  -webkit-text-fill-color: rgba(232,228,220,.92) !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
  color: rgba(232,228,220,.28) !important;
  -webkit-text-fill-color: rgba(232,228,220,.28) !important;
}
.stTextInput > div > div > input:-webkit-autofill,
.stTextInput > div > div > input:-webkit-autofill:hover,
.stTextInput > div > div > input:-webkit-autofill:focus,
.stTextArea > div > div > textarea:-webkit-autofill,
.stTextArea > div > div > textarea:-webkit-autofill:hover,
.stTextArea > div > div > textarea:-webkit-autofill:focus {
  -webkit-box-shadow: 0 0 0 1000px rgba(6,10,22,.97) inset !important;
  -webkit-text-fill-color: rgba(232,228,220,.92) !important;
  caret-color: rgba(232,228,220,.7) !important;
}
@media (max-width: 768px) {
  .stTextInput > div > div > input,
  .stTextArea > div > div > textarea {
    background: rgba(6,10,22,.9) !important;
    -webkit-text-fill-color: rgba(232,228,220,.92) !important;
  }
}

/* ── Labels ─────────────────────────────────────────────────────── */
.stTextInput label, .stTextArea label,
.stCheckbox label span, .stRadio label span,
.stFileUploader label, .stSelectbox label {
  color: rgba(232,228,220,.5) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: .7rem !important;
  font-weight: 400 !important;
  letter-spacing: .14em !important;
  text-transform: uppercase !important;
}

/* ── Checkbox / radio ────────────────────────────────────────────── */
.stCheckbox > label, .stRadio > label {
  color: rgba(232,228,220,.75) !important;
  transition: color .2s !important;
}
.stCheckbox > label:hover, .stRadio > label:hover {
  color: rgba(232,228,220,.95) !important;
}

/* ── Pill buttons ────────────────────────────────────────────────── */
.stButton > button {
  background: transparent !important;
  border: 1px solid rgba(232,228,220,.25) !important;
  border-radius: 40px !important;
  color: rgba(232,228,220,.82) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: .72rem !important;
  font-weight: 400 !important;
  letter-spacing: .18em !important;
  padding: .7em 2.2em !important;
  transition: all .4s cubic-bezier(.2,0,.2,1) !important;
}
.stButton > button:hover {
  border-color: rgba(140,180,240,.7) !important;
  background: rgba(100,150,220,.07) !important;
  color: rgba(200,225,255,.98) !important;
  box-shadow: 0 0 28px rgba(140,180,240,.2), 0 0 60px rgba(140,180,240,.06) !important;
}
.stButton > button[kind="primary"] {
  border-color: rgba(140,180,240,.5) !important;
  color: rgba(200,225,255,.95) !important;
}
.stButton > button[kind="primary"]:hover {
  border-color: rgba(140,180,240,.95) !important;
  background: rgba(100,150,220,.12) !important;
  box-shadow: 0 0 35px rgba(140,180,240,.28), 0 0 70px rgba(140,180,240,.1) !important;
}

/* ── Download buttons ────────────────────────────────────────────── */
.stDownloadButton > button {
  background: rgba(255,255,255,.03) !important;
  border: 1px solid rgba(232,228,220,.18) !important;
  border-radius: 6px !important;
  color: rgba(232,228,220,.65) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: .72rem !important;
  transition: all .3s !important;
}
.stDownloadButton > button:hover {
  border-color: rgba(232,228,220,.45) !important;
  background: rgba(255,255,255,.06) !important;
}

/* ── File uploader ───────────────────────────────────────────────── */
[data-testid="stFileUploadDropzone"] {
  background: rgba(255,255,255,.025) !important;
  border: 1px dashed rgba(232,228,220,.2) !important;
  border-radius: 8px !important;
  transition: border-color .3s, background .3s !important;
}
[data-testid="stFileUploadDropzone"]:hover {
  border-color: rgba(140,180,240,.4) !important;
  background: rgba(140,180,240,.03) !important;
}

/* ── Expander — accordion style, no boxy border ─────────────────── */
[data-testid="stExpander"] {
  background: transparent !important;
  border: none !important;
  border-bottom: 1px solid rgba(232,228,220,.06) !important;
  border-radius: 0 !important;
  margin-bottom: 0 !important;
  padding: .1rem 0 !important;
  transition: background .2s !important;
}
[data-testid="stExpander"]:first-of-type {
  border-top: 1px solid rgba(232,228,220,.06) !important;
}
[data-testid="stExpander"]:hover {
  background: rgba(255,255,255,.015) !important;
  border-color: rgba(140,180,240,.1) !important;
  box-shadow: none !important;
}
[data-testid="stExpander"] summary {
  color: rgba(232,228,220,.7) !important;
  font-size: .92rem !important;
  font-family: 'Cormorant Garamond', serif !important;
  font-weight: 300 !important;
  padding: .55rem .5rem !important;
  transition: color .25s !important;
}
[data-testid="stExpander"] summary:hover {
  color: rgba(232,228,220,.96) !important;
}
[data-testid="stExpander"] > div > div {
  padding: .2rem .5rem .8rem !important;
}

/* ── Status widget ───────────────────────────────────────────────── */
[data-testid="stStatusWidget"] {
  background: rgba(255,255,255,.04) !important;
  border: 1px solid rgba(232,228,220,.12) !important;
  border-radius: 8px !important;
}

/* ── Alerts ──────────────────────────────────────────────────────── */
[data-baseweb="notification"] {
  background: rgba(255,255,255,.04) !important;
  border-radius: 8px !important;
}

/* ── HR / code / scrollbar ───────────────────────────────────────── */
hr { border-color: rgba(232,228,220,.08) !important; }
code {
  background: rgba(255,255,255,.07) !important;
  color: rgba(160,200,255,.85) !important;
  border-radius: 3px !important;
  font-family: 'JetBrains Mono', monospace !important;
}
::-webkit-scrollbar { width: 3px; height: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(232,228,220,.12); border-radius: 2px; }
</style>
"""

# ── Custom card / badge helpers ─────────────────────────────────────────────
COMPONENT_CSS = """
<style>
/* MANDATE custom component classes */

.m-card {
  background: rgba(255,255,255,.035);
  border: 1px solid rgba(232,228,220,.1);
  border-radius: 10px;
  padding: 1.4rem 1.6rem;
  margin-bottom: .8rem;
  backdrop-filter: blur(6px);
  transition: border-color .3s, box-shadow .3s;
}
.m-card:hover {
  border-color: rgba(140,180,240,.22);
  box-shadow: 0 0 24px rgba(100,150,220,.07);
}
.m-card-risk {
  background: rgba(155,58,58,.06);
  border: 1px solid rgba(155,58,58,.24);
  border-left: 3px solid rgba(192,80,80,.65);
  border-radius: 10px;
  padding: 1.3rem 1.5rem;
  margin-bottom: .8rem;
}
.m-card-ok {
  background: rgba(58,122,90,.06);
  border: 1px solid rgba(58,122,90,.24);
  border-left: 3px solid rgba(80,160,120,.65);
  border-radius: 10px;
  padding: 1.3rem 1.5rem;
  margin-bottom: .8rem;
}
.m-card-warn {
  background: rgba(138,96,32,.06);
  border: 1px solid rgba(138,96,32,.24);
  border-left: 3px solid rgba(176,126,48,.65);
  border-radius: 10px;
  padding: 1.3rem 1.5rem;
  margin-bottom: .8rem;
}
.m-card-accent {
  background: rgba(74,127,165,.06);
  border: 1px solid rgba(74,127,165,.24);
  border-left: 3px solid rgba(110,170,210,.65);
  border-radius: 10px;
  padding: 1.3rem 1.5rem;
  margin-bottom: .8rem;
}

/* Badge */
.m-badge {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
  font-size: .63rem;
  font-weight: 500;
  letter-spacing: .1em;
  text-transform: uppercase;
  padding: .2em .65em;
  border-radius: 3px;
  border: 1px solid currentColor;
}
.b-ok     { color: rgba(80,160,120,.95);  border-color: rgba(58,122,90,.55);  background: rgba(58,122,90,.1); }
.b-risk   { color: rgba(192,80,80,.95);   border-color: rgba(155,58,58,.55);  background: rgba(155,58,58,.1); }
.b-warn   { color: rgba(176,126,48,.95);  border-color: rgba(138,96,32,.55);  background: rgba(138,96,32,.1); }
.b-accent { color: rgba(110,170,210,.95); border-color: rgba(74,127,165,.55); background: rgba(74,127,165,.1); }
.b-gold   { color: rgba(200,170,80,.95);  border-color: rgba(160,130,50,.55); background: rgba(160,130,50,.1); }
.b-muted  { color: rgba(232,228,220,.5);  border-color: rgba(232,228,220,.18);background: rgba(255,255,255,.03); }

/* Labels */
.m-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: .7rem;
  letter-spacing: .15em;
  text-transform: uppercase;
  color: rgba(232,228,220,.52);
  margin-bottom: .35rem;
}
.m-quote {
  border-left: 2px solid rgba(232,228,220,.18);
  padding: .45rem .9rem;
  margin: .45rem 0;
  font-size: .9rem;
  color: rgba(232,228,220,.72);
  font-style: italic;
  font-family: 'Cormorant Garamond', serif;
  line-height: 1.75;
}

/* Stat blocks (used as standalone via st.columns) */
.m-stat-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 2rem;
  font-weight: 400;
  color: rgba(232,228,220,.92);
  line-height: 1;
}
.m-stat-label {
  font-size: .68rem;
  letter-spacing: .15em;
  text-transform: uppercase;
  color: rgba(232,228,220,.52);
  margin-bottom: .35rem;
}
.m-stat-sub {
  font-size: .8rem;
  color: rgba(232,228,220,.58);
  margin-top: .3rem;
  line-height: 1.55;
}

/* Passport credential card */
.m-passport {
  background: linear-gradient(135deg, rgba(255,255,255,.04) 0%, rgba(100,130,200,.05) 100%);
  border: 1px solid rgba(232,228,220,.13);
  border-radius: 10px;
  padding: 2rem 2.2rem;
  backdrop-filter: blur(8px);
}

/* Hand-drawn paper document (report pages) */
.m-paper-doc {
  position: relative;
  background:
    radial-gradient(ellipse at 18% 22%, rgba(180,155,85,.06) 0%, transparent 55%),
    radial-gradient(ellipse at 82% 78%, rgba(150,120,65,.05) 0%, transparent 55%),
    linear-gradient(158deg, rgba(58,46,22,.24) 0%, rgba(22,18,10,.16) 100%);
  border: 1px solid rgba(205,185,140,.14);
  border-radius: 3px 10px 6px 5px / 9px 3px 10px 4px;
  padding: 2rem 2.2rem;
  overflow: hidden;
}
.m-paper-doc::after {
  content: 'MANDATE';
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%) rotate(-12deg);
  font-family: 'Cormorant Garamond', serif;
  font-size: 7.5rem;
  font-weight: 300;
  letter-spacing: .6em;
  color: rgba(220,195,145,.016);
  pointer-events: none;
  white-space: nowrap;
  user-select: none;
}
</style>
"""


def inject_atmosphere() -> None:
    """Call once per page render to set up background + CSS."""
    components.html(_BG_JS, height=1)
    st.markdown(GLASS_CSS + COMPONENT_CSS, unsafe_allow_html=True)
