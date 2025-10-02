# 텔레그램 메시지 전송 프로그램

텔레그램 봇을 통해 메시지, 사진, 문서를 전송할 수 있는 Python 프로그램입니다.

## 🚀 기능

- 텍스트 메시지 전송
- 사진 전송 (캡션 포함)
- 문서 전송 (캡션 포함)
- HTML/Markdown 포맷 지원
- 봇 업데이트 확인

## 📋 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 텔레그램 봇 생성:
   - [@BotFather](https://t.me/BotFather)에게 `/newbot` 명령어 전송
   - 봇 이름과 사용자명 설정
   - 받은 토큰을 복사

3. 채팅 ID 확인:
   - [@userinfobot](https://t.me/userinfobot)에게 메시지 전송
   - 본인의 채팅 ID 확인

4. 설정 파일 수정:
   - `config.py` 파일에서 `BOT_TOKEN`과 `CHAT_ID` 설정

## 🔧 사용 방법

### 기본 사용법

```python
from telegram_sender import TelegramSender

# 전송 객체 생성
sender = TelegramSender()

# 텍스트 메시지 전송
sender.send_message("안녕하세요! 🚀")

# HTML 포맷으로 메시지 전송
sender.send_message("<b>굵은 글씨</b>와 <i>기울임</i> 텍스트")

# 사진 전송
sender.send_photo("photo.jpg", "사진 설명")

# 문서 전송
sender.send_document("document.pdf", "문서 설명")
```

### 직접 실행

```bash
python telegram_sender.py
```

## 📁 파일 구조

```
telegram/
├── README.md              # 사용법 안내
├── config.py              # 봇 토큰 및 채팅 ID 설정
├── telegram_sender.py     # 메인 프로그램
└── requirements.txt       # 필요한 패키지 목록
```

## ⚠️ 주의사항

- 봇 토큰은 절대 공개하지 마세요
- 채팅 ID는 숫자로 시작하는 경우 따옴표 없이 입력하세요
- 파일 전송 시 파일 경로가 올바른지 확인하세요

## 🎯 예시

```python
# 다양한 메시지 전송 예시
sender = TelegramSender()

# 기본 메시지
sender.send_message("일반 메시지입니다.")

# HTML 포맷 메시지
sender.send_message("""
<b>제목</b>
<i>기울임 텍스트</i>
<code>코드 블록</code>
<a href="https://example.com">링크</a>
""")

# 사진과 함께 메시지
sender.send_photo("screenshot.png", "프로그램 실행 결과")

# 문서 전송
sender.send_document("report.pdf", "월간 보고서")
```

## 📞 지원

문제가 발생하면 다음을 확인해주세요:
1. 봇 토큰이 올바른지 확인
2. 채팅 ID가 정확한지 확인
3. 인터넷 연결 상태 확인
4. 파일 경로가 올바른지 확인
