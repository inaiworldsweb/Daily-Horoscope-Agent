# 🌟 Daily Horoscope Agent - Backend

Professional astrology engine with real-time ephemeris calculations using Swiss Ephemeris (pyswisseph).

## Features

- ✅ **Real planetary positions** - Swiss Ephemeris calculations
- ✅ **Transit analysis** - Aspect calculations (trine, square, conjunction, opposition, sextile)
- ✅ **Life area scores** - Love, Career, Health, Money (1-10 scale)
- ✅ **Lucky attributes** - Color, number, direction, best/avoid times
- ✅ **Birth date conversion** - Auto-detect zodiac from birth date
- ✅ **Yesterday vs Today** - Trend comparison
- ✅ **3 output formats** - JSON, Markdown, Plain text
- ✅ **Chat interface** - Natural language horoscope queries

## Architecture

```
INPUT → VALIDATOR → EPHEMERIS → TRANSIT → RAG → LLM → OUTPUT
```

1. **Input Validator** - Validates zodiac signs, birth dates, languages
2. **Ephemeris Fetcher** - Real-time planetary positions using Swiss Ephemeris
3. **Transit Calculator** - Angular relationships and life area scores
4. **RAG Engine** - Knowledge base retrieval (in-memory)
5. **Horoscope Generator** - Rule-based prediction generation
6. **Output Formatter** - JSON, Markdown, Plain text

## Setup

### Prerequisites

- Python 3.8+
- pip

### Install

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
```

### Note on pyswisseph

The `pyswisseph` package provides real astronomical calculations. If installation fails:

```bash
# Windows users may need Visual C++ build tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Alternative: use pre-built wheel
pip install pyswisseph --only-binary :all:
```

If pyswisseph is not available, the system falls back to deterministic mock positions for demo purposes.

## Run

```bash
# Development mode with auto-reload
uvicorn main:app --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

API will be available at `http://localhost:8000`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info & features |
| `/api/horoscope` | POST | Generate full horoscope by sign |
| `/api/horoscope/birth-date` | POST | Convert birth date to horoscope |
| `/api/horoscope/{sign}` | GET | Simple horoscope by sign |
| `/api/chat` | POST | Chat interface |
| `/api/compare` | GET | Compare yesterday vs today |
| `/api/planets` | GET | Current planetary positions |

### Example Requests

```bash
# Get horoscope for Leo
curl -X POST "http://localhost:8000/api/horoscope" \
  -H "Content-Type: application/json" \
  -d '{"sign": "leo"}'

# Get horoscope by birth date
curl -X POST "http://localhost:8000/api/horoscope/birth-date" \
  -H "Content-Type: application/json" \
  -d '{"birth_date": "15/08/1990"}'

# Chat interface
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What's my love forecast?", "session_id": "user123"}'

# Compare with yesterday
curl "http://localhost:8000/api/compare?sign=scorpio"

# Get current planets
curl "http://localhost:8000/api/planets"
```

## Response Format

```json
{
  "structured_data": {
    "sign": "leo",
    "date": "2024-01-15",
    "day_rating": 8,
    "overall_summary": "...",
    "love": { "prediction": "...", "score": 7.5, "advice": "..." },
    "career": { "prediction": "...", "score": 8.0, "advice": "..." },
    "health": { "prediction": "...", "score": 6.5, "advice": "..." },
    "money": { "prediction": "...", "score": 7.0, "advice": "..." },
    "lucky_colour": "Gold",
    "lucky_number": 1,
    "lucky_direction": "East",
    "best_time_window": "12:00 - 14:00",
    "avoid_time_window": "09:00 - 10:30",
    "morning_affirmation": "...",
    "planetary_highlight": "...",
    "raw_transits": [...]
  },
  "markdown_report": "## 🌟 Leo Horoscope...",
  "plain_text_summary": "Leo - 2024-01-15 - Day Rating: 8/10...",
  "images": ["..."]
}
```

## Chat Examples

- `"I'm a Scorpio"` → Full horoscope
- `"15/08/1990"` → Leo horoscope (auto-converted)
- `"love"` → Love prediction for current sign
- `"career"` → Career outlook
- `"money"` → Financial forecast
- `"health"` → Health advice
- `"lucky"` → Lucky guide
- `"compare"` or `"yesterday"` → Trend comparison

## No Database Required

All data is stored in-memory:
- Horoscope cache (same day requests)
- User sessions
- Knowledge base

No PostgreSQL, Redis, or external database needed!

## Tech Stack

- **Framework**: FastAPI (Python)
- **Astronomy**: pyswisseph (Swiss Ephemeris)
- **Validation**: Pydantic
- **CORS**: Enabled for frontend at localhost:5173
