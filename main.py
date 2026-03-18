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
for entry in feed.entries[:100]:
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
# 4. Gemini API 적용 및 맞춤형 프롬프트 (조건 강화 + 2가지 포맷 출력)
# =====================================================================
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

prompt = f"""
너는 미국 주식 전문 애널리스트야. 
다음 세 가지 데이터를 종합해서 리포트를 작성하되, [핵심 작성 조건]을 엄격하게 지켜서 두 가지 버전으로 분리해 출력해.

[데이터 1: 오늘 수집된 주요 뉴스]
{news_text}

[데이터 2: 나스닥 15개 종목 AI 분석 및 시장 지표 (구글 시트 데이터)]
{sheet_data_text}

[데이터 3: 오늘의 거시 경제 지표 (10년물, 30년물 국채 금리)]
{yield_text}

[핵심 작성 조건 - 분석 시 무조건 지킬 것]
1. 시장 심리 및 거시 지표: '공포탐욕 지수'와 '국채 금리(10년물, 30년물) 변동'을 최상단에 배치하고, 장단기 금리 흐름이 증시 심리에 미치는 영향을 코멘트해 줘.
2. 주요 종목 하이라이트 (AI 점수 75점 이상): AI 점수가 75점 이상인 종목만 선별해서 '추세 상태(차트 정보)'와 요점을 분석해. (75점 미만 종목은 리포트에서 철저히 제외할 것)
3. 거시 경제 및 주요 테마 분석: 뉴스를 활용해 반도체, 빅테크, 암호화폐 규제, 거시경제(전쟁 등 지정학적 리스크) 이슈를 심도 있게 분석해 줘.
4. 금지 사항: 뉴스나 시트 데이터, 제공된 금리 데이터 외에 임의로 수치를 지어내지 마. 철저히 제공된 팩트 기반으로만 작성해.

=========================================
위의 4가지 조건을 완벽하게 반영하여 아래 두 가지 포맷으로 작성해.

### [버전 1: 깃허브 저장용 상세 마크다운 리포트]
(이곳에는 표(Table)와 마크다운 문법을 적극 활용하여, 전문가 수준으로 아주 상세하고 깊이 있게 분석 내용을 적어줘.)

---TELEGRAM_START---

### [버전 2: 텔레그램 모바일 요약본]
(모바일 가독성을 위해 **표(Table)는 절대 사용 금지**. 핵심 내용만 줄글과 이모지, 불릿 기호(-, •)를 사용해 깔끔하게 요약해 줘.)

📊 **시장 심리 & 국채 금리**
- (공포탐욕 지수와 금리 핵심 수치 및 한 줄 평)

🚀 **오늘의 강세 종목 (75점 이상)**
- (종목명 / 점수 / 추세 상태 위주로 표 없이 깔끔하게 나열)

🌍 **핵심 거시 & 테마 요약**
- (가장 중요한 시장 이슈 2~3가지만 아주 간결하게 요약)
"""

print("AI가 맞춤형 리포트를 2가지 버전으로 작성 중이야...")
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents=prompt
)

# =====================================================================
# 4.5. 응답 텍스트 반으로 자르기 (웹용 vs 모바일용)
# =====================================================================
full_text = response.text

# 프롬프트에서 지시한 구분자(---TELEGRAM_START---)를 기준으로 텍스트 분리
if "---TELEGRAM_START---" in full_text:
    parts = full_text.split("---TELEGRAM_START---")
    md_report = parts[0].strip() # 깃허브에 저장될 마크다운 원본
    telegram_msg = parts[1].strip() # 텔레그램으로 갈 깔끔한 요약본
else:
    # 혹시라도 AI가 구분자를 빼먹었을 경우를 대비한 안전 장치
    md_report = full_text
    telegram_msg = "🔔 모바일 요약본 분리 실패 (원본 전송)\n\n" + full_text[:3800]

# =====================================================================
# 5. 마크다운 파일 저장 및 텔레그램 전송
# =====================================================================
os.makedirs("reports", exist_ok=True)
file_path = f"reports/{us_date_check}-report.md"

# 깃허브에는 상세 버전(md_report)만 저장!
with open(file_path, "w", encoding="utf-8") as f:
    f.write(md_report)
print(f"완료! {file_path} 상세 리포트 파일 생성됨.")

bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat_id = os.environ.get("TELEGRAM_CHAT_ID")

if bot_token and chat_id:
    print("텔레그램으로 모바일 요약본 전송 시작...")
    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # 텔레그램에는 모바일 전용 요약본(telegram_msg)만 전송!
    text_to_send = f"🔔 {us_date_str} 미국 증시 요약\n\n{telegram_msg}" 
    
    payload = {
        "chat_id": chat_id,
        "text": text_to_send[:4000] # 혹시 길어질까 봐 4000자로 안전하게 자름
    }
    
    res = requests.post(send_url, json=payload)
    if res.status_code == 200:
        print("✅ 텔레그램 발송 성공!")
    else:
        print(f"❌ 텔레그램 발송 실패: {res.text}")
else:
    print("텔레그램 토큰이나 챗ID가 설정되지 않았어.")
