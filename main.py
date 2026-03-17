import feedparser
import os
from datetime import datetime, timedelta
from google import genai

# 1. 미국 증시 뉴스 RSS 크롤링
rss_url = "https://finance.yahoo.com/news/rssindex"
feed = feedparser.parse(rss_url)

news_text = "오늘의 주요 뉴스:\n"
for entry in feed.entries[:7]:
    summary = entry.get('summary', entry.get('description', '요약 없음'))
    news_text += f"- {entry.title}\n  {summary}\n\n"

# 2. Gemini API 적용
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# 한국 시간 기준으로 돌릴 때 미국 날짜에 맞추기 위해 시간 차이(약 14시간)를 빼줌
us_date_obj = datetime.now() - timedelta(hours=14)
us_date_str = us_date_obj.strftime("%Y년 %m월 %d일")

# 프롬프트에 '마감 리뷰'임을 명시하고, 없는 데이터(지수)를 지어내지 못하게 통제
prompt = f"""
너는 미국 주식 전문 애널리스트야. 
다음 뉴스 헤드라인과 요약을 분석해서 '{us_date_str} 미국 증시 마감 리뷰 리포트'를 마크다운(.md) 포맷으로 작성해.

[주의사항]
1. 개장 전 예상이 아니라, 마감된 시장의 '결과'와 '이슈'를 요약할 것.
2. 제공된 뉴스 텍스트에 주요 지수(다우, 나스닥 등)의 정확한 수치가 없다면, 절대 임의로 지수 예상치나 결과를 지어내지 말 것. 
3. 철저히 뉴스에 언급된 팩트(종목, 경제 지표 등)에만 기반해서 작성할 것.
4. 결론 부분에는 개인 투자자를 위한 객관적인 코멘트를 추가할 것.

{news_text}
"""

print("AI가 리포트를 작성 중이야...")
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents=prompt
)

# 3. 마크다운 파일로 저장하기
os.makedirs("reports", exist_ok=True)
# 파일명도 미국 날짜 기준으로 생성
file_date_str = us_date_obj.strftime("%Y-%m-%d")
file_path = f"reports/{file_date_str}-report.md"

with open(file_path, "w", encoding="utf-8") as f:
    f.write(response.text)

print(f"완료! {file_path} 파일이 만들어졌어.")
