"""
Response Formatter - Makes all chat answers clean and professional
"""
import re


def format_horoscope_response(horoscope_text: str, sign: str = None, period: str = "daily") -> str:
    """Format horoscope text into clean, professional output"""
    # Clean up excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', horoscope_text)
    text = text.strip()
    
    if sign:
        header = f"## 🔮 {sign.title()} {period.title()} Horoscope\n\n"
    else:
        header = ""
    
    return header + text


def format_lucky_guide(data: dict, sign: str) -> str:
    """Format lucky color, number, direction into clean output"""
    return f"""## 🍀 Lucky Guide for {sign.title()}

| Item | Value |
|------|-------|
| 🎨 **Color** | {data.get('lucky_colour', 'N/A')} |
| 🔢 **Number** | {data.get('lucky_number', 'N/A')} |
| 🧭 **Direction** | {data.get('lucky_direction', 'N/A')} |
| ⏰ **Best Time** | {data.get('best_time_window', 'N/A')} |
| ⚠️ **Avoid** | {data.get('avoid_time_window', 'N/A')} |

✨ *Your personal lucky charm for today!*"""


def format_day_rating(data: dict, sign: str, avg_score: float) -> str:
    """Format calendar day rating into clean output"""
    if avg_score >= 7.5:
        emoji = "🟢"
        tag = "GOOD DAY"
    elif avg_score >= 5.0:
        emoji = "🟡"
        tag = "MODERATE DAY"
    else:
        emoji = "🔴"
        tag = "CHALLENGING DAY"
    
    return f"""## 📅 Calendar Rating for {sign.title()} - {data.get('date', 'Today')}

### {emoji} {tag}

**Overall Score:** ⭐ {round(avg_score, 1)}/10

| Category | Score |
|----------|-------|
| 💕 Love | {data['love']['score']}/10 |
| 💼 Career | {data['career']['score']}/10 |
| 🏥 Health | {data['health']['score']}/10 |
| 💰 Money | {data['money']['score']}/10 |

**🍀 Lucky:** {data.get('lucky_colour', 'N/A')} | **Number:** {data.get('lucky_number', 'N/A')}

**💡 Suggestion:** {get_suggestion(avg_score)}

*Use API `/api/calendar/rating?sign={sign}` to auto-tag your calendar!*"""


def get_suggestion(avg_score: float) -> str:
    if avg_score >= 7.5:
        return "Great day for important decisions, new beginnings, and social events!"
    elif avg_score >= 5.0:
        return "Good for planning, organizing, and steady progress."
    else:
        return "Take it easy, rest, reflect, and avoid major decisions."


def format_notification_preview(data: dict, sign: str) -> str:
    """Format notification preview into clean output"""
    return f"""## 🌅 Daily Horoscope Notification

### {sign.title()} - {data.get('date', 'Today')}

⭐ **Day Rating:** {data.get('day_rating', 'N/A')}/10

| Category | Score |
|----------|-------|
| 💕 Love | {data['love']['score']}/10 |
| 💼 Career | {data['career']['score']}/10 |
| 🏥 Health | {data['health']['score']}/10 |
| 💰 Money | {data['money']['score']}/10 |

**🍀 Lucky:** {data.get('lucky_colour', 'N/A')} | **Number:** {data.get('lucky_number', 'N/A')}
**⏰ Best Time:** {data.get('best_time_window', 'N/A')}

---
📱 *This is how your morning notification would look!*

**To subscribe:** Use API `/api/notification/subscribe` with your sign and preferred time."""


def format_greeting() -> str:
    return "👋 **Hello!** I'm your Daily Horoscope Agent.\n\nTell me your zodiac sign (like 'I'm Leo') and I'll share your horoscope!"


def format_topic_guide(data: dict, sign: str, topic: str) -> str:
    """Format topic-specific horoscope (love, career, health, money) into clean table output"""
    topic_emojis = {
        "love": "💕",
        "career": "💼",
        "health": "🏥",
        "money": "💰",
    }
    emoji = topic_emojis.get(topic, "🔮")
    title = topic.title()

    pred = data.get("prediction", "").strip()
    seek = data.get("seek", "").strip()
    challenge = data.get("challenge", "").strip()
    insight = data.get("insight", "").strip()

    # Build table rows for available fields
    rows = []
    if pred:
        rows.append(f"| {emoji} **{title}** | {pred} |")
    if seek:
        rows.append(f"| ✨ **Seek** | {seek} |")
    if challenge:
        rows.append(f"| ⚡ **Challenge** | {challenge} |")
    if insight:
        rows.append(f"| 💡 **Insight** | {insight} |")

    table = "\n".join(rows)

    return f"""## {emoji} {title} Guide for {sign.title()}

| Item | Guidance |
|------|----------|
{table}

✨ *Your {title.lower()} guide for today!*"""


def format_error(message: str) -> str:
    return f"⚠️ **Oops!** {message}"


