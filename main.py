import sys
import os
import requests
import time # 👈 API 호출 제한 방어를 위한 sleep
import pandas_market_calendars as mcal
from datetime import datetime, timedelta
from google import genai # 👈 client 객체 생성을 위해 추가

# 모듈 불러오기 (함수 이름 바뀐 것들 적용)
from macro_data import get_news, get_treasury_yields, get_fear_and_greed, get_market_indices, get_stock_news
from sheet_data import get_google_sheet_records
from ai_generator import generate_reports, get_gemini_scoring_analysis
from file_manager import save_and_update_index
from telegram_sender import send_alert

def check_holiday(us_date_check, us_date_str):
    nyse = mcal.get_calendar('NYSE')
    valid_days = nyse.valid_days(start_date=us_date_check, end_date=us_date_check)
    if len(valid_days) == 0:
        print(f"🛑 {us_date_check}은(는) 미국 증시 휴장일입니다.")
        sys.exit()

if __name__ == "__main__":
    # 날짜 설정
    us_date_obj = datetime.now() - timedelta(hours=14)
    us_date_str = us_date_obj.strftime("%Y년 %m월 %d일")
    us_date_check = us_date_obj.strftime("%Y-%m-%d")

    print(f"--- [DEBUG] 현재 설정된 us_date_str: {us_date_str} ---")
    
    # 휴장일 체크
    check_holiday(us_date_check, us_date_str)
    print("✅ 개장일 확인 완료! 리포트 생성을 시작합니다.")

    # 1. 글로벌 거시경제 데이터 수집 (💡 제안 1 반영: 뉴스 80개 -> 20개로 대폭 축소)
    news_text = get_news(limit=20)
    yield_text = get_treasury_yields()
    fng_text = get_fear_and_greed()
    indices_text = get_market_indices()

    # 2. 구글 시트 데이터 가져오기
    records = get_google_sheet_records()
    
    # 3. 개별 종목 뉴스 수집 및 AI 채점 진행
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    sheet_data_text = "관심 종목 AI 개별 분석 데이터 (이미 점수 높은 순으로 정렬됨):\n"
    
    if records:
        print(f"🔍 개별 종목 뉴스 수집 및 AI 분석 시작 (총 {len(records)}개 종목)...")
        
        # 결과를 임시로 담아둘 리스트 생성
        analyzed_results = []
        
        for row in records:
            ticker = str(row.get("티커", row.get("Ticker", row.get("종목명", "")))).strip()
            if not ticker: continue
            
            price = row.get("현재가", "N/A")
            rsi = row.get("RSI", "N/A")
            volume_ratio = row.get("거래량강도", "N/A")
            obv_trend = row.get("OBV추세", "N/A")
            macd_hist = row.get("MACD히스토그램", "N/A")
            ema5 = row.get("EMA5", "N/A")
            bb_upper = row.get("볼린저상단", "N/A")
            bb_lower = row.get("볼린저하단", "N/A")

            # 💡 [제안 4 반영: 비용 절감형 RSI 필터링 로직]
            # RSI가 45 이상 55 이하인 중립 구간이면 변동성이 낮다고 판단하여 AI API 호출을 생략함
            try:
                rsi_val = float(str(rsi).replace(",", "").strip())
                if 45 <= rsi_val <= 55:
                    print(f"⏩ [{ticker}] 변동성 낮음 (RSI: {rsi_val}) -> 토큰 절감을 위해 AI 정밀 분석 패스")
                    analyzed_results.append({
                        "ticker": ticker,
                        "price": price,
                        "rsi": rsi,
                        "macd_hist": macd_hist,
                        "score": 50,  # 중립 점수 부여
                        "newsScore": 50,
                        "keywords": "중립 구간 (RSI 필터링)",
                        "opinion": "RSI 지표가 완연한 중립 구간(45~55)에 머물러 있어 단기 추세 변동성이 낮으므로, API 토큰 절감을 위해 AI 호출을 생략합니다."
                    })
                    continue  # 아래 AI 호출 코드를 실행하지 않고 즉시 다음 종목 반복문으로 넘어감
            except (ValueError, TypeError):
                # 만약 RSI 값이 숫자가 아니거나 누락된 상태라면 안전하게 AI 분석을 받도록 예외 처리함
                pass

            print(f"[{ticker}] 뉴스 수집 및 AI 분석 중...")
            
            news = get_stock_news(ticker, limit=3)
            analysis = get_gemini_scoring_analysis(
                client, ticker, price, rsi, volume_ratio, obv_trend, macd_hist, ema5, bb_upper, bb_lower, news
            )
            
            # 에러 방지를 위해 점수를 확실한 숫자로 변환
            try:
                ai_score = int(analysis.get('score', 0))
                news_score = int(analysis.get('newsScore', 0))
            except:
                ai_score = 0
                news_score = 0
                
            # 분석 결과를 딕셔너리 형태로 리스트에 저장
            analyzed_results.append({
                "ticker": ticker,
                "price": price,
                "rsi": rsi,
                "macd_hist": macd_hist,
                "score": ai_score,
                "newsScore": news_score,
                "keywords": analysis.get('keywords', '-'),
                "opinion": analysis.get('opinion', '-')
            })
            
            # API 호출 제한(Rate Limit) 방지를 위한 짧은 대기 시간
            time.sleep(6)
            
        # 파이썬에서 AI 점수(score)를 기준으로 강력하게 내림차순 정렬!
        analyzed_results.sort(key=lambda x: x["score"], reverse=True)
        
        # 정렬된 순서대로 텍스트를 조립해서 AI에게 넘겨줌
        for res in analyzed_results:
            sheet_data_text += f"\n[종목: {res['ticker']}]\n"
            sheet_data_text += f"- 기술지표: 현재가 {res['price']} / RSI {res['rsi']} / MACD {res['macd_hist']}\n"
            sheet_data_text += f"- AI 점수: {res['score']}점 (뉴스 점수: {res['newsScore']}점)\n"
            sheet_data_text += f"- 핵심 키워드: {res['keywords']}\n"
            sheet_data_text += f"- AI 의견: {res['opinion']}\n"
            
    else:
        sheet_data_text += "시트에 데이터가 없습니다."
        
    # 4. 종합 AI 리포트 생성 (us_date_str 확실하게 전달!)
    md_report, telegram_msg = generate_reports(
        news_text, 
        sheet_data_text, 
        yield_text, 
        fng_text, 
        indices_text, 
        us_date_str
    )

    # 5. 파일 저장 및 전송
    save_and_update_index(us_date_check, us_date_str, md_report)
    send_alert(us_date_str, us_date_check, telegram_msg)
    
    print("🎉 모든 작업이 성공적으로 완료되었습니다!")
