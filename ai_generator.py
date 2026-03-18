import os
from google import genai

# 파라미터에 indices_text 추가
def generate_reports(news_text, sheet_data_text, yield_text, fng_text, indices_text):
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    # 프롬프트 데이터와 출력 양식에 암호화폐, 지정학 리스크 명시
    prompt = f"""
너는 미국 주식 전문 애널리스트야. 
아래 [데이터 1, 2, 3]을 종합하여, 반드시 [버전 1: 깃허브용 상세 리포트]와 [버전 2: 모바일 요약본] 두 가지를 모두 작성해야 해. 
🚨 [경고] "알겠습니다" 같은 인사말은 절대 금지! 곧바로 아래 [출력 양식]부터 시작해.

[데이터 1: 오늘 수집된 주요 뉴스]
{news_text}

[데이터 2: 나스닥 15개 종목 AI 분석 (구글 시트)]
{sheet_data_text}

[데이터 3: 오늘의 거시 경제 지표 (주요 지수, 국채 금리 및 공포탐욕 지수)]
{indices_text}
{yield_text}
{fng_text} 

[핵심 작성 조건]
1. 주요 시장 지수(S&P 500, 나스닥, 러셀 2000)의 변화와 VIX, 공포탐욕 지수, 장단기 국채 금리 변동을 종합하여 현재 시장 상황과 투자 심리를 코멘트해 줘.
2. AI 점수 75점 이상 종목만 선별해 추세 및 요점 분석 (75점 미만 철저히 제외)
3. 뉴스를 활용해 반도체, 빅테크, 거시경제, 암호화폐, 지정학적 리스크 등 주요 이슈를 심층 분석해 줘.
4. 팩트 기반 (수치 지어내기 절대 금지)

=========================================
[출력 양식] - 아래 구조를 복사해서 각 항목의 내용을 아주 풍부하게 채워 넣어!

# 📈 오늘의 미국 증시 상세 분석 리포트
## 1. 시장 지수 및 거시 경제 분석
(이곳에 3대 지수, VIX, 공포탐욕 지수, 금리 데이터를 표(Table)로 정리하고, 이 수치들이 보여주는 현재 시장의 방향성을 깊이 있게 분석해)

## 2. 주요 종목 하이라이트 (AI 점수 75점 이상)
(이곳에 75점 이상 종목들의 점수와 추세 상태를 보기 좋은 표(Table)로 정리하고, 각 종목의 요점을 상세히 적어)

## 3. 핵심 테마 및 뉴스 분석
(이곳에 데이터 1의 뉴스들을 활용해서 반도체, 빅테크, 암호화폐, 지정학적 리스크 등 주요 테마를 마크다운 리스트 형태로 깊이 있게 분석해)

---TELEGRAM_START---

📊 **증시 및 거시 지표 요약**
- (3대 지수 상승/하락 마감 요약, VIX/금리 등 핵심 수치 및 한 줄 평. 🚨표 사용 금지)

🚀 **오늘의 강세 종목 (75점 이상)**
- (종목명 / 점수 / 추세 상태 요약. 🚨표 사용 금지)

🌍 **핵심 거시 & 테마 요약**
- (반도체, 빅테크, 암호화폐, 지정학 리스크 중 가장 중요한 이슈 2~3가지만 아주 간결하게. 🚨표 사용 금지)
"""

    print("AI가 맞춤형 리포트를 2가지 버전으로 작성 중이야...")
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt
    )

    full_text = response.text.strip()

    if "---TELEGRAM_START---" in full_text:
        parts = full_text.split("---TELEGRAM_START---")
        md_report = parts[0].strip() 
        telegram_msg = parts[1].strip() 
    else:
        md_report = full_text
        telegram_msg = "🔔 모바일 요약본 분리 실패 (아래 원본을 확인하세요)\n\n" + full_text[:3800]

    return md_report, telegram_msg
