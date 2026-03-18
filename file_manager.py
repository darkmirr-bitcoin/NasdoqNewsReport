import os

def save_and_update_index(us_date_check, us_date_str, md_report):
    """생성된 마크다운을 파일로 저장하고, 깃허브 블로그(Pages)의 메인 화면 링크를 업데이트하는 함수"""
    
    # 1. 상세 리포트(.md) 파일 저장
    os.makedirs("reports", exist_ok=True) # reports 폴더가 없으면 새로 만듦
    file_path = f"reports/{us_date_check}-report.md"

    # 'w' 모드로 열어서 md_report 텍스트를 파일에 덮어씀
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_report)
    print(f"✅ 파일 생성 완료: {file_path}")

    # 2. 웹사이트 메인 화면(index.md) 업데이트
    index_path = "index.md"
    # 새로 추가할 링크 한 줄 생성 (클릭 시 해당 날짜의 리포트 파일로 이동)
    link_text = f"- [{us_date_str} 상세 리포트 보기](reports/{us_date_check}-report)\n"

    # 기존 index.md 파일이 있으면 읽어오고, 없으면 새로 뼈대를 만듦
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        lines = ["# 📈 나의 미국 증시 데일리 리포트 모아보기\n\n"]

    # 최신 리포트 링크가 항상 맨 위(3번째 줄)에 오도록 리스트의 특정 위치(인덱스 2)에 끼워 넣음
    if len(lines) >= 2:
        lines.insert(2, link_text)
    else:
        lines.append(link_text)

    # 링크가 추가된 전체 내용을 다시 index.md에 덮어씀
    with open(index_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("✅ index.md 업데이트 완료")
