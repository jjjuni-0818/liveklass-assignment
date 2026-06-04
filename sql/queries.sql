-- 쿼리 1: 이벤트 타입별 발생 횟수
SELECT event_type, COUNT(*)
FROM events
GROUP BY event_type;

-- 쿼리 2: 유저별 총 이벤트 수 (많은 순)
SELECT user_id, COUNT(*)
FROM events
GROUP BY user_id
ORDER BY COUNT(*) DESC;

-- 쿼리 3: 강의별 평균 시청 시간 (긴 순)
SELECT video_id, AVG(watch_seconds)
FROM video_play_events
GROUP BY video_id
ORDER BY AVG(watch_seconds) DESC;
