# 라이브클래스 과제 — 면접 준비 & 코드 완전 이해

> 나만 보는 공부 노트. 면접에서 설명할 수 있도록 정리.

---

## 전체 흐름 한눈에 보기

```
generator.py 실행
    ↓
이벤트 100개 랜덤 생성 (video_play or error)
    ↓
PostgreSQL DB에 저장
    ↓
queries.sql로 분석
    ↓
visualize.py로 차트 이미지 생성
```

Docker Compose로 위 전체가 명령어 하나로 자동 실행됨.

---

## generator.py 코드 완전 이해

### import 설명

```python
import psycopg2    # Python에서 PostgreSQL에 연결하는 라이브러리
import random      # 랜덤 값 뽑을 때 사용
import uuid        # 절대 겹치지 않는 고유 ID 생성
from datetime import datetime  # 현재 시간 가져올 때 사용
```

### UUID가 뭐냐

```python
event_id = str(uuid.uuid4())
# 결과: "08eb7309-aa5c-4720-8e35-53e91804175d"
```

- UUID = Universally Unique Identifier
- 전 세계에서 동시에 만들어도 절대 겹치지 않는 ID
- 주민등록번호처럼 각 이벤트에 고유한 번호를 붙여줌
- 왜 숫자(1,2,3...)가 아닌가? → 여러 서버에서 동시에 생성하면 숫자는 겹칠 수 있음

### random 관련 코드

```python
random.choice(["video_play", "error"])
# → 리스트에서 하나를 랜덤으로 선택

random.randint(1, 10)
# → 1부터 10 사이 정수 하나를 랜덤으로 선택

f"user_{random.randint(1, 10)}"
# → "user_3", "user_7" 같은 문자열 생성
# f"..." = f-string: 문자열 안에 변수 넣는 방법
```

### 이벤트 타입별 분기

```python
if event_type == "video_play":
    event["video_id"] = f"video_{random.randint(1, 20)}"
    event["course_id"] = f"course_{random.randint(1, 5)}"
    event["watch_seconds"] = random.randint(10, 3600)

elif event_type == "error":
    event["error_code"] = random.choice([400, 403, 404, 500, 503])
    event["error_message"] = random.choice(["Not Found", "Server Error", "Forbidden"])
    event["page_url"] = random.choice(["/home", "/course", "/video", "/profile"])
```

- video_play면 영상 관련 필드만 추가
- error면 에러 관련 필드만 추가
- 두 타입에 필요한 필드가 다르기 때문에 분리

### DB 저장 코드

```python
conn = psycopg2.connect(
    host="db",       # Docker Compose 서비스 이름 (localhost가 아님!)
    port=5432,       # PostgreSQL 기본 포트
    dbname="liveklass",
    user="postgres",
    password="password"
)
cursor = conn.cursor()  # SQL 실행할 커서 생성
```

```python
cursor.execute("""
    INSERT INTO events (event_id, event_type, user_id, timestamp)
    VALUES (%s, %s, %s, %s)
""", (event["event_id"], event["event_type"], event["user_id"], event["timestamp"]))
```

- `%s` = SQL에서 변수 자리 표시 (Python의 f-string과 비슷)
- 두 번째 인자 튜플의 값들이 순서대로 `%s` 자리에 들어감
- SQL injection 방지를 위해 f-string 대신 `%s` 사용

```python
conn.commit()   # 저장 확정 (이게 없으면 저장 안 됨!)
cursor.close()
conn.close()
```

---

## init.sql 코드 완전 이해

```sql
CREATE TABLE events (
    event_id  UUID PRIMARY KEY,   -- 고유 ID, 중복 불가
    event_type TEXT NOT NULL,     -- NULL 불가 (필수값)
    user_id   TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL -- 시간대 포함 시간 (TIMESTAMP with TimeZone)
);
```

```sql
CREATE TABLE video_play_events (
    event_id UUID REFERENCES events(event_id),  -- events 테이블과 연결
    video_id TEXT,
    course_id TEXT,
    watch_seconds INTEGER
);
```

