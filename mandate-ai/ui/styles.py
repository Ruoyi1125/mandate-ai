"""Global CSS injection for MANDATE UI."""

MANDATE_CSS = """
<style>
/* ──────────────────────────────────────────
   MANDATE Design System
   Palette: Ink Black / Stone / Cream / Accent Blue / Caution Red / Gold
   ────────────────────────────────────────── */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --ink:        #0d0f13;
    --slate:      #1a1d24;
    --stone:      #2b2f3a;
    --mid:        #3d4354;
    --muted:      #6b7385;
    --cream:      #e8e4dc;
    --paper:      #f4f1eb;
    --accent:     #4a7fa5;
    --accent-lt:  #6fa8cc;
    --risk:       #9b3a3a;
    --risk-lt:    #c05050;
    --gold:       #b8963c;
    --gold-lt:    #d4ae58;
    --ok:         #3a7a5a;
    --ok-lt:      #50a078;
    --warn:       #8a6020;
    --warn-lt:    #b07e30;
    --radius:     6px;
    --radius-lg:  10px;
    --shadow:     0 1px 4px rgba(0,0,0,0.35);
}

/* ── Base ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--ink) !important;
    color: var(--cream) !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
}

[data-testid="stSidebar"] {
    background-color: var(--slate) !important;
    border-right: 1px solid var(--stone) !important;
}

[data-testid="stHeader"] {
    background-color: var(--ink) !important;
    border-bottom: 1px solid var(--stone) !important;
}

/* ── Typography ── */
h1, h2, h3 { color: var(--cream) !important; letter-spacing: -0.02em; }
h1 { font-size: 2.4rem !important; font-weight: 700 !important; }
h2 { font-size: 1.4rem !important; font-weight: 600 !important; }
h3 { font-size: 1.1rem !important; font-weight: 600 !important; }
p, li { color: var(--cream) !important; line-height: 1.7; }

/* ── Main content area ── */
.block-container {
    max-width: 1100px !important;
    padding-top: 2rem !important;
    padding-bottom: 4rem !important;
}

/* ── Tabs ── */
[data-baseweb="tab-list"] {
    background-color: var(--slate) !important;
    border-bottom: 1px solid var(--stone) !important;
    gap: 0 !important;
    padding: 0 1rem !important;
}

[data-baseweb="tab"] {
    background-color: transparent !important;
    color: var(--muted) !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    padding: 0.75rem 1.2rem !important;
    border-bottom: 2px solid transparent !important;
    transition: all 0.2s ease !important;
}

[data-baseweb="tab"]:hover {
    color: var(--cream) !important;
    background-color: var(--stone) !important;
}

[aria-selected="true"][data-baseweb="tab"] {
    color: var(--accent-lt) !important;
    border-bottom-color: var(--accent-lt) !important;
    background-color: transparent !important;
}

[data-baseweb="tab-panel"] {
    background-color: var(--ink) !important;
    padding-top: 1.5rem !important;
}

/* ── Buttons ── */
.stButton > button {
    background-color: var(--stone) !important;
    color: var(--cream) !important;
    border: 1px solid var(--mid) !important;
    border-radius: var(--radius) !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.03em !important;
    padding: 0.5rem 1.2rem !important;
    transition: all 0.15s ease !important;
}

.stButton > button:hover {
    background-color: var(--mid) !important;
    border-color: var(--muted) !important;
}

.stButton > button[kind="primary"] {
    background-color: var(--accent) !important;
    border-color: var(--accent) !important;
    color: white !important;
    font-weight: 600 !important;
}

.stButton > button[kind="primary"]:hover {
    background-color: var(--accent-lt) !important;
    border-color: var(--accent-lt) !important;
}

/* ── Download buttons ── */
.stDownloadButton > button {
    background-color: var(--stone) !important;
    color: var(--cream) !important;
    border: 1px solid var(--mid) !important;
    border-radius: var(--radius) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background-color: var(--slate) !important;
    color: var(--cream) !important;
    border: 1px solid var(--stone) !important;
    border-radius: var(--radius) !important;
    font-family: 'Inter', sans-serif !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(74,127,165,0.2) !important;
}

/* Label text */
.stTextInput label, .stTextArea label, .stSelectbox label,
.stCheckbox label, .stRadio label, .stFileUploader label {
    color: var(--muted) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}

/* ── Checkbox / Radio ── */
.stCheckbox > label, .stRadio > label { color: var(--cream) !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background-color: var(--slate) !important;
    border: 1px solid var(--stone) !important;
    border-radius: var(--radius) !important;
    margin-bottom: 0.5rem !important;
}

[data-testid="stExpander"] summary {
    color: var(--cream) !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: var(--radius) !important;
    border-left-width: 3px !important;
}

/* ── Metric ── */
[data-testid="stMetric"] {
    background-color: var(--slate) !important;
    border: 1px solid var(--stone) !important;
    border-radius: var(--radius) !important;
    padding: 1rem !important;
}

[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 0.75rem !important; }
[data-testid="stMetricValue"] { color: var(--cream) !important; font-size: 1.6rem !important; }

/* ── Divider ── */
hr { border-color: var(--stone) !important; margin: 1.5rem 0 !important; }

/* ── Progress ── */
[data-testid="stProgress"] > div { background-color: var(--stone) !important; }
[data-testid="stProgress"] > div > div { background-color: var(--accent) !important; }

/* ── Caption / small text ── */
.stCaption, small { color: var(--muted) !important; }

/* ── Code blocks ── */
code {
    background-color: var(--stone) !important;
    color: var(--accent-lt) !important;
    border-radius: 3px !important;
    padding: 0.1em 0.35em !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82em !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--slate); }
::-webkit-scrollbar-thumb { background: var(--mid); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }

/* ══════════════════════════════════
   MANDATE Custom Components
   ══════════════════════════════════ */

/* ── Status badge ── */
.mandate-badge {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 0.2em 0.65em;
    border-radius: 3px;
    border: 1px solid currentColor;
}

.badge-ok      { color: var(--ok-lt);   border-color: var(--ok);   background: rgba(58,122,90,0.12); }
.badge-warn    { color: var(--warn-lt); border-color: var(--warn); background: rgba(138,96,32,0.12); }
.badge-risk    { color: var(--risk-lt); border-color: var(--risk); background: rgba(155,58,58,0.12); }
.badge-accent  { color: var(--accent-lt); border-color: var(--accent); background: rgba(74,127,165,0.12); }
.badge-neutral { color: var(--muted);   border-color: var(--mid);  background: rgba(61,67,84,0.3); }
.badge-gold    { color: var(--gold-lt); border-color: var(--gold); background: rgba(184,150,60,0.12); }

/* ── Card ── */
.mandate-card {
    background-color: var(--slate);
    border: 1px solid var(--stone);
    border-radius: var(--radius-lg);
    padding: 1.25rem 1.4rem;
    margin-bottom: 0.75rem;
}

.mandate-card-dark {
    background-color: var(--ink);
    border: 1px solid var(--stone);
    border-radius: var(--radius-lg);
    padding: 1.25rem 1.4rem;
    margin-bottom: 0.75rem;
}

.mandate-card-risk {
    background-color: rgba(155,58,58,0.08);
    border: 1px solid rgba(155,58,58,0.35);
    border-left: 3px solid var(--risk-lt);
    border-radius: var(--radius-lg);
    padding: 1.25rem 1.4rem;
    margin-bottom: 0.75rem;
}

.mandate-card-ok {
    background-color: rgba(58,122,90,0.08);
    border: 1px solid rgba(58,122,90,0.35);
    border-left: 3px solid var(--ok-lt);
    border-radius: var(--radius-lg);
    padding: 1.25rem 1.4rem;
    margin-bottom: 0.75rem;
}

.mandate-card-accent {
    background-color: rgba(74,127,165,0.07);
    border: 1px solid rgba(74,127,165,0.3);
    border-left: 3px solid var(--accent-lt);
    border-radius: var(--radius-lg);
    padding: 1.25rem 1.4rem;
    margin-bottom: 0.75rem;
}

.mandate-card-warn {
    background-color: rgba(138,96,32,0.08);
    border: 1px solid rgba(138,96,32,0.35);
    border-left: 3px solid var(--warn-lt);
    border-radius: var(--radius-lg);
    padding: 1.25rem 1.4rem;
    margin-bottom: 0.75rem;
}

/* ── Label / Tag ── */
.mandate-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.15rem;
}

/* ── Section header ── */
.mandate-section-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.2rem;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid var(--stone);
}

.mandate-section-title {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--muted);
}

.mandate-section-subtitle {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--cream);
    margin-top: 0.1rem;
}

/* ── Hero ── */
.mandate-hero {
    text-align: center;
    padding: 4rem 2rem 3rem;
}

.mandate-hero-wordmark {
    font-family: 'Inter', sans-serif;
    font-size: 4rem;
    font-weight: 700;
    letter-spacing: -0.04em;
    color: var(--cream);
    line-height: 1;
}

.mandate-hero-wordmark-sub {
    font-size: 1.3rem;
    font-weight: 300;
    color: var(--muted);
    letter-spacing: 0.12em;
    margin-top: 0.2rem;
}

.mandate-hero-tagline {
    font-size: 1.55rem;
    font-weight: 300;
    color: var(--cream);
    line-height: 1.5;
    margin: 1.8rem auto 0;
    max-width: 700px;
}

.mandate-hero-tagline strong {
    font-weight: 600;
    color: var(--accent-lt);
}

.mandate-hero-desc {
    font-size: 1.0rem;
    color: var(--muted);
    line-height: 1.7;
    max-width: 620px;
    margin: 1.2rem auto 2.2rem;
}

/* ── Pillar cards on hero ── */
.mandate-pillar-row {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 1px;
    background-color: var(--stone);
    border: 1px solid var(--stone);
    border-radius: var(--radius-lg);
    overflow: hidden;
    margin-top: 3rem;
}

.mandate-pillar {
    background-color: var(--slate);
    padding: 1.6rem 1.4rem;
    text-align: left;
}

.mandate-pillar-icon {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--accent-lt);
    margin-bottom: 0.6rem;
}

.mandate-pillar-title {
    font-size: 1.0rem;
    font-weight: 600;
    color: var(--cream);
    margin-bottom: 0.4rem;
}

.mandate-pillar-desc {
    font-size: 0.85rem;
    color: var(--muted);
    line-height: 1.6;
}

/* ── Progress stepper ── */
.mandate-stepper {
    display: flex;
    align-items: center;
    gap: 0;
    margin: 0.5rem 0 1.5rem;
    overflow-x: auto;
    padding: 0.2rem 0;
}

.mandate-step {
    display: flex;
    align-items: center;
    flex-shrink: 0;
}

.mandate-step-dot {
    width: 26px;
    height: 26px;
    border-radius: 50%;
    border: 2px solid var(--mid);
    background-color: var(--slate);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.65rem;
    font-weight: 600;
    color: var(--muted);
    flex-shrink: 0;
}

.mandate-step-dot.active {
    border-color: var(--accent-lt);
    background-color: rgba(74,127,165,0.15);
    color: var(--accent-lt);
}

.mandate-step-dot.done {
    border-color: var(--ok-lt);
    background-color: rgba(58,122,90,0.15);
    color: var(--ok-lt);
}

.mandate-step-label {
    font-size: 0.68rem;
    font-weight: 500;
    letter-spacing: 0.05em;
    color: var(--muted);
    white-space: nowrap;
    margin: 0 0.4rem;
}

.mandate-step-label.active { color: var(--accent-lt); }
.mandate-step-label.done   { color: var(--ok-lt); }

.mandate-step-line {
    height: 1px;
    width: 2rem;
    background-color: var(--stone);
    flex-shrink: 0;
}

/* ── Passport credential ── */
.mandate-passport {
    background: linear-gradient(135deg, var(--slate) 0%, #1e2232 100%);
    border: 1px solid var(--mid);
    border-radius: var(--radius-lg);
    padding: 2rem;
    position: relative;
    overflow: hidden;
}

.mandate-passport::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent), var(--gold), var(--ok-lt));
}

.mandate-passport-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--stone);
}

.mandate-passport-wordmark {
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: var(--cream);
}

.mandate-passport-title {
    font-size: 0.65rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--muted);
    margin-top: 0.2rem;
}

.mandate-passport-status {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 0.3em 0.8em;
    border-radius: var(--radius);
}

.mandate-passport-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.mandate-passport-block {
    background-color: rgba(0,0,0,0.2);
    border: 1px solid var(--stone);
    border-radius: var(--radius);
    padding: 1rem 1.1rem;
}

.mandate-passport-block-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.5rem;
}

.mandate-passport-stat {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.5rem;
    font-weight: 500;
    color: var(--cream);
    line-height: 1;
}

.mandate-passport-stat-desc {
    font-size: 0.78rem;
    color: var(--muted);
    margin-top: 0.25rem;
}

/* ── Claim card ── */
.claim-status-bar {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.6rem;
}

.claim-text {
    font-size: 1.0rem;
    font-weight: 500;
    color: var(--cream);
    line-height: 1.5;
    margin-bottom: 0.8rem;
}

.claim-evidence-item {
    background-color: rgba(0,0,0,0.2);
    border: 1px solid var(--stone);
    border-radius: var(--radius);
    padding: 0.7rem 0.9rem;
    margin-bottom: 0.4rem;
    font-size: 0.85rem;
}

.claim-source-id {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: var(--accent-lt);
}

/* ── Voice card ── */
.voice-card {
    background-color: var(--slate);
    border: 1px solid var(--stone);
    border-radius: var(--radius-lg);
    padding: 1.1rem 1.3rem;
    margin-bottom: 0.6rem;
    position: relative;
}

.voice-card.omitted {
    background-color: rgba(155,58,58,0.07);
    border-color: rgba(155,58,58,0.3);
    border-left: 3px solid var(--risk-lt);
}

.voice-card.weakened {
    background-color: rgba(138,96,32,0.07);
    border-color: rgba(138,96,32,0.3);
    border-left: 3px solid var(--warn-lt);
}

.voice-card.distorted {
    background-color: rgba(155,58,58,0.05);
    border-color: rgba(155,58,58,0.25);
    border-left: 3px solid var(--risk);
}

.voice-card.covered {
    background-color: rgba(58,122,90,0.05);
    border-color: rgba(58,122,90,0.25);
    border-left: 3px solid var(--ok-lt);
}

/* ── Authorization comparison ── */
.auth-comparison-row {
    display: grid;
    grid-template-columns: 2fr 1fr 2fr;
    gap: 0.5rem;
    padding: 0.6rem 0;
    border-bottom: 1px solid var(--stone);
    align-items: start;
    font-size: 0.88rem;
}

.auth-comparison-row:last-child { border-bottom: none; }

.auth-comparison-key {
    color: var(--muted);
    font-size: 0.8rem;
}

.auth-comparison-val {
    color: var(--cream);
    font-size: 0.88rem;
}

.auth-out-of-scope {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: var(--risk-lt);
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

.auth-ok {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: var(--ok-lt);
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* ── Lost voices section ── */
.lost-voices-header {
    background: linear-gradient(90deg, rgba(155,58,58,0.15) 0%, transparent 100%);
    border: 1px solid rgba(155,58,58,0.25);
    border-radius: var(--radius-lg);
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.5rem;
}

.lost-voices-title {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--risk-lt);
    letter-spacing: -0.01em;
}

.lost-voices-subtitle {
    font-size: 0.8rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin-top: 0.2rem;
}

/* ── Revision diff ── */
.revision-panel {
    background-color: var(--slate);
    border: 1px solid var(--stone);
    border-radius: var(--radius-lg);
    padding: 1.3rem;
    height: 100%;
}

.revision-panel-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.8rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--stone);
}

.revision-text {
    font-size: 0.92rem;
    line-height: 1.8;
    color: var(--cream);
}

/* ── Summary stats row ── */
.stats-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1px;
    background-color: var(--stone);
    border: 1px solid var(--stone);
    border-radius: var(--radius-lg);
    overflow: hidden;
    margin-bottom: 1.5rem;
}

.stat-block {
    background-color: var(--slate);
    padding: 1.2rem 1.4rem;
}

.stat-block-label {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.4rem;
}

.stat-block-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.9rem;
    font-weight: 500;
    color: var(--cream);
    line-height: 1;
}

.stat-block-sub {
    font-size: 0.8rem;
    color: var(--muted);
    margin-top: 0.3rem;
}

/* ── Quote block ── */
.mandate-quote {
    border-left: 2px solid var(--mid);
    padding: 0.4rem 0.8rem;
    margin: 0.4rem 0;
    font-size: 0.85rem;
    color: var(--muted);
    font-style: italic;
}

/* ── Method note footer ── */
.method-note {
    background-color: var(--slate);
    border: 1px solid var(--stone);
    border-radius: var(--radius);
    padding: 0.8rem 1.1rem;
    font-size: 0.78rem;
    color: var(--muted);
    margin-top: 1rem;
}

/* ── File uploader ── */
[data-testid="stFileUploadDropzone"] {
    background-color: var(--slate) !important;
    border: 1px dashed var(--mid) !important;
    border-radius: var(--radius) !important;
}

/* ── Running status widget ── */
[data-testid="stStatusWidget"] {
    background-color: var(--slate) !important;
    border: 1px solid var(--stone) !important;
    border-radius: var(--radius) !important;
}

/* ── Info / warning / error boxes ── */
[data-baseweb="notification"] {
    background-color: var(--slate) !important;
    border-radius: var(--radius) !important;
}

/* ── JSON viewer ── */
[data-testid="stJson"] {
    background-color: var(--slate) !important;
    border-radius: var(--radius) !important;
}

/* hide streamlit default header decorations */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
</style>
"""


def inject_css() -> None:
    """Inject the MANDATE design system CSS into the Streamlit page."""
    import streamlit as st
    st.markdown(MANDATE_CSS, unsafe_allow_html=True)
