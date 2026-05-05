"""
AI Real Estate Agent Team - Powered by Google Gemini
100% free with Gemini API (no credit card needed).
Get your free key at: https://aistudio.google.com/app/apikey
"""

import json
import os
import re
import time

import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
load_dotenv()

DEFAULT_GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
MODEL_ID = "gemini-2.5-flash-lite"   # Free tier: 15 RPM, 1000 req/day


# ---------------------------------------------------------------------------
# Core Gemini call
# ---------------------------------------------------------------------------

def _chat(system: str, user: str, temperature: float = 0.7) -> str:
    """Call Gemini and return the response text."""
    try:
        model = genai.GenerativeModel(
            model_name=MODEL_ID,
            system_instruction=system,
            generation_config={"temperature": temperature},
        )
        response = model.generate_content(user)
        return response.text or ""
    except Exception as exc:
        raise RuntimeError(f"Gemini call failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Stage 1 — generate property listings
# ---------------------------------------------------------------------------

def _generate_properties(city: str, state: str, criteria: dict, count: int = 10) -> list:
    system = (
        "You are a real estate listing expert with deep knowledge of US property markets. "
        "Generate realistic property listings as a valid JSON array. "
        "Use real street names, realistic prices for the area, and accurate market details. "
        "Return ONLY a raw JSON array — no markdown, no code fences, no extra text."
    )

    user = f"""Generate {count} realistic property listings for {city}, {state}.

SEARCH CRITERIA:
- Budget: {criteria.get('budget_range', 'Any')}
- Property Type: {criteria.get('property_type', 'Any')}
- Bedrooms: {criteria.get('bedrooms', 'Any')}
- Bathrooms: {criteria.get('bathrooms', 'Any')}
- Min Square Feet: {criteria.get('min_sqft', 'Any')}
- Special Features: {criteria.get('special_features', 'None')}

Return a JSON array of exactly {count} objects. Each object must have:
- "address": realistic full street address in {city}, {state}
- "price": realistic price (e.g. "$450,000")
- "bedrooms": number as string (e.g. "3")
- "bathrooms": number as string (e.g. "2")
- "square_feet": realistic sqft (e.g. "1,850")
- "property_type": type matching criteria
- "description": 1-2 sentence description
- "features": array of 3-5 feature strings
- "listing_url": realistic URL like "https://www.redfin.com/listing/12345"
- "agent_contact": e.g. "Sarah Johnson | (555) 123-4567"
- "days_on_market": e.g. "12 days"
- "year_built": e.g. "2005"

Use real {city} neighbourhood names and market-accurate prices.
Return ONLY the JSON array."""

    raw = _chat(system, user, temperature=0.7)

    # Clean response
    raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()

    # Parse JSON array
    start = raw.find("[")
    end = raw.rfind("]") + 1
    if start == -1 or end == 0:
        return []

    try:
        chunk = raw[start:end]
        chunk = re.sub(r",\s*}", "}", chunk)
        chunk = re.sub(r",\s*]", "]", chunk)
        data = json.loads(chunk)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        # Fallback — extract individual objects
        objects = re.findall(r'\{[^{}]+\}', raw, re.DOTALL)
        results = []
        for obj in objects:
            try:
                parsed = json.loads(obj)
                if "address" in parsed:
                    results.append(parsed)
            except json.JSONDecodeError:
                continue
        return results


# ---------------------------------------------------------------------------
# Stage 2 — market analysis
# ---------------------------------------------------------------------------

def _market_analysis(city: str, state: str, criteria: dict) -> str:
    system = (
        "You are a concise real-estate market analyst. "
        "Always use bullet points and keep each section under 100 words. "
        "Use up-to-date market knowledge."
    )
    user = (
        f"Provide a real estate market analysis for {city}, {state}.\n"
        f"Budget range: {criteria.get('budget_range', 'Any')}.\n"
        f"Property type: {criteria.get('property_type', 'Any')}.\n\n"
        "Cover these three sections with bullet points:\n"
        "1. **Market Condition** — buyer's or seller's market, recent price trends.\n"
        "2. **Neighbourhood Highlights** — 2-3 bullets on key areas.\n"
        "3. **Investment Outlook** — 2-3 key takeaways.\n"
        "Max 100 words per section."
    )
    return _chat(system, user, temperature=0.4)


# ---------------------------------------------------------------------------
# Stage 3 — property valuations
# ---------------------------------------------------------------------------

def _valuate_properties(properties: list, criteria: dict) -> str:
    slim = [
        {
            "number":        i,
            "address":       _get(p, "address",      "N/A"),
            "price":         _get(p, "price",         "N/A"),
            "property_type": _get(p, "property_type", "N/A"),
            "bedrooms":      _get(p, "bedrooms",       "N/A"),
            "bathrooms":     _get(p, "bathrooms",      "N/A"),
            "square_feet":   _get(p, "square_feet",    "N/A"),
        }
        for i, p in enumerate(properties, 1)
    ]

    system = (
        "You are a property valuation expert. "
        "For every property, follow the EXACT format requested. "
        "Keep each block under 60 words. Output well-formatted markdown only."
    )
    user = (
        f"USER BUDGET: {criteria.get('budget_range', 'Any')}\n\n"
        f"PROPERTIES TO ASSESS:\n{json.dumps(slim, indent=2)}\n\n"
        "For EACH property output EXACTLY this format (markdown only, no JSON):\n\n"
        "**Property [NUMBER]: [ADDRESS]**\n"
        "- Value: [Fair/Over-priced/Under-priced] — [reason]\n"
        "- Investment Potential: [High/Medium/Low] — [reason]\n"
        "- Recommendation: [one actionable insight]\n\n"
        f"Assess all {len(properties)} properties. Max 60 words per block."
    )
    return _chat(system, user, temperature=0.3)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_analysis(city: str, state: str, user_criteria: dict, progress_cb) -> dict | str:

    # Stage 1
    progress_cb(0.15, "Generating…", f"🏠 Generating listings for {city}, {state}…")
    try:
        properties = _generate_properties(city, state, user_criteria, count=10)
    except RuntimeError as exc:
        return str(exc)

    if not properties:
        return "No listings generated. Please try again."

    progress_cb(0.40, "Listings ready", f"✅ Generated {len(properties)} listings")

    # Stage 2
    progress_cb(0.55, "Market analysis…", "📊 Analysing market conditions…")
    try:
        market_analysis = _market_analysis(city, state, user_criteria)
    except RuntimeError as exc:
        market_analysis = f"Market analysis unavailable: {exc}"
    progress_cb(0.70, "Market done", "✅ Market analysis complete")

    # Stage 3
    progress_cb(0.80, "Valuating…", "💰 Valuating properties…")
    try:
        property_valuations = _valuate_properties(properties, user_criteria)
    except RuntimeError as exc:
        property_valuations = f"Valuations unavailable: {exc}"
    progress_cb(0.95, "Valuations done", "✅ Valuations complete")

    # Stage 4
    markdown_report = _build_report(
        city, state, user_criteria, properties, market_analysis, property_valuations
    )

    return {
        "properties":          properties,
        "market_analysis":     market_analysis,
        "property_valuations": property_valuations,
        "total_properties":    len(properties),
        "markdown_synthesis":  markdown_report,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get(obj, key: str, default: str = "") -> str:
    val = obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)
    return str(val) if val else default


def _build_report(city, state, criteria, properties, market, valuations) -> str:
    lines = [
        f"# Real Estate Analysis — {city}, {state}",
        f"**Budget:** {criteria.get('budget_range')} | "
        f"**Type:** {criteria.get('property_type')} | "
        f"**Beds:** {criteria.get('bedrooms')} | "
        f"**Baths:** {criteria.get('bathrooms')}",
        "", f"## Properties ({len(properties)})",
    ]
    for i, p in enumerate(properties, 1):
        url  = _get(p, "listing_url")
        link = f"[View listing]({url})" if url else "—"
        lines += [
            f"### #{i} {_get(p, 'address')}",
            f"**Price:** {_get(p, 'price')} | **Type:** {_get(p, 'property_type')} | "
            f"**Bed/Bath:** {_get(p, 'bedrooms')}/{_get(p, 'bathrooms')} | "
            f"**Sqft:** {_get(p, 'square_feet')} | **Built:** {_get(p, 'year_built')}",
            f"**Agent:** {_get(p, 'agent_contact')} | **On market:** {_get(p, 'days_on_market')}",
            link, "",
        ]
    lines += ["## Market Analysis", market or "N/A", "", "## Valuations", valuations or "N/A"]
    return "\n".join(lines)


def _extract_valuation(valuations: str, num: int, address: str) -> str:
    """Extract the valuation block for a specific property number."""
    if not valuations:
        return ""
    # Match "**Property N:" or "**Property N "
    pattern = rf"\*\*Property\s*{num}\s*[:.\-].*?(?=\*\*Property\s*\d+|$)"
    match = re.search(pattern, valuations, re.DOTALL)
    if match:
        return match.group(0).strip()
    # Fallback by paragraph
    for para in valuations.split("\n\n"):
        if f"Property {num}" in para or f"#{num}" in para:
            return para
    return f"**Property {num}**\n• Assessment not available — see Valuations tab."


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def display_results(properties, market_analysis, property_valuations, total_properties, markdown_report):
    prices = [
        int(re.sub(r"[^\d]", "", _get(p, "price")))
        for p in properties
        if re.sub(r"[^\d]", "", _get(p, "price"))
    ]
    avg_price = f"${sum(prices) // len(prices):,}" if prices else "N/A"

    type_counts: dict = {}
    for p in properties:
        t = _get(p, "property_type", "Unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
    top_type = max(type_counts, key=type_counts.get) if type_counts else "N/A"

    c1, c2, c3 = st.columns(3)
    c1.metric("🏠 Properties Found", total_properties)
    c2.metric("💲 Average Price",    avg_price)
    c3.metric("🏡 Top Type",         top_type)

    tab1, tab2, tab3 = st.tabs(["🏠 Listings", "📊 Market Analysis", "💰 Valuations"])

    with tab1:
        for i, prop in enumerate(properties, 1):
            address  = _get(prop, "address",      "Address unavailable")
            price    = _get(prop, "price",         "—")
            ptype    = _get(prop, "property_type", "—")
            beds     = _get(prop, "bedrooms",       "—")
            baths    = _get(prop, "bathrooms",      "—")
            sqft     = _get(prop, "square_feet",    "—")
            desc     = _get(prop, "description")
            url      = _get(prop, "listing_url")
            agent    = _get(prop, "agent_contact",  "—")
            dom      = _get(prop, "days_on_market", "—")
            built    = _get(prop, "year_built",     "—")
            features = prop.get("features", []) if isinstance(prop, dict) else []

            with st.container(border=True):
                h1, h2 = st.columns([3, 1])
                with h1:
                    st.subheader(f"#{i} — {address}")
                with h2:
                    st.metric("Price", price)

                d1, d2, d3 = st.columns([2, 2, 1])
                with d1:
                    st.markdown(
                        f"**Type:** {ptype}  \n"
                        f"**Beds/Baths:** {beds}/{baths}  \n"
                        f"**Sqft:** {sqft}  \n"
                        f"**Built:** {built}  \n"
                        f"**On market:** {dom}  \n"
                        f"**Agent:** {agent}"
                    )
                    if desc:
                        st.caption(desc[:250])
                    if features:
                        st.markdown("**Features:** " + " · ".join(
                            f for f in features if isinstance(f, str)
                        ))
                with d2:
                    with st.expander("💰 Investment Analysis"):
                        st.markdown(_extract_valuation(property_valuations, i, address))
                with d3:
                    if url:
                        st.link_button("View →", url, use_container_width=True)

    with tab2:
        st.subheader("📊 Market Analysis")
        st.markdown(market_analysis) if market_analysis else st.info("No market analysis available.")

    with tab3:
        st.subheader("💰 Full Investment Analysis")
        st.markdown(property_valuations) if property_valuations else st.info("No valuation data available.")

    st.divider()
    _, dl_col, _ = st.columns([1, 2, 1])
    with dl_col:
        st.download_button(
            "📄 Download Full Report", markdown_report,
            "property_analysis_report.md", "text/markdown",
            use_container_width=True,
        )


# ---------------------------------------------------------------------------
# Main Streamlit app
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="AI Real Estate Agent Team",
        page_icon="🏠",
        layout="wide",
    )

    st.title("🏠 AI Real Estate Agent Team")
    st.caption(f"Powered by Google Gemini `{MODEL_ID}` — 100% free, no credit card needed")

    with st.sidebar:
        st.header("⚙️ Configuration")

        with st.expander("🔑 API Key Status", expanded=True):
            google_key = DEFAULT_GOOGLE_API_KEY
            if google_key:
                st.success("✅ API key loaded from `.env` file")
                genai.configure(api_key=google_key)
            else:
                st.error("❌ No API key found")
                st.markdown(
                    "**Setup instructions:**\n\n"
                    "1. Get a free key at [aistudio.google.com](https://aistudio.google.com/app/apikey)\n"
                    "2. Create a `.env` file in your project folder\n"
                    "3. Add this line to `.env`:\n"
                    "```\nGOOGLE_API_KEY=your-key-here\n```\n"
                    "4. Restart the app"
                )

        with st.expander("ℹ️ How It Works", expanded=False):
            st.markdown(
                "**Three-agent pipeline powered by Gemini:**\n\n"
                "1. 🏠 Generates realistic property listings for your city\n"
                "2. 📊 Analyses real market conditions for the area\n"
                "3. 💰 Scores and recommends each property\n\n"
                "**Why no website scraping?** Real estate sites like Zillow use "
                "enterprise anti-bot systems that block all free scrapers. Gemini's "
                "real estate knowledge is more reliable."
            )

    st.header("Your Property Requirements")

    with st.form("property_prefs"):
        st.markdown("### 📍 Location & Budget")
        l1, l2 = st.columns(2)
        with l1:
            city  = st.text_input("🏙️ City",  placeholder="e.g. Austin")
            state = st.text_input("🗺️ State", placeholder="e.g. TX")
        with l2:
            min_price = st.number_input("💰 Min Price ($)", min_value=0, value=300_000, step=25_000)
            max_price = st.number_input("💰 Max Price ($)", min_value=0, value=1_000_000, step=25_000)

        st.markdown("### 🏡 Property Details")
        c1, c2, c3 = st.columns(3)
        with c1:
            property_type = st.selectbox(
                "🏠 Property Type",
                ["Any", "House", "Condo", "Townhouse", "Apartment", "Multi-family"],
            )
            bedrooms = st.selectbox("🛏️ Bedrooms", ["Any", "1", "2", "3", "4", "5+"])
        with c2:
            bathrooms = st.selectbox("🚿 Bathrooms", ["Any", "1", "1.5", "2", "2.5", "3", "4+"])
            min_sqft  = st.number_input("📐 Min Sqft", min_value=0, value=800, step=100)
        with c3:
            timeline = st.selectbox(
                "⏰ Timeline",
                ["Flexible", "< 1 month", "1–3 months", "3–6 months", "6+ months"],
            )
            urgency = st.selectbox(
                "🚨 Urgency", ["Not urgent", "Somewhat urgent", "Very urgent"]
            )

        st.markdown("### ✨ Special Features")
        special_features = st.text_area(
            "Requirements & wish-list",
            placeholder="e.g. garage, backyard, near good schools, walkable, pool…",
        )

        _, sub_col, _ = st.columns([1, 2, 1])
        with sub_col:
            submitted = st.form_submit_button(
                "🚀 Start Property Analysis",
                type="primary",
                use_container_width=True,
            )

    if submitted:
        missing = []
        if not google_key: missing.append("Google API Key")
        if not city:       missing.append("City")
        if not state:      missing.append("State")
        if missing:
            st.error(f"⚠️ Please provide: {', '.join(missing)}")
            return

        user_criteria = {
            "budget_range":     f"${min_price:,} – ${max_price:,}",
            "property_type":    property_type,
            "bedrooms":         bedrooms,
            "bathrooms":        bathrooms,
            "min_sqft":         str(min_sqft),
            "timeline":         timeline,
            "urgency":          urgency,
            "special_features": special_features or "None specified",
        }

        progress_bar  = st.progress(0)
        activity_text = st.empty()

        def progress_cb(pct, _s, activity=""):
            progress_bar.progress(pct)
            if activity:
                activity_text.text(activity)

        try:
            start  = time.perf_counter()
            result = run_analysis(
                city=city,
                state=state,
                user_criteria=user_criteria,
                progress_cb=progress_cb,
            )
            elapsed = time.perf_counter() - start
            progress_bar.progress(1.0)
            activity_text.empty()

            if isinstance(result, str):
                st.error(result)
                return

            display_results(
                result["properties"],
                result["market_analysis"],
                result["property_valuations"],
                result["total_properties"],
                result["markdown_synthesis"],
            )
            st.caption(f"⏱ Completed in {elapsed:.1f}s using `{MODEL_ID}`")

        except Exception as exc:
            st.error(f"❌ Unexpected error: {exc}")


if __name__ == "__main__":
    main()