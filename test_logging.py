#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로그 테스트 스크립트
"""

import sys
import time
from datetime import datetime
import pytz

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

def get_korean_time():
    """한국 시간을 반환"""
    return datetime.now(KST)

def test_logging():
    """로그 테스트"""
    print("=== 로그 테스트 시작 ===")
    
    for i in range(5):
        current_time = get_korean_time()
        print(f"[TEST {i+1}] 현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(2)
    
    print("=== 로그 테스트 완료 ===")

if __name__ == "__main__":
    test_logging()
