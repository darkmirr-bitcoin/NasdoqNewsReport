import os
import requests

def send_alert(us_date_str, us_date_check, telegram_msg):
    """텔레그램 봇 API를 통해 스마트폰으로 모바일 요약본을 전송하는 함수"""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if bot_token and chat_id:
        print("텔레그램으로 모바일 요약본 전송 시작...")
        send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        github_pages_url = "https://darkmirr-bitcoin.github.io/NasdoqNewsReport"
        
        # 🚨 이제 날짜별 URL이 아니라 항상 고정된 'latest.html' 로 연결해!
        report_web_link = f"{github_pages_url}/latest.html"
        
        text_to_send = f"🔔 {us_date_str} 미국 증시 요약\n\n{telegram_msg}\n\n👉 [최신 상세 리포트 웹에서 보기]\n{report_web_link}" 
        
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
