import sys
import os
import requests
import pandas_market_calendars as mcal
from datetime import datetime, timedelta

# 새로 추가된 get_market_indices 함수를 임포트 목록에 추가
from macro_data import get_news, get_treasury_yields, get_fear_and_greed, get_market_indices
from sheet_data import get_google_sheet_data
from ai_generator import generate_reports
from file_manager import save_and_update_index
from telegram_sender import send_alert

def check_holiday(us_date_check, us_date_str):
    nyse = mcal.get_calendar('NYSE')
    valid_days = nyse.valid_days(start_date=us_date_check, end_date=us_date_check)

    if len(valid_days) == 0:
        print(f"🛑 {us_date_check}은(는) 미국 증시 휴장일(주말 또는 공휴일)입니다.")
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        if bot_token and chat_id:
            send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            requests.post(send_url, json={
                "chat_id": chat_id,
                "text": f"😴 {us_date_str}은 미국 증시 휴장일입니다. 리포트를 생성하지 않습니다."
            })
        sys.exit()

if __name__ == "__main__":
    us_date_obj = datetime.now() - timedelta(hours=14)
    us_date_str = us_date_obj.strftime("%Y년 %m월 %d일")
    us_date_check = us_date_obj.strftime("%Y-%m-%d")
    print(f"기준 날짜(미국): {us_date_check}")
    
    check_holiday(us_date_check, us_date_str)
    print("✅ 개장일 확인 완료! 리포트 생성을 시작합니다.")

    # 1. 거시경제 및 구글 시트 데이터 수집
    news_text = get_news(limit=80)
    yield_text = get_treasury_yields()
    fng_text = get_fear_and_greed()
    indices_text = get_market_indices() # 👈 새로운 시장 지수 변수 추가
    sheet_data_text = get_google_sheet_data()

    # 2. AI 리포트 생성 (indices_text 추가로 넘김)
    md_report, telegram_msg = generate_reports(news_text, sheet_data_text, yield_text, fng_text, indices_text)

    # 3. 파일 저장 및 텔레그램 발송
    save_and_update_index(us_date_check, us_date_str, md_report)
    send_alert(us_date_str, us_date_check, telegram_msg)
    
    print("🎉 모든 작업이 성공적으로 완료되었습니다!")
