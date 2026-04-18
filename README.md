# 🌟 Daily Horoscope Agent

A full-stack Daily Horoscope Agent with real astronomical calculations using Swiss Ephemeris.

![Horoscope Agent](https://img.shields.io/badge/Agent-Daily%20Horoscope-purple)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-green)
![React](https://img.shields.io/badge/React-Frontend-blue)

## ✨ Features

- 🔮 **Real Ephemeris Calculations** - Uses Swiss Ephemeris (pyswisseph) for accurate planetary positions
- 📊 **Transit Analysis** - Calculates aspects (trine, square, conjunction, opposition, sextile)
- 💕 **Life Area Predictions** - Love, Career, Health, Money scores (1-10 scale)
- 🍀 **Lucky Guide** - Color, number, direction, best/avoid times
- 📅 **Birth Date Converter** - Auto-detects zodiac from birth date
- 📈 **Trend Comparison** - Yesterday vs Today analysis
- 💬 **Chat Interface** - Natural language horoscope queries
- 🎨 **3 Output Formats** - JSON, Markdown, Plain text

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│   Agent     │
│   (React)   │◄────│   (FastAPI) │◄────│   Engine    │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                                │
                         ┌──────────────────────┼──────────────────────┐
                         ▼                      ▼                      ▼
                   ┌──────────┐          ┌──────────┐          ┌──────────┐
                   │ VALIDATOR│          │EPHEMERIS │          │ TRANSIT  │
                   └──────────┘          └────┬─────┘          └────┬─────┘
                                              │                     │
                                              ▼                     ▼
                                        ┌──────────┐          ┌──────────┐
                                        │ pyswisseph│          │  RAG +   │
                                        │  (Swiss) │          │  LLM     │
                                        └──────────┘          └────┬─────┘
                                                                   │
                                                                   ▼
                                                            ┌──────────┐
                                                            │  OUTPUT  │
                                                            │ FORMATTER│
                                                            └──────────┘
```

**Pipeline**: INPUT → VALIDATOR → EPHEMERIS → TRANSIT → RAG → LLM → OUTPUT

## 📁 Project Structure

```
Daily/
├── backend/              # Python FastAPI + Agent Engine
│   ├── main.py          # API endpoints
│   ├── agent.py         # Full horoscope agent pipeline
│   ├── requirements.txt # Python dependencies
│   └── README.md        # Backend docs
│
├── frontend/            # React + Vite
│   ├── src/
│   │   └── App.jsx     # Chat interface UI
│   ├── package.json
│   └── index.html
│
└── README.md           # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### 1. Start the Backend (Python)

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the API
uvicorn main:app --reload
```

Backend will be available at `http://localhost:8000`

### 2. Start the Frontend (React)

```bash
cd frontend

# Install dependencies
npm install

# Run the app
npm run dev
```

Frontend will be available at `http://localhost:5173`

### 3. Test the Agent

Open your browser to `http://localhost:5173` and try:

1. Type your zodiac sign: `"Leo"` or `"Scorpio"`
2. Or birth date: `"15/08/1990"` or `"2004-12-12"`
3. Then ask: `"love"`, `"career"`, `"money"`, `"health"`, `"lucky"`
4. Compare trends: `"compare"` or `"yesterday"`

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/horoscope` | POST | Generate full horoscope |
| `/api/horoscope/birth-date` | POST | Birth date → horoscope |
| `/api/chat` | POST | Chat interface |
| `/api/compare` | GET | Yesterday vs Today |
| `/api/planets` | GET | Current planetary positions |

### Example API Calls

```bash
# Get horoscope for Leo
curl -X POST "http://localhost:8000/api/horoscope" \
  -H "Content-Type: application/json" \
  -d '{"sign": "leo"}'

# Chat with the agent
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What's my love forecast?"}'

# Compare with yesterday
curl "http://localhost:8000/api/compare?sign=scorpio"
```

## 📊 Response Format

```json
{
  "structured_data": {
    "sign": "leo",
    "date": "2024-01-15",
    "day_rating": 8,
    "overall_summary": "Today brings powerful energy for Leo...",
    "love": {
      "prediction": "Romantic energy flows strongly...",
      "score": 7.5,
      "advice": "Express your feelings boldly"
    },
    "career": { "prediction": "...", "score": 8.0, "advice": "..." },
    "health": { "prediction": "...", "score": 6.5, "advice": "..." },
    "money": { "prediction": "...", "score": 7.0, "advice": "..." },
    "lucky_colour": "Gold",
    "lucky_number": 1,
    "lucky_direction": "East",
    "best_time_window": "12:00 - 14:00",
    "avoid_time_window": "09:00 - 10:30",
    "morning_affirmation": "I embrace my confident nature...",
    "planetary_highlight": "Sun forms a harmonious trine...",
    "raw_transits": [...]
  },
  "markdown_report": "## 🌟 Leo Horoscope for 2024-01-15...",
  "plain_text_summary": "Leo - 2024-01-15 - Day Rating: 8/10...",
  "images": ["..."]
}
```

## 🔧 Agent Pipeline

### Step 1: Input Validation
- Validates zodiac signs (12 signs)
- Converts birth dates (DD/MM/YYYY or YYYY-MM-DD)
- Auto-detects zodiac from birth date

### Step 2: Ephemeris Fetch (Swiss Ephemeris)
- Real planetary positions (Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Rahu, Ketu)
- Current moon phase
- Day energy score (0-10)

### Step 3: Transit Calculation
- Angular relationships: Trine (120°), Square (90°), Conjunction (0°), Opposition (180°), Sextile (60°)
- Life area scores: Love, Career, Health, Money

### Step 4: RAG Engine
- In-memory knowledge base (no database required!)
- Sign traits and interpretations
- Planet-in-sign meanings

### Step 5: LLM Core (Rule-Based)
- Generates predictions based on transit scores
- Creates personalized advice
- Builds affirmations and highlights

### Step 6: Output Formatting
- **JSON** - For API consumers
- **Markdown** - For web/chat display
- **Plain Text** - For SMS/notifications

## 💬 Chat Examples

| Input | Response |
|-------|----------|
| `"I'm a Scorpio"` | Full horoscope with all predictions |
| `"15/08/1990"` | Leo horoscope (auto-converted) |
| `"love"` | Love prediction for current sign |
| `"career"` | Career outlook with score |
| `"money"` | Financial forecast |
| `"health"` | Health advice |
| `"lucky"` | Lucky color, number, direction |
| `"compare"` | Yesterday vs Today table |
| `"trends"` | Same as compare |

## 🎯 Key Features Explained

### Real Swiss Ephemeris
Uses the same astronomical library as professional astrology software. Calculates actual planetary positions based on NASA JPL data.

### Transit Analysis
Determines how planets affect your sign through angular relationships:
- **Trine (120°)** = Harmonious, beneficial
- **Square (90°)** = Tension, challenge
- **Conjunction (0°)** = Intensification
- **Opposition (180°)** = Conflict or balance
- **Sextile (60°)** = Mild opportunity

### Life Area Scores
Each area scored 1-10 based on planetary influences:
- Love: Venus, Moon, Sun
- Career: Saturn, Sun, Mars
- Health: Sun, Moon, Mars, Saturn
- Money: Jupiter, Venus, Mercury

### No Database Required
- In-memory caching
- No PostgreSQL or Redis needed
- Perfect for prototyping and small deployments

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **pyswisseph** - Swiss Ephemeris for astronomy
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server

### Frontend
- **React** - UI library
- **Vite** - Build tool
- **Inline CSS** - Styled components

## 📝 Notes

### pyswisseph Installation
Windows users may need Visual C++ build tools. If installation fails:

```bash
# Option 1: Pre-built wheel
pip install pyswisseph --only-binary :all:

# Option 2: If still fails, the system uses deterministic mock positions
# (still provides realistic demo output)
```

### Fallback Mode
If pyswisseph is not available, the agent uses deterministic mock positions based on the date. This still produces consistent, realistic horoscope output suitable for demos.

## 📜 License

MIT License - Free for personal and commercial use.

## 🙏 Credits

- Swiss Ephemeris by Astrodienst AG
- FastAPI by Sebastián Ramírez
- React by Meta

---

**Made with 💜 and real astronomical calculations** ✨
#   D a i l y - H o r o s c o p e - A g e n t  
 #   D a i l y - H o r o s c o p e - A g e n t  
 #   D a i l y - H o r o s c o p e - A g e n t  
 