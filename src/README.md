# Daily Board 모듈 구조

- `index.html`: 화면 마크업
- `assets/css/styles.css`: 전체 스타일
- `assets/js/app.js`: 앱 초기화 및 주기 작업
- `assets/js/config.js`: 공통 상수
- `assets/js/utils/date.js`: 날짜/시간 유틸리티
- `assets/js/features/autostart.js`: Windows 자동 실행 연동
- `assets/js/features/theme.js`: 라이트/다크/일출·일몰 자동 테마
- `assets/js/features/fullscreen.js`: 전체화면 제어
- `assets/js/features/clock-calendar.js`: 시계 및 월간 달력
- `assets/js/features/tabs.js`: 세로 스와이프 및 자동 탭 전환
- `assets/js/features/fuel.js`: 오피넷 유가 조회·표시
- `assets/js/features/watchdog.js`: 로컬 서버 watchdog 및 종료 알림

## 실행 주의사항

ES Module을 사용하므로 `file://`로 직접 열기보다 기존 Daily Board 로컬 서버 또는 일반 HTTP 서버에서 `index.html`을 제공해야 합니다. 기존 서버 엔드포인트(`/__autostart__`, `/__opinet__`, `/__heartbeat__`, `/__closed__`)는 그대로 유지했습니다.
