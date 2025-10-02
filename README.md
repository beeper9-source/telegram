# TV 방송 스케줄 텔레그램 알림 시스템

TV 방송 스케줄을 관리하고 지정된 시간에 텔레그램으로 알림을 전송하는 웹 애플리케이션입니다.

## 🚀 주요 기능

- **TV 방송 스케줄 관리**: 날짜, 시간(1분 단위), 채널, 방송명 설정
- **자동 알림 전송**: 설정된 시간에 자동으로 텔레그램 메시지 전송
- **사용자 관리**: 수신자 추가/삭제/활성화 관리
- **웹 인터페이스**: Streamlit 기반 사용자 친화적 UI
- **실시간 모니터링**: 스케줄 상태 및 전송 결과 확인

## 📋 설치 방법

1. **필요한 패키지 설치**:
```bash
pip install -r requirements_tv_scheduler.txt
```

2. **텔레그램 봇 생성**:
   - [@BotFather](https://t.me/BotFather)에게 `/newbot` 명령어 전송
   - 봇 이름과 사용자명 설정
   - 받은 토큰을 복사

3. **채팅 ID 확인**:
   - [@userinfobot](https://t.me/userinfobot)에게 메시지 전송
   - 본인의 채팅 ID 확인

4. **설정 파일 수정**:
   - `config.py` 파일에서 `BOT_TOKEN`과 `CHAT_IDS` 설정

## 🚀 사용 방법

### 로컬 실행

1. **웹 인터페이스 실행**:
```bash
streamlit run tv_scheduler_1minute.py --server.port 8505
```

2. **백그라운드 스케줄 서비스 실행**:
```bash
python schedule_service_server.py
```

### 서버 배포 (Streamlit Cloud)

1. **GitHub에 코드 업로드**
2. **Streamlit Cloud에서 앱 배포**:
   - Repository: `your-username/your-repo`
   - Main file path: `tv_scheduler_1minute.py`
   - Python version: 3.8+

3. **환경 변수 설정**:
   - `BOT_TOKEN`: 텔레그램 봇 토큰
   - `CHAT_IDS`: 수신자 채팅 ID들 (JSON 배열)

4. **서버에서 백그라운드 서비스 실행**:
```bash
nohup python schedule_service_server.py &
```

## 📁 파일 구조

```
telegram/
├── README.md                      # 사용법 안내
├── config.py                      # 봇 토큰 및 채팅 ID 설정
├── telegram_sender.py             # 텔레그램 메시지 전송 핵심 기능
├── tv_scheduler_1minute.py       # TV 스케줄러 웹 인터페이스
├── schedule_service_server.py     # 서버용 백그라운드 스케줄 서비스
├── users.json                     # 사용자 데이터
├── tv_schedules.json             # 스케줄 데이터
├── requirements_tv_scheduler.txt  # 필요한 패키지 목록
└── run_schedule_service_server.bat # 서버용 실행 배치 파일
```

## 🔧 주요 컴포넌트

### TVScheduler 클래스
- 스케줄 추가/삭제/수정
- 스케줄 상태 관리 (활성화/비활성화)
- 다가오는 방송 알림 표시

### ScheduleService 클래스
- 백그라운드에서 매분마다 스케줄 확인
- 자동 메시지 전송
- 전송 완료 상태 업데이트

### TelegramSender 클래스
- 텔레그램 API 연동
- 다중 수신자 메시지 전송
- 오류 처리 및 로깅

## ⚠️ 주의사항

- 봇 토큰은 절대 공개하지 마세요
- 채팅 ID는 숫자로 입력하세요 (문자열 아님)
- 서버 배포 시 백그라운드 서비스가 실행되어야 자동 전송됩니다
- 스케줄은 설정된 시간의 ±1분 내에 전송됩니다

## 🎯 사용 예시

1. **웹 인터페이스 접속**: http://localhost:8505
2. **스케줄 추가**: 날짜, 시간, 채널, 방송명 입력
3. **자동 전송**: 설정된 시간에 자동으로 텔레그램 메시지 전송
4. **수동 전송**: "지금 전송" 버튼으로 즉시 전송 가능

## 🛠️ 문제 해결

### 서버 배포 시 오류
- `ModuleNotFoundError: No module named 'schedule'`: `schedule_service_server.py` 사용
- 포트 충돌: 다른 포트 번호 사용 (`--server.port 8506`)

### 메시지 전송 실패
- 봇과 사용자가 대화를 시작했는지 확인
- 채팅 ID가 올바른지 확인
- 봇 토큰이 유효한지 확인

## 📞 지원

문제가 발생하면 다음을 확인하세요:
1. `config.py`의 봇 토큰과 채팅 ID 설정
2. 텔레그램 봇과의 대화 시작 여부
3. 네트워크 연결 상태
4. 백그라운드 서비스 실행 여부