- `REFERENCES events(event_id)` = 외래키(Foreign Key)
- events 테이블에 있는 event_id만 들어올 수 있음
- events 테이블이 부모, video_play_events가 자식

### 왜 테이블을 3개로 나눴나

```
하나의 테이블로 하면:
event_id | event_type  | video_id | watch_seconds | error_code | error_message
---------|-------------|----------|---------------|------------|---------------
uuid1    | video_play  | video_3  | 1200          | NULL       | NULL
uuid2    | error       | NULL     | NULL          | 404        | Not Found
```
→ NULL이 너무 많아서 지저분하고 어떤 이벤트인지 파악하기 어려움

```
테이블 분리하면:
events 테이블: 공통 필드만
video_play_events: video_play 전용 필드
error_events: error 전용 필드
```
→ 각 테이블이 명확하고, 필요할 때 JOIN으로 합칠 수 있음

---

## queries.sql 코드 완전 이해

```sql
-- 쿼리 1: 이벤트 타입별 발생 횟수
SELECT event_type, COUNT(*)
FROM events
GROUP BY event_type;
```

- `COUNT(*)` = 행 개수 세기
- `GROUP BY event_type` = event_type 값이 같은 것끼리 묶기
- 결과: video_play 몇 개, error 몇 개

```sql
-- 쿼리 2: 유저별 총 이벤트 수
SELECT user_id, COUNT(*)
FROM events
GROUP BY user_id
ORDER BY COUNT(*) DESC;
```

- `ORDER BY COUNT(*) DESC` = 많은 순서로 정렬 (DESC = 내림차순)

```sql
-- 쿼리 3: 강의별 평균 시청 시간
SELECT video_id, AVG(watch_seconds)
FROM video_play_events
GROUP BY video_id
ORDER BY avg DESC;
```

- `AVG()` = 평균 계산 함수
- video_play_events 테이블에서만 가져옴 (error 이벤트는 watch_seconds 없음)

---

## docker-compose.yml 코드 완전 이해

```yaml
services:
  db:           # 서비스 이름 = 컨테이너 내부 호스트명
    image: postgres   # 사용할 Docker 이미지
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d liveklass"]
      interval: 5s   # 5초마다 체크
      retries: 5     # 5번 실패하면 unhealthy
```

```yaml
  app:
    depends_on:
      db:
        condition: service_healthy  # db가 healthy 상태일 때만 실행
```

### 왜 localhost가 아니라 db인가

```
Docker Compose 안에서:
- app 컨테이너가 "localhost" 접속 → 자기 자신에게 접속 (DB 없음!)
- app 컨테이너가 "db" 접속 → db 서비스에 접속 (정상!)

Docker Compose에서는 서비스 이름이 호스트명이 됨
```

### healthcheck가 왜 필요한가

```
healthcheck 없으면:
DB 컨테이너 시작됨 → app 바로 실행 → DB 아직 준비 안 됨 → 연결 실패!

healthcheck 있으면:
DB 컨테이너 시작됨 → pg_isready로 준비 확인 → Healthy → app 실행 → 연결 성공!
```

---

## 만들면서 틀렸던 것들

### 1. localhost → db로 바꿔야 했던 이유
Docker Compose에서 각 컨테이너는 독립된 네트워크를 가짐. app 컨테이너 입장에서 localhost는 자기 자신. DB에 접속하려면 서비스 이름인 "db"를 써야 함.

### 2. queries.sql 주석을 #으로 썼던 것
Python 주석은 `#`이지만 SQL 주석은 `--`임.

```python
# Python 주석
```
```sql
-- SQL 주석
```

### 3. visualize.py 차트 저장 경로
`plt.savefig("chart.png")` → 실행 위치에 저장됨
`plt.savefig("charts/chart.png")` → charts 폴더에 저장됨

