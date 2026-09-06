import os
import json
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
    print("🚀 [감각훈련] GitHub Actions 무료 집계 시작...")
    # Collection Group으로 모든 유저 레벨 조회
    docs = db.collection_group("sensory_levels").get()
    total_participants = len(docs)
    print(f"📊 참여자 수: {total_participants}")

    if total_participants == 0:
        return

    stats_bucket = {
        g: {"sum": 0, "count": 0, "bins": [0] * 10} for g in GAME_TYPES
    }

    for doc in docs:
        data = doc.to_dict()
        levels = data.get("levels", {})
        for game in GAME_TYPES:
            lvl = levels.get(game)
            if isinstance(lvl, int) and lvl >= 1:
                clamped = min(max(lvl, 1), 300)
                bin_idx = min((clamped - 1) // 30, 9)
                stats_bucket[game]["sum"] += clamped
                stats_bucket[game]["count"] += 1
                stats_bucket[game]["bins"][bin_idx] += 1

    final_stats = {}
    for game in GAME_TYPES:
        agg = stats_bucket[game]
        avg = round(agg["sum"] / agg["count"], 1) if agg["count"] > 0 else 1.0
        final_stats[game] = {
            "avgLevel": avg,
            "totalCount": agg["count"],
            "binCounts": agg["bins"]
        }

    # public_stats/sensory_summary 덮어쓰기
    db.collection("public_stats").document("sensory_summary").set({
        "totalParticipants": total_participants,
        "lastUpdatedAt": firestore.SERVER_TIMESTAMP,
        "stats": final_stats
    })
    print("✅ 집계 문서 갱신 완료!")

if __name__ == "__main__":
    run_aggregation()
