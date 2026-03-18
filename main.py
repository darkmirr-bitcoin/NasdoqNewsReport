import feedparser
import os
import requests
import gspread
import json
import yfinance as yf
import pandas_market_calendars as mcal
import sys
from datetime import datetime, timedelta
from google import genai

# =====================================================================
# 0. 날짜 세팅 및 휴장일 체크 로직 🛑
# =====================================================================
us_date_obj = datetime.now() - timedelta(hours=14)
us_date_str = us_date_obj.strftime("%Y년 %m월 %d일")
us_date_check = us_date_obj.strftime("%Y-%m-%d")

print(f"기준 날짜(미국): {us_date_check}")

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

print("✅ 개장일 확인 완료! 리포트 생성을 시작합니다.")

# =====================================================================
# 1. 미국 증시 뉴스 RSS 크롤링
# =====================================================================
rss_url = "https://finance.yahoo.com/news/rssindex"
feed = feedparser.parse(rss_url)

news_text = "오늘의 주요 뉴스:\n"
for entry in feed.entries[:80]:
    summary = entry.get('summary', entry.get('description', '요약 없음'))
    news_text += f"- {entry.title}\n  {summary}\n\n"

# =====================================================================
# 2. 미국 10년물 & 30년물 국채 금리 데이터 가져오기 🚀
# =====================================================================
print("국채 금리 데이터(10년물, 30년물) 가져오는 중...")
yield_text = ""
try:
    # 10년물 (^TNX)
    tnx = yf.Ticker("^TNX")
    hist_10 = tnx.history(period="2d")
    if len(hist_10) >= 2:
        prev_10 = hist_10['Close'].iloc[0]
        curr_10 = hist_10['Close'].iloc[1]
        change_10 = curr_10 - prev_10
        sign_10 = "+" if change_10 > 0 else ""
        yield_text += f"- 미국 10년물 국채 금리: {curr_10:.3f}% (전일 대비 {sign_10}{change_10:.3f}%p)\n"
    elif len(hist_10) == 1:
        yield_text += f"- 미국 10년물 국채 금리: {hist_10['Close'].iloc[0]:.3f}% (전일 대비 변동폭 계산 불가)\n"

    # 30년물 (^TYX)
    tyx = yf.Ticker("^TYX")
    hist_30 = tyx.history(period="2d")
    if len(hist_30) >= 2:
        prev_30 = hist_30['Close'].iloc[0]
        curr_30 = hist_30['Close'].iloc[1]
        change_30 = curr_30 - prev_30
        sign_30 = "+" if change_30 > 0 else ""
        yield_text += f"- 미국 30년물 국채 금리: {curr_30:.3f}% (전일 대비 {sign_30}{change_30:.3f}%p)"
    elif len(hist_30) == 1:
        yield_text += f"- 미국 30년물 국채 금리: {hist_30['Close'].iloc[0]:.3f}% (전일 대비 변동폭 계산 불가)"

    if not yield_text:
        yield_text = "국채 금리 데이터를 불러오지 못했습니다. (데이터 없음)"
        
    print(f"✅ 금리 확인 완료:\n{yield_text}")
except Exception as e:
    print(f"❌ 금리 데이터 가져오기 실패: {e}")
    yield_text = f"국채 금리 데이터를 불러오지 못했습니다. ({e})"

# =====================================================================
# 2.5. CNN 공포탐욕 지수 가져오기 (새로 추가!) 🚀
# =====================================================================
print("공포탐욕 지수 데이터 가져오는 중...")
fng_text = ""
try:
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    # CNN 서버가 봇(코드) 접근을 막는 걸 방지하기 위해 브라우저인 척 위장
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    res = requests.get(url, headers=headers, timeout=10)
    
    if res.status_code == 200:
        data = res.json()
        score = round(data['fear_and_greed']['score']) # 오늘 점수
        rating = data['fear_and_greed']['rating'] # 상태 (greed, fear 등)
        prev_close = round(data['fear_and_greed']['previous_close']) # 어제 종가 기준 점수
        
        # 전일 대비 변화량 계산
        change = score - prev_close
        sign = "+" if change > 0 else ""
        
        # 상태값을 예쁜 한글로 변환
        rating_ko = {
            "extreme fear": "극도의 공포 😱",
            "fear": "공포 😨",
            "neutral": "중립 😐",
            "greed": "탐욕 😎",
            "extreme greed": "극도의 탐욕 🤑"
        }.get(rating.lower(), rating)
        
        fng_text = f"- CNN 공포탐욕 지수: {score}점 ({rating_ko}) / 전일 대비 {sign}{change}점"
        print(f"✅ 공포탐욕 확인 완료: {fng_text}")
    else:
        fng_text = "- 공포탐욕 지수: 데이터를 불러올 수 없습니다."
        print("❌ 공포탐욕 지수 API 응답 오류")
except Exception as e:
    print(f"❌ 공포탐욕 지수 가져오기 실패: {e}")
    fng_text = "- 공포탐욕 지수: 오류 발생"

