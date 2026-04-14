import os
import json
import time 
from google import genai

def get_gemini_scoring_analysis(client, ticker, price, rsi, volume_ratio, obv_trend, macd_hist, ema5, bb_upper, bb_lower, news, max_retries=3):
    """제미니 API를 호출하여 개별 종목 분석 (기존과 동일)"""
    prompt = f"""
    당신은 월스트리트의 최고 주식 분석가입니다.
    다음 {ticker} 주식의 기술적 지표와 최신 뉴스를 바탕으로 투자 매력도(0~100점)와 분석 의견을 JSON 형태로 정확히 반환하세요.
    (출력 형식은 반드시 JSON이어야 하며, 한국어로 작성하세요.)

    [기술적 지표]
    - 현재가: {price}, RSI: {rsi}, 거래량강도: {volume_ratio}%, OBV: {obv_trend}, MACD: {macd_hist}, EMA5: {ema5}, BB: {bb_upper}/{bb_lower}
    
    [최신 뉴스]
    {news}

    [출력 형식]
    {{ "score": 85, "newsScore": 80, "opinion": "...", "keywords": "..." }}
    """
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
            raw_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(raw_text)
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                time.sleep(10 * (attempt + 1))
                continue
            return {"score": 0, "newsScore": 0, "opinion": "분석 실패", "keywords": "-"}

def generate_reports(news_text, sheet_data_text, yield_text, fng_text, indices_text, us_date_str):
    """종합 리포트 생성 - us_date_str를 사용하여 날짜를 강제함"""
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    # 🚨 AI에게 날짜를 절대적으로 지키라고 명시함
    prompt = f"""
    당신은 미국 주식 전문 애널리스트입니다. 
    오늘의 리포트 기준 날짜는 반드시 **{us_date_str}** 입니다. 데이터에 포함된 다른 날짜에 상관없이 리포트 제목과 본문에는 이 날짜를 사용하세요.

    [데이터 1: 주요 뉴스]
    {news_text}
    [데이터 2: 종목 분석]
    {sheet_data_text}
    [데이터 3: 거시 지표]
    {indices_text} {yield_text} {fng_text}

    =========================================
    [출력 양식] - 아래 구조를 유지하며 내용을 채우세요.

    # 📈 오늘의 미국 증시 상세 분석 리포트 ({us_date_str})
    
    ## 1. 시장 지수 및 거시 경제 분석
    (지수, VIX, 공포탐욕, 금리 표 작성)
    **💡 거시 경제 & 시장 심리 분석:**
    ({us_date_str} 기준의 시장 상황을 상세히 설명)

    ## 2. 주요 종목 하이라이트 (AI 점수 75점 이상)
    (종목명 | 티커 | AI 점수 | 뉴스 점수 | 추세 상태 | 핵심 요약 표 작성)

    ## 3. 핵심 테마 및 뉴스 분석
    (반도체, 빅테크, 암호화폐, 지정학 리스크 등 분석)

    ---TELEGRAM_START---
    📊 **증시 및 거시 지표 요약 ({us_date_str})**
    - (핵심 요약)
    🚀 **오늘의 강세 종목 (75점 이상)**
    - (종목 요약)
    🌍 **핵심 거시 & 테마 요약**
    - (테마 요약)
    """

    response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
    full_text = response.text.strip()

    if "---TELEGRAM_START---" in full_text:
        parts = full_text.split("---TELEGRAM_START---")
        return parts[0].strip(), parts[1].strip()
    return full_text, "요약본 생성 실패"
