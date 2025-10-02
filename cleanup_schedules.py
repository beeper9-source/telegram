#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
과거 스케줄 정리 스크립트
"""

import json
import os
from datetime import datetime


def cleanup_old_schedules():
    """과거 스케줄 정리"""
    data_file = "tv_schedules.json"
    
    if not os.path.exists(data_file):
        print("❌ 스케줄 파일이 없습니다.")
        return
    
    # 스케줄 로드
    with open(data_file, 'r', encoding='utf-8') as f:
        schedules = json.load(f)
    
    current_time = datetime.now()
    print(f"🔍 현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📋 정리 전 스케줄 수: {len(schedules['schedules'])}")
    
    # 과거 스케줄 필터링 (24시간 이전)
    cleaned_schedules = []
    removed_count = 0
    
    for schedule in schedules["schedules"]:
        try:
            schedule_datetime = datetime.strptime(
                f"{schedule['date']} {schedule['time']}", 
                "%Y-%m-%d %H:%M"
            )
            
            # 24시간 이전 스케줄은 제거
            if (current_time - schedule_datetime).total_seconds() > 24 * 60 * 60:
                print(f"🗑️ 제거: {schedule['program_name']} ({schedule['time']})")
                removed_count += 1
            else:
                cleaned_schedules.append(schedule)
                
        except ValueError as e:
            print(f"❌ 시간 파싱 오류: {e}")
            # 파싱 오류가 있는 스케줄도 제거
            removed_count += 1
    
    # 정리된 스케줄 저장
    schedules["schedules"] = cleaned_schedules
    
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(schedules, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 정리 완료: {removed_count}개 제거, {len(cleaned_schedules)}개 유지")


if __name__ == "__main__":
    cleanup_old_schedules()
