#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TV 방송 스케줄 텔레그램 메시지 전송 프로그램 (1분단위 시간 입력 지원)
"""

import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime, timedelta
import time
import threading
from telegram_sender import TelegramSender
import pytz
import subprocess
import queue
import sys

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

def get_korean_time():
    """한국 시간을 반환"""
    return datetime.now(KST)


class LogMonitor:
    """스케줄 서비스 로그 모니터링 클래스"""
    def __init__(self):
        self.log_queue = queue.Queue()
        self.process = None
        self.monitoring = False
        self.logs = []
        self.max_logs = 100  # 최대 로그 개수
    
    def start_monitoring(self):
        """로그 모니터링 시작"""
        if self.monitoring:
            return True, "이미 모니터링 중입니다."
        
        try:
            # 스케줄 서비스 프로세스 시작
            self.process = subprocess.Popen(
                [sys.executable, "schedule_service_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=0,  # 버퍼링 비활성화
                encoding='utf-8',  # 명시적 인코딩
                errors='replace'  # 인코딩 오류 처리
            )
            
            self.monitoring = True
            
            # 로그 읽기 스레드 시작
            log_thread = threading.Thread(target=self._read_logs, daemon=True)
            log_thread.start()
            
            # 초기 로그 추가
            timestamp = get_korean_time().strftime('%H:%M:%S')
            self.logs.append(f"[{timestamp}] [SYSTEM] 로그 모니터링 시작됨")
            
            return True, "로그 모니터링이 시작되었습니다."
        except Exception as e:
            self.monitoring = False
            self.process = None
            return False, f"로그 모니터링 시작 실패: {e}"
    
    def stop_monitoring(self):
        """로그 모니터링 중지"""
        if not self.monitoring:
            return True, "모니터링이 이미 중지되어 있습니다."
        
        self.monitoring = False
        
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                try:
                    self.process.kill()
                except:
                    pass
            finally:
                self.process = None
        
        return True, "로그 모니터링이 중지되었습니다."
    
    def _read_logs(self):
        """로그를 읽어서 큐에 저장"""
        while self.monitoring and self.process:
            try:
                line = self.process.stdout.readline()
                if line:
                    timestamp = get_korean_time().strftime('%H:%M:%S')
                    log_entry = f"[{timestamp}] {line.strip()}"
                    self.log_queue.put(log_entry)
                    
                    # 로그 개수 제한
                    if len(self.logs) >= self.max_logs:
                        self.logs.pop(0)
                    self.logs.append(log_entry)
                elif self.process.poll() is not None:
                    # 프로세스가 종료됨
                    timestamp = get_korean_time().strftime('%H:%M:%S')
                    self.logs.append(f"[{timestamp}] [SYSTEM] 프로세스가 종료됨")
                    self.monitoring = False
                    break
                else:
                    time.sleep(0.1)
            except Exception as e:
                timestamp = get_korean_time().strftime('%H:%M:%S')
                self.logs.append(f"[{timestamp}] [ERROR] 로그 읽기 오류: {e}")
                break
    
    def get_logs(self):
        """현재까지의 로그 반환"""
        return self.logs
    
    def is_monitoring(self):
        """모니터링 상태 확인"""
        if not self.monitoring or self.process is None:
            return False
        
        # 프로세스가 실제로 실행 중인지 확인
        try:
            if self.process.poll() is not None:  # 프로세스가 종료됨
                self.monitoring = False
                self.process = None
                return False
        except:
            self.monitoring = False
            self.process = None
            return False
        
        return True


# 페이지 설정
st.set_page_config(
    page_title="TV 방송 스케줄러",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #ff6b6b;
        text-align: center;
        margin-bottom: 2rem;
    }
    .schedule-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff6b6b;
        margin-bottom: 1rem;
    }
    .channel-badge {
        background-color: #007bff;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
    }
    .time-badge {
        background-color: #28a745;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
    }
    .program-badge {
        background-color: #ffc107;
        color: black;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
    }
    .time-input-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)


class UserManager:
    def __init__(self, data_file="users.json"):
        self.data_file = data_file
        self.users = self.load_users()
    
    def load_users(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 데이터 구조 검증
                    if "users" not in data:
                        data = {"users": []}
                    return data
            except (json.JSONDecodeError, FileNotFoundError) as e:
                st.warning(f"사용자 데이터 로드 오류: {e}")
                return {"users": []}
        return {"users": []}
    
    def save_users(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            st.error(f"❌ 사용자 데이터 저장 실패: {e}")
            return False
    
    def add_user(self, user_id, name=""):
        # 중복 확인
        for user in self.users["users"]:
            if user["id"] == user_id:
                return False, f"사용자 ID {user_id}는 이미 등록되어 있습니다."
        
        new_user = {
            "id": user_id,
            "name": name,
            "active": True
        }
        
        self.users["users"].append(new_user)
        
        if self.save_users():
            return True, f"사용자 {name} ({user_id})가 성공적으로 추가되었습니다!"
        else:
            return False, f"사용자 추가에 실패했습니다."
    
    def remove_user(self, user_id):
        for i, user in enumerate(self.users["users"]):
            if user["id"] == user_id:
                removed_user = self.users["users"].pop(i)
                if self.save_users():
                    return True, f"사용자 {removed_user['name']} ({user_id})가 제거되었습니다."
                else:
                    return False, f"사용자 제거에 실패했습니다."
        
        return False, f"사용자 ID {user_id}를 찾을 수 없습니다."
    
    def get_active_user_ids(self):
        return [user["id"] for user in self.users["users"] if user["active"]]
    
    def toggle_user_status(self, user_id):
        for user in self.users["users"]:
            if user["id"] == user_id:
                user["active"] = not user["active"]
                status = "활성화" if user["active"] else "비활성화"
                if self.save_users():
                    return True, f"사용자 {user['name']} ({user_id}) 상태 변경: {status}"
                else:
                    return False, f"사용자 상태 변경에 실패했습니다."
        
        return False, f"사용자 ID {user_id}를 찾을 수 없습니다."


class TVScheduler:
    def __init__(self, data_file="tv_schedules.json"):
        self.data_file = data_file
        self.schedules = self.load_schedules()
        self.telegram_sender = TelegramSender()
        self.user_manager = UserManager()
    
    def load_schedules(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {"schedules": []}
        return {"schedules": []}
    
    def save_schedules(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.schedules, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            st.error(f"❌ 스케줄 저장 실패: {e}")
            return False
    
    def add_schedule(self, date, hour, minute, channel, program_name, message=""):
        # 중복 확인
        time_str = f"{hour:02d}:{minute:02d}"
        schedule_id = f"{date}_{time_str}_{channel}_{program_name}"
        
        for schedule in self.schedules["schedules"]:
            if schedule["id"] == schedule_id:
                return False, "동일한 스케줄이 이미 존재합니다."
        
        if not message:
            message = f"📺 {channel}에서 '{program_name}' 방송이 시작됩니다!"
        
        new_schedule = {
            "id": schedule_id,
            "date": date,
            "hour": hour,
            "minute": minute,
            "time": time_str,
            "channel": channel,
            "program_name": program_name,
            "message": message,
            "active": True,
            "sent": False,
            "created_at": get_korean_time().isoformat()
        }
        
        self.schedules["schedules"].append(new_schedule)
        
        if self.save_schedules():
            return True, f"스케줄이 성공적으로 추가되었습니다: {program_name}"
        else:
            return False, "스케줄 추가에 실패했습니다."
    
    def remove_schedule(self, schedule_id):
        for i, schedule in enumerate(self.schedules["schedules"]):
            if schedule["id"] == schedule_id:
                removed_schedule = self.schedules["schedules"].pop(i)
                if self.save_schedules():
                    return True, f"스케줄이 제거되었습니다: {removed_schedule['program_name']}"
                else:
                    return False, f"스케줄 제거에 실패했습니다."
        
        return False, "스케줄을 찾을 수 없습니다."
    
    def toggle_schedule_status(self, schedule_id):
        for schedule in self.schedules["schedules"]:
            if schedule["id"] == schedule_id:
                schedule["active"] = not schedule["active"]
                status = "활성화" if schedule["active"] else "비활성화"
                if self.save_schedules():
                    return True, f"스케줄 상태 변경: {status}"
                else:
                    return False, f"스케줄 상태 변경에 실패했습니다."
        
        return False, "스케줄을 찾을 수 없습니다."
    
    def get_upcoming_schedules(self, days=7):
        """다가오는 스케줄들을 가져옵니다"""
        upcoming = []
        today = get_korean_time().date()
        
        for schedule in self.schedules["schedules"]:
            if not schedule["active"] or schedule["sent"]:
                continue
            
            try:
                schedule_date = datetime.strptime(schedule["date"], "%Y-%m-%d").date()
                schedule_datetime = datetime.strptime(f"{schedule['date']} {schedule['time']}", "%Y-%m-%d %H:%M")
                
                # 오늘부터 지정된 일수 내의 스케줄만
                if today <= schedule_date <= today + timedelta(days=days):
                    upcoming.append({
                        **schedule,
                        "datetime": schedule_datetime,
                        "is_today": schedule_date == today,
                        "is_tomorrow": schedule_date == today + timedelta(days=1)
                    })
            except ValueError:
                continue
        
        # 시간순으로 정렬
        upcoming.sort(key=lambda x: x["datetime"])
        return upcoming
    
    def send_scheduled_message(self, schedule):
        """스케줄된 메시지를 전송합니다"""
        active_users = self.user_manager.get_active_user_ids()
        
        if not active_users:
            return False, "활성 사용자가 없습니다."
        
        # 메시지 전송
        results = self.telegram_sender.send_message_to_multiple(schedule["message"], active_users)
        
        success_count = sum(1 for r in results if r["success"])
        
        # 전송 완료 표시
        for s in self.schedules["schedules"]:
            if s["id"] == schedule["id"]:
                s["sent"] = True
                break
        
        self.save_schedules()
        
        return success_count > 0, f"{success_count}/{len(active_users)}명에게 전송 완료"


# 세션 상태 초기화
if 'tv_scheduler' not in st.session_state:
    st.session_state.tv_scheduler = TVScheduler()

if 'page' not in st.session_state:
    st.session_state.page = "dashboard"

if 'log_monitor' not in st.session_state:
    st.session_state.log_monitor = LogMonitor()


def show_dashboard():
    """대시보드 페이지"""
    st.markdown('<h1 class="main-header">📺 TV 방송 스케줄러</h1>', unsafe_allow_html=True)
    
    # 실시간 시계 표시
    current_time = get_korean_time()
    
    # 시계를 위한 placeholder
    dashboard_clock = st.empty()
    with dashboard_clock.container():
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 2rem; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 1rem; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <h2 style="color: white; font-family: 'Courier New', monospace; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                🕐 {current_time.strftime('%Y-%m-%d %H:%M:%S')}
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    scheduler = st.session_state.tv_scheduler
    schedules = scheduler.schedules["schedules"]
    active_schedules = [s for s in schedules if s["active"] and not s["sent"]]
    
    # 메트릭 카드
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="📅 총 스케줄",
            value=f"{len(schedules)}개",
            delta=None
        )
    
    with col2:
        st.metric(
            label="⏰ 활성 스케줄",
            value=f"{len(active_schedules)}개",
            delta=None
        )
    
    with col3:
        upcoming = scheduler.get_upcoming_schedules(1)  # 오늘
        st.metric(
            label="📺 오늘 방송",
            value=f"{len(upcoming)}개",
            delta=None
        )
    
    # 오늘의 방송 스케줄
    st.subheader("📺 오늘의 방송 스케줄")
    
    today_schedules = scheduler.get_upcoming_schedules(1)
    
    if today_schedules:
        for schedule in today_schedules:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"""
                <div class="schedule-card">
                    <strong>{schedule['program_name']}</strong><br>
                    <span class="channel-badge">{schedule['channel']}</span>
                    <span class="time-badge">{schedule['time']}</span>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button("📤 지금 전송", key=f"send_{schedule['id']}"):
                    success, message = scheduler.send_scheduled_message(schedule)
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
                    st.rerun()
            
            with col3:
                if st.button("❌ 삭제", key=f"delete_{schedule['id']}"):
                    success, message = scheduler.remove_schedule(schedule['id'])
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                    st.rerun()
    else:
        st.info("오늘 예정된 방송이 없습니다.")
    
    # 빠른 작업
    st.subheader("⚡ 빠른 작업")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("➕ 새 스케줄 추가", use_container_width=True):
            st.session_state.page = "add_schedule"
            st.rerun()
    
    with col2:
        if st.button("📋 전체 스케줄 보기", use_container_width=True):
            st.session_state.page = "schedule_list"
            st.rerun()
    
    with col3:
        if st.button("⚙️ 설정", use_container_width=True):
            st.session_state.page = "settings"
            st.rerun()