# =====================================================================
# 3. 구글 시트 'Today' 탭 데이터 읽어오기
# =====================================================================
google_sheets_creds_json = os.environ.get("GOOGLE_SHEETS_CREDS")
sheet_data_text = "구글 시트 'Today' 탭의 나스닥 15개 종목 AI 분석 및 시장 지표 데이터:\n"

if google_sheets_creds_json:
    try:
        print("구글 시트 데이터 읽는 중...")
        creds = json.loads(google_sheets_creds_json)
        gc = gspread.service_account_from_dict(creds)
        
        spreadsheet_id = "1_TEiYUhm8ajuw_zOf8Tzjt3eMUjlPG6a4q4ynx6fUEU"
        sh = gc.open_by_key(spreadsheet_id)
        
        worksheet = sh.worksheet("Today")
        all_values = worksheet.get_all_values()
        
        if all_values:
            sheet_data_text += "\n".join([",".join(row) for row in all_values])
            print("✅ 구글 시트 'Today' 탭 데이터 읽기 성공!")
        else:
            sheet_data_text += "시트에 데이터가 없어."
            
    except Exception as e:
        print(f"❌ 구글 시트 데이터 읽기 실패: {e}")
        sheet_data_text += f"(데이터 읽기 실패: {e})"
else:
    print("구글 시트 크레덴셜이 설정되지 않았어.")
    sheet_data_text += "(크레덴셜 미설정)"

# =====================================================================
# 4. Gemini API 적용 및 맞춤형 프롬프트 (구조 완전 고정 + 인사말 금지)
# =====================================================================
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

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
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents=prompt
)

# =====================================================================
# 4.5. 응답 텍스트 반으로 자르기 (안전망 추가)
# =====================================================================
full_text = response.text

# 혹시 모를 앞부분 공백이나 AI의 쓸데없는 인사말 잘라내기
full_text = full_text.strip()

if "---TELEGRAM_START---" in full_text:
    parts = full_text.split("---TELEGRAM_START---")
    md_report = parts[0].strip() 
    telegram_msg = parts[1].strip() 
else:
    md_report = full_text
    telegram_msg = "🔔 모바일 요약본 분리 실패 (아래 원본을 확인하세요)\n\n" + full_text[:3800]

# =====================================================================
# 5. 마크다운 파일 저장 및 웹사이트 인덱스(index.md) 업데이트
# =====================================================================
os.makedirs("reports", exist_ok=True)
file_path = f"reports/{us_date_check}-report.md"

# 깃허브에는 상세 버전(md_report) 저장
with open(file_path, "w", encoding="utf-8") as f:
    f.write(md_report)
print(f"완료! {file_path} 상세 리포트 파일 생성됨.")

# 🚀 웹사이트 메인 화면(index.md)에 새 리포트 링크 자동 추가
index_path = "index.md"
# GitHub Pages에서는 .md 확장자를 빼고 경로를 적어야 페이지 이동이 깔끔해
link_text = f"- [{us_date_str} 상세 리포트 보기](reports/{us_date_check}-report)\n"

if os.path.exists(index_path):
    with open(index_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
else:
    # index.md 파일이 없으면 새로 만듦
    lines = ["# 📈 나의 미국 증시 데일리 리포트 모아보기\n\n"]

# 최신 리포트가 맨 위에 오도록 3번째 줄에 링크 삽입
if len(lines) >= 2:
    lines.insert(2, link_text)
else:
    lines.append(link_text)

with open(index_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

# =====================================================================
# 6. 텔레그램 전송 (웹사이트 직접 연결 링크 포함)
# =====================================================================
bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat_id = os.environ.get("TELEGRAM_CHAT_ID")

if bot_token and chat_id:
    print("텔레그램으로 모바일 요약본 전송 시작...")
    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # 🚨 여기에 네 깃허브 Pages 주소를 적어줘! (마지막에 슬래시(/) 없이 적기)
    # 예시: "https://myid.github.io/my-repo"
    github_pages_url = "darkmirr-bitcoin.github.io/NasdoqNewsReport"
    # 깃허브 Pages는 .md 파일을 .html로 자동 변환해서 스킨을 씌워줌!
    report_web_link = f"{github_pages_url}/reports/{us_date_check}-report.html"
    
    # 텔레그램 메시지 하단에 웹 링크 추가
    text_to_send = f"🔔 {us_date_str} 미국 증시 요약\n\n{telegram_msg}\n\n👉 [상세 리포트 웹에서 보기]\n{report_web_link}" 
    
    payload = {
        "chat_id": chat_id,
        "text": text_to_send[:4000]
    }
    
    res = requests.post(send_url, json=payload)
    if res.status_code == 200:
        print("✅ 텔레그램 발송 성공!")
    else:
        print(f"❌ 텔레그램 발송 실패: {res.text}")
else:
    print("텔레그램 토큰이나 챗ID가 설정되지 않았어.")
