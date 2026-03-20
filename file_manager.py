import os

import os

def save_and_update_index(us_date_check, us_date_str, md_report):
    """생성된 마크다운을 파일로 저장하고, 깃허브 메인 화면과 최신 리포트 페이지를 업데이트하는 함수"""
    
    # 1. 날짜별 원본 보관 (백업용)
    os.makedirs("reports", exist_ok=True)
    file_path = f"reports/{us_date_check}-report.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_report)
    print(f"✅ 날짜별 백업 파일 생성 완료: {file_path}")

    # 2. 🌟 고정된 최신 웹페이지(latest.md) 덮어쓰기
    # 매일 이 파일이 새로운 내용으로 교체되므로, 우리는 항상 latest.html만 접속하면 됨!
    latest_path = "latest.md"
    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(md_report)
    print("✅ 최신 웹페이지(latest.md) 업데이트 완료!")

    # 3. 웹사이트 메인 화면(index.md) 업데이트 (아카이브 용도)
    index_path = "index.md"
    link_text = f"- [{us_date_str} 상세 리포트 기록](reports/{us_date_check}-report.html)\n"

    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        # 파일이 없을 때 최초 생성 (최신 페이지 접속 버튼 추가)
        lines = [
            "# 📈 나의 미국 증시 데일리 리포트\n\n",
            "👉 **[🔥 오늘의 최신 리포트 바로가기 (고정 주소)](latest.html)**\n\n",
            "### 🗂️ 지난 리포트 보관함\n"
        ]

    # 최신 리포트 기록이 보관함(🗂️) 바로 밑에 쌓이도록 위치 잡기
    insert_idx = len(lines) # 기본값: 맨 밑
    for i, line in enumerate(lines):
        if "### 🗂️ 지난 리포트 보관함" in line:
            insert_idx = i + 1
            break
            
    if len(lines) >= insert_idx:
        lines.insert(insert_idx, link_text)
    else:
        lines.append(link_text)

    with open(index_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("✅ index.md 보관함 업데이트 완료")
