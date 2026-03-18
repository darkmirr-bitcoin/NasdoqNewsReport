import feedparser
import requests
import yfinance as yf

def get_news(limit=80):
    """야후 파이낸스 RSS에서 최신 글로벌 뉴스를 가져오는 함수"""
    print("글로벌 뉴스 데이터 가져오는 중...")
    rss_url = "https://finance.yahoo.com/news/rssindex"
    
    # RSS 피드를 파싱(분석)해서 파이썬에서 쓰기 좋게 변환
    feed = feedparser.parse(rss_url)
    news_text = "오늘의 주요 뉴스:\n"
    
    # 최신 뉴스부터 limit(기본 80개)만큼 반복해서 가져옴
    for entry in feed.entries[:limit]:
        # 요약본(summary)이 없으면 설명(description)을 가져오고, 둘 다 없으면 '요약 없음' 처리
        summary = entry.get('summary', entry.get('description', '요약 없음'))
        # 제목과 요약을 문자열에 계속 누적해서 붙임
        news_text += f"- {entry.title}\n  {summary}\n\n"
        
    return news_text

def get_treasury_yields():
    """미국 10년물, 30년물 국채 금리와 전일 대비 변동폭을 가져오는 함수"""
    print("국채 금리 데이터(10년물, 30년물) 가져오는 중...")
    yield_text = ""
    try:
        # 1. 10년물 국채 금리 (^TNX) 데이터 수집
        tnx = yf.Ticker("^TNX")
        hist_10 = tnx.history(period="2d") # 어제와 오늘, 2일 치 데이터를 가져옴
        
        if len(hist_10) >= 2:
            prev_10 = hist_10['Close'].iloc[0] # 어제 종가
            curr_10 = hist_10['Close'].iloc[1] # 오늘 종가 (현재가)
            change_10 = curr_10 - prev_10      # 변동폭 계산
            sign_10 = "+" if change_10 > 0 else "" # 양수면 '+' 기호 붙이기
            yield_text += f"- 미국 10년물 국채 금리: {curr_10:.3f}% (전일 대비 {sign_10}{change_10:.3f}%p)\n"
        elif len(hist_10) == 1: # 휴일 직후 등 데이터가 하루 치만 있을 때 방어 로직
            yield_text += f"- 미국 10년물 국채 금리: {hist_10['Close'].iloc[0]:.3f}% (전일 대비 변동폭 계산 불가)\n"

        # 2. 30년물 국채 금리 (^TYX) 데이터 수집 (10년물과 동일한 로직)
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

        # 데이터를 아예 못 가져왔을 때의 예외 처리
        if not yield_text:
            yield_text = "국채 금리 데이터를 불러오지 못했습니다. (데이터 없음)"
            
        print(f"✅ 금리 확인 완료:\n{yield_text}")
    except Exception as e:
        # 라이브러리 에러나 네트워크 에러 발생 시 프로그램이 뻗지 않도록 처리
        print(f"❌ 금리 데이터 가져오기 실패: {e}")
        yield_text = f"국채 금리 데이터를 불러오지 못했습니다. ({e})"
        
    return yield_text

def get_fear_and_greed():
    """CNN 실시간 공포탐욕 지수와 전일 대비 변화를 가져오는 함수"""
    print("공포탐욕 지수 데이터 가져오는 중...")
    fng_text = ""
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        
        # 봇(Bot) 접근을 막는 서버를 속이기 위해 일반 웹 브라우저인 것처럼 헤더를 위장함
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=10)
        
        # 서버 응답이 정상(200)일 때만 데이터 파싱
        if res.status_code == 200:
            data = res.json()
            # 소수점 제거를 위해 round()로 반올림 처리
            score = round(data['fear_and_greed']['score']) # 오늘/현재 점수
            rating = data['fear_and_greed']['rating']      # 상태 텍스트 (예: greed)
            prev_close = round(data['fear_and_greed']['previous_close']) # 전일 마감 점수
            
            # 전일 대비 점수 변화량 계산
            change = score - prev_close
            sign = "+" if change > 0 else ""
            
            # 영어로 된 상태 값을 읽기 편하게 한국어와 이모지로 변환하는 사전(Dictionary)
            rating_ko = {
                "extreme fear": "극도의 공포 😱",
                "fear": "공포 😨",
                "neutral": "중립 😐",
                "greed": "탐욕 😎",
                "extreme greed": "극도의 탐욕 🤑"
            }.get(rating.lower(), rating) # 사전에 없는 값이 오면 원본 영어 그대로 출력
            
            fng_text = f"- CNN 공포탐욕 지수: {score}점 ({rating_ko}) / 전일 대비 {sign}{change}점"
            print(f"✅ 공포탐욕 확인 완료: {fng_text}")
        else:
            fng_text = "- 공포탐욕 지수: 데이터를 불러올 수 없습니다."
            print("❌ 공포탐욕 지수 API 응답 오류")
    except Exception as e:
        print(f"❌ 공포탐욕 지수 가져오기 실패: {e}")
        fng_text = "- 공포탐욕 지수: 오류 발생"
        
    return fng_text
