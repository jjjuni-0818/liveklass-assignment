import psycopg2
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 나눔고딕 폰트 직접 경로 지정
font_path = '/Users/jung/Library/Fonts/NanumGothic-Regular.ttf'
fm.fontManager.addfont(font_path)
plt.rcParams['font.family'] = 'NanumGothic'

# DB 연결 (로컬 실행용 — docker-compose up db 실행 후 사용)
# Docker 컨테이너 안에서 실행할 경우 host="db"로 변경 필요
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="liveklass",
    user="postgres",
    password="password"
)
cursor = conn.cursor()

# 차트 1: 이벤트 타입별 발생 횟수 (파이 차트)
cursor.execute("SELECT event_type, COUNT(*) FROM events GROUP BY event_type")
rows = cursor.fetchall()
labels = [row[0] for row in rows]   # event_type
values = [row[1] for row in rows]   # count

plt.figure(figsize=(6, 6))
plt.pie(values, labels=labels, autopct='%1.1f%%')
plt.title("이벤트 타입별 발생 횟수")
plt.savefig("charts/chart_event_type.png")
plt.close()
print("차트 1 저장 완료!")

# 차트 2: 유저별 총 이벤트 수 (막대 차트)
cursor.execute("SELECT user_id, COUNT(*) FROM events GROUP BY user_id ORDER BY count DESC")
rows = cursor.fetchall()
users = [row[0] for row in rows]
counts = [row[1] for row in rows]

plt.figure(figsize=(10, 5))
plt.bar(users, counts, color='steelblue')
plt.title("유저별 총 이벤트 수")
plt.xlabel("유저")
plt.ylabel("이벤트 수")
plt.savefig("charts/chart_user_events.png")
plt.close()
print("차트 2 저장 완료!")

# 차트 3: 강의별 평균 시청 시간 (막대 차트)
cursor.execute("SELECT video_id, AVG(watch_seconds) FROM video_play_events GROUP BY video_id ORDER BY avg DESC")
rows = cursor.fetchall()
videos = [row[0] for row in rows]
avgs = [float(row[1]) for row in rows]

plt.figure(figsize=(12, 5))
plt.bar(videos, avgs, color='coral')
plt.title("강의별 평균 시청 시간 (초)")
plt.xlabel("영상")
plt.ylabel("평균 시청 시간 (초)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("charts/chart_video_avg.png")
plt.close()
print("차트 3 저장 완료!")

cursor.close()
conn.close()
print("모든 차트 생성 완료!")