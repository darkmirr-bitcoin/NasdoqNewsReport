import feedparser
import os
import requests
import gspread # 👈 새로 추가
import json # 👈 새로 추가
from datetime import datetime, timedelta
from google import genai

# 1. 미국 증시 뉴스 RSS 크롤링 (야후 파이낸스)
rss_url = "https://finance.yahoo.com/news/rssindex"
feed = feedparser.parse(rss_url)

news_text = "오늘의 주요 뉴스:\n"
# 최신 뉴스를 최대 100개까지 넉넉하게 긁어오기
for entry in feed.entries[:100]:
    summary = entry.get('summary', entry.get('description', '요약 없음'))
    news_text += f"- {entry.title}\n  {summary}\n\n"


# 2. 구글 시트 데이터 읽어오기 📊 (👈 새로 추가된 부분)
google_sheets_creds_json = os.environ.get("GOOGLE_SHEETS_CREDS")
sheet_data_text = "구글 시트에 기록된 투자자 포트폴리오/관심 종목 데이터:\n"

if google_sheets_creds_json:
    try:
        print("구글 시트 데이터 읽는 중...")
        # 깃허브 Secrets에 저장된 JSON 키 내용으로 인증
        creds = json.loads(google_sheets_creds_json)
        gc = gspread.service_account_from_dict(creds)
        
        # 네가 알려준 구글 시트 URL에서 Spreadsheet ID 추출
        spreadsheet_id = "1_TEiYUhm8ajuw_zOf8Tzjt3eMUjlPG6a4q4ynx6fUEU"
        # URL의 #gid=59608910 에서 추출한 Worksheet GID
        worksheet_gid = 59608910
        
        # 스프레드시트 열기
        sh = gc.open_by_key(spreadsheet_id)
        # GID로 특정 워크시트(탭) 열기
        worksheet = sh.get_worksheet_by_id(worksheet_gid)
        
        # 워크시트의 모든 데이터를 텍스트 형태로 한꺼번에 가져오기 (가장 간단한 방법)
        all_values = worksheet.get_all_values()
        
        # 가져온 2차원 리스트 데이터를 AI가 읽기 좋은 텍스트 형식으로 변환 (CSV 느낌)
        if all_values:
            sheet_data_text += "\n".join([",".join(row) for row in all_values])
            print("✅ 구글 시트 데이터 읽기 성공!")
        else:
            sheet_data_text += "시트에 데이터가 없습니다."
            
    except Exception as e:
        print(f"❌ 구글 시트 데이터 읽기 실패: {e}")
        sheet_data_text += f"(데이터 읽기 실패: {e})"
else:
    print("구글 시트 크레덴셜이 설정되지 않아 데이터를 읽을 수 없습니다.")
    sheet_data_text += "(크레덴셜 미설정으로 데이터 없음)"


# 3. Gemini API 적용
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# 미국 날짜 기준 세팅
us_date_obj = datetime.now() - timedelta(hours=14)
us_date_str = us_date_obj.strftime("%Y년 %m월 %d일")

# 프롬프트 업데이트: 관심 섹터 최우선 분석 지시 + 구글 시트 데이터 분석 요청
prompt = f"""
너는 미국 주식 전문 애널리스트야. 
다음 두 가지 정보를 종합적으로 분석해서 '{us_date_str} 미국 증시 맞춤형 마감 리뷰 리포트'를 마크다운(.md) 포맷으로 작성해.

[정보 1: 오늘의 주요 뉴스]
{news_text}

[정보 2: 투자자 구글 시트 데이터 (포트폴리오/관심 종목 등)]
{sheet_data_text}

[핵심 분석 및 작성 조건]
1. [정보 2]의 구글 시트 데이터를 최우선으로 참고해서, 투자자가 가진 포트폴리오나 관심 종목에 직접적인 영향을 줄 수 있는 뉴스를 가장 먼저, 비중 있게 분석하고 요약해 줘.
2. 다음 테마의 뉴스를 그 다음으로 비중 있게 분석해 줘:
   - 반도체 및 빅테크 (엔비디아 등 주요 기업 동향)
   - 암호화폐 규제 (미국 내 관련 법안 흐름 등)
   - 거시경제 (중동 지정학적 리스크, 호르무즈 해협 상황, 전쟁, 금리 등)
3. 개장 전 예상이 아니라, 마감된 시장의 '결과'와 '이슈'를 요약할 것. 지수 수치가 뉴스에 없다면 절대 임의로 지어내지 말 것. 
4. 철저히 뉴스에 언급된 팩트와 시트 데이터에만 기반해서 작성할 것.
5. 결론 부분에는 투자자를 위한 객관적인 포트폴리오 대응 인사이트와 코멘트를 추가할 것.

"""

print("AI가 맞춤형 리포트를 작성 중이야...")
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents=prompt
)

# 4. 마크다운 파일로 깃허브에 저장하기
os.makedirs("reports", exist_ok=True)
file_date_str = us_date_obj.strftime("%Y-%m-%d")
file_path = f"reports/{file_date_str}-report.md"

with open(file_path, "w", encoding="utf-8") as f:
    f.write(response.text)

print(f"완료! {file_path} 파일이 만들어졌어.")


# 5. 텔레그램으로 리포트 전송하기 🚀 (안전한 무조건 발송 모드)
bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat_id = os.environ.get("TELEGRAM_CHAT_ID")

if bot_token and chat_id:
    print("텔레그램으로 메시지 전송 시작...")
    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # 텔레그램 글자 수 제한 안전하게 자르기
    text_to_send = f"🔔 {us_date_str} 맞춤형 리포트 도착!\n\n{response.text[:3800]}..." 
    
    payload = {
        "chat_id": chat_id,
        "text": text_to_send
        # parse_mode: Markdown 은 에러 방지를 위해 지워둠
    }
    
    res = requests.post(send_url, json=payload)
    if res.status_code == 200:
        print("✅ 텔레그램 발송 성공!")
    else:
        print(f"❌ 텔레그램 발송 실패: {res.text}")
else:
    print("텔레그램 토큰이나 챗ID가 설정되지 않았어.")
