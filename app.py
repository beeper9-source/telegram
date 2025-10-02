#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
텔레그램 전송 대상 관리 웹 애플리케이션
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import json
import os
from user_manager import UserManager
from telegram_sender import TelegramSender

app = Flask(__name__)
app.secret_key = 'telegram_bot_secret_key_2024'

# 전역 변수
user_manager = UserManager()
telegram_sender = TelegramSender()


@app.route('/')
def index():
    """메인 페이지"""
    users = user_manager.users["users"]
    active_count = len(user_manager.get_active_user_ids())
    return render_template('index.html', users=users, active_count=active_count)


@app.route('/users')
def users():
    """사용자 목록 페이지"""
    users = user_manager.users["users"]
    return render_template('users.html', users=users)


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    """사용자 추가"""
    if request.method == 'POST':
        try:
            user_id = int(request.form['user_id'])
            name = request.form['name'].strip()
            if not name:
                name = f"사용자{user_id}"
            
            if user_manager.add_user(user_id, name):
                flash(f'사용자 {name} ({user_id})가 성공적으로 추가되었습니다!', 'success')
            else:
                flash(f'사용자 추가에 실패했습니다. 이미 등록된 사용자일 수 있습니다.', 'error')
        except ValueError:
            flash('올바른 사용자 ID를 입력하세요.', 'error')
        except Exception as e:
            flash(f'오류가 발생했습니다: {str(e)}', 'error')
        
        return redirect(url_for('users'))
    
    return render_template('add_user.html')


@app.route('/remove_user/<int:user_id>')
def remove_user(user_id):
    """사용자 제거"""
    if user_manager.remove_user(user_id):
        flash(f'사용자 ID {user_id}가 성공적으로 제거되었습니다!', 'success')
    else:
        flash(f'사용자 제거에 실패했습니다.', 'error')
    
    return redirect(url_for('users'))


@app.route('/toggle_user/<int:user_id>')
def toggle_user(user_id):
    """사용자 활성/비활성 토글"""
    if user_manager.toggle_user_status(user_id):
        flash('사용자 상태가 변경되었습니다!', 'success')
    else:
        flash('사용자 상태 변경에 실패했습니다.', 'error')
    
    return redirect(url_for('users'))


@app.route('/send_message', methods=['GET', 'POST'])
def send_message():
    """메시지 전송 페이지"""
    if request.method == 'POST':
        message = request.form['message'].strip()
        if not message:
            flash('메시지를 입력하세요.', 'error')
            return redirect(url_for('send_message'))
        
        active_users = user_manager.get_active_user_ids()
        if not active_users:
            flash('활성 사용자가 없습니다.', 'error')
            return redirect(url_for('send_message'))
        
        # 메시지 전송
        results = telegram_sender.send_message_to_multiple(message, active_users)
        
        success_count = sum(1 for r in results if r["success"])
        flash(f'메시지 전송 완료: {success_count}/{len(active_users)}명에게 성공적으로 전송되었습니다!', 'success')
        
        return redirect(url_for('send_message'))
    
    active_users = user_manager.get_active_user_ids()
    return render_template('send_message.html', active_users=active_users)


@app.route('/update_config')
def update_config():
    """config.py 파일 업데이트"""
    if user_manager.update_config_file():
        flash('config.py 파일이 성공적으로 업데이트되었습니다!', 'success')
    else:
        flash('config.py 파일 업데이트에 실패했습니다.', 'error')
    
    return redirect(url_for('index'))


@app.route('/api/users')
def api_users():
    """사용자 목록 API"""
    return jsonify(user_manager.users)


@app.route('/api/send_test')
def api_send_test():
    """테스트 메시지 전송 API"""
    active_users = user_manager.get_active_user_ids()
    if not active_users:
        return jsonify({"error": "활성 사용자가 없습니다."}), 400
    
    message = "웹에서 전송한 테스트 메시지입니다! 🚀"
    results = telegram_sender.send_message_to_multiple(message, active_users)
    
    success_count = sum(1 for r in results if r["success"])
    return jsonify({
        "message": "테스트 메시지 전송 완료",
        "success_count": success_count,
        "total_count": len(active_users),
        "results": results
    })


if __name__ == '__main__':
    # 템플릿 폴더 생성
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    
    print("🚀 텔레그램 전송 대상 관리 웹 애플리케이션을 시작합니다...")
    print("📱 브라우저에서 http://localhost:5000 으로 접속하세요")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
