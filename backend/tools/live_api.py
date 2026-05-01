import httpx
import asyncio
import os
import json
import hashlib
from datetime import date, datetime, timedelta
from typing import Optional

BASE = os.getenv("FREE_HOROSCOPE_API_BASE", "https://freehoroscopeapi.com/api/v1")

SIGNS = [
    "aries","taurus","gemini","cancer","leo","virgo",
    "libra","scorpio","sagittarius","capricorn","aquarius","pisces"
]

BIRTH_DATE_TO_SIGN = [
    ((1,1),(1,19),"capricorn"),   ((1,20),(2,18),"aquarius"),
    ((2,19),(3,20),"pisces"),     ((3,21),(4,19),"aries"),
    ((4,20),(5,20),"taurus"),     ((5,21),(6,20),"gemini"),
    ((6,21),(7,22),"cancer"),     ((7,23),(8,22),"leo"),
    ((8,23),(9,22),"virgo"),      ((9,23),(10,22),"libra"),
    ((10,23),(11,21),"scorpio"),  ((11,22),(12,21),"sagittarius"),
    ((12,22),(12,31),"capricorn")
]

LUCKY_DATA = {
    "aries":       {"colour":"Red",          "number":9,  "direction":"East",  "day_tag_threshold":6},
    "taurus":      {"colour":"Green",         "number":6,  "direction":"South", "day_tag_threshold":6},
    "gemini":      {"colour":"Yellow",        "number":5,  "direction":"West",  "day_tag_threshold":6},
    "cancer":      {"colour":"White",         "number":2,  "direction":"North", "day_tag_threshold":6},
    "leo":         {"colour":"Gold",          "number":1,  "direction":"East",  "day_tag_threshold":7},
    "virgo":       {"colour":"Navy Blue",     "number":4,  "direction":"South", "day_tag_threshold":6},
    "libra":       {"colour":"Pink",          "number":7,  "direction":"West",  "day_tag_threshold":6},
    "scorpio":     {"colour":"Crimson",       "number":8,  "direction":"North", "day_tag_threshold":6},
    "sagittarius": {"colour":"Purple",        "number":3,  "direction":"East",  "day_tag_threshold":7},
    "capricorn":   {"colour":"Dark Grey",     "number":10, "direction":"South", "day_tag_threshold":6},
    "aquarius":    {"colour":"Electric Blue", "number":11, "direction":"West",  "day_tag_threshold":6},
    "pisces":      {"colour":"Sea Green",     "number":12, "direction":"North", "day_tag_threshold":6},
}

def birth_date_to_sign(birth_date: str) -> str:
    try:
        if "/" in birth_date:
            dt = datetime.strptime(birth_date, "%d/%m/%Y")
        else:
            dt = datetime.strptime(birth_date, "%Y-%m-%d")
        month, day = dt.month, dt.day
        for (sm, sd), (em, ed), sign in BIRTH_DATE_TO_SIGN:
            if (month == sm and day >= sd) or (month == em and day <= ed):
                return sign
        return "capricorn"
    except Exception:
        return "aries"

async def _get(endpoint: str, sign: str) -> dict:
    url = f"{BASE}/get-horoscope/{endpoint}"
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(url, params={"sign": sign.lower()})
            r.raise_for_status()
            return r.json().get("data", {})
    except Exception as e:
        return {"sign": sign, "horoscope": "", "error": str(e)}

async def _get_tarot_random() -> dict:
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(f"{BASE}/tarot/cards/random", params={"n": 1, "minor": "true"})
            r.raise_for_status()
            cards = r.json().get("cards", [{}])
            return cards[0] if cards else {}
    except Exception:
        return {}

