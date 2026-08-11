import os
import json
from datetime import datetime
import google.generativeai as genai

# 1. API 키 설정 (GitHub Secrets에서 가져옴)
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

genai.configure(api_key=api_key)

# 2. 오늘 날짜 및 요일 구하기 (예: 2026-08-11)
today_str = datetime.now().strftime("%Y-%m-%d")

# 3. Gemini 모델 설정 (가장 가볍고 빠른 flash 모델 활용)
generation_config = {
    "temperature": 0.7,
    "response_mime_type": "application/json", # 결과를 무조건 JSON으로 강제
}

model = genai.GenerativeModel(
    model_name="gemini-3.5-flash-lite",
    generation_config=generation_config,
    system_instruction=f"""너는 운동습관을 개선하려는 제자에게 현실적인 내공과 경공, 신체 단련을 가이드하는 
    통찰력이 뛰어나면서 지혜롭고 재치가 있는 무림 고수 '싸부'이다. 
    말투는 고풍스럽고 엄숙하면서도 격려가 담겨 있어야 한다. 그리고 재치와 통찰력을 담아서 깨달음을 줄 수 있으면 좋겠어."
)

prompt = f"""
오늘 날짜는 {today_str}이다. 
이 날자의 특성을 고려하여 제자에게 줄 금일의 수련 훈수를 사자성어나 명언 등을 인용하여 아래의 JSON 규격에 딱 맞춰서 한 가지만 생성해다오.
다른 설명이나 마크다운 기호 없이 오직 아래 JSON 구조만 출력할 것.
400글자 이내로 조언 할 것.
매일 조언을 하기 때문에 항상 새로운 조언을 할 것.
{{
  "date": "{today_str}",
  "advice": "여기에 사부의 묵직한 조언과 훈수를 줄바꿈(\\n)을 포함하여 작성할 것. (예: 관절은 쇠와 같아서...)"
}}
"""

print(f"[{today_str}] 사부의 훈수를 생성하는 중...")
response = model.generate_content(prompt)
result_json_str = response.text.strip()

# JSON 유효성 검증
try:
    parsed_data = json.loads(result_json_str)
except json.JSONDecodeError:
    # 혹시 모를 파싱 에러 방어
    parsed_data = {
        "date": today_str,
        "advice": "오늘 하루도 관절을 아끼고 바닥을 움켜쥐듯 차분하게 수련에 임하게나."
    }

# 4. 파일로 저장 (앱이 긁어갈 단일 JSON 파일)
file_path = "daily_advice.json"
with open(file_path, "w", encoding="utf-8") as f:
    json.dump(parsed_data, f, ensure_ascii=False, indent=2)

print("일일 조언 JSON 생성 완료!")