### 4. 가상환경(venv)을 써야 하는 이유
프로젝트마다 독립된 패키지 환경이 필요하기 때문.
A 프로젝트에서 psycopg2 2.8, B 프로젝트에서 psycopg2 2.9를 쓰면 충돌 가능.
venv로 각 프로젝트별 독립된 패키지 공간을 만들어 해결.

---

## 면접 예상 질문 & 답변

### Q. 이 과제에서 뭘 만들었는지 설명해주세요.

> 교육 플랫폼에서 발생하는 이벤트 로그를 수집하고 저장하고 분석하는 파이프라인을 만들었습니다. Python으로 이벤트를 생성하고 PostgreSQL에 저장한 다음 SQL로 분석하고 matplotlib으로 차트를 만들었습니다. Docker Compose로 명령어 하나에 전체가 실행되도록 구성했습니다.

---

### Q. 왜 테이블을 3개로 나눴나요?

> 이벤트 타입마다 필요한 필드가 다르기 때문입니다. 하나의 테이블에 다 넣으면 video_play 이벤트에 error_code가, error 이벤트에 video_id가 NULL로 채워져서 데이터가 지저분해집니다. 테이블을 분리하면 각 타입에 필요한 필드만 들어가서 깔끔하고, event_id로 연결해서 필요할 때 JOIN도 가능합니다.

---

### Q. UUID를 쓴 이유가 뭔가요?

> 이벤트마다 고유한 ID가 필요한데, 단순 숫자(1,2,3)는 여러 서버에서 동시에 생성하면 겹칠 수 있습니다. UUID는 전 세계에서 동시에 만들어도 겹치지 않아서 분산 환경에서도 안전하게 사용할 수 있습니다.

---

### Q. Docker Compose에서 localhost 대신 db를 쓴 이유가 뭔가요?

> Docker Compose 안에서 각 컨테이너는 독립된 네트워크를 가집니다. app 컨테이너 입장에서 localhost는 자기 자신을 가리키기 때문에 DB에 접속할 수 없습니다. Docker Compose에서는 서비스 이름이 호스트명이 되기 때문에 host="db"로 써야 합니다.

---

### Q. healthcheck는 왜 추가했나요?

> depends_on만 쓰면 DB 컨테이너가 시작됐다는 것만 확인하고 app을 실행합니다. 하지만 PostgreSQL이 완전히 준비되기 전에 app이 연결을 시도해서 실패할 수 있습니다. healthcheck로 pg_isready 명령어를 주기적으로 실행해서 DB가 실제로 쿼리를 받을 준비가 됐을 때만 app을 실행하도록 했습니다.

---

### Q. GROUP BY가 뭔가요?

> SQL에서 특정 컬럼의 값이 같은 행들을 묶어서 집계할 때 씁니다. 예를 들어 `GROUP BY event_type`을 하면 video_play끼리, error끼리 묶어서 각각 COUNT, AVG 같은 집계 함수를 적용할 수 있습니다.

---

### Q. 파이프라인이 뭔가요?

> 데이터가 단계별로 흘러가는 흐름입니다. 이 과제에서는 이벤트 생성 → DB 저장 → SQL 분석 → 시각화 순서로 데이터가 흘러갑니다. 실제 서비스에서는 유저 행동 → Kafka 수집 → DB 적재 → 대시보드 순서로 이어집니다.

---

### Q. AVG, COUNT 같은 함수를 집계 함수라고 하는데 다른 건 뭐가 있나요?

> COUNT(개수), AVG(평균), SUM(합계), MAX(최대값), MIN(최소값)이 있습니다. 이번 과제에서는 COUNT로 이벤트 발생 횟수를, AVG로 평균 시청 시간을 구했습니다.

---

### Q. 이 과제에서 아쉬운 점이나 개선하고 싶은 부분이 있나요?