async def get_life_area_predictions(sign: str) -> dict:
    import anthropic
    sign = sign.lower()
    daily_data = await _get("daily", sign)
    horoscope_text = daily_data.get("horoscope", "")
    if not horoscope_text:
        return {
            "sign": sign,
            "date": str(date.today()),
            "love":   {"prediction": "Data unavailable", "score": 5.0, "advice": "Stay positive"},
            "career": {"prediction": "Data unavailable", "score": 5.0, "advice": "Stay focused"},
            "health": {"prediction": "Data unavailable", "score": 5.0, "advice": "Rest well"},
            "money":  {"prediction": "Data unavailable", "score": 5.0, "advice": "Be cautious"},
            "day_rating": 5.0,
            "overall_summary": "Horoscope data temporarily unavailable.",
            "raw_horoscope": horoscope_text
        }
    lucky = LUCKY_DATA.get(sign, {})
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    prompt = f"""You are a professional astrologer. 
Given this daily horoscope for {sign.title()}: 

"{horoscope_text}"

Split it into 4 life areas and output ONLY valid JSON, no extra text:
{{
  "day_rating": <number 1-10>,
  "overall_summary": "<2 sentence summary>",
  "love":   {{"prediction": "<love prediction>",   "score": <1-10>, "advice": "<one tip>"}},
  "career": {{"prediction": "<career prediction>", "score": <1-10>, "advice": "<one tip>"}},
  "health": {{"prediction": "<health prediction>", "score": <1-10>, "advice": "<one tip>"}},
  "money":  {{"prediction": "<money prediction>",  "score": <1-10>, "advice": "<one tip>"}}
}}"""
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    result = json.loads(response.content[0].text.strip())
    result["sign"] = sign
    result["date"] = str(date.today())
    result["raw_horoscope"] = horoscope_text
    result["lucky"] = lucky
    return result

async def get_push_notification_summary(sign: str) -> dict:
    sign = sign.lower()
    daily_data = await _get("daily", sign)
    horoscope  = daily_data.get("horoscope", "")
    lucky      = LUCKY_DATA.get(sign, {})
    if not horoscope:
        return {
            "sign":  sign,
            "title": f"🌟 {sign.title()} Horoscope",
            "body":  "Your stars are aligning today. Open the app to see your full reading.",
            "short": "Check your horoscope today!"
        }
    sentences = horoscope.replace("!", ".").replace("?", ".").split(".")
    summary   = ". ".join(s.strip() for s in sentences[:2] if s.strip()) + "."
    return {
        "sign":  sign,
        "date":  str(date.today()),
        "title": f"🌟 {sign.title()} — {date.today().strftime('%b %d')}",
        "body":  summary[:200],
        "short": f"{sign.title()}: {summary[:100]}...",
        "lucky_colour":    lucky.get("colour", ""),
        "lucky_number":    lucky.get("number", ""),
        "lucky_direction": lucky.get("direction", ""),
        "push_payload": {
            "notification": {
                "title": f"🌟 Your {sign.title()} Horoscope",
                "body":  summary[:160]
            },
            "data": {
                "sign":   sign,
                "date":   str(date.today()),
                "screen": "horoscope_detail"
            }
        }
    }

async def get_yesterday_vs_today(sign: str, db=None) -> dict:
    import anthropic
    sign = sign.lower()
    today_data = await _get("daily", sign)
    today_text = today_data.get("horoscope", "")
    weekly_data = await _get("weekly", sign)
    weekly_text = weekly_data.get("horoscope", "")
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    today_str     = date.today().strftime("%B %d")
    yesterday_str = (date.today() - timedelta(days=1)).strftime("%B %d")
    prompt = f"""You are a professional astrologer.

Today's horoscope for {sign.title()} ({today_str}):
"{today_text}"

Weekly context:
"{weekly_text[:400]}"

Based on the weekly context and today's horoscope, generate BOTH today AND yesterday scores.
Output ONLY valid JSON:
{{
  "today": {{
    "date": "{str(date.today())}",
    "day_rating": <1-10>,
    "love": <1-10>,
    "career": <1-10>,
    "health": <1-10>,
    "money": <1-10>,
    "summary": "<today in one sentence>"
  }},
  "yesterday": {{
    "date": "{str(date.today() - timedelta(days=1))}",
    "day_rating": <1-10>,
    "love": <1-10>,
    "career": <1-10>,
    "health": <1-10>,
    "money": <1-10>,
    "summary": "<yesterday in one sentence>"
  }},
  "trend": {{
    "love":   "<improved|declined|stable>",
    "career": "<improved|declined|stable>",
    "health": "<improved|declined|stable>",
    "money":  "<improved|declined|stable>",
    "overall": "<brief trend insight for {sign.title()}>"
  }}
}}"""
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )
    result = json.loads(response.content[0].text.strip())
    result["sign"] = sign
    return result

