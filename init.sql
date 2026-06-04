-- 공통 이벤트 테이블
CREATE TABLE events (
    event_id  UUID PRIMARY KEY,
    event_type TEXT NOT NULL,
    user_id   TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL
);

-- 영상 재생 이벤트 테이블
CREATE TABLE video_play_events (
    event_id      UUID REFERENCES events(event_id),
    video_id      TEXT,
    course_id     TEXT,
    watch_seconds INTEGER
);

-- 에러 이벤트 테이블
CREATE TABLE error_events (
    event_id      UUID REFERENCES events(event_id),
    error_code    INTEGER,
    error_message TEXT,
    page_url      TEXT
);