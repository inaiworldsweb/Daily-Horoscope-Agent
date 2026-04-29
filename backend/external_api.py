"""
FreeHoroscopeAPI.com Integration
Fetches real daily/weekly/monthly horoscopes from live API
"""

import requests
import json
from typing import Optional, Dict, Any
from datetime import datetime

BASE_URL = "https://freehoroscopeapi.com/api/v1"

ZODIAC_SIGNS = [
    "aries", "taurus", "gemini", "cancer",
    "leo", "virgo", "libra", "scorpio",
    "sagittarius", "capricorn", "aquarius", "pisces"
]


def get_daily_horoscope(sign: str, day: str = "today") -> Optional[Dict[str, Any]]:
    """Fetch daily horoscope from freehoroscopeapi.com"""
    sign = sign.lower().strip()
    if sign not in ZODIAC_SIGNS:
        return None

    try:
        url = f"{BASE_URL}/get-horoscope/daily"
        params = {"sign": sign, "day": day}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "data" in data and "horoscope" in data["data"]:
            return {
                "sign": data["data"]["sign"],
                "date": data["data"]["date"],
                "period": data["data"]["period"],
                "horoscope": data["data"]["horoscope"],
                "source": "freehoroscopeapi.com"
            }
        return None
    except Exception as e:
        print(f"⚠️ Error fetching daily horoscope: {e}")
        return None


def get_weekly_horoscope(sign: str) -> Optional[Dict[str, Any]]:
    """Fetch weekly horoscope from freehoroscopeapi.com"""
    sign = sign.lower().strip()
    if sign not in ZODIAC_SIGNS:
        return None

    try:
        url = f"{BASE_URL}/get-horoscope/weekly"
        params = {"sign": sign}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "data" in data and "horoscope" in data["data"]:
            return {
                "sign": data["data"]["sign"],
                "week": data["data"].get("week", ""),
                "period": data["data"]["period"],
                "horoscope": data["data"]["horoscope"],
                "source": "freehoroscopeapi.com"
            }
        return None
    except Exception as e:
        print(f"⚠️ Error fetching weekly horoscope: {e}")
        return None


def get_monthly_horoscope(sign: str) -> Optional[Dict[str, Any]]:
    """Fetch monthly horoscope from freehoroscopeapi.com"""
    sign = sign.lower().strip()
    if sign not in ZODIAC_SIGNS:
        return None

    try:
        url = f"{BASE_URL}/get-horoscope/monthly"
        params = {"sign": sign}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "data" in data and "horoscope" in data["data"]:
            return {
                "sign": data["data"]["sign"],
                "month": data["data"].get("month", ""),
                "period": data["data"]["period"],
                "horoscope": data["data"]["horoscope"],
                "source": "freehoroscopeapi.com"
            }
        return None
    except Exception as e:
        print(f"⚠️ Error fetching monthly horoscope: {e}")
        return None


def format_horoscope_reply(horoscope_data: Dict[str, Any], topic: Optional[str] = None) -> str:
    """Format API horoscope into a nice markdown reply"""
    if not horoscope_data:
        return "Sorry, I couldn't fetch the horoscope right now. Please try again later."

    sign = horoscope_data.get("sign", "Unknown")
    period = horoscope_data.get("period", "daily").title()
    date_info = horoscope_data.get("date", "")
    week_info = horoscope_data.get("week", "")
    month_info = horoscope_data.get("month", "")
    horoscope = horoscope_data.get("horoscope", "")

    # Clean up horoscope text
    horoscope = horoscope.replace("\n\n", "\n").strip()

    header = f"## 🔮 {sign.title()} {period} Horoscope"
    if date_info:
        header += f"\n**Date:** {date_info}"
    if week_info:
        header += f"\n**Week:** {week_info}"
    if month_info:
        header += f"\n**Month:** {month_info}"

    return f"""{header}

{horoscope}

---
*Powered by [freehoroscopeapi.com](https://freehoroscopeapi.com)*
"""


def get_tarot_random(n: int = 1, minor: bool = False) -> Optional[Dict[str, Any]]:
    """Fetch random tarot card(s)"""
    try:
        url = f"{BASE_URL}/tarot/cards/random"
        params = {"n": n, "minor": str(minor).lower()}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"⚠️ Error fetching tarot: {e}")
        return None
