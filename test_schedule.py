#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
스케줄 서비스 테스트
"""

import json
import os
from datetime import datetime, timedelta
from telegram_sender import TelegramSender


class UserManager:
    def __init__(self, data_file="users.json"):
        self.data_file = data_file
        self.users = self.load_users()
    
    def load_users(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {"users": []}
        return {"users": []}
    
    def get_active_user_ids(self):
        return [user["id"] for user in self.users["users"] if user["active"]]


def test_schedule_check():
    """스케줄 체크 테스트"""
    telegram_sender = TelegramSender()
    user_manager = UserManager()
    
    # 스케줄 데이터 로드
    data_file = "tv_schedules.json"
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            schedules = json.load(f)
    else:
        schedules = {"schedules": []}
    
    current_time = datetime.now()
    print(f"🔍 현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📋 총 스케줄 수: {len(schedules['schedules'])}")
    
    for i, schedule_item in enumerate(schedules["schedules"]):
        print(f"\n--- 스케줄 {i+1} ---")
        print(f"ID: {schedule_item['id']}")
        print(f"날짜: {schedule_item['date']}")
        print(f"시간: {schedule_item['time']}")
        print(f"활성화: {schedule_item['active']}")
        print(f"전송완료: {schedule_item['sent']}")
        
        if not schedule_item["active"] or schedule_item["sent"]:
            print("⏭️ 건너뜀 (비활성화 또는 전송완료)")
            continue
        
        try:
            # 스케줄 시간 파싱
            schedule_datetime = datetime.strptime(
                f"{schedule_item['date']} {schedule_item['time']}", 
                "%Y-%m-%d %H:%M"
            )
            
            print(f"📅 스케줄 시간: {schedule_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 현재 시간과 비교
            time_diff = abs((current_time - schedule_datetime).total_seconds())
            print(f"⏰ 시간 차이: {time_diff:.0f}초")
            
            if time_diff <= 60:  # 1분 이내
                print("🚀 전송 조건 만족!")
                
                # 활성 사용자 확인
                active_users = user_manager.get_active_user_ids()
                print(f"👥 활성 사용자: {active_users}")
                
                if active_users:
                    print("📤 메시지 전송 시도...")
                    results = telegram_sender.send_message_to_multiple(
                        schedule_item["message"], 
                        active_users
                    )
                    
                    success_count = sum(1 for r in results if r["success"])
                    print(f"✅ 전송 결과: {success_count}/{len(active_users)}명 성공")
                    
                    # 전송 완료 표시
                    schedule_item["sent"] = True
                    
                    # 파일 저장
                    with open(data_file, 'w', encoding='utf-8') as f:
                        json.dump(schedules, f, ensure_ascii=False, indent=2)
                    print("💾 스케줄 상태 업데이트 완료")
                else:
                    print("⚠️ 활성 사용자가 없습니다.")
            else:
                print(f"⏳ 아직 시간이 안됨 (차이: {time_diff:.0f}초)")
                
        except ValueError as e:
            print(f"❌ 시간 파싱 오류: {e}")


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
    data_file = "tv_schedules.json"
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            schedules = json.load(f)
    else:
        schedules = {"schedules": []}
    
    # 테스트 스케줄 추가
    schedules["schedules"].append(test_schedule)
    
    # 저장
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(schedules, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 테스트 스케줄 추가: {test_time.strftime('%Y-%m-%d %H:%M')}")


if __name__ == "__main__":
    print("🧪 스케줄 서비스 테스트")
    print("=" * 50)
    
    # 테스트 스케줄 추가
    add_test_schedule()
    
    # 스케줄 체크 테스트
    test_schedule_check()
