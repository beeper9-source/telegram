#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
텔레그램 메시지 전송 프로그램
"""

import requests
import json
import ssl
import urllib3
from config import BOT_TOKEN, CHAT_ID, CHAT_IDS

# SSL 경고 비활성화 (개발 환경에서만 사용)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TelegramSender:
    def __init__(self, bot_token=None, chat_id=None):
        """
        텔레그램 메시지 전송 클래스 초기화
        
        Args:
            bot_token (str): 텔레그램 봇 토큰
            chat_id (str): 메시지를 받을 채팅 ID
        """
        self.bot_token = bot_token or BOT_TOKEN
        self.chat_id = chat_id or CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, message, parse_mode="HTML"):
        """
        텔레그램으로 메시지 전송
        
        Args:
            message (str): 전송할 메시지
            parse_mode (str): 메시지 파싱 모드 (HTML, Markdown 등)
        
        Returns:
            dict: API 응답 결과
        """
        url = f"{self.base_url}/sendMessage"
        
        data = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        
        try:
            response = requests.post(url, data=data, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"메시지 전송 실패: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"오류 상세: {error_detail}")
                except:
                    print(f"응답 내용: {e.response.text}")
            return None
    
    def send_photo(self, photo_path, caption=""):
        """
        텔레그램으로 사진 전송
        
        Args:
            photo_path (str): 전송할 사진 파일 경로
            caption (str): 사진 설명
        
        Returns:
            dict: API 응답 결과
        """
        url = f"{self.base_url}/sendPhoto"
        
        try:
            with open(photo_path, 'rb') as photo:
                files = {"photo": photo}
                data = {
                    "chat_id": self.chat_id,
                    "caption": caption
                }
                response = requests.post(url, files=files, data=data, verify=False)
                response.raise_for_status()
                return response.json()
        except FileNotFoundError:
            print(f"사진 파일을 찾을 수 없습니다: {photo_path}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"사진 전송 실패: {e}")
            return None
    
    def send_document(self, document_path, caption=""):
        """
        텔레그램으로 문서 전송
        
        Args:
            document_path (str): 전송할 문서 파일 경로
            caption (str): 문서 설명
        
        Returns:
            dict: API 응답 결과
        """
        url = f"{self.base_url}/sendDocument"
        
        try:
            with open(document_path, 'rb') as document:
                files = {"document": document}
                data = {
                    "chat_id": self.chat_id,
                    "caption": caption
                }
                response = requests.post(url, files=files, data=data, verify=False)
                response.raise_for_status()
                return response.json()
        except FileNotFoundError:
            print(f"문서 파일을 찾을 수 없습니다: {document_path}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"문서 전송 실패: {e}")
            return None
    
    def get_updates(self):
        """
        봇이 받은 최신 메시지들 가져오기
        
        Returns:
            dict: API 응답 결과
        """
        url = f"{self.base_url}/getUpdates"
        
        try:
            response = requests.get(url, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"업데이트 가져오기 실패: {e}")
            return None
    
    def send_message_to_multiple(self, message, chat_ids=None, parse_mode="HTML"):
        """
        여러 채팅에 메시지 전송
        
        Args:
            message (str): 전송할 메시지
            chat_ids (list): 채팅 ID 리스트 (None이면 config에서 가져옴)
            parse_mode (str): 메시지 파싱 모드
        
        Returns:
            list: 각 전송 결과 리스트
        """
        if chat_ids is None:
            chat_ids = CHAT_IDS
        
        results = []
        print(f"📤 {len(chat_ids)}명에게 메시지 전송 시작...")
        
        for i, chat_id in enumerate(chat_ids, 1):
            print(f"[{i}/{len(chat_ids)}] 채팅 ID {chat_id}로 전송 중...")
            
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            try:
                response = requests.post(url, data=data, verify=False)
                response.raise_for_status()
                result = response.json()
                results.append({"chat_id": chat_id, "success": True, "result": result})
                print(f"✅ 메시지 전송 성공 (채팅 ID: {chat_id})")
            except requests.exceptions.RequestException as e:
                results.append({"chat_id": chat_id, "success": False, "error": str(e)})
                print(f"❌ 메시지 전송 실패 (채팅 ID: {chat_id}): {e}")
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_detail = e.response.json()
                        print(f"   오류 상세: {error_detail}")
                    except:
                        print(f"   응답 내용: {e.response.text}")
        
        # 결과 요약
        success_count = sum(1 for r in results if r["success"])
        print(f"\n📊 전송 결과: {success_count}/{len(chat_ids)}명 성공")
        
        return results
    
    def send_photo_to_multiple(self, photo_path, caption="", chat_ids=None):
        """
        여러 채팅에 사진 전송
        
        Args:
            photo_path (str): 전송할 사진 파일 경로
            caption (str): 사진 설명
            chat_ids (list): 채팅 ID 리스트 (None이면 config에서 가져옴)
        
        Returns:
            list: 각 전송 결과 리스트
        """
        if chat_ids is None:
            chat_ids = CHAT_IDS
        
        results = []
        print(f"📷 {len(chat_ids)}명에게 사진 전송 시작...")
        
        for i, chat_id in enumerate(chat_ids, 1):
            print(f"[{i}/{len(chat_ids)}] 채팅 ID {chat_id}로 사진 전송 중...")
            
            url = f"{self.base_url}/sendPhoto"
            
            try:
                with open(photo_path, 'rb') as photo:
                    files = {"photo": photo}
                    data = {
                        "chat_id": chat_id,
                        "caption": caption
                    }
                    response = requests.post(url, files=files, data=data, verify=False)
                    response.raise_for_status()
                    result = response.json()
                    results.append({"chat_id": chat_id, "success": True, "result": result})
                    print(f"✅ 사진 전송 성공 (채팅 ID: {chat_id})")
            except FileNotFoundError:
                results.append({"chat_id": chat_id, "success": False, "error": "파일을 찾을 수 없습니다"})
                print(f"❌ 사진 파일을 찾을 수 없습니다: {photo_path}")
                break  # 파일이 없으면 나머지도 실패할 것이므로 중단
            except requests.exceptions.RequestException as e:
                results.append({"chat_id": chat_id, "success": False, "error": str(e)})
                print(f"❌ 사진 전송 실패 (채팅 ID: {chat_id}): {e}")
        
        # 결과 요약
        success_count = sum(1 for r in results if r["success"])
        print(f"\n📊 사진 전송 결과: {success_count}/{len(chat_ids)}명 성공")
        
        return results


def main():
    """메인 함수 - 사용 예시"""
    
    # 설정 확인
    if BOT_TOKEN == "your_bot_token_here" or CHAT_ID == "your_chat_id_here":
        print("⚠️  config.py 파일에서 BOT_TOKEN과 CHAT_ID를 설정해주세요!")
        print("1. BotFather(@BotFather)에서 봇을 생성하고 토큰을 받으세요")
        print("2. @userinfobot을 통해 본인의 채팅 ID를 확인하세요")
        return
    
    # 텔레그램 전송 객체 생성
    sender = TelegramSender()
    
    # 봇 정보 확인
    print("🔍 봇 정보 확인 중...")
    updates = sender.get_updates()
    if updates and updates.get("ok"):
        print("✅ 봇 연결 성공!")
        if updates["result"]:
            print(f"📨 최근 메시지 수: {len(updates['result'])}")
        else:
            print("⚠️  아직 봇과의 대화가 없습니다.")
            print("텔레그램에서 봇을 찾아 /start 명령어를 전송하세요!")
    else:
        print("❌ 봇 연결 실패!")
        return
    
    # 여러 사용자에게 메시지 전송
    print("\n📤 여러 사용자에게 메시지 전송 시도 중...")
    message = "프로그램 목록 : https://telegram-5ut28rtfjubjj6ekx5pndy.streamlit.app/"
    results = sender.send_message_to_multiple(message)
    
    # 전송 결과 확인
    success_count = sum(1 for r in results if r["success"])
    if success_count > 0:
        print(f"\n🎉 총 {success_count}명에게 메시지가 성공적으로 전송되었습니다!")
    else:
        print("\n❌ 모든 사용자에게 메시지 전송에 실패했습니다.")
        print("봇과의 대화를 시작했는지 확인해주세요.")
        print("텔레그램에서 봇을 찾아 /start 명령어를 전송하세요!")


if __name__ == "__main__":
    main()
