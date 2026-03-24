import os
import json
import time # 👈 재시도 대기를 위해 추가
from google import genai

def get_gemini_scoring_analysis(client, ticker, price, rsi, volume_ratio, obv_trend, macd_hist, ema5, bb_upper, bb_lower, news, max_retries=3):
    """제미니 API를 호출하여 기술적 지표와 뉴스를 종합 분석합니다. (429 에러 시 자동 재시도)"""
    prompt = f"""
    당신은 월스트리트의 최고 주식 분석가입니다.
    다음 {ticker} 주식의 기술적 지표와 최신 뉴스를 바탕으로 투자 매력도(0~100점)와 분석 의견을 JSON 형태로 정확히 반환하세요.

    [기술적 지표]
    - 현재가: {price}
    - RSI: {rsi}
    - 거래량강도: {volume_ratio}%
    - OBV추세: {obv_trend}
    - MACD히스토그램: {macd_hist}
    - EMA5: {ema5}
    - 볼린저밴드: 상단 {bb_upper}, 하단 {bb_lower}

    [최신 뉴스]
    {news}

    [출력 형식 (오직 JSON만 출력할 것, 마크다운 코드 블록 절대 금지)]
    {{
        "score": 85,
        "newsScore": 80,
        "opinion": "AI 수요 증가와 함께 견조한 상승세 유지 중. RSI가 다소 높으나 MACD 및 OBV 추세가 긍정적임. (한국어로 작성)",
        "keywords": "AI 칩, 데이터센터, 실적 호조 (한국어로 작성)"
    }}
    """

    # max_retries(기본 3번)만큼 반복해서 시도함
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt
            )
            
            raw_text = response.text.replace("```json", "").replace("```", "").strip()
            result = json.loads(raw_text)
            return result
            
        except json.JSONDecodeError:
            print(f"❌ JSON 파싱 에러 ({ticker}): 제미니가 형식을 어겼습니다.")
            return {"score": 0, "newsScore": 0, "opinion": "AI 분석 형식 오류", "keywords": "-"}
            
        except Exception as e:
            # 에러 메시지에 '429'가 포함되어 있고, 아직 재시도 기회가 남아있다면
            if "429" in str(e) and attempt < max_retries - 1:
                wait_time = 10 * (attempt + 1) # 처음엔 10초, 두 번째엔 20초 대기
                print(f"⚠️ 429 에러 발생 ({ticker}) - {wait_time}초 후 재시도 (현재 {attempt+1}/{max_retries}회)")
                time.sleep(wait_time)
                continue # 다시 for문 처음으로 돌아가서 재시도
            else:
                # 429 에러가 아니거나, 3번 다 실패했을 경우
                print(f"❌ API 호출 에러 ({ticker}): {e}")
                return {"score": 0, "newsScore": 0, "opinion": "AI 연동 실패", "keywords": "-"}

# 👇 1. 함수 괄호 맨 끝에 us_date_str 추가!
def generate_reports(news_text, sheet_data_text, yield_text, fng_text, indices_text, us_date_str):
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    prompt = f"""
    당신은 월스트리트의 최고 주식 분석가입니다. 
    아래 [데이터 1, 2, 3]을 종합하여, 반드시 [버전 1: 깃허브용 상세 리포트]와 [버전 2: 모바일 요약본] 두 가지를 모두 작성해야 해. 
    🚨 [경고] "알겠습니다" 같은 인사말은 절대 금지! 곧바로 아래 [출력 양식]부터 시작해.

    [데이터 1: 오늘 수집된 주요 뉴스]
    {news_text}

    [데이터 2: 개별 종목 AI 분석 (이미 파이썬이 점수 높은 순으로 정렬해 둠)]
    {sheet_data_text}

    [데이터 3: 오늘의 거시 경제 지표]
    {indices_text}
    {yield_text}
    {fng_text} 

    [핵심 작성 조건]
    1. 주요 시장 지수의 변화와 VIX, 공포탐욕 지수, 특히 10년물/30년물 국채 금리 변동을 종합하여 현재 시장 상황을 분석해.
    2. 개별 종목은 AI 점수 75점 이상만 선별해서 표로 만들 것. (데이터 2가 이미 1등부터 정렬되어 있으니 그 순서대로 출력할 것)
    3. 표(Table)를 만들 때 반드시 '종목명(Company Name)'과 '티커(Ticker)' 열(Column)을 분리해.
    4. 뉴스를 활용해 반도체, 빅테크, 거시경제, 암호화폐, 지정학적 리스크 등 주요 이슈를 심층 분석
    5. 팩트 기반 (수치 지어내기 절대 금지)

    =========================================
    [출력 양식] - 아래 구조를 복사해서 각 항목의 내용을 아주 풍부하게 채워 넣어!

    # 👇 2. 제목 옆에 날짜 변수 추가!
    # 📈 오늘의 미국 증시 상세 분석 리포트 ({us_date_str})
    
    ## 1. 시장 지수 및 거시 경제 분석
    (이곳에 3대 지수, VIX, 공포탐욕 지수, 국채 금리 데이터를 하나의 깔끔한 표(Table)로 정리해)
    
    **💡 거시 경제 & 시장 심리 분석:**
    (표 바로 아래에 줄글로 3대 지수 흐름, 공포탐욕 지수 상태, 그리고 장단기 국채 금리 변동이 증시에 미치는 영향과 의미를 반드시 상세하게 설명해 줘!)

    ## 2. 주요 종목 하이라이트 (AI 점수 75점 이상)
    (이곳에 점수가 높은 순서대로 표를 작성해 줘. 표의 열은 반드시 [종목명 | 티커 | AI 점수 | 뉴스 점수 | 추세 상태 | 핵심 요약] 으로 명확히 6칸으로 분리해서 그려줘.)

    ## 3. 핵심 테마 및 뉴스 분석
    (이곳에 데이터 1의 뉴스들을 활용해서 반도체, 빅테크, 암호화폐, 지정학적 리스크 등 주요 테마를 마크다운 리스트 형태로 깊이 있게 분석해)

    ---TELEGRAM_START---

    📊 **증시 및 거시 지표 요약**
    - (3대 지수 마감 요약, VIX, 국채 금리 등 핵심 수치 및 한 줄 평. 🚨표 사용 금지)

    🚀 **오늘의 강세 종목 (75점 이상)**
    - (여기도 AI 점수 높은 순으로 정렬. 종목명(티커) / 점수 / 추세 상태 요약. 🚨표 사용 금지)

    🌍 **핵심 거시 & 테마 요약**
    - (반도체, 빅테크, 암호화폐, 지정학 리스크 중 가장 중요한 이슈 2~3가지만 아주 간결하게. 🚨표 사용 금지)
    """

    print("AI가 맞춤형 리포트를 2가지 버전으로 작성 중이야...")
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt
    ))

    full_text = response.text.strip()

    if "---TELEGRAM_START---" in full_text:
        parts = full_text.split("---TELEGRAM_START---")
        md_report = parts[0].strip() 
        telegram_msg = parts[1].strip() 
    else:
        md_report = full_text
        telegram_msg = "🔔 모바일 요약본 분리 실패 (아래 원본을 확인하세요)\n\n" + full_text[:3800]

    return md_report, telegram_msg