> 세 가지 있습니다. 첫째, 지금은 이벤트를 한 번에 100개 생성하고 끝나는데, 실제 서비스처럼 실시간으로 계속 이벤트가 들어오는 구조로 만들고 싶습니다. 둘째, 시각화를 matplotlib 스크립트로 했는데 Grafana 같은 대시보드 도구를 연결하면 실시간으로 볼 수 있을 것 같습니다. 셋째, 비밀번호가 코드에 직접 쓰여 있는데 환경변수로 관리하는 게 보안상 더 좋습니다.

---

## AWS 아키텍처 완전 이해

### AWS 아키텍처가 뭐냐

지금 우리 과제는 **내 맥북에서만** 돌아가요.

```
내 맥북
├── Docker (PostgreSQL)
├── Python generator.py
└── Python visualize.py
```

근데 실제 라이브클래스 서비스는 전국 유저가 동시에 접속해요.
맥북으로는 감당이 안 됩니다. 그래서 **AWS(아마존 클라우드)** 라는 거대한 서버에 올리는 거예요.

**아키텍처** = 어떤 서비스들을 어떻게 연결해서 쓸지 **설계도**
집 짓기 전에 설계도 그리는 것처럼, 서비스 만들기 전에 어떤 AWS 서비스들을 어떻게 연결할지 그림으로 그린 것.

---

### 현재 구현 vs AWS 서비스 대응

```
현재 (내 맥북)              AWS (클라우드)
─────────────────────────────────────────
Docker PostgreSQL      →   Amazon RDS
generator.py           →   AWS Lambda
docker-compose         →   Amazon ECS
visualize.py           →   Amazon QuickSight
```

---

### 각 AWS 서비스 설명 + 선택 이유

#### Amazon RDS (현재: Docker PostgreSQL)

**RDS가 뭐냐**
- RDS = Relational Database Service
- 아마존이 대신 관리해주는 데이터베이스
- 지금 Docker로 내가 직접 PostgreSQL을 띄우는데, RDS를 쓰면 아마존이 대신 관리해줌

**왜 RDS를 선택했나**
- 지금 PostgreSQL을 쓰고 있어서 그대로 마이그레이션 가능
- 자동 백업 → 데이터가 날아가도 복구 가능
- 스케일 업 → 유저가 늘어나면 DB 용량을 쉽게 늘릴 수 있음
- 서버 관리 안 해도 됨 → 아마존이 알아서 패치, 유지보수

**면접 설명 방법**
> "현재 Docker로 PostgreSQL을 로컬에서 실행하는데, 실제 서비스라면 Amazon RDS로 이전하겠습니다. 기존 PostgreSQL 코드를 그대로 쓸 수 있고 자동 백업과 스케일 업이 가능해서 선택했습니다."

---

#### AWS Lambda (현재: generator.py)

**Lambda가 뭐냐**
- 서버 없이 함수만 올려두면 필요할 때 실행되는 서비스
- 지금 generator.py를 직접 실행하는데, Lambda에 올리면 이벤트가 발생할 때마다 자동 실행됨
- 평소엔 비용 0원, 실행될 때만 과금

**왜 Lambda를 선택했나**
- 이벤트 수집은 요청이 들어올 때만 실행되면 충분 → 항상 켜둘 필요 없음
- 항상 켜두는 서버보다 훨씬 저렴
- 서버 관리 불필요

**면접 설명 방법**
> "이벤트 수집 함수는 유저 행동이 있을 때만 실행되면 되기 때문에 항상 켜두는 서버가 필요 없습니다. AWS Lambda를 쓰면 함수가 실행될 때만 비용이 발생해서 비용 효율적입니다."

---

#### Amazon ECS (현재: docker-compose)

**ECS가 뭐냐**
- ECS = Elastic Container Service
- Docker 컨테이너를 AWS에서 실행하고 관리하는 서비스
- 지금 docker-compose.yml로 로컬에서 컨테이너를 띄우는데, ECS는 이걸 클라우드에서 해줌

