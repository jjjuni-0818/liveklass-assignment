import psycopg2
import matplotlib
matplotlib.use('Agg')  # 서버 환경에서 GUI 없이 차트 생성
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import io
import base64
from flask import Flask, render_template_string

app = Flask(__name__)

# 나눔고딕 폰트 설정 (없으면 기본 폰트 사용)
font_path = os.path.expanduser('~/Library/Fonts/NanumGothic-Regular.ttf')
if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    plt.rcParams['font.family'] = 'NanumGothic'

def get_db():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="liveklass",
        user="postgres",
        password="password"
    )

def chart_to_base64(fig):
    """matplotlib 차트를 base64 문자열로 변환 (HTML에 삽입하기 위해)"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64

@app.route('/')
def index():
    conn = get_db()
    cursor = conn.cursor()

    # 차트 1: 이벤트 타입별 발생 횟수 (파이 차트)
    cursor.execute("SELECT event_type, COUNT(*) FROM events GROUP BY event_type")
    rows = cursor.fetchall()
    labels = [row[0] for row in rows]
    values = [row[1] for row in rows]

    fig1, ax1 = plt.subplots(figsize=(6, 6))
    ax1.pie(values, labels=labels, autopct='%1.1f%%')
    ax1.set_title("이벤트 타입별 발생 횟수")
    chart1 = chart_to_base64(fig1)

    # 차트 2: 유저별 총 이벤트 수 (막대 차트)
    cursor.execute("SELECT user_id, COUNT(*) FROM events GROUP BY user_id ORDER BY COUNT(*) DESC")
    rows = cursor.fetchall()
    users = [row[0] for row in rows]
    counts = [row[1] for row in rows]

    fig2, ax2 = plt.subplots(figsize=(10, 5))
    ax2.bar(users, counts, color='steelblue')
    ax2.set_title("유저별 총 이벤트 수")
    ax2.set_xlabel("유저")
    ax2.set_ylabel("이벤트 수")
    chart2 = chart_to_base64(fig2)

    # 차트 3: 강의별 평균 시청 시간 (막대 차트)
    cursor.execute("SELECT video_id, AVG(watch_seconds) FROM video_play_events GROUP BY video_id ORDER BY AVG(watch_seconds) DESC")
    rows = cursor.fetchall()
    videos = [row[0] for row in rows]
    avgs = [float(row[1]) for row in rows]

    fig3, ax3 = plt.subplots(figsize=(12, 5))
    ax3.bar(videos, avgs, color='coral')
    ax3.set_title("강의별 평균 시청 시간 (초)")
    ax3.set_xlabel("영상")
    ax3.set_ylabel("평균 시청 시간 (초)")
    plt.xticks(rotation=45)
    chart3 = chart_to_base64(fig3)

    cursor.close()
    conn.close()

    # HTML 페이지로 렌더링
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>라이브클래스 이벤트 분석 대시보드</title>
        <style>
            body { font-family: sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f9f9f9; }
            h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
            h2 { color: #555; margin-top: 40px; }
            img { max-width: 100%; border: 1px solid #ddd; border-radius: 8px; padding: 10px; background: white; }
        </style>
    </head>
    <body>
        <h1>라이브클래스 이벤트 분석 대시보드</h1>

        <h2>이벤트 타입별 발생 횟수</h2>
        <img src="data:image/png;base64,{{ chart1 }}">

        <h2>유저별 총 이벤트 수</h2>
        <img src="data:image/png;base64,{{ chart2 }}">

        <h2>강의별 평균 시청 시간</h2>
        <img src="data:image/png;base64,{{ chart3 }}">
    </body>
    </html>
    """
    return render_template_string(html, chart1=chart1, chart2=chart2, chart3=chart3)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
