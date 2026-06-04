import psycopg2 # 생성된 이벤트 목록을 PostgreSQL 데이터베이스에 저장하기 위해 psycopg2 라이브러리를 사용
import random
import uuid
from datetime import datetime

print("이벤트 생성기 시작!")

def generate_event():
    event_type = random.choice(["video_play", "error"])
    # 모든 이벤트에 공통으로 들어가는 필드
    event = {
        "event_id": str(uuid.uuid4()),          # 이벤트 고유 ID (겹치지 않게 UUID 사용)
        "event_type": event_type,                # 이벤트 종류
        "user_id": f"user_{random.randint(1, 10)}",  # user_1 ~ user_10 중 랜덤
        "timestamp": datetime.now().isoformat(), # 현재 시간 (예: 2026-06-04T14:30:00)
    }
    # 이벤트 타입에 따라 추가 필드가 달라짐
    if event_type == "video_play":
        # 영상 재생 이벤트일 때만 추가되는 필드
        event["video_id"] = f"video_{random.randint(1, 20)}"      # video_1 ~ video_20
        event["course_id"] = f"course_{random.randint(1, 5)}"     # course_1 ~ course_5
        event["watch_seconds"] = random.randint(10, 3600)          # 10초 ~ 1시간 사이 랜덤

    elif event_type == "error":
        # 에러 이벤트일 때만 추가되는 필드
        event["error_code"] = random.choice([400, 403, 404, 500, 503])  # 실제 HTTP 에러 코드
        event["error_message"] = random.choice(["Not Found", "Server Error", "Forbidden"])
        event["page_url"] = random.choice(["/home", "/course", "/video", "/profile"])  # 어느 페이지에서 발생했는지
    
    return event  # 완성된 이벤트 딕셔너리 반환


def save_events_to_db(events):
    # DB 연결 설정
    conn = psycopg2.connect(
        host="db",
        port=5432,
        dbname="liveklass",
        user="postgres",
        password="password"
    )
    cursor = conn.cursor()

    for event in events:
        # events 테이블에 삽입
        cursor.execute("""
            INSERT INTO events (event_id, event_type, user_id, timestamp)
            VALUES (%s, %s, %s, %s)
        """, (
            event["event_id"],
            event["event_type"],
            event["user_id"],
            event["timestamp"]
        ))

        if event["event_type"] == "video_play":
            # video_play_events 테이블에 삽입
            cursor.execute("""
                INSERT INTO video_play_events (event_id, video_id, course_id, watch_seconds)
                VALUES (%s, %s, %s, %s)
            """, (
                event["event_id"],
                event["video_id"],
                event["course_id"],
                event["watch_seconds"]
            ))
        elif event["event_type"] == "error":
            # error_events 테이블에 삽입
            cursor.execute("""
                INSERT INTO error_events (event_id, error_code, error_message, page_url)
                VALUES (%s, %s, %s, %s)
            """, (
                event["event_id"],
                event["error_code"],
                event["error_message"],
                event["page_url"]
            ))

    conn.commit()
    cursor.close()
    conn.close()
    print("DB 저장 완료")

# 이벤트 100개 생성 후 DB에 저장
events = []
for i in range(100):
    event = generate_event()
    events.append(event)

print(f"총 {len(events)}개 이벤트 생성 완료!")
save_events_to_db(events)  # DB에 저장