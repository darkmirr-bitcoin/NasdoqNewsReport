📌 시스템 아키텍처 (System Architecture)
이 프로젝트는 100% 서버리스(Serverless) 환경에서 동작하는 개인 맞춤형 미국 증시 데일리 리포트 자동화 시스템이야.
GitHub Actions를 스케줄러로 활용하여 매일 정해진 시간에 작동하며,
외부 API와 구글 시트 데이터를 수집한 뒤 Gemini AI를 통해 분석 리포트를 생성하고 텔레그램으로 전송해.

⚙️ 전체 동작 흐름 (Workflow)
스케줄링 및 실행 (GitHub Actions)

매일 지정된 시간(한국 시간 아침 8시)에 자동으로 파이썬 스크립트(main.py)가 실행돼.

휴장일 필터링 (pandas_market_calendars)

가장 먼저 뉴욕증권거래소(NYSE) 달력을 확인해서 당일이 주말이거나 공휴일(휴장일)인 경우,
텔레그램으로 휴장 알림만 보내고 프로세스를 즉시 종료해. API 낭비를 막기 위한 장치야.

데이터 수집 (Data Fetching)

글로벌 뉴스: 야후 파이낸스 RSS 피드에서 최신 미국 증시 기사 최대 100개를 수집.

거시 경제 지표: yfinance 라이브러리를 통해 미국 10년물(^TNX), 30년물(^TYX) 국채 금리와 전일 대비 변동폭을 수집.

사용자 커스텀 데이터: gspread를 통해 사용자 개인의 구글 시트에 접근. 'Today' 탭에 기록된 나스닥 15개 종목의 
AI 분석 점수, 차트 추세 상태, 공포탐욕 지수를 가져와.
(*gspread는 나스닥 15개의 차트 데이터를 이용해서 ai로 해당 데이터 기준으로 점수를 뽑고 추세 를 뽑아오는 역할)

AI 분석 및 리포트 생성 (Google Gemini 2.0 Flash)

수집된 3가지 데이터(뉴스, 금리, 구글 시트 데이터)를 조합하여 Gemini API에 전송해.

프롬프트 엔지니어링을 통해 ① 공포탐욕 지수 및 금리 코멘트, ② AI 점수 75점 이상 종목 하이라이트, 
③ 거시 경제 및 테마 뉴스 분석 순서로 마크다운 형식의 리포트를 작성하도록 제어해.

결과 저장 및 알림 전송 (GitHub & Telegram)

완성된 .md 리포트 파일은 GitHub 저장소의 reports/ 폴더에 날짜별로 자동 저장(Commit & Push)돼.

동시에 Telegram Bot API를 통해 사용자의 스마트폰으로 요약된 리포트 메시지가 실시간 전송돼.

🛠️ 주요 기술 스택 (Tech Stack)
Language: Python 3.11

CI/CD & Scheduler: GitHub Actions (cron trigger)

AI Model: Google Gemini 2.0 Flash

Data Sources: * Yahoo Finance RSS / yfinance

Google Sheets API (gspread)

Notification: Telegram Bot API

🔐 필요 환경 변수 (Secrets)
이 프로그램이 정상 작동하려면 GitHub Repository Secrets에 아래 4가지 키가 등록되어 있어야 해.

GEMINI_API_KEY: 구글 Gemini API 통신을 위한 키

GOOGLE_SHEETS_CREDS: 구글 시트 접근을 위한 서비스 계정 JSON 키

TELEGRAM_BOT_TOKEN: 텔레그램 봇 API 토큰

TELEGRAM_CHAT_ID: 메시지를 수신할 텔레그램 Chat ID