**왜 ECS를 선택했나**
- 지금 Docker Compose로 컨테이너를 관리하는 구조를 그대로 AWS에서 실행 가능
- Fargate 옵션을 쓰면 서버 관리 없이 컨테이너만 올릴 수 있음
- 컨테이너가 죽으면 자동으로 재시작

**면접 설명 방법**
> "현재 Docker Compose로 컨테이너를 관리하는데, 이 구조 그대로 Amazon ECS에 올릴 수 있습니다. Fargate를 쓰면 서버 없이 컨테이너만 관리할 수 있어서 선택했습니다."

---

#### Amazon QuickSight (현재: visualize.py)

**QuickSight가 뭐냐**
- AWS에서 제공하는 BI(Business Intelligence) 대시보드 도구
- 지금 visualize.py 스크립트를 직접 실행해야 차트가 생성되는데
- QuickSight는 RDS에 연결해두면 자동으로 실시간 대시보드를 보여줌

**왜 QuickSight를 선택했나**
- RDS(PostgreSQL)에 직접 연결 가능
- 스크립트 실행 없이 실시간으로 데이터 확인 가능
- 비개발자도 드래그앤드롭으로 차트 만들 수 있음

**면접 설명 방법**
> "현재는 visualize.py 스크립트를 수동으로 실행해야 차트가 생성됩니다. Amazon QuickSight를 RDS에 연결하면 별도 코드 없이 실시간 대시보드를 볼 수 있어서 선택했습니다."

---

### 면접에서 AWS 아키텍처 질문 받으면

**Q. AWS 아키텍처를 설명해주세요.**

> "현재 구현은 로컬 환경에서 Docker Compose로 실행됩니다. 실제 서비스로 운영한다면 각 컴포넌트를 AWS 서비스로 대체할 수 있습니다. PostgreSQL은 관리형 데이터베이스인 RDS로, 이벤트 수집 함수는 서버리스인 Lambda로, 컨테이너 실행은 ECS로, 시각화는 QuickSight로 이전할 수 있습니다. 이렇게 하면 서버 관리 부담 없이 확장 가능한 구조가 됩니다."

**Q. 서버리스가 뭔가요? (Lambda 관련)**

> "서버리스는 서버가 없다는 게 아니라, 개발자가 서버를 직접 관리하지 않아도 된다는 뜻입니다. AWS Lambda는 코드(함수)만 올려두면 필요할 때 자동으로 실행되고, 실행된 만큼만 비용을 냅니다."

---

## 핵심 키워드 정리

| 키워드 | 설명 |
|--------|------|
| 이벤트 로그 | 시스템에서 발생하는 행동 기록 (클릭, 재생, 에러 등) |
| 파이프라인 | 데이터가 단계별로 흘러가는 흐름 |
| UUID | 전 세계적으로 고유한 ID |
| psycopg2 | Python에서 PostgreSQL 연결하는 라이브러리 |
| f-string | 문자열 안에 변수 넣는 Python 문법 |
| PRIMARY KEY | 테이블에서 각 행을 고유하게 식별하는 컬럼 |
| FOREIGN KEY | 다른 테이블의 컬럼을 참조하는 컬럼 (REFERENCES) |
| GROUP BY | 같은 값끼리 묶어서 집계 |
| healthcheck | 컨테이너가 정상 동작하는지 주기적으로 확인 |
| depends_on | 특정 서비스가 준비된 후에 실행되도록 설정 |
| 가상환경(venv) | 프로젝트별 독립된 Python 패키지 환경 |
| AWS | Amazon Web Services, 아마존 클라우드 서비스 |
| RDS | Relational Database Service, 관리형 DB 서비스 |
| Lambda | 서버 없이 함수만 실행하는 서비스 (서버리스) |
| ECS | Elastic Container Service, 컨테이너 실행 관리 |
| QuickSight | AWS BI 대시보드 도구 |
| 서버리스 | 서버를 직접 관리하지 않고 코드만 올리는 방식 |
| 아키텍처 | 서비스들을 어떻게 연결할지 설계도 |
