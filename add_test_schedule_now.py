#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
현재 시간 + 1분에 테스트 스케줄 추가
"""

import json
import pytz
from datetime import datetime, timedelta

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

def get_korean_time():
    """한국 시간을 반환"""
    return datetime.now(KST)

def add_test_schedule():
    """현재 시간 + 1분에 테스트 스케줄 추가"""
    now = get_korean_time()
    test_time = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
    
    test_schedule = {
        "id": f"test_{test_time.strftime('%Y%m%d_%H%M')}",
        "date": test_time.strftime("%Y-%m-%d"),
        "hour": test_time.hour,
        "minute": test_time.minute,
        "time": test_time.strftime("%H:%M"),
        "channel": "테스트채널",
        "program_name": "자동발송테스트",
        "message": f"🚀 자동 발송 테스트 - {test_time.strftime('%H:%M')}",
        "active": True,
        "sent": False,
        "created_at": now.isoformat()
    }
    
    # 기존 스케줄 로드
    with open('tv_schedules.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 테스트 스케줄 추가
    data["schedules"].append(test_schedule)
    
    # 저장
    with open('tv_schedules.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 테스트 스케줄 추가 완료!")
    print(f"📅 날짜: {test_time.strftime('%Y-%m-%d')}")
    print(f"⏰ 시간: {test_time.strftime('%H:%M')}")
    print(f"📺 방송명: 자동발송테스트")
    print(f"🕐 현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏳ 발송 예정: {test_time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    add_test_schedule()