def show_add_schedule():
    """스케줄 추가 페이지"""
    st.markdown('<h1 class="main-header">➕ 새 방송 스케줄 추가</h1>', unsafe_allow_html=True)
    
    # 실시간 시계 표시
    current_time = get_korean_time()
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 1rem; padding: 0.5rem; background-color: #e3f2fd; border-radius: 0.5rem;">
        <span style="color: #1976d2; font-family: 'Courier New', monospace; font-weight: bold;">
            🕐 현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("add_schedule_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📅 방송 정보")
            
            date = st.date_input(
                "방송 날짜",
                value=get_korean_time().date(),
                min_value=get_korean_time().date()
            )
            
            # 시간 입력을 1분단위로 변경
            st.markdown('<div class="time-input-container">', unsafe_allow_html=True)
            st.markdown("**⏰ 방송 시간**")
            
            time_col1, time_col2 = st.columns(2)
            
            with time_col1:
                hour = st.selectbox(
                    "시",
                    options=list(range(24)),
                    index=get_korean_time().hour,
                    format_func=lambda x: f"{x:02d}시"
                )
            
            with time_col2:
                minute = st.selectbox(
                    "분",
                    options=list(range(60)),  # 1분 단위로 변경 (00분~59분)
                    index=0,
                    format_func=lambda x: f"{x:02d}분"
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 시간 미리보기
            time_str = f"{hour:02d}:{minute:02d}"
            st.info(f"🕐 설정된 시간: **{time_str}**")
            
            channel = st.text_input(
                "채널명",
                placeholder="예: KBS1, MBC, SBS, tvN 등"
            )
            
            program_name = st.text_input(
                "방송명",
                placeholder="예: 뉴스데스크, 무한도전 등"
            )
        
        with col2:
            st.subheader("📝 메시지 설정")
            
            message = st.text_area(
                "전송할 메시지",
                placeholder="기본 메시지: 📺 {채널}에서 '{방송명}' 방송이 시작됩니다!",
                height=200,
                help="빈칸으로 두면 기본 메시지가 사용됩니다."
            )
            
            # 미리보기
            if channel and program_name:
                preview_message = message if message else f"📺 {channel}에서 '{program_name}' 방송이 시작됩니다!"
                st.markdown("**미리보기:**")
                st.info(preview_message)
        
        col_submit1, col_submit2 = st.columns(2)
        
        with col_submit1:
            if st.form_submit_button("✅ 스케줄 추가", use_container_width=True):
                if channel and program_name:
                    success, message = st.session_state.tv_scheduler.add_schedule(
                        date.strftime("%Y-%m-%d"),
                        hour,
                        minute,
                        channel,
                        program_name,
                        message
                    )
                    
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
                else:
                    st.error("채널명과 방송명을 입력하세요.")
        
        with col_submit2:
            if st.form_submit_button("❌ 취소", use_container_width=True):
                st.session_state.page = "dashboard"
                st.rerun()
    
    # 인기 채널 버튼
    st.subheader("📺 인기 채널 빠른 선택")
    
    popular_channels = ["KBS1", "KBS2", "MBC", "SBS", "tvN", "JTBC", "채널A", "MBN", "EBS", "KBS WORLD"]
    
    cols = st.columns(5)
    for i, channel in enumerate(popular_channels):
        with cols[i % 5]:
            if st.button(channel, key=f"channel_{channel}"):
                st.session_state.selected_channel = channel
                st.rerun()
    
    # 빠른 시간 설정 (더 세밀한 시간대 추가)
    st.subheader("⏰ 빠른 시간 설정")
    
    quick_times = [
        ("아침 뉴스", 7, 0),
        ("점심 뉴스", 12, 0),
        ("저녁 뉴스", 18, 0),
        ("뉴스데스크", 20, 0),
        ("심야 뉴스", 23, 0),
        ("드라마", 21, 0),
        ("예능", 22, 0),
        ("아침 7시 30분", 7, 30),
        ("점심 12시 30분", 12, 30),
        ("저녁 6시 30분", 18, 30),
        ("뉴스 8시 30분", 20, 30),
        ("드라마 9시 30분", 21, 30)
    ]
    
    quick_cols = st.columns(4)
    for i, (name, h, m) in enumerate(quick_times):
        with quick_cols[i % 4]:
            if st.button(f"{name}\n{h:02d}:{m:02d}", key=f"quick_{name}"):
                st.session_state.quick_hour = h
                st.session_state.quick_minute = m
                st.rerun()


def show_schedule_list():
    """스케줄 목록 페이지"""
    st.markdown('<h1 class="main-header">📋 전체 방송 스케줄</h1>', unsafe_allow_html=True)
    
    # 실시간 시계 표시
    current_time = get_korean_time()
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 1rem; padding: 0.5rem; background-color: #f3e5f5; border-radius: 0.5rem;">
        <span style="color: #7b1fa2; font-family: 'Courier New', monospace; font-weight: bold;">
            🕐 현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    scheduler = st.session_state.tv_scheduler
    schedules = scheduler.schedules["schedules"]
    
    if not schedules:
        st.info("등록된 스케줄이 없습니다.")
        if st.button("➕ 첫 번째 스케줄 추가"):
            st.session_state.page = "add_schedule"
            st.rerun()
        return
    
    # 필터 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_option = st.selectbox(
            "필터",
            ["전체", "활성", "비활성", "전송완료", "미전송"]
        )
    
    with col2:
        sort_option = st.selectbox(
            "정렬",
            ["날짜순", "시간순", "채널순", "방송명순"]
        )
    
    with col3:
        if st.button("🔄 새로고침"):
            st.rerun()
    
    # 필터링
    filtered_schedules = schedules.copy()
    
    if filter_option == "활성":
        filtered_schedules = [s for s in filtered_schedules if s["active"]]
    elif filter_option == "비활성":
        filtered_schedules = [s for s in filtered_schedules if not s["active"]]
    elif filter_option == "전송완료":
        filtered_schedules = [s for s in filtered_schedules if s["sent"]]
    elif filter_option == "미전송":
        filtered_schedules = [s for s in filtered_schedules if not s["sent"]]
    
    # 정렬
    if sort_option == "날짜순":
        filtered_schedules.sort(key=lambda x: (x["date"], x["time"]))
    elif sort_option == "시간순":
        filtered_schedules.sort(key=lambda x: x["time"])
    elif sort_option == "채널순":
        filtered_schedules.sort(key=lambda x: x["channel"])
    elif sort_option == "방송명순":
        filtered_schedules.sort(key=lambda x: x["program_name"])
    
    # 스케줄 표시
    for schedule in filtered_schedules:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            status_icon = "🟢" if schedule["active"] else "🔴"
            sent_icon = "✅" if schedule["sent"] else "⏳"
            
            st.markdown(f"""
            **{status_icon} {schedule['program_name']}** {sent_icon}<br>
            📺 {schedule['channel']} | 📅 {schedule['date']} {schedule['time']}
            """)
        
        with col2:
            if st.button("토글", key=f"toggle_{schedule['id']}"):
                success, message = scheduler.toggle_schedule_status(schedule['id'])
                if success:
                    st.success(message)
                else:
                    st.error(message)
                st.rerun()
        
        with col3:
            if st.button("전송", key=f"send_{schedule['id']}"):
                success, message = scheduler.send_scheduled_message(schedule)
                if success:
                    st.success(message)
                else:
                    st.error(message)
                st.rerun()
        
        with col4:
            if st.button("삭제", key=f"delete_{schedule['id']}"):
                success, message = scheduler.remove_schedule(schedule['id'])
                if success:
                    st.success(message)
                else:
                    st.error(message)
                st.rerun()
        
        st.markdown("---")


