import feedparser
import os
from datetime import datetime
from google import genai

# 1. 미국 증시 뉴스 RSS 크롤링 (야후 파이낸스)
rss_url = "https://finance.yahoo.com/news/rssindex"
feed = feedparser.parse(rss_url)

news_text = "오늘의 주요 뉴스:\n"
# 최신 뉴스 7개 추출
for entry in feed.entries[:7]:
    # description이 없으면 summary를 찾고, 둘 다 없으면 '요약 없음' 처리해서 에러 방지
    summary = entry.get('summary', entry.get('description', '요약 없음'))
    news_text += f"- {entry.title}\n  {summary}\n\n"

# 2. Gemini API 최신 버전(google-genai) 적용
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

prompt = f"""
너는 미국 주식 전문 애널리스트야. 다음 뉴스 헤드라인과 요약을 분석해서 
오늘의 미국 증시 데일리 리포트를 가독성 좋은 마크다운(.md) 포맷으로 작성해줘.
결론 부분에는 개인 투자자를 위한 간단한 코멘트도 추가해 줘.

{news_text}
"""

print("AI가 리포트를 작성 중이야...")
# 최신 API 문법으로 리포트 생성
response = client.models.generate_content(
    model='gemini-1.5-flash',
    contents=prompt
)

# 3. 마크다운 파일로 저장하기
os.makedirs("reports", exist_ok=True)
today = datetime.now().strftime("%Y-%m-%d")
file_path = f"reports/{today}-report.md"

with open(file_path, "w", encoding="utf-8") as f:
    f.write(response.text)

print(f"완료! {file_path} 파일이 만들어졌어.")
