from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import our Daily Horoscope Agent
from agent import DailyHoroscopeAgent, ChatInterface

# Environment variables
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

app = FastAPI(
    title="Daily Horoscope Agent API",
    version="2.0.0",
    debug=DEBUG
)

# CORS - Allow frontend URL from environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
horoscope_agent = DailyHoroscopeAgent()
chat_interface = ChatInterface()

class HoroscopeRequest(BaseModel):
    sign: str
    date: Optional[str] = None
    language: str = "en"
    user_id: str = "default"

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class BirthDateRequest(BaseModel):
    birth_date: str  # DD/MM/YYYY or YYYY-MM-DD
    date: Optional[str] = None
    language: str = "en"
    user_id: str = "default"

@app.get("/")
def read_root():
    return {
        "message": "🌟 Daily Horoscope Agent API",
        "version": "2.0.0",
        "features": [
            "Real-time ephemeris calculations (Swiss Ephemeris)",
            "Transit analysis for all 12 zodiac signs",
            "Love, Career, Health, Money predictions",
            "Lucky color, number, direction, best time",
            "Yesterday vs Today comparison",
            "Birth date to zodiac sign conversion",
            "RAG-powered knowledge base (traits, compatibility, elements)"
        ],
        "endpoints": [
            "/api/horoscope - Generate full horoscope",
            "/api/horoscope/birth-date - Convert birth date to horoscope",
            "/api/chat - Chat interface",
            "/api/compare - Compare yesterday vs today",
            "/api/rag/ask - Ask knowledge questions (traits, compatibility, etc.)",
            "/api/rag/sign/{sign} - Get complete sign info"
        ],
        "rag_examples": [
            "What are Leo's traits?",
            "Tell me about Scorpio love",
            "What element is Taurus?",
            "Who is compatible with Cancer?"
        ]
    }

@app.post("/api/horoscope")
def get_horoscope(request: HoroscopeRequest):
    """
    Generate a complete daily horoscope for a zodiac sign
    """
    try:
        result = horoscope_agent.generate_horoscope(
            sign_or_date=request.sign,
            date_str=request.date,
            language=request.language,
            user_id=request.user_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating horoscope: {str(e)}")

@app.post("/api/horoscope/birth-date")
def get_horoscope_by_birth_date(request: BirthDateRequest):
    """
    Convert birth date to zodiac sign and generate horoscope
    """
    try:
        result = horoscope_agent.generate_horoscope(
            sign_or_date=request.birth_date,
            date_str=request.date,
            language=request.language,
            user_id=request.user_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating horoscope: {str(e)}")

@app.post("/api/chat")
def chat(request: ChatRequest):
    """
    Chat interface for the horoscope agent
    """
    try:
        reply = chat_interface.chat(request.message, request.session_id)
        return {
            "reply": reply,
            "session_id": request.session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@app.get("/api/compare")
def compare_horoscope(sign: str, user_id: str = "default"):
    """
    Compare today's horoscope with yesterday's
    """
    try:
        result = horoscope_agent.compare_with_yesterday(sign, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison error: {str(e)}")

@app.get("/api/horoscope/{sign}")
def get_horoscope_simple(sign: str, date: Optional[str] = None):
    """
    Simple GET endpoint for horoscope by sign
    """
    try:
        result = horoscope_agent.generate_horoscope(
            sign_or_date=sign,
            date_str=date
        )
        return result["structured_data"]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

class RAGQuestionRequest(BaseModel):
    question: str
    sign: Optional[str] = None

@app.post("/api/rag/ask")
def ask_rag(request: RAGQuestionRequest):
    """
    Ask a knowledge-based question about zodiac signs using RAG
    
    Examples:
    - "What are Leo's traits?"
    - "Tell me about Scorpio love compatibility"
    - "What element is Taurus?"
    - "What's the ruling planet of Gemini?"
    """
    from agent import RAGEngine
    try:
        rag = RAGEngine()
        answer = rag.answer_question(request.question, request.sign)
        return {
            "question": request.question,
            "answer": answer,
            "source": "Zodiac Knowledge Base (RAG)",
            "sign": request.sign
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG error: {str(e)}")

@app.get("/api/rag/sign/{sign}")
def get_sign_info(sign: str):
    """
    Get complete zodiac sign information from RAG dataset
    """
    from agent import ZODIAC_DATASET
    try:
        sign_lower = sign.lower()
        if sign_lower not in ZODIAC_DATASET:
            raise HTTPException(status_code=404, detail=f"Sign '{sign}' not found")
        return {
            "sign": sign,
            "data": ZODIAC_DATASET[sign_lower]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/planets")
def get_current_planets():
    """
    Get current planetary positions (for debugging)
    """
    from datetime import datetime
    positions = horoscope_agent.ephemeris.get_planetary_positions(datetime.now())
    return {
        "date": datetime.now().isoformat(),
        "positions": [
            {
                "planet": p.planet,
                "sign": p.sign,
                "degree": round(p.degree, 2),
                "retrograde": p.retrograde
            }
            for p in positions
        ],
        "moon_phase": horoscope_agent.ephemeris.get_moon_phase(datetime.now()),
        "swisseph_available": horoscope_agent.ephemeris.swisseph_available
    }

@app.get("/api/config")
def get_config():
    """
    Get current environment configuration (for debugging)
    """
    return {
        "port": PORT,
        "host": HOST,
        "frontend_url": FRONTEND_URL,
        "debug": DEBUG,
        "swisseph_available": horoscope_agent.ephemeris.swisseph_available
    }

if __name__ == "__main__":
    import uvicorn
    print(f"🌟 Starting Daily Horoscope Agent...")
    print(f"✨ Using real Swiss Ephemeris for planetary calculations")
    print(f"🔧 Debug mode: {DEBUG}")
    print(f"🌐 Allowed origins: {FRONTEND_URL}")
    print(f"📊 API available at http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
