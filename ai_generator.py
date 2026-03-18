import os
from google import genai

def generate_reports(news_text, sheet_data_text, yield_text, fng_text):
    """수집된 데이터들을 조합해 Gemini AI에게 던지고 두 가지 버전의 리포트를 생성하는 함수"""
    # GitHub Secrets에서 Gemini API 키 가져와서 클라이언트 설정
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    # AI에게 지시할 프롬프트(명령어) 작성
    prompt = f"""
너는 미국 주식 전문 애널리스트야. 
아래 [데이터 1, 2, 3]을 종합하여, 반드시 [버전 1: 깃허브용 상세 리포트]와 [버전 2: 모바일 요약본] 두 가지를 모두 작성해야 해. 
🚨 [경고] "알겠습니다" 같은 인사말은 절대 금지! 곧바로 아래 [출력 양식]부터 시작해.

[데이터 1: 오늘 수집된 주요 뉴스]
{news_text}

[데이터 2: 나스닥 15개 종목 AI 분석 (구글 시트)]
{sheet_data_text}

[데이터 3: 오늘의 거시 경제 지표 (국채 금리 및 공포탐욕 지수)]
{yield_text}
{fng_text} 

[핵심 작성 조건]
1. 시장 심리(공포탐욕 지수)와 장단기 국채 금리 변동 코멘트
2. AI 점수 75점 이상 종목만 선별해 추세 및 요점 분석 (75점 미만 철저히 제외)
3. 뉴스를 활용해 반도체, 빅테크, 매크로 이슈 심층 분석
4. 팩트 기반 (수치 지어내기 절대 금지)

=========================================
[출력 양식] - 아래 구조를 복사해서 각 항목의 내용을 아주 풍부하게 채워 넣어!

# 📈 오늘의 미국 증시 상세 분석 리포트
## 1. 시장 심리 및 거시 지표
(이곳에 공포탐욕 지수와 금리 데이터를 표(Table)와 상세한 설명으로 깊이 있게 분석해)

## 2. 주요 종목 하이라이트 (AI 점수 75점 이상)
(이곳에 75점 이상 종목들의 점수와 추세 상태를 보기 좋은 표(Table)로 정리하고, 각 종목의 요점을 상세히 적어)

## 3. 핵심 테마 및 뉴스 분석
(이곳에 데이터 1의 뉴스들을 활용해서 빅테크, 매크로 등 주요 테마를 마크다운 리스트 형태로 깊이 있게 분석해)

---TELEGRAM_START---

📊 **시장 심리 & 국채 금리**
- (공포탐욕 지수와 금리 핵심 수치 및 한 줄 평. 🚨표 사용 금지)

🚀 **오늘의 강세 종목 (75점 이상)**
- (종목명 / 점수 / 추세 상태 요약. 🚨표 사용 금지)

🌍 **핵심 거시 & 테마 요약**
- (가장 중요한 시장 이슈 2~3가지만 아주 간결하게. 🚨표 사용 금지)
"""

    print("AI가 맞춤형 리포트를 2가지 버전으로 작성 중이야...")
    # Gemini 2.0 Flash 모델을 호출해서 프롬프트 전송
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt
    )

    # 응답 결과의 앞뒤 공백 및 줄바꿈 정리
    full_text = response.text.strip()

    # 우리가 프롬프트에 심어둔 '---TELEGRAM_START---' 구분자를 기준으로 텍스트를 반으로 쪼갬
    if "---TELEGRAM_START---" in full_text:
        parts = full_text.split("---TELEGRAM_START---")
        md_report = parts[0].strip()     # 쪼갠 결과물의 앞부분: 깃허브용 웹 상세 리포트
        telegram_msg = parts[1].strip()  # 쪼갠 결과물의 뒷부분: 텔레그램 모바일 요약본
    else:
        # AI가 지시를 어기고 구분자를 안 썼을 때 파일이 날아가는 걸 막기 위한 안전망
        md_report = full_text
        telegram_msg = "🔔 모바일 요약본 분리 실패 (아래 원본을 확인하세요)\n\n" + full_text[:3800]

    return md_report, telegram_msg
