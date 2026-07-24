# Daily Board EXE 자동 종료 버전

## 동작
- `DailyBoard.exe` 실행 시 콘솔 창 없이 로컬 서버가 시작됩니다.
- 기본 브라우저에서 Daily Board가 열립니다.
- 페이지는 2초마다 서버에 생존 신호를 보냅니다.
- 탭 또는 브라우저가 닫혀 8초 동안 신호가 없으면 EXE와 서버가 자동 종료됩니다.
- `pagehide` 이벤트가 정상 전달되면 거의 즉시 종료됩니다.

## 빌드
1. `build-exe.bat` 실행
2. `dist\DailyBoard.exe` 생성
3. 생성된 EXE 실행

## 주의
브라우저의 탭 복원, 절전, 디버거 중단 등으로 JavaScript가 8초 이상 멈추면
서버가 종료될 수 있습니다. 필요하면 `daily_board_launcher.pyw`의
`HEARTBEAT_TIMEOUT_SECONDS` 값을 늘리세요.

이 방식에서는 `stop-daily-board.bat`이 실제로 실행되는 것이 아니라,
동일한 결과로 EXE 프로세스와 HTTP 서버가 자체 종료됩니다.
