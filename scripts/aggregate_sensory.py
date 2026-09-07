import os
import json
from collections import defaultdict
import firebase_admin
from firebase_admin import credentials, firestore

# 1. 깃허브 시크릿에서 Firebase 인증 정보 로드
service_account_info = json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"])
cred = credentials.Certificate(service_account_info)
firebase_admin.initialize_app(cred)
db = firestore.client()

GAME_TYPES = [
    "COLOR_REACTION",
    "BALL_BALANCE",
    "AUDITORY_REACTION",
    "TIME_PERCEPTION",
    "CLAIRVOYANCE",
    "FUTURE_PREDICTION"
]

def run_aggregation():
    print("🚀 [감각훈련] GitHub Actions 원천 데이터 집계 시작...")
    # Collection Group으로 모든 유저 레벨 조회
    docs = db.collection_group("sensory_levels").get()
    total_participants = len(docs)
    print(f"📊 참여자 수: {total_participants}")

    if total_participants == 0:
        return

    # 게임별: 총합, 참여자수, 레벨별 카운트(0명인 레벨은 생성되지 않음)
    stats_bucket = {
        g: {
            "sum": 0,
            "count": 0,
            "distribution": defaultdict(int)
        } for g in GAME_TYPES
    }

    for doc in docs:
        data = doc.to_dict()
        levels = data.get("levels", {})
        for game in GAME_TYPES:
            lvl = levels.get(game)
            if isinstance(lvl, int) and lvl >= 1:
                # 비정상 수치 방지를 위한 클램핑 (1 ~ 300)
                clamped = min(max(lvl, 1), 300)
                stats_bucket[game]["sum"] += clamped
                stats_bucket[game]["count"] += 1
                stats_bucket[game]["distribution"][clamped] += 1

    final_stats = {}
    for game in GAME_TYPES:
        agg = stats_bucket[game]
        avg = round(agg["sum"] / agg["count"], 1) if agg["count"] > 0 else 1.0
        
        # 레벨 순서대로 정렬하고 Firestore 필드 키 규격에 맞춰 문자열 키로 변환
        sorted_distribution = {
            str(lvl): agg["distribution"][lvl]
            for lvl in sorted(agg["distribution"].keys())
        }

        final_stats[game] = {
            "avgLevel": avg,
            "totalCount": agg["count"],
            "distribution": sorted_distribution  # { "1": 34, "5": 12, "88": 1 ... }
        }

    # public_stats/sensory_summary 덮어쓰기
    db.collection("public_stats").document("sensory_summary").set({
        "totalParticipants": total_participants,
        "lastUpdatedAt": firestore.SERVER_TIMESTAMP,
        "stats": final_stats
    })
    print("✅ 원천 레벨 분포 집계 완료!")

if __name__ == "__main__":
    run_aggregation()
