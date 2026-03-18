import sys
import os
import requests
import pandas_market_calendars as mcal
from datetime import datetime, timedelta

# 우리가 분리해 둔 각각의 부품(모듈) 파이썬 파일들에서 필요한 함수들을 가져옴
from macro_data import get_news, get_treasury_yields, get_fear_and_greed
from sheet_data import get_google_sheet_data
from ai_generator import generate_reports
from file_manager import save_and_update_index
from telegram_sender import send_alert

def check_holiday(us_date_check, us_date_str):
    """뉴욕증권거래소(NYSE) 휴장일인지 확인하고, 쉬는 날이면 스크립트를 즉시 종료하는 함수"""
    nyse = mcal.get_calendar('NYSE')
    # 기준 날짜(us_date_check)에 시장이 열렸는지 달력 데이터로 조회
    valid_days = nyse.valid_days(start_date=us_date_check, end_date=us_date_check)

    # valid_days에 데이터가 없으면(len이 0이면) 휴장일(주말/공휴일)임
    if len(valid_days) == 0:
        print(f"🛑 {us_date_check}은(는) 미국 증시 휴장일(주말 또는 공휴일)입니다.")
        
        # 휴장일 알림 텔레그램 전송 (선택사항)
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        if bot_token and chat_id:
            send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            requests.post(send_url, json={
                "chat_id": chat_id,
                "text": f"😴 {us_date_str}은 미국 증시 휴장일입니다. 리포트를 생성하지 않습니다."
            })
        
        # API 낭비를 막기 위해 여기서 파이썬 프로그램 자체를 강제 종료함
        sys.exit()

# 파이썬 스크립트가 실행될 때 가장 먼저 시작되는 핵심 블록
if __name__ == "__main__":
    # 0. 날짜 세팅
    # 한국 시간 아침에 돌리므로 시차를 고려해 14시간을 빼서 미국 현지 날짜로 맞춤
    us_date_obj = datetime.now() - timedelta(hours=14)
    us_date_str = us_date_obj.strftime("%Y년 %m월 %d일") # 텍스트용 예시: 2026년 03월 18일
    us_date_check = us_date_obj.strftime("%Y-%m-%d")    # 시스템/파일명용 예시: 2026-03-18
    print(f"기준 날짜(미국): {us_date_check}")
    
    # 0.5 휴장일 체크 (쉬는 날이면 여기서 프로그램 종료됨)
    check_holiday(us_date_check, us_date_str)
    print("✅ 개장일 확인 완료! 리포트 생성을 시작합니다.")

    # 1. 분리해 둔 모듈들을 호출해서 재료(데이터) 수집
    news_text = get_news(limit=80)             # 뉴스 기사 80개
    yield_text = get_treasury_yields()         # 국채 금리
    fng_text = get_fear_and_greed()            # 공포탐욕 지수
    sheet_data_text = get_google_sheet_data()  # 구글 시트 데이터

    # 2. 수집된 재료들을 AI 생성 모듈에 넘겨서 두 가지 버전 리포트 받아오기
    md_report, telegram_msg = generate_reports(news_text, sheet_data_text, yield_text, fng_text)

    # 3. 결과물 처리 모듈 호출 (깃허브 파일 저장 및 텔레그램 메시지 발송)
    save_and_update_index(us_date_check, us_date_str, md_report)
    send_alert(us_date_str, us_date_check, telegram_msg)
    
    print("🎉 모든 작업이 성공적으로 완료되었습니다!")
