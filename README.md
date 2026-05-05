# 🏠 AI Real Estate Agent Team

A multi-agent property analysis system powered by **Google Gemini** that generates realistic property listings, analyzes market conditions, and provides investment recommendations for any US city — all through a clean Streamlit interface.

**100% free to run** — uses Google Gemini's free tier (no credit card required)

---

## ✨ Features

- 🤖 **Three specialized AI agents** working in sequence
- 🏘️ **Hyper-local listings** with real neighborhood names, zip codes, and street names
- 📊 **Market analysis** covering trends, key areas, and investment outlook
- 💰 **Per-property valuations** with Fair/Over-priced/Under-priced ratings
- 📄 **Downloadable reports** in Markdown format
- 🔒 **Secure key handling** — API key never displayed in UI
- ⚡ **Fast** — full analysis in ~10-15 seconds

---

## 🎬 Demo

The app runs locally at `http://localhost:8501` and produces output like this:

**📍 Listings Tab**
```
#1 — 7801 W 150th Terrace, Overland Park, KS 66223
Price: $725,000 | Type: House | Beds/Baths: 4/3 | Sqft: 2,800
Built: 2015 | On market: 8 days
Features: Hardwood floors · 3-car garage · Finished basement · Pool
```

**📊 Market Analysis Tab**
- **Market Condition** — Seller's market with steady price appreciation
- **Neighborhood Highlights** — Blue Valley, Leawood, Mission Hills
- **Investment Outlook** — Strong rental demand, top-rated schools

**💰 Valuations Tab**
```
Property 1: 7801 W 150th Terrace
- Value: Fair — Priced within typical range for size and area
- Investment Potential: Medium — Solid family home, steady appreciation
- Recommendation: Consider for long-term family occupancy or rental
```

---

## 🏗️ Architecture

The app uses a **sequential three-agent pipeline**:

```
┌──────────────────────┐
│  User Input          │
│  (City, Budget, etc) │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 🏠 Property Search   │ → Generates 10 realistic listings
│    Agent             │   in JSON format
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 📊 Market Analysis   │ → Analyzes neighborhood trends
│    Agent             │   and investment outlook
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 💰 Valuation Agent   │ → Scores each property and
│                      │   gives recommendations
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│  Streamlit UI        │
│  + Markdown Report   │
└──────────────────────┘
```

Each agent has its own system prompt and temperature settings tuned for its specific task.

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| **AI Model** | Google Gemini 2.5 Flash-Lite |
| **Web UI** | Streamlit |
| **Language** | Python 3.10+ |
| **Config** | python-dotenv |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Free Google AI API key

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/yourusername/ai-real-estate.git
cd ai-real-estate
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Get your free Google API key**

- Go to https://aistudio.google.com/app/apikey
- Sign in with Google
- Click **Create API Key**
- Copy the key (starts with `AIza...`)

> ✅ No credit card required
> ✅ Free tier: 15 requests/minute, 1,000 requests/day

**4. Create a `.env` file in the project folder**
```bash
GOOGLE_API_KEY=AIza...your-key-here
```

**5. Run the app**
```bash
streamlit run ai_real_estate_agent_team.py
```

Your browser will open at `http://localhost:8501` 🎉

---

## 📖 Usage

1. **Enter location** — City and state (e.g., Austin, TX)
2. **Set budget range** — Min and max price
3. **Configure preferences** — Property type, bedrooms, bathrooms, square footage
4. **Add special requirements** — Garage, pool, near good schools, etc.
5. **Click "Start Property Analysis"**
6. **Wait ~10-15 seconds** for the three-agent pipeline to complete
7. **Browse the three tabs** — Listings, Market Analysis, Valuations
8. **Download the full report** as Markdown

---

## 📁 Project Structure

```
ai-real-estate/
├── ai_real_estate_agent_team.py  # Main app
├── requirements.txt               # Python dependencies
├── .env                          # Your API key (not in git)
├── .gitignore                    # Excludes .env from commits
└── README.md                     # This file
```

---

## ⚠️ Important Notes

### About the Listings

This app uses **AI-generated property data** for demonstration purposes:

| Field | Real or AI-Generated? |
|---|---|
| Street names | ✅ Real |
| Neighborhoods | ✅ Real |
| Zip codes | ✅ Real |
| Prices | ⚠️ Realistic estimates |
| Phone numbers | ❌ Fictional (555 prefix) |
| Agent names | ❌ Made up |
| Listing URLs | ❌ Not actual links |

**Why?** Real estate sites like Zillow and Realtor.com use enterprise anti-bot systems (PerimeterX, Cloudflare) that block all free scrapers. Production deployments would integrate with paid APIs like:

- Bridge Interactive
- RentSpree
- RealEstateAPI.com
- MLS data feeds (license required)

### Security

- ✅ API key is loaded from `.env` only — never visible in UI
- ✅ `.env` is in `.gitignore` — won't be pushed to GitHub
- ✅ Always rotate your key if it's ever exposed

---

## 🔧 Configuration

### Change the Gemini model

Edit `MODEL_ID` at the top of the file:

```python
MODEL_ID = "gemini-2.5-flash-lite"   # Default — best free tier
# MODEL_ID = "gemini-2.5-flash"       # Better quality, lower quota
# MODEL_ID = "gemini-2.5-pro"         # Best quality, lowest quota
```

| Model | RPM | Daily Quota |
|---|---|---|
| `gemini-2.5-flash-lite` | 15 | 1,000 |
| `gemini-2.5-flash` | 10 | 250 |
| `gemini-2.5-pro` | 5 | 100 |

### Change number of listings

Find this line and change `count=10`:
```python
properties = _generate_properties(city, state, user_criteria, count=10)
```

### Adjust agent creativity

Each agent has its own temperature (0.0 = deterministic, 1.0 = creative):
```python
return _chat(system, user, temperature=0.7)  # listings
return _chat(system, user, temperature=0.4)  # market analysis
return _chat(system, user, temperature=0.3)  # valuations
```

---

## 🐛 Troubleshooting

**"No API key found"**
→ Make sure `.env` exists in the same folder as the script with `GOOGLE_API_KEY=...`

**"429 Quota exceeded"**
→ You've hit the free tier daily limit (1,000 requests). Wait until midnight Pacific Time, or switch to a paid tier.

**"Model not found"**
→ Google deprecated some older models. Update `MODEL_ID` to a current one.

**App is slow**
→ Reduce `count=10` to `count=5` for half the generation time.

---

## 🔮 Future Improvements

- [ ] Integrate paid real estate API for actual listings
- [ ] Add property comparison feature
- [ ] Save search history with `streamlit-extras`
- [ ] Add map visualization with `folium`
- [ ] Mortgage calculator integration
- [ ] Multi-language support
- [ ] Export to PDF instead of just Markdown
- [ ] Add user authentication for saved searches

---

## 📄 License

MIT License — feel free to use this project for your portfolio or as a learning resource.

---

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io)
- Powered by [Google Gemini](https://ai.google.dev)

---

## 👤 Author

Sivarkamani

Built as part of an AI/ML portfolio project demonstrating multi-agent LLM orchestration.

**Star ⭐ this repo if you found it helpful!**