def show_settings():
    """설정 페이지"""
    st.markdown('<h1 class="main-header">⚙️ 설정</h1>', unsafe_allow_html=True)
    
    # 실시간 시계 표시
    current_time = get_korean_time()
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 1rem; padding: 0.5rem; background-color: #fff3e0; border-radius: 0.5rem;">
        <span style="color: #f57c00; font-family: 'Courier New', monospace; font-weight: bold;">
            🕐 현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    scheduler = st.session_state.tv_scheduler
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 통계")
        
        schedules = scheduler.schedules["schedules"]
        active_count = len([s for s in schedules if s["active"]])
        sent_count = len([s for s in schedules if s["sent"]])
        
        st.metric("총 스케줄", len(schedules))
        st.metric("활성 스케줄", active_count)
        st.metric("전송 완료", sent_count)
        
        # 데이터 백업
        if st.button("💾 데이터 백업"):
            backup_data = {
                "schedules": schedules,
                "users": scheduler.user_manager.users,
                "backup_time": get_korean_time().isoformat()
            }
            
            with open(f"backup_{get_korean_time().strftime('%Y%m%d_%H%M%S')}.json", 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            st.success("백업이 완료되었습니다!")
    
    with col2:
        st.subheader("🔧 관리")
        
        if st.button("🗑️ 전송완료 스케줄 정리"):
            original_count = len(schedules)
            scheduler.schedules["schedules"] = [s for s in schedules if not s["sent"]]
            removed_count = original_count - len(scheduler.schedules["schedules"])
            
            if scheduler.save_schedules():
                st.success(f"{removed_count}개의 전송완료 스케줄이 정리되었습니다.")
            else:
                st.error("정리에 실패했습니다.")
        
        if st.button("🔄 모든 스케줄 초기화"):
            if st.checkbox("정말로 모든 스케줄을 삭제하시겠습니까?"):
                scheduler.schedules["schedules"] = []
                if scheduler.save_schedules():
                    st.success("모든 스케줄이 삭제되었습니다.")
                else:
                    st.error("삭제에 실패했습니다.")


def show_log_monitor():
    """로그 모니터링 페이지"""
    st.markdown('<h1 class="main-header">📊 스케줄 서비스 로그 모니터</h1>', unsafe_allow_html=True)
    
    # 실시간 시계 표시
    current_time = get_korean_time()
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 1rem; padding: 0.5rem; background-color: #e8f5e8; border-radius: 0.5rem;">
        <span style="color: #2e7d32; font-family: 'Courier New', monospace; font-weight: bold;">
            🕐 현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    log_monitor = st.session_state.log_monitor
    
    # 제어 버튼
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🚀 모니터링 시작", use_container_width=True):
            success, message = log_monitor.start_monitoring()
            if success:
                st.success(message)
            else:
                st.error(message)
            st.rerun()
    
    with col2:
        if st.button("⏹️ 모니터링 중지", use_container_width=True):
            success, message = log_monitor.stop_monitoring()
            if success:
                st.success(message)
            else:
                st.error(message)
            st.rerun()
    
    with col3:
        if st.button("🔄 새로고침", use_container_width=True):
            st.rerun()
    
    with col4:
        if st.button("🗑️ 로그 지우기", use_container_width=True):
            log_monitor.logs = []
            st.success("로그가 지워졌습니다.")
            st.rerun()
    
    # 모니터링 상태 표시
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        if log_monitor.is_monitoring():
            st.success("🟢 모니터링 활성")
        else:
            st.error("🔴 모니터링 비활성")
    
    with status_col2:
        st.info(f"📊 로그 개수: {len(log_monitor.logs)}개")
    
    with status_col3:
        # 디버깅 정보 표시
        st.text(f"프로세스: {'있음' if log_monitor.process else '없음'}")
        st.text(f"상태 플래그: {log_monitor.monitoring}")
        if log_monitor.process:
            try:
                poll_result = log_monitor.process.poll()
                st.text(f"프로세스 상태: {'실행중' if poll_result is None else f'종료됨({poll_result})'}")
            except:
                st.text("프로세스 상태: 확인불가")
    
    # 로그 표시 영역
    st.subheader("📋 실시간 로그")
    
    if log_monitor.logs:
        # 로그를 역순으로 표시 (최신 로그가 위에)
        logs_display = log_monitor.logs[-50:]  # 최근 50개만 표시
        logs_display.reverse()
        
        # 로그 컨테이너
        log_container = st.container()
        
        with log_container:
            for log in logs_display:
                # 로그 타입에 따른 색상 구분
                if "❌" in log or "오류" in log or "실패" in log:
                    st.error(log)
                elif "✅" in log or "성공" in log or "완료" in log:
                    st.success(log)
                elif "🚀" in log or "시작" in log:
                    st.info(log)
                elif "📺" in log or "방송" in log:
                    st.warning(log)
                else:
                    st.text(log)
    else:
        st.info("로그가 없습니다. 모니터링을 시작하세요.")
    
    # 자동 새로고침 설정
    st.subheader("⚙️ 자동 새로고침 설정")
    auto_refresh = st.checkbox("자동 새로고침 (5초마다)", value=True)
    
    if auto_refresh and log_monitor.is_monitoring():
        time.sleep(5)
        st.rerun()


def show_user_management():
    """사용자 관리 페이지"""
    st.markdown('<h1 class="main-header">👥 사용자 관리</h1>', unsafe_allow_html=True)
    
    # 실시간 시계 표시
    current_time = get_korean_time()
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 1rem; padding: 0.5rem; background-color: #e3f2fd; border-radius: 0.5rem;">
        <span style="color: #1976d2; font-family: 'Courier New', monospace; font-weight: bold;">
            🕐 현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    scheduler = st.session_state.tv_scheduler
    user_manager = scheduler.user_manager
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["👥 사용자 목록", "➕ 사용자 추가", "⚙️ 사용자 설정"])
    
    with tab1:
        st.subheader("📋 등록된 사용자 목록")
        
        # 디버깅 정보 표시
        with st.expander("🔧 디버깅 정보", expanded=False):
            st.write(f"**데이터 파일**: {user_manager.data_file}")
            st.write(f"**파일 존재**: {os.path.exists(user_manager.data_file)}")
            st.write(f"**사용자 데이터 구조**: {list(user_manager.users.keys())}")
            st.write(f"**사용자 수**: {len(user_manager.users.get('users', []))}")
        
        users = user_manager.users.get("users", [])
        
        if not users:
            st.info("등록된 사용자가 없습니다.")
            st.markdown("""
            **사용자를 추가하려면:**
            1. 위의 "➕ 사용자 추가" 탭을 클릭하세요
            2. 텔레그램 사용자 ID와 이름을 입력하세요
            3. "✅ 사용자 추가" 버튼을 클릭하세요
            """)
        else:
            # 사용자 통계
            active_users = [u for u in users if u["active"]]
            inactive_users = [u for u in users if not u["active"]]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("총 사용자", len(users))
            with col2:
                st.metric("활성 사용자", len(active_users))
            with col3:
                st.metric("비활성 사용자", len(inactive_users))
            
            st.markdown("---")
            
            # 사용자 목록 표시
            for i, user in enumerate(users):
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                    
                    with col1:
                        status_icon = "🟢" if user["active"] else "🔴"
                        st.write(f"**{status_icon} {user['name']}**")
                        st.caption(f"ID: {user['id']}")
                    
                    with col2:
                        if user["active"]:
                            st.success("활성")
                        else:
                            st.error("비활성")
                    
                    with col3:
                        if st.button("토글", key=f"toggle_user_{i}"):
                            success, message = user_manager.toggle_user_status(user["id"])
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                            st.rerun()
                    
                    with col4:
                        if st.button("수정", key=f"edit_user_{i}"):
                            st.session_state.editing_user_id = user["id"]
                            st.session_state.editing_user_name = user["name"]
                            st.rerun()
                    
                    with col5:
                        if st.button("삭제", key=f"delete_user_{i}"):
                            if st.checkbox(f"정말로 {user['name']}을(를) 삭제하시겠습니까?", key=f"confirm_delete_{i}"):
                                success, message = user_manager.remove_user(user["id"])
                                if success:
                                    st.success(message)
                                else:
                                    st.error(message)
                                st.rerun()
                    
                    st.markdown("---")
    
    with tab2:
        st.subheader("➕ 새 사용자 추가")
        
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                user_id = st.text_input(
                    "사용자 ID",
                    placeholder="예: 123456789",
                    help="텔레그램 사용자 ID를 입력하세요"
                )
            
            with col2:
                user_name = st.text_input(
                    "사용자 이름",
                    placeholder="예: 홍길동",
                    help="사용자의 이름을 입력하세요"
                )
            
            col_submit1, col_submit2 = st.columns(2)
            
            with col_submit1:
                if st.form_submit_button("✅ 사용자 추가", use_container_width=True):
                    if user_id and user_name:
                        # 숫자 ID 확인
                        try:
                            int(user_id)
                            success, message = user_manager.add_user(user_id, user_name)
                            if success:
                                st.success(message)
                                st.balloons()
                            else:
                                st.error(message)
                        except ValueError:
                            st.error("사용자 ID는 숫자여야 합니다.")
                    else:
                        st.error("사용자 ID와 이름을 모두 입력하세요.")
            
            with col_submit2:
                if st.form_submit_button("❌ 취소", use_container_width=True):
                    st.rerun()
        
        # 사용자 ID 확인 도움말
        st.info("""
        **📱 텔레그램 사용자 ID 확인 방법:**
        1. [@userinfobot](https://t.me/userinfobot)에게 메시지 전송
        2. 받은 메시지에서 숫자 ID 복사
        3. 위 입력란에 붙여넣기
        """)
    
    with tab3:
        st.subheader("⚙️ 사용자 설정")
        
        # 사용자 수정 폼
        if 'editing_user_id' in st.session_state:
            st.markdown("### ✏️ 사용자 정보 수정")
            
            with st.form("edit_user_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    edit_id = st.text_input(
                        "사용자 ID",
                        value=st.session_state.editing_user_id,
                        disabled=True,
                        help="사용자 ID는 변경할 수 없습니다"
                    )
                
                with col2:
                    edit_name = st.text_input(
                        "사용자 이름",
                        value=st.session_state.editing_user_name,
                        help="새로운 이름을 입력하세요"
                    )
                
                col_submit1, col_submit2 = st.columns(2)
                
                with col_submit1:
                    if st.form_submit_button("💾 저장", use_container_width=True):
                        if edit_name:
                            # 사용자 이름 업데이트
                            for user in user_manager.users["users"]:
                                if user["id"] == st.session_state.editing_user_id:
                                    user["name"] = edit_name
                                    break
                            
                            if user_manager.save_users():
                                st.success(f"사용자 '{edit_name}' 정보가 업데이트되었습니다.")
                                del st.session_state.editing_user_id
                                del st.session_state.editing_user_name
                                st.rerun()
                            else:
                                st.error("사용자 정보 업데이트에 실패했습니다.")
                        else:
                            st.error("사용자 이름을 입력하세요.")
                
                with col_submit2:
                    if st.form_submit_button("❌ 취소", use_container_width=True):
                        del st.session_state.editing_user_id
                        del st.session_state.editing_user_name
                        st.rerun()
        
        # 일괄 작업
        st.markdown("### 🔧 일괄 작업")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🟢 모든 사용자 활성화", use_container_width=True):
                for user in user_manager.users["users"]:
                    user["active"] = True
                if user_manager.save_users():
                    st.success("모든 사용자가 활성화되었습니다.")
                else:
                    st.error("사용자 활성화에 실패했습니다.")
                st.rerun()
        
        with col2:
            if st.button("🔴 모든 사용자 비활성화", use_container_width=True):
                for user in user_manager.users["users"]:
                    user["active"] = False
                if user_manager.save_users():
                    st.success("모든 사용자가 비활성화되었습니다.")
                else:
                    st.error("사용자 비활성화에 실패했습니다.")
                st.rerun()
        
        with col3:
            if st.button("🗑️ 비활성 사용자 삭제", use_container_width=True):
                original_count = len(user_manager.users["users"])
                user_manager.users["users"] = [u for u in user_manager.users["users"] if u["active"]]
                removed_count = original_count - len(user_manager.users["users"])
                
                if user_manager.save_users():
                    st.success(f"{removed_count}명의 비활성 사용자가 삭제되었습니다.")
                else:
                    st.error("사용자 삭제에 실패했습니다.")
                st.rerun()
        
        # 데이터 백업/복원
        st.markdown("### 💾 데이터 관리")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 사용자 데이터 백업", use_container_width=True):
                backup_data = {
                    "users": user_manager.users,
                    "backup_time": get_korean_time().isoformat()
                }
                
                filename = f"users_backup_{get_korean_time().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)
                
                st.success(f"백업이 완료되었습니다: {filename}")
        
        with col2:
            uploaded_file = st.file_uploader(
                "사용자 데이터 복원",
                type=['json'],
                help="백업된 JSON 파일을 선택하세요"
            )
            
            if uploaded_file is not None:
                try:
                    data = json.load(uploaded_file)
                    if "users" in data:
                        user_manager.users = data["users"]
                        if user_manager.save_users():
                            st.success("사용자 데이터가 복원되었습니다.")
                            st.rerun()
                        else:
                            st.error("데이터 복원에 실패했습니다.")
                    else:
                        st.error("올바른 백업 파일이 아닙니다.")
                except Exception as e:
                    st.error(f"파일 읽기 오류: {e}")


