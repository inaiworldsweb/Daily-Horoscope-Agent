from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import json
import os
# Production Configuration for Render
# Import our Daily Horoscope Agent
from agent import DailyHoroscopeAgent, ChatInterface
from database import db_manager

# Production URLs
PORT = 10000  # Render requires this port
HOST = "0.0.0.0"
FRONTEND_URL = "https://daily-horoscope-agent-fronted.onrender.com"
DEBUG = False

app = FastAPI(
    title="Daily Horoscope Agent API",
    version="2.0.0",
    debug=DEBUG
)

# CORS - Allow production frontend and localhost for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "https://daily-horoscope-agent-fronted.onrender.com"
    ],
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
    session_id: str = Field(default="default", alias="sessionId")

    class Config:
        populate_by_name = True

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

# ============================================================================
# CHAT HISTORY ENDPOINTS
# ============================================================================

@app.get("/api/chat/history/{session_id}")
def get_chat_history(session_id: str, limit: int = 50):
    """
    Get chat history for a specific session
    """
    try:
        history = db_manager.get_chat_history(session_id, limit)
        # Convert ObjectId to string for JSON serialization
        for item in history:
            item['_id'] = str(item['_id'])
            if 'timestamp' in item:
                item['timestamp'] = item['timestamp'].isoformat() if item['timestamp'] else None
        return {
            "session_id": session_id,
            "messages": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chat history: {str(e)}")

@app.get("/api/chat/sessions")
def get_all_sessions(limit: int = 100):
    """
    Get all chat sessions
    """
    try:
        sessions = db_manager.get_all_sessions(limit)
        # Convert ObjectId to string for JSON serialization
        for session in sessions:
            session['_id'] = str(session['_id'])
            if 'last_active' in session:
                session['last_active'] = session['last_active'].isoformat() if session['last_active'] else None
            if 'created_at' in session:
                session['created_at'] = session['created_at'].isoformat() if session['created_at'] else None
        return {
            "sessions": sessions,
            "count": len(sessions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving sessions: {str(e)}")

@app.get("/api/chat/stats/{session_id}")
def get_session_stats(session_id: str):
    """
    Get statistics for a specific session
    """
    try:
        stats = db_manager.get_session_stats(session_id)
        if stats.get('session_info') and stats['session_info'].get('_id'):
            stats['session_info']['_id'] = str(stats['session_info']['_id'])
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving session stats: {str(e)}")

@app.get("/api/chat/stats")
def get_database_stats():
    """
    Get overall database statistics
    """
    try:
        return db_manager.get_database_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving database stats: {str(e)}")


# ============================================================================
# PUSH NOTIFICATION ENDPOINTS
# ============================================================================

class NotificationRequest(BaseModel):
    sign: str
    email: Optional[str] = None
    time: str = "08:00"  # Default morning time
    enabled: bool = True

@app.post("/api/notification/subscribe")
def subscribe_notification(request: NotificationRequest):
    """
    Subscribe to daily horoscope push notifications
    
    Simulates setting up a morning push notification.
    In production, this would integrate with Firebase/OneSignal/etc.
    """
    try:
        from database import db_manager
        if db_manager.connected:
            db_manager.db['notifications'].update_one(
                {"sign": request.sign.lower(), "email": request.email},
                {"$set": {
                    "sign": request.sign.lower(),
                    "email": request.email,
                    "time": request.time,
                    "enabled": request.enabled,
                    "subscribed_at": datetime.utcnow()
                }},
                upsert=True
            )
        return {
            "status": "subscribed",
            "sign": request.sign,
            "delivery_time": request.time,
            "message": f"You'll receive daily horoscope for {request.sign.title()} at {request.time} every morning! 🌅"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Subscription error: {str(e)}")

@app.post("/api/notification/send")
def send_notification(sign: str, test_mode: bool = False):
    """
    Send/Preview a daily horoscope notification
    
    Returns the notification content that would be sent.
    """
    try:
        result = horoscope_agent.generate_horoscope(sign)
        data = result["structured_data"]
        
        # Create a concise notification-style summary
        notification = {
            "title": f"🌟 {sign.title()} Daily Horoscope",
            "body": f"Day Rating: {data['day_rating']}/10 | "
                    f"Love: {data['love']['score']}/10 | "
                    f"Career: {data['career']['score']}/10 | "
                    f"💰 Money: {data['money']['score']}/10",
            "lucky_color": data['lucky_colour'],
            "lucky_number": data['lucky_number'],
            "best_time": data['best_time_window'],
            "preview": f"{data['overall_summary'][:100]}..." if len(data['overall_summary']) > 100 else data['overall_summary'],
            "full_horoscope": result["markdown_report"]
        }
        
        return {
            "notification": notification,
            "test_mode": test_mode,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notification error: {str(e)}")


# ============================================================================
# CALENDAR INTEGRATION ENDPOINTS
# ============================================================================

@app.get("/api/calendar/rating")
def get_calendar_rating(sign: str, date_str: Optional[str] = None):
    """
    Get a day rating for calendar integration.
    
    Tags the day as GOOD, MODERATE, or CHALLENGING based on horoscope scores.
    
    Use this to auto-tag days in your calendar app.
    """
    try:
        result = horoscope_agent.generate_horoscope(sign, date_str)
        data = result["structured_data"]
        
        # Calculate overall day rating
        scores = [
            data['love']['score'],
            data['career']['score'],
            data['health']['score'],
            data['money']['score']
        ]
        avg_score = sum(scores) / len(scores)
        
        # Determine tag
        if avg_score >= 7.5:
            tag = "🟢 GOOD DAY"
            color = "#4CAF50"
            suggestion = "Great day for important decisions, new beginnings, and social events!"
        elif avg_score >= 5.0:
            tag = "🟡 MODERATE DAY"
            color = "#FFC107"
            suggestion = "Good for planning, organizing, and steady progress."
        else:
            tag = "🔴 CHALLENGING DAY"
            color = "#F44336"
            suggestion = "Take it easy, rest, reflect, and avoid major decisions."
        
        return {
            "sign": sign,
            "date": data['date'],
            "tag": tag,
            "color": color,
            "average_score": round(avg_score, 1),
            "scores": {
                "love": data['love']['score'],
                "career": data['career']['score'],
                "health": data['health']['score'],
                "money": data['money']['score']
            },
            "lucky_color": data['lucky_colour'],
            "lucky_number": data['lucky_number'],
            "best_time": data['best_time_window'],
            "suggestion": suggestion,
            "calendar_event_title": f"{sign.title()} Horoscope: {tag}",
            "calendar_event_description": f"Day Rating: {round(avg_score, 1)}/10\n"
                                           f"Love: {data['love']['score']}/10\n"
                                           f"Career: {data['career']['score']}/10\n"
                                           f"Health: {data['health']['score']}/10\n"
                                           f"Money: {data['money']['score']}/10\n\n"
                                           f"Lucky: {data['lucky_colour']} | Number: {data['lucky_number']}\n\n"
                                           f"{suggestion}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calendar rating error: {str(e)}")

@app.get("/api/calendar/month")
def get_month_calendar(sign: str):
    """
    Get a full month calendar with daily ratings for a sign.
    
    Returns 30 days of ratings for calendar tagging.
    """
    try:
        from datetime import timedelta
        ratings = []
        base_date = datetime.now()
        
        for i in range(30):
            date = base_date + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            try:
                result = horoscope_agent.generate_horoscope(sign, date_str)
                data = result["structured_data"]
                
                scores = [
                    data['love']['score'],
                    data['career']['score'],
                    data['health']['score'],
                    data['money']['score']
                ]
                avg = sum(scores) / len(scores)
                
                if avg >= 7.5:
                    tag = "good"
                    color = "#4CAF50"
                elif avg >= 5.0:
                    tag = "moderate"
                    color = "#FFC107"
                else:
                    tag = "challenging"
                    color = "#F44336"
                
                ratings.append({
                    "date": date_str,
                    "tag": tag,
                    "color": color,
                    "average_score": round(avg, 1),
                    "lucky_color": data['lucky_colour'],
                    "lucky_number": data['lucky_number']
                })
            except:
                ratings.append({
                    "date": date_str,
                    "tag": "unknown",
                    "color": "#9E9E9E",
                    "average_score": None,
                    "lucky_color": None,
                    "lucky_number": None
                })
        
        return {
            "sign": sign,
            "month": base_date.strftime("%B %Y"),
            "days": ratings,
            "summary": {
                "good_days": len([r for r in ratings if r["tag"] == "good"]),
                "moderate_days": len([r for r in ratings if r["tag"] == "moderate"]),
                "challenging_days": len([r for r in ratings if r["tag"] == "challenging"])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Month calendar error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    print(f"🌟 Starting Daily Horoscope Agent...")
    print(f"✨ Using real Swiss Ephemeris for planetary calculations")
    print(f"🔧 Debug mode: {DEBUG}")
    print(f"🌐 Allowed origins: {FRONTEND_URL}")
    print(f"📊 API available at http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