async def get_lucky_items(sign: str) -> dict:
    sign = sign.lower()
    daily_data, tarot_card = await asyncio.gather(
        _get("daily", sign),
        _get_tarot_random()
    )
    lucky = LUCKY_DATA.get(sign, {})
    horoscope = daily_data.get("horoscope", "")
    day_hash   = int(hashlib.md5(f"{sign}{date.today()}".encode()).hexdigest(), 16)
    start_hour = 6 + (day_hash % 12)
    end_hour   = start_hour + 2
    lucky_time = f"{start_hour}:00 {'AM' if start_hour < 12 else 'PM'} - {end_hour}:00 {'AM' if end_hour < 12 else 'PM'}"
    avoid_hour = (start_hour + 5) % 24
    avoid_time = f"{avoid_hour}:00 {'AM' if avoid_hour < 12 else 'PM'} - {(avoid_hour+1)%24}:00 {'AM' if (avoid_hour+1)<12 else 'PM'}"
    return {
        "sign":              sign,
        "date":              str(date.today()),
        "lucky_colour":      lucky.get("colour", "Gold"),
        "lucky_number":      lucky.get("number", 7),
        "lucky_direction":   lucky.get("direction", "East"),
        "lucky_time":        lucky_time,
        "avoid_time":        avoid_time,
        "lucky_gemstone":    _sign_gemstone(sign),
        "lucky_planet":      _sign_planet(sign),
        "tarot_card": {
            "name":         tarot_card.get("name", ""),
            "meaning":      tarot_card.get("meaning_up", ""),
            "description":  tarot_card.get("desc", "")[:200] if tarot_card.get("desc") else ""
        },
        "daily_affirmation": _affirmation(sign, horoscope),
        "horoscope_snippet": horoscope[:150] + "..." if len(horoscope) > 150 else horoscope
    }

def _sign_gemstone(sign: str) -> str:
    gems = {
        "aries":"Red Coral","taurus":"Diamond","gemini":"Emerald",
        "cancer":"Pearl","leo":"Ruby","virgo":"Emerald",
        "libra":"Diamond","scorpio":"Red Coral","sagittarius":"Yellow Sapphire",
        "capricorn":"Blue Sapphire","aquarius":"Blue Sapphire","pisces":"Yellow Sapphire"
    }
    return gems.get(sign, "Crystal")

def _sign_planet(sign: str) -> str:
    planets = {
        "aries":"Mars","taurus":"Venus","gemini":"Mercury","cancer":"Moon",
        "leo":"Sun","virgo":"Mercury","libra":"Venus","scorpio":"Mars/Pluto",
        "sagittarius":"Jupiter","capricorn":"Saturn","aquarius":"Saturn/Uranus","pisces":"Jupiter/Neptune"
    }
    return planets.get(sign, "Sun")

def _affirmation(sign: str, horoscope: str) -> str:
    affirmations = {
        "aries":"I lead with courage and act with confidence today.",
        "taurus":"I attract abundance and beauty into my life today.",
        "gemini":"My words carry power and create meaningful connections today.",
        "cancer":"I trust my intuition and nurture myself and others today.",
        "leo":"I shine my authentic light and inspire those around me today.",
        "virgo":"I bring precision and care to everything I do today.",
        "libra":"I create harmony and attract beautiful relationships today.",
        "scorpio":"I embrace transformation and step into my full power today.",
        "sagittarius":"I expand my horizons and welcome new adventures today.",
        "capricorn":"I build lasting success through focused, disciplined action today.",
        "aquarius":"I embrace innovation and contribute meaningfully to the world today.",
        "pisces":"I trust my intuition and create beauty from my dreams today."
    }
    return affirmations.get(sign, "I embrace this day with gratitude and purpose.")

