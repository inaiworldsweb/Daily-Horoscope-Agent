from fastapi import APIRouter
from pydantic import BaseModel
from tools.live_api import (
    get_full_horoscope,
    get_life_area_predictions,
    get_push_notification_summary,
    get_yesterday_vs_today,
    get_lucky_items,
    get_calendar_tag,
    birth_date_to_sign
)

router = APIRouter()

class HoroscopeRequest(BaseModel):
    sign:       str | None = None
    birth_date: str | None = None

# USE CASE 1 — love/career/health/money
@router.post("/horoscope/predictions")
async def predictions(req: HoroscopeRequest):
    sign = req.sign or birth_date_to_sign(req.birth_date or "")
    return await get_life_area_predictions(sign)

# USE CASE 2 — push notification
@router.get("/horoscope/push/{sign}")
async def push_notification(sign: str):
    return await get_push_notification_summary(sign)

# USE CASE 3 — yesterday vs today
@router.get("/horoscope/compare/{sign}")
async def compare(sign: str):
    return await get_yesterday_vs_today(sign)

# USE CASE 4 — lucky items
@router.get("/horoscope/lucky/{sign}")
async def lucky(sign: str):
    return await get_lucky_items(sign)

# USE CASE 5 — calendar tag
@router.get("/horoscope/calendar/{sign}")
async def calendar(sign: str):
    return await get_calendar_tag(sign)

# ALL IN ONE — single endpoint, all 5 use cases
@router.post("/horoscope/full")
async def full_horoscope(req: HoroscopeRequest):
    return await get_full_horoscope(
        sign=req.sign,
        birth_date=req.birth_date
    )