def main():
    """메인 함수"""
    # 사이드바 네비게이션
    with st.sidebar:
        st.title("📺 TV 스케줄러")
        
        if st.button("🏠 대시보드", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
        
        if st.button("➕ 스케줄 추가", use_container_width=True):
            st.session_state.page = "add_schedule"
            st.rerun()
        
        if st.button("📋 스케줄 목록", use_container_width=True):
            st.session_state.page = "schedule_list"
            st.rerun()
        
        if st.button("⚙️ 설정", use_container_width=True):
            st.session_state.page = "settings"
            st.rerun()
        
        if st.button("📊 로그 모니터", use_container_width=True):
            st.session_state.page = "log_monitor"
            st.rerun()
        
        if st.button("👥 사용자 관리", use_container_width=True):
            st.session_state.page = "user_management"
            st.rerun()
        
        st.markdown("---")
        
        # 실시간 시계
        st.markdown("### 🕐 현재 시간")
        current_time = get_korean_time()
        
        # 시계를 위한 placeholder
        clock_placeholder = st.empty()
        with clock_placeholder.container():
            st.markdown(f"""
            <div style="text-align: center; padding: 0.5rem; background-color: #f0f2f6; border-radius: 0.5rem;">
                <h3 style="color: #007bff; font-family: 'Courier New', monospace; margin: 0;">
                    {current_time.strftime('%Y-%m-%d %H:%M:%S')}
                </h3>
            </div>
            """, unsafe_allow_html=True)
        
        # 1초마다 자동 새로고침
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = time.time()
        
        current_timestamp = time.time()
        if current_timestamp - st.session_state.last_refresh >= 1.0:
            st.session_state.last_refresh = current_timestamp
            st.rerun()
        
        # 현재 상태 표시
        scheduler = st.session_state.tv_scheduler
        schedules = scheduler.schedules["schedules"]
        active_schedules = [s for s in schedules if s["active"] and not s["sent"]]
        
        st.metric("총 스케줄", f"{len(schedules)}개")
        st.metric("활성 스케줄", f"{len(active_schedules)}개")
        
        # 오늘의 방송
        today_schedules = scheduler.get_upcoming_schedules(1)
        if today_schedules:
            st.markdown("**📺 오늘의 방송:**")
            for schedule in today_schedules[:3]:  # 최대 3개만 표시
                st.write(f"• {schedule['time']} {schedule['program_name']}")
    
    # 페이지 라우팅
    if st.session_state.page == "dashboard":
        show_dashboard()
    elif st.session_state.page == "add_schedule":
        show_add_schedule()
    elif st.session_state.page == "schedule_list":
        show_schedule_list()
    elif st.session_state.page == "settings":
        show_settings()
    elif st.session_state.page == "log_monitor":
        show_log_monitor()
    elif st.session_state.page == "user_management":
        show_user_management()


if __name__ == "__main__":
    main()
