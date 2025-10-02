#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동 발송 테스트
"""

import json
import pytz
from datetime import datetime
from telegram_sender import TelegramSender

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

def get_korean_time():
    """한국 시간을 반환"""
    return datetime.now(KST)

class UserManager:
    def __init__(self, data_file="users.json"):
        self.data_file = data_file
        self.users = self.load_users()
    
    def load_users(self):
        import os
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {"users": []}
        return {"users": []}
    
    def get_active_user_ids(self):
        return [user["id"] for user in self.users["users"] if user["active"]]

def test_auto_send():
    """자동 발송 테스트"""
    telegram_sender = TelegramSender()
    user_manager = UserManager()
    
    # 스케줄 데이터 로드
    with open('tv_schedules.json', 'r', encoding='utf-8') as f:
        schedules = json.load(f)
    
    current_time = get_korean_time()
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
            
            # 한국 시간대로 변환
            schedule_datetime = KST.localize(schedule_datetime)
            
            print(f"📅 스케줄 시간: {schedule_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 현재 시간과 비교 (1분 오차 허용)
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
                    with open('tv_schedules.json', 'w', encoding='utf-8') as f:
                        json.dump(schedules, f, ensure_ascii=False, indent=2)
                    print("💾 스케줄 상태 업데이트 완료")
                else:
                    print("⚠️ 활성 사용자가 없습니다.")
            else:
                print(f"⏳ 아직 시간이 안됨 (차이: {time_diff:.0f}초)")
                
        except ValueError as e:
            print(f"❌ 시간 파싱 오류: {e}")

if __name__ == "__main__":
    test_auto_send()
