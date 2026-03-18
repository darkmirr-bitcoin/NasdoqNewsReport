import os
import json
import gspread

def get_google_sheet_data():
    """개인 구글 시트의 'Today' 탭에서 나스닥 종목 AI 분석 데이터를 읽어오는 함수"""
    # GitHub Secrets에 등록해 둔 구글 서비스 계정 인증키를 가져옴
    google_sheets_creds_json = os.environ.get("GOOGLE_SHEETS_CREDS")
    sheet_data_text = "구글 시트 'Today' 탭의 나스닥 15개 종목 AI 분석 및 시장 지표 데이터:\n"

    # 인증키가 정상적으로 설정되어 있는지 확인
    if google_sheets_creds_json:
        try:
            print("구글 시트 데이터 읽는 중...")
            # JSON 텍스트를 파이썬 딕셔너리로 변환 후 gspread에 인증
            creds = json.loads(google_sheets_creds_json)
            gc = gspread.service_account_from_dict(creds)
            
            # 구글 시트 URL에 있는 고유 ID를 이용해 시트 열기
            spreadsheet_id = "1_TEiYUhm8ajuw_zOf8Tzjt3eMUjlPG6a4q4ynx6fUEU"
            sh = gc.open_by_key(spreadsheet_id)
            worksheet = sh.worksheet("Today") # 'Today' 탭 선택
            
            # 탭 안의 모든 데이터를 2차원 리스트 형태로 가져옴
            all_values = worksheet.get_all_values()
            
            if all_values:
                # 리스트 안의 각 행(row)을 콤마(,)로 연결해서 하나의 거대한 텍스트로 합침
                sheet_data_text += "\n".join([",".join(row) for row in all_values])
                print("✅ 구글 시트 'Today' 탭 데이터 읽기 성공!")
            else:
                sheet_data_text += "시트에 데이터가 없어."
        except Exception as e:
            # 권한이 없거나 탭 이름이 틀렸을 때 예외 처리
            print(f"❌ 구글 시트 데이터 읽기 실패: {e}")
            sheet_data_text += f"(데이터 읽기 실패: {e})"
    else:
        print("구글 시트 크레덴셜이 설정되지 않았어.")
        sheet_data_text += "(크레덴셜 미설정)"
        
    return sheet_data_text
