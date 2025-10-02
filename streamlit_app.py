#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
텔레그램 전송 대상 관리 Streamlit 애플리케이션
"""

import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
from telegram_sender import TelegramSender

# 페이지 설정
st.set_page_config(
    page_title="텔레그램 전송 대상 관리",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #0088cc;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #0088cc;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f5c6cb;
    }
    .telegram-button {
        background-color: #0088cc;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        cursor: pointer;
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
    
    def update_config_file(self):
        active_ids = self.get_active_user_ids()
        
        try:
            with open("config.py", 'r', encoding='utf-8') as f:
                content = f.read()
            
            import re
            pattern = r'CHAT_IDS = \[.*?\]'
            replacement = f'CHAT_IDS = {active_ids}'
            
            new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
            with open("config.py", 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return True, f"config.py 파일이 업데이트되었습니다. ({len(active_ids)}명)"
            
        except Exception as e:
            return False, f"config.py 파일 업데이트 실패: {e}"


# 세션 상태 초기화
if 'user_manager' not in st.session_state:
    st.session_state.user_manager = UserManager()

if 'telegram_sender' not in st.session_state:
    st.session_state.telegram_sender = TelegramSender()

if 'page' not in st.session_state:
    st.session_state.page = "dashboard"


def show_dashboard():
    """대시보드 페이지"""
    st.markdown('<h1 class="main-header">🤖 텔레그램 전송 대상 관리</h1>', unsafe_allow_html=True)
    
    users = st.session_state.user_manager.users["users"]
    active_count = len(st.session_state.user_manager.get_active_user_ids())
    
    # 메트릭 카드
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="📊 총 사용자",
            value=f"{len(users)}명",
            delta=None
        )
    
    with col2:
        st.metric(
            label="✅ 활성 사용자",
            value=f"{active_count}명",
            delta=None
        )
    
    with col3:
        if st.button("🧪 테스트 전송", use_container_width=True):
            active_users = st.session_state.user_manager.get_active_user_ids()
            if not active_users:
                st.error("활성 사용자가 없습니다.")
            else:
                with st.spinner("테스트 메시지 전송 중..."):
                    message = "Streamlit에서 전송한 테스트 메시지입니다! 🚀"
                    results = st.session_state.telegram_sender.send_message_to_multiple(message, active_users)
                    
                    success_count = sum(1 for r in results if r["success"])
                    if success_count > 0:
                        st.success(f"✅ 테스트 메시지 전송 완료: {success_count}/{len(active_users)}명 성공!")
                        st.balloons()
                    else:
                        st.error("❌ 테스트 메시지 전송에 실패했습니다.")
    
    # 최근 사용자 목록
    st.subheader("📋 사용자 목록")
    
    if users:
        # 데이터프레임으로 표시
        df_data = []
        for user in users:
            df_data.append({
                "이름": user["name"],
                "사용자 ID": user["id"],
                "상태": "🟢 활성" if user["active"] else "🔴 비활성"
            })
        
        df = pd.DataFrame(df_data)
        
        # 컬럼 설정
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
        
        with col2:
            st.subheader("⚡ 빠른 작업")
            if st.button("➕ 사용자 추가", use_container_width=True):
                st.session_state.page = "add_user"
                st.rerun()
            
            if st.button("📤 메시지 전송", use_container_width=True):
                st.session_state.page = "send_message"
                st.rerun()
            
            if st.button("⚙️ config.py 업데이트", use_container_width=True):
                success, message = st.session_state.user_manager.update_config_file()
                if success:
                    st.success(message)
                else:
                    st.error(message)
    else:
        st.info("등록된 사용자가 없습니다. 첫 번째 사용자를 추가해보세요!")
        if st.button("➕ 첫 번째 사용자 추가", use_container_width=True):
            st.session_state.page = "add_user"
            st.rerun()


def show_add_user():
    """사용자 추가 페이지"""
    st.markdown('<h1 class="main-header">➕ 사용자 추가</h1>', unsafe_allow_html=True)
    
    with st.form("add_user_form"):
        st.subheader("새 사용자 정보")
        
        user_id = st.number_input(
            "사용자 ID",
            min_value=1,
            help="텔레그램 사용자 ID를 입력하세요. @userinfobot을 통해 확인할 수 있습니다."
        )
        
        name = st.text_input(
            "사용자 이름",
            placeholder="예: 홍길동",
            help="이름을 입력하지 않으면 '사용자{ID}'로 자동 설정됩니다."
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("✅ 사용자 추가", use_container_width=True):
                if user_id:
                    if not name:
                        name = f"사용자{user_id}"
                    
                    success, message = st.session_state.user_manager.add_user(user_id, name)
                    
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
                else:
                    st.error("사용자 ID를 입력하세요.")
        
        with col2:
            if st.form_submit_button("❌ 취소", use_container_width=True):
                st.session_state.page = "dashboard"
                st.rerun()
    
    # 사용자 ID 확인 방법 안내
    with st.expander("📖 사용자 ID 확인 방법"):
        st.markdown("""
        1. 텔레그램에서 [@userinfobot](https://t.me/userinfobot)을 찾습니다
        2. 봇에게 아무 메시지나 전송합니다
        3. 봇이 응답으로 보내는 숫자가 사용자 ID입니다
        4. 해당 ID를 위의 입력란에 입력하세요
        
        **주의**: 사용자 ID는 숫자여야 하며, 음수일 수도 있습니다 (그룹 채팅의 경우).
        """)


def show_send_message():
    """메시지 전송 페이지"""
    st.markdown('<h1 class="main-header">📤 메시지 전송</h1>', unsafe_allow_html=True)
    
    active_users = st.session_state.user_manager.get_active_user_ids()
    
    if not active_users:
        st.warning("활성 사용자가 없습니다. 사용자를 추가하거나 활성화하세요.")
        if st.button("👥 사용자 관리로 이동"):
            st.session_state.page = "dashboard"
            st.rerun()
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📝 메시지 작성")
        
        # 메시지 템플릿
        template = st.selectbox(
            "메시지 템플릿",
            ["직접 입력", "인사말", "공지사항", "테스트 메시지"]
        )
        
        if template == "인사말":
            default_message = "안녕하세요! 텔레그램 메시지 전송 테스트입니다. 🚀"
        elif template == "공지사항":
            default_message = """<b>📢 공지사항</b>

안녕하세요.

중요한 공지사항을 전달드립니다.

감사합니다."""
        elif template == "테스트 메시지":
            default_message = f"테스트 메시지입니다.\n\n전송 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            default_message = ""
        
        message = st.text_area(
            "메시지 내용",
            value=default_message,
            height=200,
            help="HTML 태그를 사용할 수 있습니다. 예: <b>굵은 글씨</b>, <i>기울임</i>"
        )
        
        col_send1, col_send2 = st.columns(2)
        
        with col_send1:
            if st.button("📤 메시지 전송", use_container_width=True):
                if message.strip():
                    with st.spinner("메시지 전송 중..."):
                        results = st.session_state.telegram_sender.send_message_to_multiple(message, active_users)
                        
                        success_count = sum(1 for r in results if r["success"])
                        
                        if success_count > 0:
                            st.success(f"✅ 메시지 전송 완료: {success_count}/{len(active_users)}명에게 성공적으로 전송되었습니다!")
                            st.balloons()
                        else:
                            st.error("❌ 메시지 전송에 실패했습니다.")
                else:
                    st.error("메시지를 입력하세요.")
        
        with col_send2:
            if st.button("👁️ 미리보기", use_container_width=True):
                if message.strip():
                    st.markdown("**미리보기:**")
                    st.markdown(message, unsafe_allow_html=True)
                else:
                    st.warning("미리보기할 메시지가 없습니다.")
    
    with col2:
        st.subheader("👥 전송 대상")
        
        st.info(f"**{len(active_users)}명**의 활성 사용자에게 전송됩니다.")
        
        # 전송 대상 목록
        for user_id in active_users:
            st.write(f"• {user_id}")
        
        st.markdown("---")
        
        if st.button("👥 사용자 관리", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()


def show_user_management():
    """사용자 관리 페이지"""
    st.markdown('<h1 class="main-header">👥 사용자 관리</h1>', unsafe_allow_html=True)
    
    users = st.session_state.user_manager.users["users"]
    
    if not users:
        st.info("등록된 사용자가 없습니다.")
        if st.button("➕ 첫 번째 사용자 추가"):
            st.session_state.page = "add_user"
            st.rerun()
        return
    
    # 사용자 목록 표시
    for i, user in enumerate(users):
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            st.write(f"**{user['name']}** (ID: {user['id']})")
        
        with col2:
            if user["active"]:
                st.success("🟢 활성")
            else:
                st.error("🔴 비활성")
        
        with col3:
            if st.button(f"토글", key=f"toggle_{user['id']}"):
                success, message = st.session_state.user_manager.toggle_user_status(user['id'])
                if success:
                    st.success(message)
                else:
                    st.error(message)
                st.rerun()
        
        with col4:
            if st.button(f"삭제", key=f"delete_{user['id']}"):
                success, message = st.session_state.user_manager.remove_user(user['id'])
                if success:
                    st.success(message)
                else:
                    st.error(message)
                st.rerun()
        
        st.markdown("---")


def main():
    """메인 함수"""
    # 사이드바 네비게이션
    with st.sidebar:
        st.title("🤖 텔레그램 관리")
        
        if st.button("🏠 대시보드", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
        
        if st.button("➕ 사용자 추가", use_container_width=True):
            st.session_state.page = "add_user"
            st.rerun()
        
        if st.button("👥 사용자 관리", use_container_width=True):
            st.session_state.page = "user_management"
            st.rerun()
        
        if st.button("📤 메시지 전송", use_container_width=True):
            st.session_state.page = "send_message"
            st.rerun()
        
        st.markdown("---")
        
        # 현재 상태 표시
        users = st.session_state.user_manager.users["users"]
        active_count = len(st.session_state.user_manager.get_active_user_ids())
        
        st.metric("총 사용자", f"{len(users)}명")
        st.metric("활성 사용자", f"{active_count}명")
        
        st.markdown("---")
        
        # 설정 정보
        st.subheader("⚙️ 설정")
        if st.button("config.py 업데이트", use_container_width=True):
            success, message = st.session_state.user_manager.update_config_file()
            if success:
                st.success(message)
            else:
                st.error(message)
    
    # 페이지 라우팅
    if st.session_state.page == "dashboard":
        show_dashboard()
    elif st.session_state.page == "add_user":
        show_add_user()
    elif st.session_state.page == "user_management":
        show_user_management()
    elif st.session_state.page == "send_message":
        show_send_message()


if __name__ == "__main__":
    main()
