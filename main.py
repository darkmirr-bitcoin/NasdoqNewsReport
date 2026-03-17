import feedparser
import os
import requests # 👈 새로 추가된 부분
from datetime import datetime, timedelta
from google import genai

# 1. 미국 증시 뉴스 RSS 크롤링
rss_url = "https://finance.yahoo.com/news/rssindex"
feed = feedparser.parse(rss_url)

news_text = "오늘의 주요 뉴스:\n"
for entry in feed.entries[:100]:
    summary = entry.get('summary', entry.get('description', '요약 없음'))
    news_text += f"- {entry.title}\n  {summary}\n\n"

# 2. Gemini API 적용
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
us_date_obj = datetime.now() - timedelta(hours=14)
us_date_str = us_date_obj.strftime("%Y년 %m월 %d일")

prompt = f"""
너는 미국 주식 전문 애널리스트야. 
다음 뉴스 헤드라인과 요약을 분석해서 '{us_date_str} 미국 증시 마감 리뷰 리포트'를 마크다운(.md) 포맷으로 작성해.

[핵심 분석 조건]
1. 다음 테마의 뉴스를 최우선으로 비중 있게 분석하고 요약해 줘:
   - 반도체 및 빅테크 (엔비디아 등 주요 기업 동향)
   - 암호화폐 규제 (미국 내 관련 법안 흐름 등)
   - 거시경제 (중동 지정학적 리스크, 호르무즈 해협 상황, 전쟁, 금리 등)
2. 개장 전 예상이 아니라, 마감된 시장의 '결과'와 '이슈'를 요약할 것.
3. 제공된 뉴스 텍스트에 주요 지수의 정확한 수치가 없다면 절대 임의로 지수 예상치나 결과를 지어내지 말 것. 
4. 철저히 뉴스에 언급된 팩트(종목, 경제 지표 등)에만 기반해서 작성할 것.
5. 결론 부분에는 개인 투자자를 위한 객관적인 인사이트와 코멘트를 추가할 것.

{news_text}
"""

print("AI가 리포트를 작성 중이야...")
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents=prompt
)

# 3. 마크다운 파일로 깃허브에 저장하기
os.makedirs("reports", exist_ok=True)
file_date_str = us_date_obj.strftime("%Y-%m-%d")
file_path = f"reports/{file_date_str}-report.md"

with open(file_path, "w", encoding="utf-8") as f:
    f.write(response.text)
print(f"완료! {file_path} 파일이 만들어졌어.")

# 4. 텔레그램으로 리포트 전송하기 🚀
bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat_id = os.environ.get("TELEGRAM_CHAT_ID")

if bot_token and chat_id:
    print("텔레그램으로 메시지 전송 시작...")
    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # 텔레그램은 한 번에 최대 4096자까지만 보낼 수 있어서 안전하게 잘라줌
    text_to_send = response.text[:4000] 
    
    payload = {
        "chat_id": chat_id,
        "text": text_to_send,
        "parse_mode": "Markdown" # 마크다운 서식을 적용해서 예쁘게 보여줌
    }
    
    res = requests.post(send_url, json=payload)
    if res.status_code == 200:
        print("✅ 텔레그램 발송 성공!")
    else:
        print(f"❌ 텔레그램 발송 실패: {res.text}")
else:
    print("텔레그램 토큰이나 챗ID가 설정되지 않았어.")
