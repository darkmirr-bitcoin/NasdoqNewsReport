import os
import requests

def send_alert(us_date_str, us_date_check, telegram_msg):
    """텔레그램 봇 API를 통해 스마트폰으로 모바일 요약본을 전송하는 함수"""
    # GitHub Secrets에서 봇 토큰과 대화방(Chat) ID 가져오기
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if bot_token and chat_id:
        print("텔레그램으로 모바일 요약본 전송 시작...")
        # 텔레그램 메시지 발송 공식 API 주소
        send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        # 깃허브 Pages 상세 리포트 웹페이지 링크 조립
        github_pages_url = "https://darkmirr-bitcoin.github.io/NasdoqNewsReport"
        # 깃허브 스킨 테마가 적용되도록 끝에 .md 대신 .html을 붙임
        report_web_link = f"{github_pages_url}/reports/{us_date_check}-report.html"
        
        # AI가 만든 요약본(telegram_msg) 하단에 웹 링크를 붙여서 최종 메시지 완성
        text_to_send = f"🔔 {us_date_str} 미국 증시 요약\n\n{telegram_msg}\n\n👉 [상세 리포트 웹에서 보기]\n{report_web_link}" 
        
        # 텔레그램 API 스펙에 맞춰 JSON 페이로드(전송할 데이터 덩어리) 세팅
        payload = {
            "chat_id": chat_id,
            "text": text_to_send[:4000] # 텔레그램 1회 전송 글자수 제한(4096자) 방어
        }
        
        # POST 방식으로 데이터 전송 후 결과 확인
        res = requests.post(send_url, json=payload)
        if res.status_code == 200:
            print("✅ 텔레그램 발송 성공!")
        else:
            print(f"❌ 텔레그램 발송 실패: {res.text}")
    else:
        print("텔레그램 토큰이나 챗ID가 설정되지 않았어.")
