#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
현재 시간에 테스트 스케줄 추가
"""

import json
import os
from datetime import datetime, timedelta
import pytz

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

def get_korean_time():
    """한국 시간을 반환"""
    return datetime.now(KST)

def add_test_schedule():
    """현재 시간에 테스트 스케줄 추가"""
    current_time = get_korean_time()
    
    # 현재 시간 + 1분 후에 테스트 스케줄 추가
    test_time = current_time + timedelta(minutes=1)
    
    schedule_data = {
        "id": f"test_{test_time.strftime('%Y%m%d_%H%M')}",
        "date": test_time.strftime("%Y-%m-%d"),
        "hour": test_time.hour,
        "minute": test_time.minute,
        "time": test_time.strftime("%H:%M"),
        "channel": "테스트채널",
        "program_name": "로그테스트",
        "message": f"[TEST] 로그 테스트 - {test_time.strftime('%H:%M')}",
        "active": True,
        "sent": False,
        "created_at": current_time.isoformat()
    }
    
    # 기존 스케줄 로드
    if os.path.exists("tv_schedules.json"):
        with open("tv_schedules.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {"schedules": []}
    
    # 새 스케줄 추가
    data["schedules"].append(schedule_data)
    
    # 저장
    with open("tv_schedules.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"[SUCCESS] 테스트 스케줄 추가됨: {test_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"[INFO] 스케줄 ID: {schedule_data['id']}")
    print(f"[INFO] 메시지: {schedule_data['message']}")

if __name__ == "__main__":
    add_test_schedule()
