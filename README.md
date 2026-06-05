# 라이브클래스 코딩 과제 — 이벤트 로그 파이프라인

---

## 구현 내용

| 항목 | 설명 |
|------|------|
| 이벤트 생성기 | 교육 플랫폼에서 발생하는 이벤트(영상 재생, 에러)를 Python으로 시뮬레이션 |
| DB 저장 | 이벤트를 이벤트 타입별로 PostgreSQL 테이블에 분리 저장 |
| 데이터 분석 | SQL 쿼리 3개로 이벤트 현황 집계 |
| Docker 구성 | docker-compose 명령어 하나로 DB 실행 + 이벤트 생성 + 저장 자동화 |
| 시각화 | Flask 웹 서버로 분석 결과를 브라우저 대시보드로 제공 |
| AWS 아키텍처 | 실제 서비스 운영 시 AWS 전환 설계 |

---

## 기술 스택

| 역할 | 기술 |
|------|------|
| 이벤트 생성 및 DB 저장 | Python, psycopg2 |
| 데이터베이스 | PostgreSQL |
| 시각화 | matplotlib, Flask |
| 컨테이너 | Docker, Docker Compose |
| AWS 전환 설계 | Lambda, RDS, ECS, QuickSight |

---

## 이벤트 설계 의도

부트캠프에서 실시간 온라인 강의를 들으면서 질문을 바로 못하다 보니 이해가 안 되는 부분을 다시 돌려보는 일이 많았습니다. 그때 어느 구간을 몇 번이나 다시 봤는지 데이터가 있다면 수강생이 어려워하는 부분을 파악할 수 있겠다는 생각이 들었고, 그게 이번 이벤트 설계의 출발점이었습니다.

**video_play** — 영상 재생 이벤트
- 수강생이 강의 영상을 재생할 때 발생
- 어떤 강좌의 어떤 영상을 얼마나 시청했는지 추적
- 출력 예시: `{ event_type: "video_play", course_id: "course_2", video_id: "video_5", watch_seconds: 320 }`

**error** — 에러 발생 이벤트
- 서비스 이용 중 에러가 발생할 때 기록
- 어떤 페이지에서 어떤 에러가 발생했는지 추적
- 출력 예시: `{ event_type: "error", error_code: 404, page_url: "/course/vod" }`

page_url은 라이브클래스 서비스의 실제 주요 페이지(대시보드, 라이브 강의, VOD, 결제, 마이페이지)를 기반으로 설계했습니다.

---

## 실행 방법

### 사전 준비
- Docker Desktop 설치 및 실행
- Python 3.11+

### 1. 레포 클론
```bash
git clone https://github.com/jjjuni-0818/liveklass-assignment.git
cd liveklass-assignment
```

### 2. DB 실행 + 이벤트 생성 + 저장
```bash
docker-compose up
```
명령어 하나로 아래가 순서대로 자동 실행됩니다:
- PostgreSQL DB 컨테이너 실행
- `sql/init.sql`로 테이블 자동 생성
- `src/generator.py`로 이벤트 100개 생성 후 DB 저장

### 3. 분석 대시보드 실행
```bash
# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# DB 실행 중인 상태에서 (터미널 1)
docker-compose up db

# 대시보드 실행 (터미널 2)
python3 src/app.py
```
브라우저에서 `http://localhost:5001` 접속하면 분석 차트 3개를 대시보드로 확인할 수 있습니다.

---

## DB 스키마 설계

```
events              — 공통 필드 (모든 이벤트)
video_play_events   — 영상 재생 전용 필드
error_events        — 에러 전용 필드
```

이벤트 타입마다 필요한 데이터가 달라서, 하나의 테이블에 모두 넣으면 video_play 이벤트에 error_code가, error 이벤트에 video_id가 빈 칸으로 남게 됩니다. 테이블을 분리하면 각 이벤트 타입에 필요한 필드만 저장되고, event_id로 연결해서 필요할 때 JOIN으로 합칠 수 있습니다.

---

## 분석 쿼리

```sql
-- 1. 이벤트 타입별 발생 횟수
SELECT event_type, COUNT(*)
FROM events
GROUP BY event_type;

-- 2. 유저별 총 이벤트 수 (많은 순)
SELECT user_id, COUNT(*)
FROM events
GROUP BY user_id
ORDER BY COUNT(*) DESC;

-- 3. 강의별 평균 시청 시간 (긴 순)
SELECT video_id, AVG(watch_seconds)
FROM video_play_events
GROUP BY video_id
ORDER BY AVG(watch_seconds) DESC;
```

---

## 구현하면서 고민한 점

**테이블을 어떻게 나눌지**
처음엔 이벤트를 테이블 하나에 다 넣으려 했는데, 한 곳에 다 적으면 비어있는 칸이 너무 많아지고 보기도 불편할 것 같았습니다. 그래서 공통 필드는 events 테이블에 두고 이벤트 타입별 필드는 별도 테이블로 분리했습니다.

**필드 구성**
"재생했다"는 사실만 저장하면 분석이 안 됩니다. 어떤 강좌의 어떤 영상을 얼마나 봤는지까지 있어야 의미 있는 데이터가 된다고 생각해서 course_id, video_id, watch_seconds를 추가했습니다.

**Docker Compose DB 연결**
`host="localhost"`로 연결했는데 계속 실패했습니다. Docker Compose 안에서는 컨테이너끼리 서비스 이름으로 통신한다는 걸 찾아보고 `host="db"`로 바꿔서 해결했습니다.

**처음엔 막막했지만**
과제를 처음 받았을 때는 어디서부터 시작해야 할지 막막했는데, 이벤트 설계 → DB 저장 → 분석 → 시각화 순서로 하나씩 해결하다 보니 전체 흐름이 완성됐습니다.

---

## AWS 아키텍처 (선택 과제 B)

실제 서비스로 운영한다면 아래와 같이 AWS로 전환할 수 있습니다.

![AWS Architecture](charts/aws_architecture.png)

**현재 → AWS 전환 설계**

| 현재 구현 | AWS 서비스 | 선택 이유 |
|-----------|-----------|---------|
| generator.py | AWS Lambda | 이벤트는 유저가 뭔가 할 때만 생기는 거라서 24시간 서버를 켜둘 필요가 없음. 필요할 때만 실행되는 Lambda가 맞는 것 같아서 선택 |
| Docker PostgreSQL | Amazon RDS | 지금 쓰는 PostgreSQL 그대로 올릴 수 있고, 직접 관리 안 해도 돼서 선택 |
| docker-compose | Amazon ECS | 지금 Docker Compose로 컨테이너 띄우는 구조를 그대로 클라우드에 올릴 수 있어서 선택 |
| Flask 대시보드 | Amazon QuickSight | RDS랑 연결하면 Flask 서버 따로 안 켜도 차트를 볼 수 있어서 선택 |

---

## 파일 구조

```
liveklass-assignment/
├── src/
│   ├── generator.py    # 이벤트 생성 + DB 저장
│   ├── app.py          # Flask 대시보드 서버
│   └── visualize.py    # 차트 이미지 저장 (파일 출력용)
├── sql/
│   ├── init.sql        # DB 테이블 생성
│   └── queries.sql     # 분석 쿼리
├── charts/             # 차트 이미지
├── docker-compose.yml
├── requirements.txt
└── README.md
```
