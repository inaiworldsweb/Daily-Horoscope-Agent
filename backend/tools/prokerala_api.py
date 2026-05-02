"""
Prokerala API Integration — Direct HTTP calls with OAuth 2.0
Correct endpoints discovered from official PHP SDK source code:
  - Daily:        /v2/horoscope/daily
  - Daily Adv:    /v2/horoscope/daily/advanced
  - Daily Love:   /v2/horoscope/daily/love-compatibility
  - Panchang:     /v2/panchang
  NOTE: Prokerala does NOT have weekly/monthly horoscope endpoints.
"""
import os
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from dotenv import load_dotenv
load_dotenv()

# ── Configuration ──
TOKEN_URL  = "https://api.prokerala.com/token"
API_BASE   = "https://api.prokerala.com"
CLIENT_ID     = os.getenv("PROKERALA_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("PROKERALA_CLIENT_SECRET", "")

# Cached token
_token_cache: Dict[str, Any] = {"access_token": None, "expires_at": None}


def _fetch_token_sync() -> str:
    """Fetch OAuth2 token (client credentials flow) with caching."""
    global _token_cache
    if _token_cache["access_token"] and _token_cache["expires_at"]:
        if datetime.utcnow() < _token_cache["expires_at"] - timedelta(seconds=60):
            return _token_cache["access_token"]

    if not CLIENT_ID or not CLIENT_SECRET:
        raise RuntimeError("PROKERALA_CLIENT_ID and PROKERALA_CLIENT_SECRET must be set in .env")

    resp = httpx.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["access_token"] = data["access_token"]
    expires_in = data.get("expires_in", 3600)
    _token_cache["expires_at"] = datetime.utcnow() + timedelta(seconds=expires_in)
    return _token_cache["access_token"]


def _prokerala_get_sync(path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Authenticated GET to Prokerala API."""
    token = _fetch_token_sync()
    url = f"{API_BASE}{path}"
    resp = httpx.get(
        url,
        params=params or {},
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


# ── Daily Horoscope (simple) ──
def get_daily_horoscope_prokerala_sync(sign: str, dt: Optional[str] = None) -> Dict[str, Any]:
    """Fetch daily horoscope from Prokerala API.
    Endpoint: /v2/horoscope/daily  (params: datetime, sign)
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        return {"source": "prokerala", "sign": sign, "error": "PROKERALA_CLIENT_ID and PROKERALA_CLIENT_SECRET must be set in .env"}

    if not dt:
        dt = datetime.now().strftime("%Y-%m-%dT09:00:00+05:30")
    elif "T" not in dt:
        dt = f"{dt}T09:00:00+05:30"

    try:
        data = _prokerala_get_sync("/v2/horoscope/daily", {
            "sign": sign.lower(),
            "datetime": dt,
        })
        return {"source": "prokerala", "sign": sign.lower(), "date": dt, "data": data}
    except Exception as e:
        return {"source": "prokerala", "sign": sign, "date": dt, "error": str(e)}


# ── Daily Horoscope (advanced — with aspects, seek, challenge, insight) ──
def get_daily_horoscope_advanced_prokerala_sync(sign: str, dt: Optional[str] = None, htype: str = "general") -> Dict[str, Any]:
    """Fetch advanced daily horoscope from Prokerala API.
    Endpoint: /v2/horoscope/daily/advanced  (params: datetime, sign, type)
    type: general, love, career, health, etc.
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        return {"source": "prokerala", "sign": sign, "error": "PROKERALA_CLIENT_ID and PROKERALA_CLIENT_SECRET must be set in .env"}

    if not dt:
        dt = datetime.now().strftime("%Y-%m-%dT09:00:00+05:30")
    elif "T" not in dt:
        dt = f"{dt}T09:00:00+05:30"

    try:
        data = _prokerala_get_sync("/v2/horoscope/daily/advanced", {
            "sign": sign.lower(),
            "datetime": dt,
            "type": htype.lower(),
        })
        return {"source": "prokerala", "sign": sign.lower(), "date": dt, "type": htype, "data": data}
    except Exception as e:
        return {"source": "prokerala", "sign": sign, "date": dt, "type": htype, "error": str(e)}


# ── Weekly / Monthly — NOT available on Prokerala API ──
# Prokerala only offers daily horoscope endpoints.
# Weekly/monthly will fall back to freehoroscopeapi.com in agent.py

def get_weekly_horoscope_prokerala_sync(sign: str) -> Dict[str, Any]:
    """Prokerala does NOT have a weekly horoscope endpoint. Returns error."""
    return {"source": "prokerala", "sign": sign, "error": "Prokerala API does not provide weekly horoscope. Using fallback."}

def get_monthly_horoscope_prokerala_sync(sign: str) -> Dict[str, Any]:
    """Prokerala does NOT have a monthly horoscope endpoint. Returns error."""
    return {"source": "prokerala", "sign": sign, "error": "Prokerala API does not provide monthly horoscope. Using fallback."}


# ── Panchang ──
def get_panchang_prokerala_sync(
    dt: Optional[str] = None,
    lat: float = 28.6139,
    lon: float = 77.2090,
) -> Dict[str, Any]:
    """Fetch Panchang from Prokerala API.
    Endpoint: /v2/panchang  (params: datetime, latitude, longitude, ayanamsa)
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        return {"source": "prokerala", "error": "PROKERALA_CLIENT_ID and PROKERALA_CLIENT_SECRET must be set in .env"}

    if not dt:
        dt = datetime.now().strftime("%Y-%m-%dT09:00:00+05:30")
    elif "T" not in dt:
        dt = f"{dt}T09:00:00+05:30"

    try:
        data = _prokerala_get_sync("/v2/astrology/panchang", {
            "datetime": dt,
            "latitude": lat,
            "longitude": lon,
            "ayanamsa": 1,
        })
        return {"source": "prokerala", "date": dt, "location": {"lat": lat, "lon": lon}, "data": data}
    except Exception as e:
        return {"source": "prokerala", "date": dt, "location": {"lat": lat, "lon": lon}, "error": str(e)}


# ── Lucky Details (combines Panchang + Horoscope) ──
def get_lucky_details_prokerala_sync(sign: str, dt: Optional[str] = None) -> Dict[str, Any]:
    """Combine Panchang + daily horoscope for lucky items."""
    panchang = get_panchang_prokerala_sync(dt)
    horoscope = get_daily_horoscope_prokerala_sync(sign, dt)

    p_data = panchang.get("data", {})
    tithi_name = ""
    nakshatra_name = ""
    if isinstance(p_data, dict):
        tithi = p_data.get("tithi") or p_data.get("tithis", [{}])[0]
        if isinstance(tithi, dict):
            tithi_name = tithi.get("name", "")
        nakshatra = p_data.get("nakshatra") or p_data.get("nakshatras", [{}])[0]
        if isinstance(nakshatra, dict):
            nakshatra_name = nakshatra.get("name", "")

    return {
        "source": "prokerala",
        "sign": sign.lower(),
        "date": dt or datetime.now().strftime("%Y-%m-%d"),
        "tithi": tithi_name,
        "nakshatra": nakshatra_name,
        "panchang": panchang,
        "horoscope": horoscope,
        "lucky_number": hash((sign, dt)) % 9 + 1,
        "lucky_colour": "Gold" if tithi_name else "",
        "lucky_direction": "East" if nakshatra_name else "",
    }


# ── Formatter ──
def format_prokerala_horoscope_reply(horoscope_result: Dict[str, Any], topic: Optional[str] = None) -> str:
    """Format Prokerala horoscope response into markdown reply."""
    if not horoscope_result:
        return "Sorry, I couldn't fetch the horoscope right now. Please try again later."

    sign = horoscope_result.get("sign", "Unknown").title()
    dt = horoscope_result.get("date", "Today")

    if "error" in horoscope_result:
        return f"⚠️ Could not fetch Prokerala horoscope for **{sign}**: {horoscope_result['error']}"

    raw = horoscope_result.get("data", {})
    if not isinstance(raw, dict):
        raw = {"result": str(raw)}

    # Unwrap Prokerala envelope: {"status":"ok","data":{...}}
    if "status" in raw and "data" in raw:
        raw = raw["data"]

    # ── Extract prediction text ──
    horoscope_text = ""
    topic_lower = topic.lower() if topic else None

    # Simple daily response: data.daily_prediction.prediction
    dp = raw.get("daily_prediction")
    if isinstance(dp, dict):
        horoscope_text = dp.get("prediction", "")

    # Advanced daily response: data.daily_predictions[0].predictions[0].prediction
    if not horoscope_text:
        dps = raw.get("daily_predictions")
        if isinstance(dps, list) and dps:
            for dp_item in dps:
                preds = dp_item.get("predictions", [])
                for pred in preds:
                    pred_type = pred.get("type", "").lower()
                    pred_text = pred.get("prediction", "")
                    if not pred_text:
                        continue
                    # If topic requested, only show matching prediction
                    # Money maps to career (Prokerala combines Career & Money)
                    matched = (pred_type == topic_lower)
                    if topic_lower == "money" and pred_type == "career":
                        matched = True
                    if topic_lower and not matched:
                        continue
                    seek = pred.get("seek", "")
                    challenge = pred.get("challenge", "")
                    insight = pred.get("insight", "")
                    horoscope_text += f"**{pred_type.title()}**: {pred_text}\n\n"
                    if seek:
                        horoscope_text += f"✨ **Seek**: {seek}\n\n"
                    if challenge:
                        horoscope_text += f"⚡ **Challenge**: {challenge}\n\n"
                    if insight:
                        horoscope_text += f"💡 **Insight**: {insight}\n\n"

    # Generic fallback
    if not horoscope_text:
        for key in ("prediction", "horoscope", "general", "result", "description", "text"):
            val = raw.get(key)
            if val and isinstance(val, str) and len(val) > 20:
                horoscope_text = val
                break

    if not horoscope_text:
        horoscope_text = str(raw)

    horoscope_text = horoscope_text.replace("&#039;", "'").replace("&amp;", "&").strip()

    # ── Clean table format for topic-specific requests ──
    if topic_lower:
        topic_emojis = {"love": "💕", "career": "💼", "health": "🏥", "money": "💰"}
        emoji = topic_emojis.get(topic_lower, "🔮")
        title = topic.title()

        # Extract fields from the prediction text
        rows = []
        main_pred = ""
        seek_val = ""
        challenge_val = ""
        insight_val = ""

        # Re-extract from raw structure for cleaner formatting
        dps_raw = raw.get("daily_predictions")
        if isinstance(dps_raw, list) and dps_raw:
            for dp_item in dps_raw:
                preds = dp_item.get("predictions", [])
                for pred in preds:
                    pred_type_raw = pred.get("type", "").lower()
                    # Money maps to career (Prokerala combines Career & Money)
                    matched = (pred_type_raw == topic_lower)
                    if topic_lower == "money" and pred_type_raw == "career":
                        matched = True
                    if not matched:
                        continue
                    main_pred = pred.get("prediction", "").strip()
                    seek_val = pred.get("seek", "").strip()
                    challenge_val = pred.get("challenge", "").strip()
                    insight_val = pred.get("insight", "").strip()
                    break

        if main_pred:
            rows.append(f"| {emoji} **{title}** | {main_pred} |")
        if seek_val:
            rows.append(f"| ✨ **Seek** | {seek_val} |")
        if challenge_val:
            rows.append(f"| ⚡ **Challenge** | {challenge_val} |")
        if insight_val:
            rows.append(f"| 💡 **Insight** | {insight_val} |")

        if rows:
            table = "\n".join(rows)
            return f"""## {emoji} {title} Guide for {sign}

| Item | Guidance |
|------|----------|
{table}

✨ *Your {title.lower()} guide for today!*"""

    header = f"## 🔮 {sign} Daily Horoscope"
    if dt:
        header += f"\n**Date:** {dt[:10] if len(dt) > 10 else dt}"
    topic_line = f"\n**Topic:** {topic.title()}" if topic else ""

    return f"""{header}{topic_line}

{horoscope_text}

---
*Powered by [Prokerala Astrology API](https://www.prokerala.com)*
"""


# ── TEST ──
if __name__ == "__main__":
    print("Testing Prokerala API (direct HTTP)...")
    print(f"Client ID Set: {bool(CLIENT_ID)}")
    print(f"Client Secret Set: {bool(CLIENT_SECRET)}")

    if CLIENT_ID and CLIENT_SECRET:
        print("\n1. Daily horoscope (simple)...")
        result = get_daily_horoscope_prokerala_sync("leo")
        has_error = "error" in result
        print(f"   {'ERROR' if has_error else 'OK'}: {result.get('error', 'Got data')}")

        print("\n2. Daily horoscope (advanced)...")
        result2 = get_daily_horoscope_advanced_prokerala_sync("leo", htype="general")
        has_error2 = "error" in result2
        print(f"   {'ERROR' if has_error2 else 'OK'}: {result2.get('error', 'Got data')}")

        print("\n3. Format test...")
        print(format_prokerala_horoscope_reply(result))
    else:
        print("Set PROKERALA_CLIENT_ID and PROKERALA_CLIENT_SECRET in .env")
