"""
Multimodal Construction Intelligence Platform
Skill Wallet — Capstone Project 1

A production-ready Streamlit application that combines Google Gemini
multimodal AI with domain-specific construction engineering logic to
deliver:
  • Site Safety & PPE Audit
  • Crack Diagnostics & Structural Integrity
  • Planning & Real-Estate Valuation
  • Daily Site Assistant & Weather-Aware Advisory
"""

import streamlit as st
import json
import textwrap
from datetime import datetime

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from PIL import Image

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Page Configuration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="Construction Intelligence Platform",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Minimal, targeted CSS — only what Streamlit can't do natively
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
/* Tighten tab label weight */
button[data-baseweb="tab"] { font-weight: 600 !important; }

/* Progress bar */
.progress-track {
    width: 100%; height: 14px;
    background: #242736; border-radius: 100px;
    overflow: hidden; margin: 0.5rem 0;
}
.progress-fill {
    height: 100%; border-radius: 100px;
    background: linear-gradient(90deg, #6c63ff, #18ffff);
    transition: width 0.6s ease;
}

/* Gradient title */
.grad-title {
    text-align: center; font-weight: 800; font-size: 2rem;
    background: linear-gradient(135deg, #6c63ff, #18ffff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0;
}
.grad-subtitle {
    text-align: center; color: #9e9eb8; font-size: 0.92rem;
    margin-top: 2px; margin-bottom: 1.5rem;
}
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helper Utilities
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_download_json(data: dict, filename: str = "report.json"):
    """Render a download button for a JSON blob."""
    st.download_button(
        label="⬇️  Download JSON Report",
        data=json.dumps(data, indent=2, ensure_ascii=False),
        file_name=filename,
        mime="application/json",
        use_container_width=True,
    )


def _parse_json_from_response(text: str) -> dict | None:
    """Best-effort extraction of a JSON object from Gemini's response text."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return None


def _get_gemini_model():
    """Return configured Gemini GenerativeModel or None."""
    api_key = st.session_state.get("gemini_api_key", "")
    if not api_key or not GENAI_AVAILABLE:
        return None
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-2.0-flash")
    except Exception:
        return None


def _call_gemini(prompt: str, image: Image.Image | None = None) -> str | None:
    """Send a prompt (with optional image) to Gemini and return text response."""
    model = _get_gemini_model()
    if model is None:
        return None
    parts = ([image] if image else []) + [prompt]
    try:
        return model.generate_content(parts, stream=False).text
    except Exception as exc:
        st.error(f"Gemini API error: {exc}")
        return None


def fmt_inr(val: float) -> str:
    """Format a number into INR Lakhs / Crores."""
    if val >= 1e7:
        return f"₹ {val / 1e7:.2f} Cr"
    if val >= 1e5:
        return f"₹ {val / 1e5:.2f} L"
    return f"₹ {val:,.0f}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Demonstration / Fallback Data
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEMO_PPE_REPORT = {
    "safety_score": 62,
    "overall_status": "Needs Improvement",
    "ppe_detection": {
        "hard_hat_helmet":      {"detected": True,  "compliant": True,  "notes": "Yellow hard hats visible on 3 of 5 workers"},
        "high_visibility_vest": {"detected": True,  "compliant": False, "notes": "Only 2 of 5 workers wearing hi-vis vests"},
        "steel_toe_boots":      {"detected": False, "compliant": False, "notes": "Unable to confirm protective footwear on any worker"},
        "safety_harness":       {"detected": False, "compliant": False, "notes": "Workers at elevation (~4 m) without fall-arrest harness"},
        "safety_gloves":        {"detected": True,  "compliant": True,  "notes": "Leather work gloves observed on 4 workers"},
        "eye_protection":       {"detected": False, "compliant": False, "notes": "No safety goggles during grinding operations"},
    },
    "site_hazards": [
        {"hazard": "Workers at height without fall protection",   "severity": "Critical", "osha_ref": "29 CFR 1926.501",    "remedy": "Immediately provide full-body harnesses with anchorage; halt elevated work until compliant"},
        {"hazard": "Loose rebar ends protruding near walkway",    "severity": "High",     "osha_ref": "29 CFR 1926.701(b)", "remedy": "Cap all exposed rebar ends with mushroom-type protectors"},
        {"hazard": "Missing hi-vis vests in active vehicle zone", "severity": "High",     "osha_ref": "29 CFR 1926.201",    "remedy": "Issue ANSI Class 2 vests to all personnel in equipment zones"},
        {"hazard": "Grinding dust without respiratory protection","severity": "Medium",   "osha_ref": "29 CFR 1926.103",    "remedy": "Provide P100 half-face respirators and enforce usage during grinding"},
        {"hazard": "Unsecured material stack near edge",          "severity": "Medium",   "osha_ref": "29 CFR 1926.250",    "remedy": "Restack materials ≥ 1.8 m from leading edge with toe boards"},
        {"hazard": "No first-aid station signage visible",        "severity": "Low",      "osha_ref": "29 CFR 1926.50",     "remedy": "Post first-aid kit location signs at site entry and every floor"},
    ],
}

DEMO_CRACK_REPORT = {
    "defect_type": "Settlement Crack",
    "estimated_crack_width_mm": 1.8,
    "severity": "Medium-High",
    "urgency": "Schedule repair within 2 weeks",
    "root_causes": [
        "Differential foundation settlement due to non-uniform soil bearing capacity",
        "Possible inadequate compaction of backfill material",
        "Seasonal moisture variation causing expansive soil movement",
    ],
    "structural_risk": "Moderate — does not indicate imminent collapse but progressive widening may compromise load transfer across the section",
    "recommended_repairs": [
        {"method": "Epoxy Injection",      "details": "Inject low-viscosity structural epoxy (ASTM C881 Type IV) to restore tensile continuity; suitable for cracks 0.5–3 mm", "estimated_cost_inr": "₹ 350–500 / running ft"},
        {"method": "Structural Re-grouting","details": "Pressure-grout foundation voids with cementitious micro-fine grout to arrest further settlement",                      "estimated_cost_inr": "₹ 15,000–25,000 / location"},
        {"method": "CFRP Wrap",             "details": "Apply Carbon Fibre Reinforced Polymer strips across crack path for added flexural strength if crack exceeds 2.5 mm",     "estimated_cost_inr": "₹ 1,200–1,800 / sqft"},
    ],
    "monitoring_plan": "Install crack gauge (demec points) across fracture; record width at 7-day intervals for 60 days. If growth > 0.1 mm/month, escalate to structural engineer.",
    "is_456_reference": "IS 456:2000 Clause 35.3.2 — Permissible crack width for moderate exposure = 0.3 mm (current crack exceeds limit)",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIDEBAR — kept lean
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with st.sidebar:
    st.markdown("## 🏗️ Construction Intelligence")
    st.caption("Skill Wallet · Capstone Project 1")
    st.divider()

    # API Key — the only critical input
    api_key_input = st.text_input(
        "🔑 Google Gemini API Key",
        type="password",
        placeholder="Paste your key here…",
        help="Get a free key at https://aistudio.google.com/apikey",
    )
    if api_key_input:
        st.session_state["gemini_api_key"] = api_key_input
        st.success("API key active", icon="✅")
    else:
        st.session_state["gemini_api_key"] = ""
        st.info("Demo mode — results are simulated", icon="🎭")

    st.divider()

    # Architecture — collapsed by default, minimal
    with st.expander("Architecture", expanded=False):
        st.code(
            "Streamlit UI\n  ↕ multimodal prompts\n"
            "Gemini 2.0 Flash (Vision+LLM)\n  ↕ structured JSON\n"
            "Domain Logic (PPE · Crack · Valuation · Chat)",
            language=None,
        )
        st.caption("Zero external DB · 1-click Streamlit Cloud deploy")

    with st.expander("Modules", expanded=False):
        st.markdown(
            "1. 🦺 Site Safety & PPE Audit *(Epic 2)*\n"
            "2. 🔍 Crack Diagnostics *(Epic 2)*\n"
            "3. 📊 Planning & Valuation *(Epic 3)*\n"
            "4. 💬 Site Assistant *(Epic 5)*"
        )

    st.divider()
    st.caption(f"v1.0.0 · {datetime.now().strftime('%d %b %Y')}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown('<p class="grad-title">🏗️ Multimodal Construction Intelligence Platform</p>', unsafe_allow_html=True)
st.markdown('<p class="grad-subtitle">AI-Powered Site Safety · Structural Diagnostics · Project Valuation · Smart Advisory</p>', unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TABS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

tab1, tab2, tab3, tab4 = st.tabs([
    "🦺 PPE Audit",
    "🔍 Crack Diagnostics",
    "📊 Valuation",
    "💬 Site Assistant",
])


# ──────────────────────────────────────────────────────────────────────
# TAB 1 — Site Safety & PPE Audit
# ──────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Site Safety & PPE Compliance Audit")
    st.caption("Upload a construction site photograph for AI-powered OSHA & IS 456 safety analysis.")

    uploaded_ppe = st.file_uploader(
        "Upload site photo",
        type=["jpg", "jpeg", "png"],
        key="ppe_upload",
    )

    if uploaded_ppe:
        image = Image.open(uploaded_ppe)
        with st.expander("📷 Uploaded Photo", expanded=True):
            st.image(image, use_container_width=True)

        if st.button("🔍  Analyse Safety & PPE", key="btn_ppe", type="primary", use_container_width=True):
            with st.spinner("Analysing image for PPE compliance and site hazards…"):
                prompt = textwrap.dedent("""\
                You are an expert OSHA-certified construction safety auditor.
                Carefully analyse this construction site photograph and return a STRICT JSON object
                (no markdown fences, no commentary) with this exact schema:

                {
                  "safety_score": <int 0-100>,
                  "overall_status": "<Safe | Needs Improvement | Unsafe | Critical>",
                  "ppe_detection": {
                    "hard_hat_helmet":       {"detected": <bool>, "compliant": <bool>, "notes": "<string>"},
                    "high_visibility_vest":  {"detected": <bool>, "compliant": <bool>, "notes": "<string>"},
                    "steel_toe_boots":       {"detected": <bool>, "compliant": <bool>, "notes": "<string>"},
                    "safety_harness":        {"detected": <bool>, "compliant": <bool>, "notes": "<string>"},
                    "safety_gloves":         {"detected": <bool>, "compliant": <bool>, "notes": "<string>"},
                    "eye_protection":        {"detected": <bool>, "compliant": <bool>, "notes": "<string>"}
                  },
                  "site_hazards": [
                    {
                      "hazard": "<description>",
                      "severity": "<Low | Medium | High | Critical>",
                      "osha_ref": "<OSHA standard reference>",
                      "remedy": "<corrective action>"
                    }
                  ]
                }

                Standards: OSHA 29 CFR 1926, IS 456:2000, IS 3696.
                Be thorough — identify at least 3 hazards. Return ONLY the JSON object.
                """)

                raw = _call_gemini(prompt, image)
                report = _parse_json_from_response(raw) if raw else None
                if report is None:
                    st.info("Using demonstration data (no API key or parsing issue).", icon="🎭")
                    report = DEMO_PPE_REPORT
                st.session_state["ppe_report"] = report

    # ── Render results ──
    report = st.session_state.get("ppe_report")
    if report:
        st.divider()
        score = report.get("safety_score", 0)
        status = report.get("overall_status", "Unknown")
        ppe = report.get("ppe_detection", {})
        hazards = report.get("site_hazards", [])
        detected = sum(1 for v in ppe.values() if isinstance(v, dict) and v.get("detected"))
        compliant = sum(1 for v in ppe.values() if isinstance(v, dict) and v.get("compliant"))

        # ── Metrics row (native st.metric — clean, consistent) ──
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Safety Score", f"{score}/100")
        m2.metric("Overall Status", status)
        m3.metric("PPE Detected", f"{detected}/6")
        m4.metric("PPE Compliant", f"{compliant}/6")

        # ── PPE Checklist ──
        with st.expander("📋 PPE Compliance Checklist", expanded=True):
            for key, val in ppe.items():
                if not isinstance(val, dict):
                    continue
                label = key.replace("_", " ").title()
                det_icon = "✅" if val.get("detected") else "❌"
                comp_icon = "✅" if val.get("compliant") else "❌"
                st.markdown(f"**{label}** — Detected {det_icon}  Compliant {comp_icon}")
                if val.get("notes"):
                    st.caption(val["notes"])

        # ── Hazards ──
        with st.expander(f"⚠️ Identified Hazards ({len(hazards)})", expanded=True):
            for h in hazards:
                sev = h.get("severity", "Medium")
                icon = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(sev, "🟡")
                st.markdown(f"{icon} **{sev}** — {h.get('hazard', '')}")
                st.caption(f"OSHA: {h.get('osha_ref', 'N/A')}  ·  Remedy: {h.get('remedy', '—')}")

        # ── Download ──
        render_download_json(report, "ppe_safety_report.json")


# ──────────────────────────────────────────────────────────────────────
# TAB 2 — Crack Diagnostics & Structural Integrity
# ──────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Crack Diagnostics & Structural Integrity")
    st.caption("Upload a photo of a concrete or masonry surface to classify cracks and get repair recommendations.")

    uploaded_crack = st.file_uploader(
        "Upload surface photo",
        type=["jpg", "jpeg", "png"],
        key="crack_upload",
    )

    if uploaded_crack:
        crack_img = Image.open(uploaded_crack)
        with st.expander("📷 Uploaded Photo", expanded=True):
            st.image(crack_img, use_container_width=True)

        if st.button("🔬  Diagnose Crack", key="btn_crack", type="primary", use_container_width=True):
            with st.spinner("Running structural analysis…"):
                prompt = textwrap.dedent("""\
                You are a licensed structural engineer specialising in concrete pathology.
                Analyse this image showing a crack or defect on a concrete/masonry surface.
                Return a STRICT JSON object (no markdown fences) with this schema:

                {
                  "defect_type": "<Hairline | Settlement | Structural Shear | Thermal Expansion | Spalling | Other>",
                  "estimated_crack_width_mm": <float>,
                  "severity": "<Low | Medium | Medium-High | High | Critical>",
                  "urgency": "<string — when to repair>",
                  "root_causes": ["<cause 1>", "<cause 2>"],
                  "structural_risk": "<assessment string>",
                  "recommended_repairs": [
                    {
                      "method": "<repair method>",
                      "details": "<description>",
                      "estimated_cost_inr": "<cost string>"
                    }
                  ],
                  "monitoring_plan": "<string>",
                  "is_456_reference": "<relevant IS 456 clause>"
                }

                Reference standards: IS 456:2000, ACI 318, ASTM C881.
                Return ONLY the JSON object.
                """)

                raw = _call_gemini(prompt, crack_img)
                crack_report = _parse_json_from_response(raw) if raw else None
                if crack_report is None:
                    st.info("Using demonstration data.", icon="🎭")
                    crack_report = DEMO_CRACK_REPORT
                st.session_state["crack_report"] = crack_report

    # ── Render crack results ──
    cr = st.session_state.get("crack_report")
    if cr:
        st.divider()

        # ── Key metrics ──
        m1, m2, m3 = st.columns(3)
        m1.metric("Defect Type", cr.get("defect_type", "—"))
        m2.metric("Crack Width", f"{cr.get('estimated_crack_width_mm', '—')} mm")
        m3.metric("Severity", cr.get("severity", "—"))

        st.info(f"**Urgency:** {cr.get('urgency', '—')}", icon="⏱️")

        # ── Root causes ──
        with st.expander("🔬 Root Cause Analysis", expanded=True):
            for i, cause in enumerate(cr.get("root_causes", []), 1):
                st.markdown(f"{i}. {cause}")

        # ── Risk ──
        st.warning(f"**Structural Risk:** {cr.get('structural_risk', '—')}", icon="⚠️")

        # ── Repairs ──
        with st.expander("🔧 Recommended Repairs", expanded=True):
            for rep in cr.get("recommended_repairs", []):
                st.markdown(f"**{rep.get('method', '')}** — {rep.get('estimated_cost_inr', '')}")
                st.caption(rep.get("details", ""))

        # ── Monitoring & standards ──
        col_a, col_b = st.columns(2)
        with col_a:
            with st.expander("📐 Monitoring Plan"):
                st.write(cr.get("monitoring_plan", "—"))
        with col_b:
            with st.expander("📖 IS 456 Reference"):
                st.code(cr.get("is_456_reference", "—"), language=None)

        render_download_json(cr, "crack_diagnostics_report.json")


# ──────────────────────────────────────────────────────────────────────
# TAB 3 — Planning & Real-Estate Valuation
# ──────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Planning & Real-Estate Valuation")
    st.caption("Estimate project budget, asset valuation, and material requirements for Indian construction projects.")

    # ── Inputs in a clean 2×2 grid ──
    col_a, col_b = st.columns(2)
    with col_a:
        structure_type = st.selectbox(
            "Structure Type",
            ["Residential Apartment", "Independent House / Villa",
             "Commercial Office", "Industrial Warehouse",
             "Government / Institutional", "High-Rise Tower (> 15 floors)"],
        )
        built_up_sqft = st.number_input(
            "Built-Up Area (sqft)", min_value=200, max_value=500_000,
            value=2000, step=100,
        )
    with col_b:
        location_tier = st.selectbox(
            "Location Tier",
            ["Tier 1 (Mumbai, Delhi, Bangalore, etc.)",
             "Tier 2 (Pune, Jaipur, Lucknow, etc.)",
             "Tier 3 (Indore, Coimbatore, Bhopal, etc.)"],
        )
        completion_pct = st.slider("Completion %", 0, 100, 35)

    if st.button("📈  Calculate Valuation", type="primary", use_container_width=True):
        # ── Cost-rate matrices ──
        cost_rates = {
            "Residential Apartment":         {"Tier 1": 2800, "Tier 2": 1900, "Tier 3": 1400},
            "Independent House / Villa":     {"Tier 1": 3200, "Tier 2": 2200, "Tier 3": 1600},
            "Commercial Office":             {"Tier 1": 3500, "Tier 2": 2500, "Tier 3": 1800},
            "Industrial Warehouse":          {"Tier 1": 1800, "Tier 2": 1300, "Tier 3": 900},
            "Government / Institutional":    {"Tier 1": 2600, "Tier 2": 1800, "Tier 3": 1300},
            "High-Rise Tower (> 15 floors)": {"Tier 1": 4500, "Tier 2": 3200, "Tier 3": 2400},
        }
        market_mult = {
            "Residential Apartment":         {"Tier 1": 2.4, "Tier 2": 1.8, "Tier 3": 1.5},
            "Independent House / Villa":     {"Tier 1": 2.6, "Tier 2": 2.0, "Tier 3": 1.6},
            "Commercial Office":             {"Tier 1": 2.8, "Tier 2": 2.1, "Tier 3": 1.7},
            "Industrial Warehouse":          {"Tier 1": 1.6, "Tier 2": 1.4, "Tier 3": 1.2},
            "Government / Institutional":    {"Tier 1": 1.8, "Tier 2": 1.5, "Tier 3": 1.3},
            "High-Rise Tower (> 15 floors)": {"Tier 1": 3.0, "Tier 2": 2.3, "Tier 3": 1.9},
        }
        steel_rates = {
            "Residential Apartment": 4.5, "Independent House / Villa": 4.0,
            "Commercial Office": 5.0, "Industrial Warehouse": 6.0,
            "Government / Institutional": 4.8, "High-Rise Tower (> 15 floors)": 5.5,
        }
        cement_rates = {
            "Residential Apartment": 0.45, "Independent House / Villa": 0.40,
            "Commercial Office": 0.48, "Industrial Warehouse": 0.38,
            "Government / Institutional": 0.44, "High-Rise Tower (> 15 floors)": 0.50,
        }

        tier_key = location_tier.split("(")[0].strip()
        rate = cost_rates.get(structure_type, {}).get(tier_key, 2000)
        mult = market_mult.get(structure_type, {}).get(tier_key, 1.8)

        total_budget = rate * built_up_sqft
        capex = total_budget * (completion_pct / 100)
        market_val = total_budget * mult * (0.5 + 0.5 * completion_pct / 100)
        steel_kg = steel_rates.get(structure_type, 4.5) * built_up_sqft
        cement_bags = cement_rates.get(structure_type, 0.45) * built_up_sqft

        st.session_state["valuation"] = {
            "total_budget": total_budget, "capex": capex,
            "market_val": market_val, "steel_kg": steel_kg,
            "cement_bags": cement_bags, "completion_pct": completion_pct,
            "structure_type": structure_type, "built_up_sqft": built_up_sqft,
            "location_tier": tier_key,
        }

    # ── Render valuation results ──
    v = st.session_state.get("valuation")
    if v:
        st.divider()

        # ── Financial metrics ──
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Budget", fmt_inr(v["total_budget"]))
        c2.metric("CapEx Incurred", fmt_inr(v["capex"]))
        c3.metric("Market Valuation", fmt_inr(v["market_val"]))
        c4.metric("Completion", f"{v['completion_pct']}%")

        # ── Materials ──
        with st.expander("🏗️ Material Requirements", expanded=True):
            mc1, mc2 = st.columns(2)
            mc1.metric("Steel (TMT Bars)", f"{v['steel_kg']:,.0f} kg",
                       delta=f"≈ {v['steel_kg'] / 1000:.1f} tonnes", delta_color="off")
            mc2.metric("Cement (50 kg bags)", f"{v['cement_bags']:,.0f} bags",
                       delta=f"≈ {v['cement_bags'] * 50 / 1000:.1f} tonnes", delta_color="off")

        # ── Milestone progress ──
        with st.expander("📈 Milestone Progress", expanded=True):
            milestones = [
                ("Foundation & Substructure", 15),
                ("Superstructure (RCC Frame)", 40),
                ("Brickwork & Masonry", 55),
                ("Plumbing & Electrical", 70),
                ("Plastering & Flooring", 85),
                ("Finishing & Handover", 100),
            ]
            pct = v["completion_pct"]
            for name, threshold in milestones:
                icon = "✅" if pct >= threshold else ("🔄" if pct >= threshold - 15 else "⬜")
                st.markdown(f"{icon}  **{name}** — {threshold}%")

            st.markdown(
                f'<div class="progress-track"><div class="progress-fill" style="width:{pct}%"></div></div>',
                unsafe_allow_html=True,
            )

        # ── 3D Rendering (Pollinations AI) ──
        with st.expander("🎨 Conceptual 3D Architectural Rendering", expanded=False):
            render_prompt = (
                f"Photorealistic 3D architectural rendering of a {v['structure_type'].lower()}, "
                f"{v['built_up_sqft']} sqft, modern Indian {v['location_tier']} city, "
                f"construction {v['completion_pct']}% complete, "
                f"cinematic lighting, professional visualization, 8k"
            )
            encoded = render_prompt.replace(" ", "%20")
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=576&nologo=true"
            st.image(url, caption="AI-Generated Rendering (Pollinations AI)", use_container_width=True)
            st.caption(f"Prompt: _{render_prompt}_")


# ──────────────────────────────────────────────────────────────────────
# TAB 4 — Daily Site Assistant & Weather-Aware Advisory
# ──────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Daily Site Assistant & Weather-Aware Advisory")

    # ── Weather Advisory ──
    weather = st.selectbox(
        "🌦️ Current Weather Condition",
        ["Normal", "High Wind", "Heavy Rain", "Extreme Heat"],
    )

    ADVISORIES = {
        "High Wind": [
            ("🏗️ Suspend Crane Operations",
             "All crane and lifting operations must be halted when wind speed exceeds 20 m/s (72 km/h) per IS 4573:1982. Secure boom in weathervane position.",
             "error"),
            ("🧱 Scaffold Inspection Required",
             "Inspect all scaffolding tie-backs and bracing. Ensure debris nets are secured. Remove loose materials from elevated platforms.",
             "warning"),
            ("🪖 Secure Personal Equipment",
             "Workers must secure all tools with lanyards. Hard hats must have chin straps engaged. Suspend rooftop work if gusts > 50 km/h.",
             "warning"),
        ],
        "Heavy Rain": [
            ("⚡ Electrical Hazard Mitigation",
             "De-energise all temporary power connections in exposed areas. GFCI protection mandatory. Cover DB boxes with weatherproof enclosures.",
             "error"),
            ("🏗️ Excavation Safety",
             "Monitor trench walls for slumping. Pump out accumulated water before re-entry. No entry to excavations > 1.5 m without shoring inspection.",
             "error"),
            ("🧪 Concrete Curing Protocol",
             "Freshly poured concrete (< 24 hr) must be covered with polythene sheets. Delay finishing operations. Check slump values if rain contaminates batch.",
             "warning"),
        ],
        "Extreme Heat": [
            ("🌡️ Heat Stress Prevention",
             "Mandatory rest breaks: 15 min every hour when WBGT > 32°C. Provide ORS/electrolyte stations at 50 m intervals. Watch for heat exhaustion signs.",
             "error"),
            ("🧪 Concrete & Mortar Adjustments",
             "Use chilled mixing water or ice. Reduce batch-to-placement time to < 30 min. Apply curing compound or wet hessian within 30 min of finishing.",
             "warning"),
            ("🔥 Fire & Hot Work Protocols",
             "Double fire-watch radius during welding/cutting. Ensure extinguishers within 10 m of any hot work. No flammable storage in direct sunlight.",
             "warning"),
        ],
        "Normal": [
            ("✅ Standard Operations",
             "All construction activities may proceed per schedule. Conduct daily toolbox talk and verify PPE compliance before work begins.",
             "info"),
            ("📋 Routine Checklist",
             "Verify scaffold tags, equipment pre-use inspection, housekeeping rounds, and material delivery schedule. Update site diary.",
             "info"),
        ],
    }

    with st.expander(f"⚠️ Safety Alerts — {weather}", expanded=True):
        for title, alert_text, level in ADVISORIES.get(weather, []):
            if level == "error":
                st.error(f"**{title}**\n\n{alert_text}", icon="🚨")
            elif level == "warning":
                st.warning(f"**{title}**\n\n{alert_text}", icon="⚠️")
            else:
                st.info(f"**{title}**\n\n{alert_text}", icon="ℹ️")

    st.divider()

    # ── Chatbot (using native st.chat_message) ──
    st.markdown("#### 🤖 Construction Engineering Assistant")

    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []

    # Render history with native chat bubbles
    for msg in st.session_state["chat_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input
    user_input = st.chat_input("Ask about construction, safety, materials, codes…")
    if user_input:
        st.session_state["chat_messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                system_prompt = textwrap.dedent(f"""\
                You are a senior construction engineering assistant with expertise in:
                - Indian Standards (IS 456, IS 1893, IS 875, IS 3696)
                - OSHA regulations (29 CFR 1926)
                - Structural engineering, concrete technology, and geotechnical engineering
                - Construction project management and cost estimation (Indian context, INR)
                - Safety management systems

                Current weather at site: {weather}

                Provide clear, practical, and actionable answers. Reference specific code clauses
                where applicable. Format your response with markdown for readability.
                """)

                full_prompt = system_prompt + "\n\n"
                for msg in st.session_state["chat_messages"]:
                    role_label = "User" if msg["role"] == "user" else "Assistant"
                    full_prompt += f"**{role_label}:** {msg['content']}\n\n"
                full_prompt += "**Assistant:**"

                response = _call_gemini(full_prompt)
                if response is None:
                    response = (
                        "Great construction engineering question! Here are key considerations:\n\n"
                        "1. **Material Selection** — Verify materials meet BIS specifications. "
                        "For structural concrete, ensure M20 grade minimum per IS 456:2000.\n\n"
                        "2. **Quality Assurance** — Cube-test sampling at ≥ 1 sample per 50 m³ "
                        "or per day of concreting, whichever is more frequent.\n\n"
                        "3. **Safety First** — Conduct daily toolbox talks covering the day's "
                        "specific hazards. Maintain an updated risk register.\n\n"
                        "Would you like me to dive deeper into any of these areas?"
                    )

                st.markdown(response)
                st.session_state["chat_messages"].append({"role": "assistant", "content": response})

    if st.session_state["chat_messages"]:
        if st.button("🗑️  Clear Chat", use_container_width=True):
            st.session_state["chat_messages"] = []
            st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Footer
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.divider()
st.caption(
    "🏗️ Multimodal Construction Intelligence Platform · Skill Wallet Capstone Project 1  ·  "
    "Built with Streamlit & Google Gemini · Zero DB Dependencies · 1-Click Deploy"
)