async def get_calendar_tag(sign: str, target_date: date = None) -> dict:
    import anthropic
    sign = sign.lower()
    if not target_date:
        target_date = date.today()
    daily_data, monthly_data = await asyncio.gather(
        _get("daily", sign),
        _get("monthly", sign)
    )
    daily_text   = daily_data.get("horoscope", "")
    monthly_text = monthly_data.get("horoscope", "")
    lucky        = LUCKY_DATA.get(sign, {})
    threshold    = lucky.get("day_tag_threshold", 6)
    if not daily_text:
        return {
            "sign":        sign,
            "date":        str(target_date),
            "tag":         "neutral_day",
            "colour_code": "#888888",
            "emoji":       "⚪",
            "rating":      5.0,
            "reason":      "Planetary data unavailable — neutral day.",
            "calendar_event": {
                "title":       f"{sign.title()} — Neutral Day",
                "description": "Check your horoscope for updates.",
                "colour":      "graphite"
            }
        }
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    prompt = f"""You are a professional astrologer.

Today's horoscope for {sign.title()} on {target_date}:
"{daily_text}"

Monthly context:
"{monthly_text[:300]}"

Rate this day and output ONLY valid JSON:
{{
  "rating": <number 1-10>,
  "tag": "<good_day|bad_day|neutral_day>",
  "reason": "<one sentence explanation>",
  "dominant_energy": "<positive|negative|mixed>",
  "best_activity": "<what to do today>",
  "avoid_activity": "<what to avoid today>"
}}"""
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    ai = json.loads(response.content[0].text.strip())
    rating = ai.get("rating", 5)
    tag    = ai.get("tag", "neutral_day")
    colour_map = {
        "good_day":    {"hex": "#34c97b", "emoji": "🟢", "google": "sage"},
        "bad_day":     {"hex": "#ff6b6b", "emoji": "🔴", "google": "tomato"},
        "neutral_day": {"hex": "#f5a623", "emoji": "🟡", "google": "banana"}
    }
    colours = colour_map.get(tag, colour_map["neutral_day"])
    return {
        "sign":              sign,
        "date":              str(target_date),
        "tag":               tag,
        "rating":            rating,
        "colour_code":       colours["hex"],
        "emoji":             colours["emoji"],
        "reason":            ai.get("reason", ""),
        "dominant_energy":   ai.get("dominant_energy", "mixed"),
        "best_activity":     ai.get("best_activity", ""),
        "avoid_activity":    ai.get("avoid_activity", ""),
        "calendar_event": {
            "title":       f"{sign.title()} — {tag.replace('_',' ').title()} {colours['emoji']}",
            "description": ai.get("reason", ""),
            "date":        str(target_date),
            "colour":      colours["google"],
            "all_day":     True
        }
    }

async def get_full_horoscope(sign: str = None, birth_date: str = None) -> dict:
    if not sign and birth_date:
        sign = birth_date_to_sign(birth_date)
    if not sign:
        raise ValueError("Provide either sign or birth_date")
    sign = sign.lower()
    predictions, push_notif, lucky_items, calendar_tag = await asyncio.gather(
        get_life_area_predictions(sign),
        get_push_notification_summary(sign),
        get_lucky_items(sign),
        get_calendar_tag(sign)
    )
    return {
        "sign":        sign,
        "date":        str(date.today()),
        "birth_date":  birth_date or "",
        "predictions": predictions,
        "push_notification": push_notif,
        "lucky": lucky_items,
        "calendar": calendar_tag,
        "api_source": "freehoroscopeapi.com",
        "fetched_at": datetime.utcnow().isoformat()
    }
