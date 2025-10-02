#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
테스트 스케줄 추가
"""

import json
from datetime import datetime, timedelta


def add_test_schedule():
    """테스트용 스케줄 추가"""
    now = datetime.now()
    test_time = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
    
    test_schedule = {
        "id": f"test_{test_time.strftime('%Y%m%d_%H%M')}",
        "date": test_time.strftime("%Y-%m-%d"),
        "hour": test_time.hour,
        "minute": test_time.minute,
        "time": test_time.strftime("%H:%M"),
        "channel": "테스트채널",
        "program_name": "테스트방송",
        "message": f"🧪 테스트 메시지 - {test_time.strftime('%H:%M')}",
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
    
    print(f"✅ 테스트 스케줄 추가: {test_time.strftime('%Y-%m-%d %H:%M')}")


if __name__ == "__main__":
    add_test_schedule()
