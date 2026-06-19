"""Full-screen animated MANDATE hero — embedded via st.components.v1.html."""
from __future__ import annotations

import streamlit.components.v1 as components


def render_hero() -> None:
    """Render the immersive animated hero page."""
    components.html(_HERO_HTML, height=1200, scrolling=False)


_HERO_HTML = r"""
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=Inter:wght@200;300;400;500&display=swap" rel="stylesheet">

<style>
:root {
  --ink: #05090f;
  --navy: #070d1a;
  --cream: #e8e4dc;
  --muted: rgba(232,228,220,0.42);
  --ghost: rgba(232,228,220,0.15);
  --accent-glow: rgba(140,180,240,0.7);
}

*,*::before,*::after { margin:0; padding:0; box-sizing:border-box; }

html,body {
  width:100%; height:100%;
  overflow:hidden;
  background:var(--ink);
  color:var(--cream);
  user-select:none;
  -webkit-font-smoothing:antialiased;
}

/* ─── CANVAS ─────────────────────────────────────── */
#c {
  position:fixed;
  top:0; left:0;
  width:100%; height:100%;
  z-index:0;
}

/* ─── INTRO OVERLAY ──────────────────────────────── */
#intro {
  position:fixed; inset:0;
  background:#000;
  z-index:900;
  display:flex;
  align-items:center;
  justify-content:center;
  flex-direction:column;
  gap:1rem;
  animation:introFade 3.2s cubic-bezier(.4,0,.2,1) forwards;
}

@keyframes introFade {
  0%,55% { opacity:1; }
  100%    { opacity:0; pointer-events:none; }
}

.intro-word {
  font-family:'Cormorant Garamond',serif;
  font-size:clamp(3rem,9vw,7.5rem);
  font-weight:300;
  letter-spacing:.4em;
  color:rgba(232,228,220,0);
  text-indent:.4em;
  animation:introWord 2.4s ease-out .2s forwards;
}

@keyframes introWord {
  0%   { color:rgba(232,228,220,0);
         text-shadow:none; }
  40%  { color:rgba(232,228,220,.95);
         text-shadow:0 0 80px rgba(140,180,240,.9),
                     0 0 200px rgba(140,180,240,.3); }
  100% { color:rgba(232,228,220,.55);
         text-shadow:0 0 40px rgba(140,180,240,.4); }
}

.intro-line {
  width:clamp(80px,12vw,140px);
  height:1px;
  background:linear-gradient(90deg,transparent,rgba(232,228,220,.3),transparent);
  animation:introLine 2s ease-out .6s both;
}

@keyframes introLine {
  from { transform:scaleX(0); opacity:0; }
  to   { transform:scaleX(1); opacity:1; }
}

/* ─── VOICE FRAGMENTS ────────────────────────────── */
.frag {
  position:fixed;
  font-family:'Cormorant Garamond',serif;
  font-style:italic;
  font-weight:300;
  font-size:clamp(.6rem,1.1vw,.82rem);
  color:var(--ghost);
  white-space:nowrap;
  pointer-events:none;
  z-index:5;
  animation:fragDrift linear infinite both;
}

@keyframes fragDrift {
  0%   { opacity:0; transform:translate(0,0); }
  20%  { opacity:var(--peak,0.55); }
  80%  { opacity:var(--peak,0.55); }
  100% { opacity:0; transform:translate(var(--dx,8px),var(--dy,20px)); }
}

/* ─── HERO CONTENT ───────────────────────────────── */
#hero {
  position:fixed; inset:0;
  z-index:10;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  padding:2rem;
  opacity:0;
  animation:heroReveal 1.6s cubic-bezier(.2,0,.2,1) 2.8s forwards;
}

@keyframes heroReveal {
  from { opacity:0; transform:translateY(14px); }
  to   { opacity:1; transform:translateY(0); }
}

.mandate-word {
  font-family:'Cormorant Garamond',serif;
  font-size:clamp(3.8rem,10vw,8rem);
  font-weight:300;
  letter-spacing:.38em;
  text-indent:.38em;
  color:var(--cream);
  line-height:1;
  text-shadow:
    0 0 60px rgba(140,180,240,.55),
    0 0 160px rgba(100,150,220,.2);
}

.ch-title {
  font-family:'Inter','PingFang SC',sans-serif;
  font-size:clamp(.72rem,1.8vw,1rem);
  font-weight:200;
  letter-spacing:.65em;
  text-indent:.65em;
  color:var(--muted);
  margin-top:.5em;
  margin-bottom:2.4em;
}

.tagline {
  font-family:'Cormorant Garamond',serif;
  font-size:clamp(1.1rem,2.8vw,1.85rem);
  font-weight:300;
  letter-spacing:.06em;
  line-height:2;
  color:var(--cream);
  text-align:center;
}

.tagline { margin-bottom: 3em; }

/* ─── CTA BUTTONS ────────────────────────────────── */
.cta-row { display:flex; gap:2rem; align-items:center; }

.btn-enter {
  font-family:'Inter',sans-serif;
  font-size:.75rem;
  font-weight:400;
  letter-spacing:.18em;
  color:var(--cream);
  background:transparent;
  border:1px solid rgba(232,228,220,.35);
  border-radius:40px;
  padding:.75em 2.5em;
  cursor:pointer;
  transition:all .4s ease;
  text-decoration:none;
  display:inline-block;
  backdrop-filter:blur(6px);
}

.btn-enter:hover {
  border-color:rgba(232,228,220,.9);
  background:rgba(232,228,220,.07);
  box-shadow:0 0 40px rgba(140,180,240,.18),
             0 0 80px rgba(140,180,240,.06);
  text-shadow:0 0 20px rgba(232,228,220,.4);
}

.btn-demo {
  font-family:'Inter',sans-serif;
  font-size:.72rem;
  font-weight:300;
  letter-spacing:.14em;
  color:var(--muted);
  background:transparent;
  border:none;
  cursor:pointer;
  text-decoration:none;
  transition:color .3s;
}

.btn-demo:hover { color:var(--cream); }

/* ─── BOTTOM PILLARS ─────────────────────────────── */
#pillars {
  position:fixed;
  bottom:2.2rem;
  left:0;
  right:0;
  display:flex;
  gap:3.5rem;
  justify-content:center;
  align-items:center;
  z-index:10;
  opacity:0;
  animation:heroReveal 1.6s cubic-bezier(.2,0,.2,1) 3.4s forwards;
}

.pillar {
  display:flex; flex-direction:column;
  align-items:center; gap:.35rem;
}

.p-icon { width:26px; height:26px; opacity:.4; }

.p-en {
  font-family:'Inter',sans-serif;
  font-size:.56rem; font-weight:500;
  letter-spacing:.22em;
  color:var(--muted);
  text-transform:uppercase;
}

.p-zh {
  font-family:'Inter','PingFang SC',sans-serif;
  font-size:.6rem; font-weight:300;
  letter-spacing:.12em;
  color:var(--ghost);
}

.p-sep {
  width:1px; height:28px;
  background:linear-gradient(to bottom,
    transparent, rgba(232,228,220,.2), transparent);
}
</style>
</head>
<body>

<canvas id="c"></canvas>

<!-- ── Intro ── -->
<div id="intro">
  <div class="intro-word">MANDATE</div>
  <div class="intro-line"></div>
</div>

<!-- ── Floating voice fragments ── -->
<span class="frag" style="top:12%;left:6%;     --peak:.6; --dx:10px;--dy:22px; animation-duration:13s;animation-delay:3.1s;">"我认为……"</span>
<span class="frag" style="top:19%;right:9%;    --peak:.5; --dx:-9px;--dy:16px; animation-duration:17s;animation-delay:3.6s;">"他们认为……"</span>
<span class="frag" style="top:7%; left:32%;    --peak:.45;--dx:6px; --dy:28px; animation-duration:15s;animation-delay:4.1s;">"有些人觉得……"</span>
<span class="frag" style="top:16%;right:26%;   --peak:.5; --dx:-8px;--dy:18px; animation-duration:19s;animation-delay:3.9s;">"普遍认为……"</span>
<span class="frag" style="top:30%;left:4%;     --peak:.55;--dx:12px;--dy:-8px; animation-duration:16s;animation-delay:4.3s;">"据我所知……"</span>
<span class="frag" style="top:70%;right:7%;    --peak:.42;--dx:-5px;--dy:-18px;animation-duration:14s;animation-delay:4.6s;">"一种观点是……"</span>
<span class="frag" style="top:77%;left:10%;    --peak:.38;--dx:8px; --dy:-10px;animation-duration:18s;animation-delay:5.1s;">"如果被误判呢？"</span>
<span class="frag" style="top:86%;right:20%;   --peak:.32;--dx:-12px;--dy:-8px;animation-duration:21s;animation-delay:3.3s;">"我想知道谁能看到这些数据"</span>
<span class="frag" style="top:60%;left:2%;     --peak:.38;--dx:14px;--dy:12px; animation-duration:23s;animation-delay:4.9s;">"我支持，但……"</span>
<span class="frag" style="top:42%;right:3%;    --peak:.35;--dx:-7px;--dy:15px; animation-duration:20s;animation-delay:5.4s;">"取决于算法是否公开"</span>

<!-- ── Hero content ── -->
<div id="hero">
  <div class="mandate-word">MANDATE</div>
  <div class="ch-title">代 言 权</div>
  <div class="tagline">
    AI可以生成一种声音。<br>但它有资格代表谁？
  </div>
  <div class="cta-row">
    <a class="btn-enter" href="javascript:void(0)" onclick="go('start')">· 进入体验 ·</a>
    <a class="btn-demo"  href="javascript:void(0)" onclick="go('demo')" >载入演示案例 ○</a>
  </div>
</div>

<!-- ── Bottom pillars ── -->
<div id="pillars">
  <div class="pillar">
    <svg class="p-icon" viewBox="0 0 26 26" fill="none"
         stroke="rgba(232,228,220,.7)" stroke-width="1" stroke-linecap="round">
      <circle cx="13" cy="13" r="5.5"/>
      <line x1="13" y1="1"  x2="13" y2="7"/>
      <line x1="13" y1="19" x2="13" y2="25"/>
      <line x1="1"  y1="13" x2="7"  y2="13"/>
      <line x1="19" y1="13" x2="25" y2="13"/>
    </svg>
    <div class="p-en">SOURCE</div>
    <div class="p-zh">来 源</div>
  </div>

  <div class="p-sep"></div>

  <div class="pillar">
    <svg class="p-icon" viewBox="0 0 26 26" fill="none"
         stroke="rgba(232,228,220,.7)" stroke-width="1" stroke-linecap="round">
      <line x1="2"  y1="13" x2="2"  y2="13"/>
      <line x1="6"  y1="9"  x2="6"  y2="17"/>
      <line x1="10" y1="5"  x2="10" y2="21"/>
      <line x1="13" y1="3"  x2="13" y2="23"/>
      <line x1="16" y1="5"  x2="16" y2="21"/>
      <line x1="20" y1="9"  x2="20" y2="17"/>
      <line x1="24" y1="13" x2="24" y2="13"/>
    </svg>
    <div class="p-en">VOICE</div>
    <div class="p-zh">声 音</div>
  </div>

  <div class="p-sep"></div>

  <div class="pillar">
    <svg class="p-icon" viewBox="0 0 26 26" fill="none"
         stroke="rgba(232,228,220,.7)" stroke-width="1" stroke-linecap="round">
      <circle cx="13" cy="13" r="3"/>
      <circle cx="13" cy="13" r="7"/>
      <circle cx="13" cy="13" r="11" stroke-dasharray="2.5 3.5"/>
    </svg>
    <div class="p-en">MANDATE</div>
    <div class="p-zh">授 权</div>
  </div>
</div>

<script>
/* ── Canvas ─────────────────────────────────────────────────────── */
const C   = document.getElementById('c');
const ctx = C.getContext('2d');
let W, H, T = 0;

function resize() {
  W = C.width  = window.innerWidth;
  H = C.height = window.innerHeight;
}
resize();
window.addEventListener('resize', resize);

/* Stars */
const STARS = Array.from({length: 130}, () => ({
  x: Math.random(),
  y: Math.random(),
  r: Math.random() * .9 + .2,
  ph: Math.random() * Math.PI * 2,
  sp: Math.random() * .4 + .15,
}));

/* Left wave — dense organic terrain */
function drawLeft(t) {
  for (let layer = 0; layer < 14; layer++) {
    const alpha   = .018 + layer * .007;
    const xCenter = W * .1 + layer * 16;
    ctx.beginPath();
    ctx.strokeStyle = `rgba(255,255,255,${alpha})`;
    ctx.lineWidth   = 1;

    const yTop = H * .22, yBot = H * .78;
    const span = yBot - yTop;

    for (let i = 0; i <= 200; i++) {
      const p = i / 200;
      const y = yTop + p * span;
      const env = Math.sin(p * Math.PI);
      const amp = (18 + layer * 9) * env;
      const x   = xCenter
        + Math.sin(p * 20 + t * .55 + layer * .9) * amp * .55
        + Math.sin(p * 8  + t * .28 + layer * .5) * amp * .35
        + Math.cos(p * 5  + t * .15)               * amp * .1;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();
  }

  /* soft glow on left cluster */
  const g = ctx.createRadialGradient(W*.18, H*.5, 0, W*.18, H*.5, W*.22);
  g.addColorStop(0, 'rgba(120,165,230,.05)');
  g.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W*.4, H);
}

/* Right wave — flowing silk threads */
function drawRight(t) {
  for (let i = 0; i < 20; i++) {
    const alpha = .015 + Math.abs(Math.sin(i * .35)) * .018;
    const baseX = W * .64 + i * 22;
    const yOff  = H * (-.08 + i * .065);
    ctx.beginPath();
    ctx.strokeStyle = `rgba(255,255,255,${alpha})`;
    ctx.lineWidth   = .65;

    for (let j = 0; j <= 160; j++) {
      const p = j / 160;
      const x = baseX
        + Math.sin(p * Math.PI * 3   + t * .38 + i * .65) * (22 + i * 3.5)
        + Math.cos(p * Math.PI * 1.3 + t * .18)            * 10;
      const y = yOff + p * H * 1.15;
      j === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();
  }

  /* convergence glow on right */
  const g = ctx.createRadialGradient(W*.82, H*.32, 0, W*.82, H*.32, W*.2);
  g.addColorStop(0, 'rgba(150,195,255,.055)');
  g.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = g;
  ctx.fillRect(W*.56, 0, W*.44, H);
}

/* Center ambient nebula */
function drawNebula(t) {
  const pulse = 1 + Math.sin(t * .45) * .08;
  const g = ctx.createRadialGradient(W*.5, H*.44, 0, W*.5, H*.44, 260*pulse);
  g.addColorStop(0,   'rgba(90,130,200,.09)');
  g.addColorStop(.45, 'rgba(50,80,150,.04)');
  g.addColorStop(1,   'rgba(0,0,0,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);
}

function frame() {
  ctx.clearRect(0, 0, W, H);

  /* solid bg */
  ctx.fillStyle = '#05090f';
  ctx.fillRect(0, 0, W, H);

  /* stars */
  STARS.forEach(s => {
    const br = .3 + .35 * Math.sin(T * s.sp + s.ph);
    ctx.beginPath();
    ctx.arc(s.x*W, s.y*H, s.r, 0, Math.PI*2);
    ctx.fillStyle = `rgba(255,255,255,${br})`;
    ctx.fill();
  });

  drawNebula(T);
  drawLeft(T);
  drawRight(T);

  T += .007;
  requestAnimationFrame(frame);
}
frame();

/* ── Make this iframe fill the full browser viewport ────────────── */
(function fullscreen() {
  try {
    var P = window.parent;
    var frames = P.document.querySelectorAll('iframe');
    for (var i = 0; i < frames.length; i++) {
      (function(f) {
        try {
          if (f.contentWindow === window) {
            f.style.cssText = [
              'position:fixed', 'top:0', 'left:0',
              'width:100vw', 'height:100vh',
              'z-index:500', 'border:none', 'display:block'
            ].join('!important;') + '!important;';
          }
        } catch(e2) {}
      })(frames[i]);
    }
  } catch(e) {}
})();

/* ── Navigation ────────────────────────────────────────────────── */
function go(action) {
  try {
    window.top.location.href =
      window.top.location.origin +
      window.top.location.pathname +
      '?action=' + action;
  } catch(e) {
    window.location.href = '?action=' + action;
  }
}
</script>
</body>
</html>
"""
