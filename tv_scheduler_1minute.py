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
import schedule
import time
import threading
from telegram_sender import TelegramSender

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
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
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
            "created_at": datetime.now().isoformat()
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
        today = datetime.now().date()
        
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


def show_dashboard():
    """대시보드 페이지"""
    st.markdown('<h1 class="main-header">📺 TV 방송 스케줄러</h1>', unsafe_allow_html=True)
    
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
    
    with st.form("add_schedule_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📅 방송 정보")
            
            date = st.date_input(
                "방송 날짜",
                value=datetime.now().date(),
                min_value=datetime.now().date()
            )
            
            # 시간 입력을 1분단위로 변경
            st.markdown('<div class="time-input-container">', unsafe_allow_html=True)
            st.markdown("**⏰ 방송 시간**")
            
            time_col1, time_col2 = st.columns(2)
            
            with time_col1:
                hour = st.selectbox(
                    "시",
                    options=list(range(24)),
                    index=datetime.now().hour,
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
                "backup_time": datetime.now().isoformat()
            }
            
            with open(f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w', encoding='utf-8') as f:
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
        
        st.markdown("---")
        
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


if __name__ == "__main__":
    main()
