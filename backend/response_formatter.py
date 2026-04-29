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


def format_full_details(data: dict, sign: str, api_text: str = None) -> str:
    """Format ALL horoscope details into one unified clean response"""
    date = data.get('date', 'Today')
    day_rating = data.get('day_rating', 'N/A')
    
    love = data.get('love', {})
    career = data.get('career', {})
    health = data.get('health', {})
    money = data.get('money', {})
    
    # Build the unified response
    result = f"""## 🔮 {sign.title()} Complete Horoscope - {date}

### ⭐ Overall Day Rating: {day_rating}/10

---

### 💕 Love & Relationships (Score: {love.get('score', 'N/A')}/10)
{love.get('prediction', 'N/A')}

💡 *Advice: {love.get('advice', 'N/A')}*

---

### 💼 Career & Work (Score: {career.get('score', 'N/A')}/10)
{career.get('prediction', 'N/A')}

💡 *Advice: {career.get('advice', 'N/A')}*

---

### 🏥 Health & Wellness (Score: {health.get('score', 'N/A')}/10)
{health.get('prediction', 'N/A')}

💡 *Advice: {health.get('advice', 'N/A')}*

---

### 💰 Money & Finance (Score: {money.get('score', 'N/A')}/10)
{money.get('prediction', 'N/A')}

💡 *Advice: {money.get('advice', 'N/A')}*

---

### 🍀 Lucky Guide for {sign.title()}
| Item | Value |
|------|-------|
| 🎨 **Color** | {data.get('lucky_colour', 'N/A')} |
| 🔢 **Number** | {data.get('lucky_number', 'N/A')} |
| 🧭 **Direction** | {data.get('lucky_direction', 'N/A')} |
| ⏰ **Best Time** | {data.get('best_time_window', 'N/A')} |
| ⚠️ **Avoid** | {data.get('avoid_time_window', 'N/A')} |

---

✨ *Have a wonderful day, {sign.title()}!* 🌟"""
    
    return result
