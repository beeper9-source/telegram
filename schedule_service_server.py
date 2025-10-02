#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TV 방송 스케줄 백그라운드 서비스 (서버용 - schedule 라이브러리 없이)
"""

import time
import json
import os
import threading
from datetime import datetime
from telegram_sender import TelegramSender
import pytz

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
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {"users": []}
        return {"users": []}
    
    def get_active_user_ids(self):
        return [user["id"] for user in self.users["users"] if user["active"]]


class ScheduleService:
    def __init__(self):
        self.telegram_sender = TelegramSender()
        self.user_manager = UserManager()
        self.data_file = "tv_schedules.json"
        self.running = False
        self.check_thread = None
    
    def load_schedules(self):
        """스케줄 데이터 로드"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {"schedules": []}
        return {"schedules": []}
    
    def save_schedules(self, schedules):
        """스케줄 데이터 저장"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(schedules, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ 스케줄 저장 실패: {e}")
            return False
    
    def check_and_send_messages(self):
        """현재 시간에 맞는 메시지들을 확인하고 전송"""
        schedules = self.load_schedules()
        current_time = get_korean_time()
        
        print(f"🔍 스케줄 확인 중... 현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📋 총 스케줄 수: {len(schedules['schedules'])}")
        
        active_schedules = [s for s in schedules["schedules"] if s["active"] and not s["sent"]]
        print(f"⏰ 활성 스케줄 수: {len(active_schedules)}")
        
        for i, schedule_item in enumerate(schedules["schedules"]):
            print(f"\n--- 스케줄 {i+1}: {schedule_item['program_name']} ---")
            print(f"📅 날짜: {schedule_item['date']}")
            print(f"⏰ 시간: {schedule_item['time']}")
            print(f"🟢 활성화: {schedule_item['active']}")
            print(f"📤 전송완료: {schedule_item['sent']}")
            
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
                    print(f"🚀 전송 조건 만족! 방송 알림 전송 시작...")
                    print(f"📺 방송명: {schedule_item['program_name']}")
                    print(f"📺 채널: {schedule_item['channel']}")
                    
                    # 메시지 전송
                    active_users = self.user_manager.get_active_user_ids()
                    print(f"👥 활성 사용자: {active_users}")
                    
                    if active_users:
                        results = self.telegram_sender.send_message_to_multiple(
                            schedule_item["message"], 
                            active_users
                        )
                        
                        success_count = sum(1 for r in results if r["success"])
                        print(f"✅ 전송 완료: {success_count}/{len(active_users)}명")
                        
                        # 전송 완료 표시
                        schedule_item["sent"] = True
                        self.save_schedules(schedules)
                        print("💾 스케줄 상태 업데이트 완료")
                    else:
                        print("⚠️ 활성 사용자가 없습니다.")
                else:
                    print(f"⏳ 아직 시간이 안됨 (차이: {time_diff:.0f}초)")
                        
            except ValueError as e:
                print(f"❌ 스케줄 시간 파싱 오류: {e}")
                continue
            except Exception as e:
                print(f"❌ 예상치 못한 오류: {e}")
                continue
    
    def schedule_checker(self):
        """스케줄 체크를 위한 백그라운드 스레드"""
        while self.running:
            try:
                self.check_and_send_messages()
                # 60초 대기 (매분 체크)
                time.sleep(60)
            except Exception as e:
                print(f"❌ 스케줄 체크 오류: {e}")
                time.sleep(60)  # 오류 발생 시에도 계속 실행
    
    def start_service(self):
        """서비스 시작"""
        print("🚀 TV 방송 스케줄 서비스 시작...")
        print("⏰ 매분마다 스케줄을 확인합니다.")
        
        self.running = True
        
        # 백그라운드 스레드 시작
        self.check_thread = threading.Thread(target=self.schedule_checker, daemon=True)
        self.check_thread.start()
        
        # 메인 스레드는 대기
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_service()
    
    def stop_service(self):
        """서비스 중지"""
        print("⏹️ TV 방송 스케줄 서비스 중지...")
        self.running = False
        if self.check_thread:
            self.check_thread.join(timeout=5)


def main():
    """메인 함수"""
    service = ScheduleService()
    
    try:
        service.start_service()
    except KeyboardInterrupt:
        service.stop_service()
    except Exception as e:
        print(f"❌ 서비스 오류: {e}")
        service.stop_service()


if __name__ == "__main__":
    main()
