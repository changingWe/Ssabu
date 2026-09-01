import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import google.generativeai as genai

# 1. API 키 설정 (GitHub Secrets에서 가져옴)
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

genai.configure(api_key=api_key)

# 2. 오늘 날짜 구하기 (Asia/Seoul 기준)
today_str = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")

# 3. Gemini 모델 설정
generation_config = {
    "temperature": 0.7,
    "response_mime_type": "application/json",
}

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=generation_config,
    system_instruction="""너는 운동습관을 개선하려는 제자에게 현실적인 내공과 경공, 신체 단련을 가이드하는 
    통찰력이 뛰어나면서 지혜롭고 재치가 있는 무림 고수 '싸부'이다. 
    말투는 고풍스럽고 엄숙하면서도 격려가 담겨 있어야 한다. 그리고 재치와 통찰력을 담아서 깨달음을 줄 수 있으면 좋겠어."""
)

prompt = f"""
오늘 날짜는 {today_str}이다. 
조언의 가장 큰 목적은 제자의 운동하는 습관을 잡는 것임을 잊지 말고
제자에게 줄 금일의 수련 가르침을 사자성어나 명언 등을 인용하여 조언을 해줘.
특히, 습관과 관련된 유명인의 명언이나 이야기가 실리면 좋을거 같아.

아래의 JSON 규격에 딱 맞춰서 재치와 통찰력을 담아서 깨달음을 담아서 한 가지만 생성해다오.
다른 설명이나 마크다운 기호 없이 오직 아래 JSON 구조만 출력할 것.
400글자 내외로 가르침을 줄 것.
매일 조언을 하기 때문에 항상 새로운 조언을 할 것.
{{
  "date": "{today_str}",
  "advice": "여기에 사부의 묵직한 조언과 훈수를 줄바꿈(\\n)을 포함하여 작성할 것. (예: 관절은 쇠와 같아서...)"
}}
"""

print(f"[{today_str}] 사부의 훈수를 생성하는 중...")
response = model.generate_content(prompt)
result_json_str = response.text.strip()

# JSON 유효성 검증 및 파싱
try:
    parsed_data = json.loads(result_json_str)
except json.JSONDecodeError:
    parsed_data = {
        "date": today_str,
        "advice": "오늘 하루도 관절을 아끼고 바닥을 움켜쥐듯 차분하게 수련에 임하게나."
    }

# 4-1. 당일 단일 파일 저장 (앱에서 실시간 조회용)
daily_file_path = "daily_advice.json"
with open(daily_file_path, "w", encoding="utf-8") as f:
    json.dump(parsed_data, f, ensure_ascii=False, indent=2)
print(f"✅ 당일 조언 파일 갱신 완료: {daily_file_path}")

# 4-2. 누적 아카이브 파일 저장 (동일 날짜 덮어쓰기 로직)
archive_file_path = "daily_advice_archive.json"
archive_list = []

# 기존 아카이브 파일이 존재하면 불러오기
if os.path.exists(archive_file_path):
    try:
        with open(archive_file_path, "r", encoding="utf-8") as f:
            archive_list = json.load(f)
            if not isinstance(archive_list, list):
                archive_list = []
    except (json.JSONDecodeError, IOError):
        archive_list = []

# 동일 날짜가 있으면 덮어쓰기, 없으면 새로 추가
updated = False
for i, item in enumerate(archive_list):
    if item.get("date") == parsed_data["date"]:
        archive_list[i] = parsed_data  # 덮어쓰기
        updated = True
        print(f"🔄 [{parsed_data['date']}] 기존 아카이브 기록을 갱신했습니다.")
        break

if not updated:
    archive_list.append(parsed_data)  # 신규 추가
    print(f"➕ [{parsed_data['date']}] 신규 조언을 아카이브에 추가했습니다.")

# 날짜 순서대로 오름차순 정렬 (과거 -> 최신)
archive_list.sort(key=lambda x: x.get("date", ""))

# 아카이브 파일 쓰기
with open(archive_file_path, "w", encoding="utf-8") as f:
    json.dump(archive_list, f, ensure_ascii=False, indent=2)

print(f"📚 전체 아카이브 누적 완료 (총 {len(archive_list)}건)")
