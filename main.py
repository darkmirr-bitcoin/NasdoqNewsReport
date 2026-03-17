import feedparser
import os
import requests
import gspread
import json
from datetime import datetime, timedelta
from google import genai

# 1. 미국 증시 뉴스 RSS 크롤링 (야후 파이낸스)
rss_url = "https://finance.yahoo.com/news/rssindex"
feed = feedparser.parse(rss_url)

news_text = "오늘의 주요 뉴스:\n"
for entry in feed.entries[:100]:
    summary = entry.get('summary', entry.get('description', '요약 없음'))
    news_text += f"- {entry.title}\n  {summary}\n\n"

# 1.5. 미국 10년물 국채 금리 데이터 가져오기 (새로 추가 🚀)
print("국채 금리 데이터 가져오는 중...")
try:
    # ^TNX 는 미국 10년물 국채 금리의 티커야
    tnx = yf.Ticker("^TNX")
    # 최근 2일치 데이터를 가져와서 어제와 오늘 비교
    hist = tnx.history(period="2d")
    
    if len(hist) >= 2:
        prev_close = hist['Close'].iloc[0] # 어제 종가
        current_yield = hist['Close'].iloc[1] # 오늘(현재) 금리
        change = current_yield - prev_close
        
        # 변동 폭에 따라 +, - 기호 붙이기
        sign = "+" if change > 0 else ""
        yield_text = f"미국 10년물 국채 금리: {current_yield:.3f}% (전일 대비 {sign}{change:.3f}%p)"
    else:
        # 주말이나 휴장일이라 데이터가 1개만 나올 경우
        current_yield = hist['Close'].iloc[0]
        yield_text = f"미국 10년물 국채 금리: {current_yield:.3f}% (전일 대비 변동폭 계산 불가 - 휴장 등)"
        
    print(f"✅ 금리 확인: {yield_text}")
except Exception as e:
    print(f"❌ 금리 데이터 가져오기 실패: {e}")
    yield_text = "국채 금리 데이터를 불러오지 못했습니다."

# 2. 구글 시트 'Today' 탭 데이터 읽어오기
google_sheets_creds_json = os.environ.get("GOOGLE_SHEETS_CREDS")
sheet_data_text = "구글 시트 'Today' 탭의 나스닥 15개 종목 AI 분석 및 시장 지표 데이터:\n"

if google_sheets_creds_json:
    try:
        print("구글 시트 데이터 읽는 중...")
        creds = json.loads(google_sheets_creds_json)
        gc = gspread.service_account_from_dict(creds)
        
        spreadsheet_id = "1_TEiYUhm8ajuw_zOf8Tzjt3eMUjlPG6a4q4ynx6fUEU"
        sh = gc.open_by_key(spreadsheet_id)
        
        # 'Today' 탭을 이름으로 직접 찾아서 열기
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

# 3. Gemini API 적용 및 맞춤형 프롬프트
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
us_date_obj = datetime.now() - timedelta(hours=14)
us_date_str = us_date_obj.strftime("%Y년 %m월 %d일")

# 프롬프트 업데이트: 75점 이상 종목, 추세 상태, 공포탐욕 지수, 거시경제 집중 분석
prompt = f"""
너는 미국 주식 전문 애널리스트야. 
다음 두 가지 데이터를 종합해서 '{us_date_str} 미국 증시 마감 리뷰 및 종목 분석 리포트'를 마크다운(.md) 포맷으로 작성해.

[데이터 1: 오늘 수집된 주요 뉴스]
{news_text}

[데이터 2: 나스닥 15개 종목 AI 분석 및 시장 지표 (구글 시트 데이터)]
{sheet_data_text}

[데이터 3: 오늘의 거시 경제 지표 (팩트 데이터)]
{yield_text}  # 👈 여기에 아까 가져온 금리 텍스트를 넣어줌!

[핵심 작성 조건 - 이 순서와 비중을 반드시 지킬 것]
1. 시장 심리 및 거시 지표: [데이터 2]의 '공포탐욕 지수'와 [데이터 3]의 '국채 금리 변동'을 리포트 최상단에 배치해. 현재 시장의 심리 상태와 금리 변동이 증시에 미치는 영향을 짧게 코멘트해 줘.
2. 주요 종목 하이라이트 (AI 점수 75점 이상): [데이터 2]를 분석해서 'AI 점수가 75점 이상'인 종목들만 선별해. 그리고 해당 종목들의 '추세 상태'와 요점을 중심으로 분석 내용을 적어 줘. (75점 미만은 철저히 생략)
3. 테마 및 주요 뉴스 분석: [데이터 1]의 뉴스를 활용해서 반도체, 빅테크 등 섹터 흐름과 지정학적 리스크 등 주요 이슈를 심도 있게 분석해 줘. 
4. 금지 사항: 뉴스나 시트 데이터, 제공된 금리 데이터 외에 임의로 수치를 지어내지 마. 철저히 제공된 팩트 기반으로만 작성해.
"""

print("AI가 맞춤형 리포트를 작성 중이야...")
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents=prompt
)

# 4. 마크다운 파일 저장
os.makedirs("reports", exist_ok=True)
file_date_str = us_date_obj.strftime("%Y-%m-%d")
file_path = f"reports/{file_date_str}-report.md"

with open(file_path, "w", encoding="utf-8") as f:
    f.write(response.text)
print(f"완료! {file_path} 파일 생성됨.")

# 5. 텔레그램 전송
bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat_id = os.environ.get("TELEGRAM_CHAT_ID")

if bot_token and chat_id:
    print("텔레그램으로 메시지 전송 시작...")
    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    text_to_send = f"🔔 {us_date_str} 분석 리포트 도착!\n\n{response.text[:3800]}..." 
    
    payload = {
        "chat_id": chat_id,
        "text": text_to_send
    }
    
    res = requests.post(send_url, json=payload)
    if res.status_code == 200:
        print("✅ 텔레그램 발송 성공!")
    else:
        print(f"❌ 텔레그램 발송 실패: {res.text}")
else:
    print("텔레그램 토큰이나 챗ID가 설정되지 않았어.")
