import os
import json
import time 
from google import genai

# (get_gemini_scoring_analysis 함수는 이전과 동일하므로 생략)

def generate_reports(news_text, sheet_data_text, yield_text, fng_text, indices_text, us_date_str):
    """종합 리포트 생성 - AI의 날짜 오판을 방지하기 위해 강제 지침 강화"""
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    # 🚨 AI에게 날짜를 강제하는 섹션을 최상단에 배치
    prompt = f"""
    [SYSTEM CRITICAL INSTRUCTION]
    당신은 오늘이 반드시 **{us_date_str}** 임을 인지해야 합니다. 
    제공되는 뉴스나 지표 데이터의 날짜가 {us_date_str} 이전(예: 금요일 데이터)이더라도, 리포트의 제목과 모든 서술은 반드시 **{us_date_str}** 기준으로 작성하세요. 
    절대로 다른 날짜(예: 4월 11일 등)를 제목에 사용하지 마세요.

    [데이터 1: 수집 뉴스]
    {news_text}
    [데이터 2: 종목 분석]
    {sheet_data_text}
    [데이터 3: 거시 지표]
    {indices_text} {yield_text} {fng_text}

    =========================================
    [출력 양식] - 이 구조를 그대로 복사해서 내용을 채우세요.

    # 📈 오늘의 미국 증시 상세 분석 리포트 ({us_date_str})
    
    ## 1. 시장 지수 및 거시 경제 분석
    (이곳에 지표 표를 작성)
    
    **💡 거시 경제 & 시장 심리 분석 ({us_date_str} 기준):**
    (현재 시장 상황을 상세히 설명)

    ## 2. 주요 종목 하이라이트 (AI 점수 75점 이상)
    (종목명 | 티커 | AI 점수 | 뉴스 점수 | 추세 상태 | 핵심 요약 표 작성)

    ## 3. 핵심 테마 및 뉴스 분석
    (뉴스 테마 분석)

    ---TELEGRAM_START---
    📊 **증시 및 거시 지표 요약 ({us_date_str})**
    - (핵심 요약)
    
    🚀 **오늘의 강세 종목 (75점 이상)**
    - (종목 요약)
    """

    print(f"DEBUG: AI에게 전달되는 날짜 문자열 -> {us_date_str}")
    
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt
    )
    # (이하 텍스트 분리 로직 동일)
    full_text = response.text.strip()
    if "---TELEGRAM_START---" in full_text:
        parts = full_text.split("---TELEGRAM_START---")
        return parts[0].strip(), parts[1].strip()
    return full_text, "요약본 생성 실패"