def format_comparison(yesterday_data: dict, today_data: dict, sign: str) -> str:
    """Format yesterday vs today comparison"""
    y_score = yesterday_data.get('day_rating', 0)
    t_score = today_data.get('day_rating', 0)
    diff = t_score - y_score
    
    if diff > 0:
        trend = "📈 Improved"
    elif diff < 0:
        trend = "📉 Decreased"
    else:
        trend = "➡️ Same"
    
    return f"""## 📊 {sign.title()} Trend: Yesterday vs Today

**Overall Trend:** {trend} ({diff:+.1f} points)

| Category | Yesterday | Today | Change |
|----------|-----------|-------|--------|
| 💕 Love | {yesterday_data['love']['score']}/10 | {today_data['love']['score']}/10 | {today_data['love']['score'] - yesterday_data['love']['score']:+.1f} |
| 💼 Career | {yesterday_data['career']['score']}/10 | {today_data['career']['score']}/10 | {today_data['career']['score'] - yesterday_data['career']['score']:+.1f} |
| 🏥 Health | {yesterday_data['health']['score']}/10 | {today_data['health']['score']}/10 | {today_data['health']['score'] - yesterday_data['health']['score']:+.1f} |
| 💰 Money | {yesterday_data['money']['score']}/10 | {today_data['money']['score']}/10 | {today_data['money']['score'] - yesterday_data['money']['score']:+.1f} |

**🍀 Today's Lucky:** {today_data.get('lucky_colour', 'N/A')} | **Number:** {today_data.get('lucky_number', 'N/A')}"""


def format_sign_profile(sign: str, horoscope_data: dict, rag_traits: str = "") -> str:
    """Format comprehensive sign profile with all details in one format"""
    d = horoscope_data
    sign_title = sign.title()
    
    # Sign details from zodiac knowledge
    sign_details = {
        "aries": {"element": "Fire", "planet": "Mars", "dates": "Mar 21 - Apr 19", "symbol": "♈"},
        "taurus": {"element": "Earth", "planet": "Venus", "dates": "Apr 20 - May 20", "symbol": "♉"},
        "gemini": {"element": "Air", "planet": "Mercury", "dates": "May 21 - Jun 20", "symbol": "♊"},
        "cancer": {"element": "Water", "planet": "Moon", "dates": "Jun 21 - Jul 22", "symbol": "♋"},
        "leo": {"element": "Fire", "planet": "Sun", "dates": "Jul 23 - Aug 22", "symbol": "♌"},
        "virgo": {"element": "Earth", "planet": "Mercury", "dates": "Aug 23 - Sep 22", "symbol": "♍"},
        "libra": {"element": "Air", "planet": "Venus", "dates": "Sep 23 - Oct 22", "symbol": "♎"},
        "scorpio": {"element": "Water", "planet": "Pluto", "dates": "Oct 23 - Nov 21", "symbol": "♏"},
        "sagittarius": {"element": "Fire", "planet": "Jupiter", "dates": "Nov 22 - Dec 21", "symbol": "♐"},
        "capricorn": {"element": "Earth", "planet": "Saturn", "dates": "Dec 22 - Jan 19", "symbol": "♑"},
        "aquarius": {"element": "Air", "planet": "Uranus", "dates": "Jan 20 - Feb 18", "symbol": "♒"},
        "pisces": {"element": "Water", "planet": "Neptune", "dates": "Feb 19 - Mar 20", "symbol": "♓"}
    }
    
    info = sign_details.get(sign.lower(), {"element": "Unknown", "planet": "Unknown", "dates": "Unknown", "symbol": "✨"})
    
    profile = f"""# {info['symbol']} {sign_title} Profile

## Basic Info
| Attribute | Value |
|-----------|-------|
| 🔥 Element | {info['element']} |
| 🪐 Ruling Planet | {info['planet']} |
| 📅 Date Range | {info['dates']} |
| 📅 Today | {d.get('date', 'Today')} |

---

## Today's Horoscope Summary
{d.get('overall_summary', 'Daily horoscope available.')}

---

## Today's Ratings
| Category | Score |
|----------|-------|
| 💕 Love | {d['love']['score']}/10 |
| 💼 Career | {d['career']['score']}/10 |
| 🏥 Health | {d['health']['score']}/10 |
| 💰 Money | {d['money']['score']}/10 |
| ⭐ Overall | {d.get('day_rating', 'N/A')}/10 |

---

## 🍀 Lucky Guide
| Item | Value |
|------|-------|
| 🎨 Color | {d.get('lucky_colour', 'N/A')} |
| 🔢 Number | {d.get('lucky_number', 'N/A')} |
| 🧭 Direction | {d.get('lucky_direction', 'N/A')} |
| ⏰ Best Time | {d.get('best_time_window', 'N/A')} |
| ⚠️ Avoid | {d.get('avoid_time_window', 'N/A')} |

---

## Key Predictions
**Love:** {d['love']['prediction']}

**Career:** {d['career']['prediction']}

**Health:** {d['health']['prediction']}

**Money:** {d['money']['prediction']}

---

*Your complete {sign_title} profile for today! ✨*"""
    
    return profile
