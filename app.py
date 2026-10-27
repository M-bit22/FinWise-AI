import csv
import io
import json
import os
from datetime import datetime

import streamlit as st
import matplotlib.pyplot as plt

from src.config import CURRENCIES, FINANCIAL_GOALS
from src.financial_calculator import calculate_finances
from src.chains import get_finwise_chain, stream_recommendations, repair_finwise_response
from src.cache_manager import setup_caching
from src.utils import parse_llm_json

st.set_page_config(
    page_title="FinWise AI · Personal Finance",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Premium dark fintech design inspired by the supplied reference image.
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root {
  --bg:#090a0b; --sidebar:#101112; --panel:#141516; --panel2:#191a1c;
  --border:#292b2d; --text:#f2f3f3; --muted:#898d91; --green:#8ce65b;
  --green2:#b2ff80; --green-bg:#1a2b16; --red:#ff7373; --amber:#f4c66a;
}
html, body, [class*="css"] { font-family:'Manrope',sans-serif; }
.stApp { background:var(--bg); color:var(--text); }
[data-testid="stHeader"] { background:rgba(9,10,11,.92); }
[data-testid="stToolbar"] { right:1rem; }
.block-container { max-width:1600px; padding-top:1.45rem; padding-bottom:3rem; }
[data-testid="stSidebar"] { background:var(--sidebar); border-right:1px solid #202123; }
[data-testid="stSidebar"] > div:first-child { padding-top:1.5rem; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#a7aaad; }
h1,h2,h3,h4 { letter-spacing:-.045em !important; color:var(--text) !important; }
h1 { font-size:1.8rem !important; font-weight:750 !important; }
h2 { font-size:1.35rem !important; }
h3 { font-size:1.08rem !important; }
p, label, li { color:#d7d9da; }
small,.muted { color:var(--muted); }
div[data-testid="stMetric"] { background:transparent; padding:.15rem 0; }
[data-testid="stMetricLabel"] { color:#a1a4a7 !important; font-size:.78rem !important; }
[data-testid="stMetricValue"] { color:#f4f5f5 !important; font-family:'DM Mono',monospace; font-size:1.65rem !important; }
[data-testid="stMetricDelta"] { font-size:.75rem !important; }
.stButton > button, .stDownloadButton > button {
  border:1px solid #343638; border-radius:12px; min-height:2.6rem;
  background:#1a1b1d; color:#f3f4f4; font-weight:650;
  transition:all .18s ease; box-shadow:none;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  border-color:var(--green); color:var(--green2); background:#1a2118;
  transform:translateY(-1px);
}
.stButton > button[kind="primary"], .stFormSubmitButton > button {
  background:var(--green) !important; border-color:var(--green) !important; color:#080a07 !important;
}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button:hover {
  background:var(--green2) !important; color:#080a07 !important;
}
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] div[data-baseweb="select"], [data-testid="stTextArea"] textarea {
  background:#171819 !important; border-color:#343638 !important; border-radius:10px !important;
  color:#f4f5f5 !important;
}
[data-testid="stTabs"] button { color:#969a9d; border-radius:10px 10px 0 0; }
[data-testid="stTabs"] button[aria-selected="true"] { color:var(--green2); }
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background:var(--green); }
hr { border-color:#282a2c !important; }
div[data-testid="stAlert"] { border-radius:12px; }
div[data-testid="stExpander"] { border:1px solid var(--border); border-radius:12px; background:#111213; }
div[data-testid="stForm"] { border:1px solid var(--border); border-radius:16px; padding:1rem 1.1rem; background:#101112; }
div[data-testid="stProgressBar"] > div > div { background:var(--green) !important; }
.fw-brand { display:flex; align-items:center; gap:10px; padding:4px 2px 22px; font-size:1.2rem; font-weight:800; letter-spacing:-.04em; color:#f6f7f7; }
.fw-mark { width:34px; height:34px; border-radius:11px; display:grid; place-items:center; color:#11150d; background:var(--green); font-size:21px; font-weight:900; }
.fw-accent { color:var(--green); }
.eyebrow { color:#8d9295; font-size:.7rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; margin-bottom:7px; }
.hero-balance { font-family:'DM Mono',monospace; font-size:clamp(2.2rem,4vw,3.7rem); line-height:1.12; letter-spacing:-.075em; font-weight:500; color:#f5f6f6; margin:.15rem 0 .45rem; }
.hero-sub { color:#9b9fa2; font-size:.85rem; }
.hero-panel { padding:1.35rem 1.5rem; border:1px solid #292c2d; border-radius:20px; background:radial-gradient(ellipse at 85% 0%,rgba(140,230,91,.09),transparent 42%),linear-gradient(135deg,#17191a,#101112); min-height:175px; animation:rise .45s ease both; }
.panel { background:linear-gradient(145deg,#171819,#121314); border:1px solid #282a2c; border-radius:17px; padding:1.1rem 1.15rem; height:100%; animation:rise .45s ease both; }
.panel-title { font-size:.95rem; font-weight:750; margin-bottom:5px; color:#f0f1f1; }
.panel-note { font-size:.76rem; color:#898e91; }
.metric-card { background:#141516; border:1px solid #292b2d; border-radius:15px; padding:1rem 1.05rem; min-height:115px; animation:rise .45s ease both; }
.metric-label { color:#9da1a4; font-size:.76rem; margin-bottom:.6rem; }
.metric-value { color:#f3f4f4; font-family:'DM Mono',monospace; font-size:1.45rem; letter-spacing:-.06em; }
.metric-foot { color:#8ce65b; font-size:.72rem; margin-top:.45rem; }
.pill { display:inline-block; border-radius:99px; padding:5px 9px; background:#1b2a17; color:#a9f783; font-size:.7rem; font-weight:750; }
.pill-neutral { background:#242628; color:#b4b7b9; }
.sidebar-label { color:#6f7478; font-size:.68rem; font-weight:800; letter-spacing:.12em; text-transform:uppercase; margin:1.25rem 0 .45rem; }
.insight { border-left:3px solid var(--green); background:#151a13; border-radius:0 12px 12px 0; padding:.85rem 1rem; color:#dfe8d9; margin:.5rem 0; }
/* ChatGPT-inspired sidebar navigation: compact rows, quiet active surface, no radio controls. */
[data-testid="stSidebar"] .fw-brand { padding:3px 4px 26px; }
[data-testid="stSidebar"] .sidebar-label { margin:1.15rem 0 .45rem; }
[data-testid="stSidebar"] [data-testid="stButton"] { margin:0; }
[data-testid="stSidebar"] [data-testid="stButton"] button {
  width:100%; text-align:left; justify-content:flex-start; border:1px solid transparent;
  border-radius:9px; min-height:2.45rem; padding:0 .75rem; margin:0;
  background:transparent; color:#b9bbbe; box-shadow:none; font-size:.88rem; font-weight:500;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
  background:#1b1c1e; color:#f4f5f5; border-color:transparent; transform:none;
}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
  background:#252628 !important; color:#f6f6f6 !important; border-color:#303234 !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] * { color:#f6f6f6 !important; }
.sidebar-status { background:linear-gradient(145deg,#1b1d1e,#131415); border:1px solid #2a2c2d; border-radius:13px; padding:12px; margin-top:8px; }
.sidebar-status-title { font-size:.76rem; font-weight:750; color:#e7e9e9; }
.sidebar-status-sub { color:#8e9396; font-size:.68rem; margin-top:4px; }
.plain-explain { background:#141815; border:1px solid #2c3b27; border-radius:15px; padding:1rem 1.1rem; }
.plain-explain h4 { margin:0 0 8px 0; font-size:.98rem; }
.plain-explain li { color:#d5ded0; margin:.3rem 0; }
@keyframes rise { from {opacity:0; transform:translateY(7px)} to {opacity:1; transform:translateY(0)} }
@media (prefers-reduced-motion: reduce) { * {animation:none !important; transition:none !important;} }
</style>
""", unsafe_allow_html=True)

def money(value, symbol):
    return f"{symbol}{value:,.2f}"

def panel(title, subtitle=""):
    st.markdown(f'<div class="panel"><div class="panel-title">{title}</div><div class="panel-note">{subtitle}</div></div>', unsafe_allow_html=True)

def render_list(items, empty_text="No recommendations available yet."):
    if items:
        for item in items:
            st.markdown(f"- {item}")
    else:
        st.caption(empty_text)

def render_finance_bar_chart(labels, values, title, currency_symbol=None, height=3.0):
    """Render a dark-theme Matplotlib chart with clockwise-rotated x-axis labels."""
    fig, ax = plt.subplots(figsize=(8.2, height))
    fig.patch.set_facecolor("#141516")
    ax.set_facecolor("#141516")
    bars = ax.bar(range(len(labels)), values, color="#8ce65b", width=0.62)
    ax.set_title(title, color="#f2f3f3", fontsize=11, loc="left", pad=14, fontweight="bold")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=-45, ha="left", color="#b2b6b8", fontsize=8)
    ax.tick_params(axis="y", colors="#969b9e", labelsize=8)
    ax.grid(axis="y", color="#303234", linewidth=.65, alpha=.75)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#303234")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#303234")
    if currency_symbol:
        ax.set_ylabel(currency_symbol, color="#92979a", fontsize=8)
    for bar, value in zip(bars, values):
        ax.annotate(f"{value:,.0f}", (bar.get_x()+bar.get_width()/2, bar.get_height()),
                    xytext=(0, 4), textcoords="offset points", ha="center", va="bottom",
                    color="#dfe2df", fontsize=8)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def plain_language_findings(ai_data, calc_results, income, savings, debt, expenses, symbol):
    """Create understandable takeaways even if Gemini returns only a short summary."""
    findings = ai_data.get("key_findings", []) if isinstance(ai_data, dict) else []
    if isinstance(findings, str):
        findings = [x.strip(" •-") for x in findings.splitlines() if x.strip()]
    findings = [str(x).strip() for x in findings if str(x).strip()]
    if len(findings) < 4:
        total = calc_results["total_expenses"]
        remaining = calc_results["remaining_income"]
        largest = max(expenses.items(), key=lambda item: item[1]) if expenses else ("expenses", 0)
        candidates = [
            f"You bring in {symbol}{income:,.2f} each month and your listed expenses add up to {symbol}{total:,.2f}.",
            (f"After the listed expenses, about {symbol}{remaining:,.2f} remains each month." if remaining >= 0
             else f"Your listed expenses are about {symbol}{abs(remaining):,.2f} higher than your monthly income."),
            f"Your largest listed spending category is {largest[0].replace('_',' ').title()} at {symbol}{largest[1]:,.2f} per month.",
            f"Your current savings are {symbol}{savings:,.2f}. Compare this amount with essential monthly costs to estimate how much of a buffer you have.",
            (f"Debt payments are {symbol}{debt:,.2f} per month; keep these commitments in mind before increasing discretionary spending."
             if debt > 0 else "No monthly debt payment was entered; check whether any loan or credit payments need to be included."),
            (f"Listed expenses use {calc_results['expense_ratio']:.1f}% of your monthly income." if income > 0
             else "Add your monthly income to calculate useful spending ratios.")
        ]
        for item in candidates:
            if item not in findings:
                findings.append(item)
            if len(findings) >= 6:
                break
    return findings[:8]


def make_csv(expenses, currency, income, savings, debt, results):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["FinWise AI financial snapshot"])
    writer.writerow(["Generated", datetime.now().isoformat(timespec="minutes")])
    writer.writerow(["Currency", currency])
    writer.writerow(["Monthly income", income])
    writer.writerow(["Current savings", savings])
    writer.writerow(["Monthly debt payments", debt])
    writer.writerow(["Total expenses", results["total_expenses"]])
    writer.writerow(["Remaining income", results["remaining_income"]])
    writer.writerow([])
    writer.writerow(["Expense category", "Amount"])
    for category, amount in expenses.items():
        writer.writerow([category.replace("_", " ").title(), amount])
    return buffer.getvalue()

# Sidebar navigation: button rows styled like a modern LLM workspace.
st.session_state.setdefault("navigation", "Dashboard")
st.session_state.setdefault("currency_select", CURRENCIES[0])

with st.sidebar:
    st.markdown('<div class="fw-brand"><span class="fw-mark">◈</span><span>FinWise<span class="fw-accent">.</span> AI</span></div>', unsafe_allow_html=True)
    if st.button("＋  New analysis", key="new_analysis", use_container_width=True):
        for key in ["analysis", "ai_data", "chain_inputs", "expenses_dict", "calc_results",
                    "profile_snapshot", "ai_error", "ai_raw_response", "submitted"]:
            st.session_state.pop(key, None)
        st.session_state["navigation"] = "Dashboard"
        st.rerun()

    st.markdown('<div class="sidebar-label">Workspace</div>', unsafe_allow_html=True)
    nav_items = [
        ("Dashboard", "⌂", "Dashboard"),
        ("Budget planner", "▤", "Budget planner"),
        ("Spending analysis", "▥", "Spending analysis"),
        ("AI insights", "✳", "AI insights"),
        ("Settings", "⚙", "Settings"),
    ]
    for nav_key, nav_icon, nav_label in nav_items:
        if st.button(f"{nav_icon}   {nav_label}", key=f"nav_{nav_key}", use_container_width=True,
                     type="primary" if st.session_state["navigation"] == nav_key else "secondary"):
            st.session_state["navigation"] = nav_key
            st.rerun()
    page = st.session_state["navigation"]

    st.markdown('<div class="sidebar-label" style="margin-top:1.6rem">Profile status</div>', unsafe_allow_html=True)
    st.markdown('<span class="pill pill-neutral">● Personal workspace</span>', unsafe_allow_html=True)
    _health_data = st.session_state.get("ai_data", {})
    _health = _health_data.get("financial_health_score", "—") if not _health_data.get("_parse_error") else "—"
    _health_label = f"{_health}/100 health score" if str(_health) != "—" else "Run an analysis to get your score"
    st.markdown(
        f'<div class="sidebar-status"><div class="sidebar-status-title">◉ &nbsp; Financial pulse</div>'
        f'<div class="sidebar-status-sub">{_health_label}</div>'
        f'<div class="sidebar-status-sub">Your numbers are calculated locally</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown('<div class="sidebar-label">Preferences</div>', unsafe_allow_html=True)
    cache_option = st.selectbox("Caching layer", ["InMemoryCache", "SQLiteCache"], key="cache_layer")
    setup_caching(cache_option)
    if st.button("↻  Reset financial inputs", key="reset_inputs", use_container_width=True):
        for key in ["analysis", "ai_data", "chain_inputs", "expenses_dict", "calc_results",
                    "profile_snapshot", "ai_error", "ai_raw_response", "submitted"]:
            st.session_state.pop(key, None)
        st.rerun()
    st.caption("Educational use only · Not financial advice")

# Settings is a dedicated route: do not render the financial profile form on this page.
if page == "Settings":
    st.markdown('<div class="eyebrow">PREFERENCES</div>', unsafe_allow_html=True)
    st.title("Settings")
    st.caption("Choose how FinWise AI displays and interprets your financial profile.")
    settings_tabs = st.tabs(["Currency & profile", "AI analysis", "App preferences", "About"])
    with settings_tabs[0]:
        st.markdown("### Financial profile currency")
        st.caption("Choose the currency in which you enter income, expenses, and savings. The same currency label is sent to Gemini for its analysis.")
        current_currency = st.session_state.get("currency_select", CURRENCIES[0])
        selected_currency = st.selectbox(
            "Currency used for this financial profile",
            CURRENCIES,
            index=CURRENCIES.index(current_currency) if current_currency in CURRENCIES else 0,
            key="settings_currency",
        )
        if selected_currency != st.session_state.get("currency_select"):
            st.session_state["currency_select"] = selected_currency
            st.success(f"Profile currency updated to {selected_currency}. Re-run your analysis to refresh existing results.")
        st.info("This sets the denomination of the amounts you enter; it does not convert amounts using live exchange rates.")
        st.markdown("**Supported currencies**")
        for cur in CURRENCIES:
            st.markdown(f"- {cur}")
    with settings_tabs[1]:
        st.markdown("### AI analysis")
        st.write("Gemini explains the financial figures and suggests practical actions. Python calculates the numeric totals and ratios.")
        st.write(f"**Configured model:** `{os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')}`")
        st.write("AI output is treated as guidance, not as verified financial, tax, or investment advice.")
        if st.session_state.get("ai_error"):
            st.error("The last AI request did not complete successfully.")
            with st.expander("Technical details", expanded=True):
                st.code(st.session_state.get("ai_error", "Unknown error"))
                raw = st.session_state.get("ai_raw_response", "")
                if raw:
                    st.text_area("Raw model response", raw, height=220, disabled=True)
        else:
            st.success("No AI error is recorded for the current session.")
    with settings_tabs[2]:
        st.markdown("### App preferences")
        st.write(f"**Caching layer:** {cache_option}")
        st.write("**Appearance:** Dark fintech theme")
        st.write("Your financial inputs are currently held in the Streamlit session; they are not saved as a permanent bank record.")
    with settings_tabs[3]:
        st.markdown("### About FinWise AI")
        st.write("FinWise AI is an educational personal-finance dashboard that combines deterministic Python calculations with AI-generated explanations.")
        st.warning("FinWise AI is not a bank, wallet provider, or certified financial adviser.")
    st.stop()

# Top heading
top_left, top_right = st.columns([3, 1], vertical_alignment="center")
with top_left:
    st.markdown('<div class="eyebrow">PERSONAL FINANCE WORKSPACE</div>', unsafe_allow_html=True)
    st.title("Your money, in focus.")
    st.caption("A clear view of your budget, spending habits, and next best steps.")
with top_right:
    st.markdown('<div style="text-align:right"><span class="pill">● FINWISE AI</span></div>', unsafe_allow_html=True)

# The selected currency is the denomination for the values entered into this profile.
currency = st.session_state.get("currency_select", CURRENCIES[0])
curr_symbol = currency.split(" ", 1)[1].strip("()")

defaults = {
    "monthly_income": 5000.0, "current_savings": 1000.0,
    "financial_goal": FINANCIAL_GOALS[0], "debt_payment": 200.0,
    "housing": 1200.0, "food": 600.0, "transportation": 300.0,
    "utilities": 200.0, "education": 100.0, "healthcare": 150.0,
    "entertainment": 200.0, "loan_debt": 200.0, "other_exp": 150.0,
}
for key, value in defaults.items():
    st.session_state.setdefault(key, value)

# Planner is available in a dedicated view and as a compact expander on the dashboard.
page = page.split("  ", 1)[-1] if "  " in page else page

if page == "Budget planner":
    st.markdown("### Build your monthly budget")
    st.caption("Enter your figures below, then analyze them to refresh your dashboard and AI insights.")
    form_container = st.container()
else:
    with st.expander("＋ Edit your financial profile", expanded=False):
        form_container = st.container()

with form_container:
    with st.form("financial_form", border=False):
        st.markdown("#### Income, savings & goals")
        c1, c2, c3 = st.columns(3)
        with c1:
            monthly_income = st.number_input("Monthly income", min_value=0.0, step=100.0, key="monthly_income")
            current_savings = st.number_input("Current savings", min_value=0.0, step=50.0, key="current_savings")
        with c2:
            financial_goal = st.selectbox("Primary financial goal", FINANCIAL_GOALS, key="financial_goal")
            debt_payment = st.number_input("Monthly debt / loan payments", min_value=0.0, step=50.0, key="debt_payment")
        with c3:
            st.markdown('<div class="insight">Your numbers stay in this session. Run an analysis to calculate your budget and generate personalized AI guidance.</div>', unsafe_allow_html=True)
        st.markdown("#### Monthly expense breakdown")
        e1, e2, e3 = st.columns(3)
        with e1:
            housing = st.number_input("Housing / rent", min_value=0.0, key="housing")
            food = st.number_input("Food / groceries", min_value=0.0, key="food")
            transportation = st.number_input("Transportation", min_value=0.0, key="transportation")
        with e2:
            utilities = st.number_input("Utilities", min_value=0.0, key="utilities")
            education = st.number_input("Education", min_value=0.0, key="education")
            healthcare = st.number_input("Healthcare", min_value=0.0, key="healthcare")
        with e3:
            entertainment = st.number_input("Entertainment", min_value=0.0, key="entertainment")
            loan_debt = st.number_input("Loan / debt service", min_value=0.0, key="loan_debt")
            other_exp = st.number_input("Other expenses", min_value=0.0, key="other_exp")
        submitted = st.form_submit_button("Analyze financial health  →", type="primary", use_container_width=True)

if submitted:
    expenses_dict = {
        "housing": housing, "food": food, "transportation": transportation,
        "utilities": utilities, "education": education, "healthcare": healthcare,
        "entertainment": entertainment, "loan_debt": loan_debt, "other": other_exp,
    }
    calc_results = calculate_finances(monthly_income, expenses_dict, current_savings, loan_debt)
    chain_inputs = {
        "monthly_income": f"{curr_symbol}{monthly_income:,.2f}",
        "total_expenses": f"{curr_symbol}{calc_results['total_expenses']:,.2f}",
        "remaining_income": f"{curr_symbol}{calc_results['remaining_income']:,.2f}",
        "savings": f"{curr_symbol}{current_savings:,.2f}",
        "savings_ratio": calc_results["savings_ratio"],
        "expense_ratio": calc_results["expense_ratio"],
        "financial_goal": financial_goal,
        "currency_label": currency,
        "currency_code": currency.split(" ", 1)[0],
        "expense_breakdown": str(expenses_dict),
    }
    st.session_state["expenses_dict"] = expenses_dict
    st.session_state["calc_results"] = calc_results
    st.session_state["chain_inputs"] = chain_inputs
    st.session_state["profile_snapshot"] = {
        "monthly_income": monthly_income, "current_savings": current_savings,
        "debt_payment": debt_payment, "financial_goal": financial_goal,
        "currency": currency, "curr_symbol": curr_symbol,
    }
    with st.spinner("Gemini is reviewing your financial profile…"):
        try:
            # Try provider JSON mode first; retry once with plain text if the
            # provider returns an empty or non-JSON answer.
            response = get_finwise_chain(json_mode=True).invoke(chain_inputs)
            raw_content = getattr(response, "content", response)
            ai_data = parse_llm_json(raw_content)
            if ai_data.get("_parse_error"):
                retry_response = get_finwise_chain(json_mode=False).invoke(chain_inputs)
                retry_content = getattr(retry_response, "content", retry_response)
                retry_data = parse_llm_json(retry_content)
                if not retry_data.get("_parse_error"):
                    ai_data = retry_data
                    st.session_state["ai_error"] = None
                    st.session_state["ai_raw_response"] = ""
                else:
                    # Last recovery step: ask Gemini to repair the malformed output into JSON.
                    try:
                        repaired_content = repair_finwise_response(retry_content or raw_content)
                        repaired_data = parse_llm_json(repaired_content)
                    except Exception as repair_exc:
                        repaired_content = ""
                        repaired_data = parse_llm_json("")
                        st.session_state["ai_repair_error"] = str(repair_exc)
                    if not repaired_data.get("_parse_error"):
                        ai_data = repaired_data
                        st.session_state["ai_error"] = None
                        st.session_state["ai_raw_response"] = ""
                    else:
                        st.session_state["ai_error"] = (
                            "Gemini responded, but the original, retry, and repair responses were not valid JSON. "
                            "See the raw responses below for the provider/model diagnostic."
                        )
                        st.session_state["ai_raw_response"] = (
                            "FIRST RESPONSE:\n" + str(raw_content)[:2500] +
                            "\n\nRETRY RESPONSE:\n" + str(retry_content)[:2500] +
                            "\n\nREPAIR RESPONSE:\n" + str(repaired_content)[:2500]
                        )
            else:
                st.session_state["ai_error"] = None
                st.session_state["ai_raw_response"] = ""
        except Exception as exc:
            ai_data = parse_llm_json("")
            st.session_state["ai_error"] = str(exc)
            st.session_state["ai_raw_response"] = ""
        st.session_state["ai_data"] = ai_data
    st.session_state["analysis"] = True
    st.session_state["submitted"] = True
    st.session_state["scroll_to_dashboard"] = True

has_analysis = bool(st.session_state.get("analysis"))
if has_analysis:
    calc_results = st.session_state["calc_results"]
    expenses_dict = st.session_state["expenses_dict"]
    chain_inputs = st.session_state["chain_inputs"]
    ai_data = st.session_state.get("ai_data", {})
    snapshot = st.session_state["profile_snapshot"]
    symbol = snapshot["curr_symbol"]
    income = snapshot["monthly_income"]
    savings = snapshot["current_savings"]
    debt = snapshot["debt_payment"]
else:
    # A preview uses the default/current inputs locally; AI analysis starts after submit.
    expenses_dict = {
        "housing": st.session_state["housing"], "food": st.session_state["food"],
        "transportation": st.session_state["transportation"], "utilities": st.session_state["utilities"],
        "education": st.session_state["education"], "healthcare": st.session_state["healthcare"],
        "entertainment": st.session_state["entertainment"], "loan_debt": st.session_state["loan_debt"],
        "other": st.session_state["other_exp"],
    }
    income = st.session_state["monthly_income"]
    savings = st.session_state["current_savings"]
    debt = st.session_state["debt_payment"]
    symbol = curr_symbol
    calc_results = calculate_finances(income, expenses_dict, savings, st.session_state["loan_debt"])
    ai_data = {}
    chain_inputs = None

# Scroll the main viewport to the refreshed dashboard after a form submission.
st.markdown('<div id="dashboard-start"></div>', unsafe_allow_html=True)
if st.session_state.pop("scroll_to_dashboard", False):
    st.components.v1.html(
        """<script>
        const target = window.parent.document.getElementById('dashboard-start');
        if (target) { target.scrollIntoView({behavior: 'smooth', block: 'start'}); }
        else { window.parent.scrollTo({top: window.parent.document.body.scrollHeight, behavior: 'smooth'}); }
        </script>""",
        height=0,
    )

# Main balance hero and wallet-style cards
st.markdown('<div class="eyebrow">OVERVIEW / MONTHLY SNAPSHOT</div>', unsafe_allow_html=True)
hero_left, hero_right = st.columns([1.7, 1], gap="large")
with hero_left:
    st.markdown(f"""
    <div class="hero-panel">
      <div class="eyebrow">ESTIMATED MONTH-END BALANCE</div>
      <div class="hero-balance">{money(calc_results['remaining_income'], symbol)}</div>
      <div class="hero-sub">Income after listed expenses · <span class="fw-accent">{calc_results['expense_ratio']:.1f}%</span> of income goes to expenses</div>
      <div style="margin-top:18px"><span class="pill">● {'Budget surplus' if calc_results['remaining_income'] >= 0 else 'Budget deficit'}</span> &nbsp; <span class="pill pill-neutral">{financial_goal if not has_analysis else snapshot['financial_goal']}</span></div>
    </div>
    """, unsafe_allow_html=True)
with hero_right:
    st.markdown(f"""
    <div class="hero-panel" style="min-height:175px">
      <div class="eyebrow">SAVINGS POSITION</div>
      <div class="hero-balance" style="font-size:2.35rem">{money(savings, symbol)}</div>
      <div class="hero-sub">Current savings · {calc_results['savings_ratio']:.1f}% of monthly income</div>
      <div style="margin-top:18px"><span class="pill pill-neutral">Goal: {financial_goal if not has_analysis else snapshot['financial_goal']}</span></div>
    </div>
    """, unsafe_allow_html=True)

st.write("")
m1, m2, m3, m4 = st.columns(4, gap="medium")
cards = [
    ("MONTHLY INCOME", money(income, symbol), "Your monthly inflow"),
    ("TOTAL EXPENSES", money(calc_results["total_expenses"], symbol), f"{calc_results['expense_ratio']:.1f}% of income"),
    ("DEBT PAYMENTS", money(debt, symbol), "Monthly commitments"),
    ("SAVINGS RATE", f"{calc_results['savings_ratio']:.1f}%", "Savings / income"),
]
for col, (label, value, foot) in zip([m1,m2,m3,m4], cards):
    with col:
        st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-foot">↗ {foot}</div></div>', unsafe_allow_html=True)

st.write("")
if page == "Spending analysis":
    st.markdown("### Spending analysis")
elif page == "AI insights":
    st.markdown("### AI financial insights")
elif page == "Budget planner":
    st.markdown("### Budget preview")
else:
    st.markdown("### Financial workspace")

tab_names = ["Overview", "Spending", "Action plan", "Live AI"]
tab1, tab2, tab3, tab4 = st.tabs(tab_names)

with tab1:
    left, right = st.columns([1.2, 1], gap="large")
    with left:
        st.markdown('<div class="panel-title">Income vs. spending</div><div class="panel-note">Your current monthly position</div>', unsafe_allow_html=True)
        render_finance_bar_chart(["Income", "Expenses", "Remaining"], [income, calc_results["total_expenses"], calc_results["remaining_income"]], "Monthly cash flow", symbol, height=3.0)
    with right:
        score = (
            calc_results["preliminary_score"]
            if ai_data.get("_parse_error") or not has_analysis
            else ai_data.get("financial_health_score", calc_results["preliminary_score"])
        )
        try:
            score = max(0, min(100, int(float(score))))
        except (ValueError, TypeError):
            score = int(calc_results["preliminary_score"])
        risk = ai_data.get("risk_level", "Not assessed" if not has_analysis else "MEDIUM")
        st.markdown('<div class="panel-title">Financial health</div><div class="panel-note">A simple score based on your financial profile</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="hero-balance" style="font-size:3rem;margin-top:16px">{score}<span style="font-size:1.05rem;color:#92979a"> / 100</span></div>', unsafe_allow_html=True)
        st.progress(score / 100)
        st.markdown(f'<span class="pill">{risk.upper()}</span>', unsafe_allow_html=True)
        if has_analysis and ai_data.get("financial_summary"):
            st.write("")
            st.write(ai_data.get("financial_summary", ""))
        elif has_analysis:
            st.write(
                f"Based on the figures entered, monthly income is {symbol}{income:,.2f}, "
                f"listed expenses are {symbol}{calc_results['total_expenses']:,.2f}, and "
                f"the estimated remainder is {symbol}{calc_results['remaining_income']:,.2f}. "
                "This is a calculation-based summary; AI commentary is shown separately when available."
            )
        else:
            st.caption("Run an analysis to add a personalized summary and risk assessment.")
    st.write("")
    st.markdown('<div class="panel-title">Quick priorities</div>', unsafe_allow_html=True)
    priorities = ai_data.get("top_priorities", []) if has_analysis else []
    if has_analysis:
        priorities = [str(item).strip() for item in priorities if str(item).strip()]
        if len(priorities) < 6:
            fallback_priorities = [
                f"Review {max(expenses_dict, key=expenses_dict.get).replace('_',' ')} spending first; it is currently your largest listed category.",
                "Set a realistic monthly spending limit for non-essential purchases.",
                "Schedule a weekly 10-minute budget check so small overruns are spotted early.",
                "Build or maintain an emergency buffer based on essential monthly costs.",
                "Review recurring subscriptions and bills for costs you no longer need.",
                "Revisit your savings goal each month and adjust the target if your income changes.",
            ]
            for candidate in fallback_priorities:
                if candidate not in priorities:
                    priorities.append(candidate)
                if len(priorities) >= 6:
                    break
    if priorities:
        for idx, item in enumerate(priorities[:8], start=1):
            st.markdown(f'<div class="insight"><strong>{idx:02d}</strong> &nbsp; {item}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="insight">Start by checking your largest expense categories, then run an analysis to get personalized priorities.</div>', unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="plain-explain"><h4>Analysis explained — in plain English</h4>', unsafe_allow_html=True)
    if has_analysis:
        findings = plain_language_findings(ai_data, calc_results, income, savings, debt, expenses_dict, symbol)
        for finding in findings:
            st.markdown(f"- {finding}")
    else:
        st.markdown("- **Income** is the money you expect to receive in a month.")
        st.markdown("- **Expenses** are the costs you entered. The largest categories are usually the best place to review first.")
        st.markdown("- **Remaining balance** is income minus the expenses listed here; it is not a bank balance.")
        st.markdown("- Run the analysis to add AI-generated explanations and personalized next steps.")
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown("#### Where your money goes")
    expense_rows = sorted(expenses_dict.items(), key=lambda item: item[1], reverse=True)
    chart_col, detail_col = st.columns([1.1, 1], gap="large")
    with chart_col:
        render_finance_bar_chart([name.replace("_"," ").title() for name, amount in expense_rows], [amount for name, amount in expense_rows], "Monthly spending by category", symbol, height=3.8)
    with detail_col:
        for name, amount in expense_rows:
            pct = (amount / calc_results["total_expenses"] * 100) if calc_results["total_expenses"] else 0
            st.markdown(f"**{name.replace('_',' ').title()}** <span style='float:right;color:#f2f3f3;font-family:monospace'>{money(amount, symbol)}</span>", unsafe_allow_html=True)
            st.progress(pct / 100)
            st.caption(f"{pct:.1f}% of listed expenses")
    if has_analysis:
        st.markdown("#### AI observations")
        for item in ai_data.get("spending_analysis", []):
            with st.expander(item.get("category", "Category")):
                st.write("**Observation**")
                st.write(item.get("observation", ""))
                st.write("**Recommendation**")
                st.write(item.get("recommendation", ""))
    else:
        st.info("Run an analysis to receive AI observations for each spending category.")

with tab3:
    budget_col, savings_col = st.columns(2, gap="large")
    with budget_col:
        st.markdown('<div class="panel-title">Budget recommendations</div>', unsafe_allow_html=True)
        render_list(ai_data.get("budget_recommendations", []) if has_analysis else [])
    with savings_col:
        st.markdown('<div class="panel-title">Savings strategy</div>', unsafe_allow_html=True)
        render_list(ai_data.get("savings_strategy", []) if has_analysis else [])
    st.write("")
    st.markdown('<div class="panel-title">Next month action plan</div>', unsafe_allow_html=True)
    actions = ai_data.get("next_month_action_plan", []) if has_analysis else []
    if actions:
        for idx, action in enumerate(actions):
            st.checkbox(action, key=f"action_{idx}")
    else:
        st.caption("Your personalized action plan will appear after analysis.")
    st.write("")
    st.download_button(
        "↓ Export financial snapshot (CSV)",
        data=make_csv(expenses_dict, currency, income, savings, debt, calc_results),
        file_name="finwise_financial_snapshot.csv",
        mime="text/csv",
    )

with tab4:
    if has_analysis and st.session_state.get("ai_error"):
        st.error("Gemini analysis is unavailable for this run. The dashboard's numeric calculations are still available.")
        with st.expander("AI diagnostics", expanded=True):
            st.code(st.session_state.get("ai_error", "Unknown error"))
            raw = st.session_state.get("ai_raw_response", "")
            if raw:
                st.text_area("Raw model response", raw, height=220, disabled=True)
    st.markdown('<div class="panel-title">Live AI narrative</div><div class="panel-note">Stream a fresh response using your current financial profile.</div>', unsafe_allow_html=True)
    if not has_analysis:
        st.info("Analyze your financial profile first to prepare the inputs for live recommendations.")
    elif st.button("↗ Stream fresh recommendations", type="primary"):
        try:
            st.write_stream(stream_recommendations(chain_inputs))
        except Exception as exc:
            st.error(f"Could not stream recommendations: {exc}")
    if has_analysis and st.session_state.get("ai_error"):
        st.error("AI response issue: the local financial calculations are available, but Gemini's response could not be used. Review the details below, then run the analysis again.")
        with st.expander("Technical details"):
            st.code(st.session_state["ai_error"])
            raw_response = st.session_state.get("ai_raw_response", "")
            if raw_response:
                st.markdown("**Gemini raw response (for debugging)**")
                st.code(raw_response)

st.divider()
foot_left, foot_right = st.columns([3,1])
with foot_left:
    st.caption("FinWise AI · Personal finance insights, made clearer.")
with foot_right:
    st.caption("Educational use only")
