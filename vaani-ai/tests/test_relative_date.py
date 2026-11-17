"""
Tests for Relative Date & Day Parsing and Timezone Handling
Verifies:
1. 'which date is tomorrow' -> 18 November 2026 (with today = 17 November 2026 IST)
2. 'which day is tomorrow' -> Wednesday
3. 'what is today's date' -> 17 November 2026
4. 'which date is yesterday' -> 16 November 2026
5. 'कल की तारीख क्या है' -> 18 November 2026 / 18 नवंबर 2026
6. 'aaj ki tareekh kya hai' -> 17 November 2026
7. Timezone rollover: At 23:30 IST vs 00:30 IST, date rolls over in Asia/Kolkata, not UTC
8. Regression: Unrelated intents (time, joke, etc.) remain intact.
"""

from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import pytest

from nlp.chatbot import Chatbot
from nlp.pipeline import process, _now


@pytest.fixture
def bot():
    return Chatbot()


# Fixed IST reference: Tuesday, 17 November 2026, 14:30 IST
REF_NOW_IST = datetime(2026, 11, 17, 14, 30, tzinfo=ZoneInfo("Asia/Kolkata"))


def test_which_date_is_tomorrow(bot):
    res = bot.respond("which date is tomorrow", "en", "auto", now=REF_NOW_IST)
    reply = res["reply"]
    assert "18 November 2026" in reply
    assert "Wednesday" in reply


def test_which_day_is_tomorrow(bot):
    res = bot.respond("which day is tomorrow", "en", "auto", now=REF_NOW_IST)
    reply = res["reply"]
    assert "Wednesday" in reply
    assert "18" not in reply  # Weekday only query


def test_what_is_today_date(bot):
    res = bot.respond("what is today's date", "en", "auto", now=REF_NOW_IST)
    reply = res["reply"]
    assert "17 November 2026" in reply or "17-11-2026" in reply


def test_which_date_is_yesterday(bot):
    res = bot.respond("which date is yesterday", "en", "auto", now=REF_NOW_IST)
    reply = res["reply"]
    assert "16 November 2026" in reply
    assert "Monday" in reply


def test_hindi_tomorrow_date(bot):
    res = bot.respond("कल की तारीख क्या है", "hi", "auto", now=REF_NOW_IST)
    reply = res["reply"]
    # Should give tomorrow's date in Hindi: 18 नवंबर 2026
    assert "18" in reply
    assert "नवंबर" in reply or "18-11-2026" in reply
    assert "बुधवार" in reply


def test_hindi_tomorrow_weekday(bot):
    res = bot.respond("कल कौन सा दिन है", "hi", "auto", now=REF_NOW_IST)
    reply = res["reply"]
    assert "बुधवार" in reply


def test_hinglish_today_date(bot):
    res = bot.respond("aaj ki tareekh kya hai", "hinglish", "auto", now=REF_NOW_IST)
    reply = res["reply"]
    assert "17-11-2026" in reply or "17 November 2026" in reply


def test_gujarati_tomorrow_date_and_day(bot):
    # Date
    res_date = bot.respond("કાલે કઈ તારીખ છે", "gu", "auto", now=REF_NOW_IST)
    assert "18" in res_date["reply"]
    assert "નવેમ્બર" in res_date["reply"]
    assert "બુધવાર" in res_date["reply"]

    # Weekday
    res_day = bot.respond("કાલે કયો વાર છે", "gu", "auto", now=REF_NOW_IST)
    assert "બુધવાર" in res_day["reply"]


def test_timezone_rollover_asia_kolkata_vs_utc():
    """
    Test that at 00:30 IST on 18 Nov, UTC is still 19:00 on 17 Nov.
    The date must reflect 18 Nov (Asia/Kolkata), not 17 Nov (UTC).
    """
    # 23:30 IST on 17 Nov 2026 (18:00 UTC)
    t_2330_ist = datetime(2026, 11, 17, 23, 30, tzinfo=ZoneInfo("Asia/Kolkata"))
    bot = Chatbot()
    res_2330 = bot.respond("what is today's date", "en", "auto", now=t_2330_ist)
    assert "17 November 2026" in res_2330["reply"] or "17-11-2026" in res_2330["reply"]

    # 00:30 IST on 18 Nov 2026 (19:00 UTC on 17 Nov)
    t_0030_ist = datetime(2026, 11, 18, 0, 30, tzinfo=ZoneInfo("Asia/Kolkata"))
    res_0030 = bot.respond("what is today's date", "en", "auto", now=t_0030_ist)
    assert "18 November 2026" in res_0030["reply"] or "18-11-2026" in res_0030["reply"]

    # At 00:30 IST on 18 Nov, tomorrow is 19 Nov
    res_tomorrow_0030 = bot.respond("which date is tomorrow", "en", "auto", now=t_0030_ist)
    assert "19 November 2026" in res_tomorrow_0030["reply"]


def test_unrelated_queries_regression(bot):
    """Ensure 'what time is it' and 'tell me a joke' are completely unaffected."""
    time_res = bot.respond("what time is it", "en", "auto", now=REF_NOW_IST)
    assert time_res["intent"] == "ask_time"
    assert "current time is" in time_res["reply"].lower()

    joke_res = bot.respond("tell me a joke", "en", "auto", now=REF_NOW_IST)
    assert joke_res["intent"] == "joke"
    assert len(joke_res["reply"]) > 10
