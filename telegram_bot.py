import requests
import config

class TelegramBot:
    def __init__(self):
        self.token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
    
    def send_message(self, message):
        """텔레그램 메시지 전송"""
        if not config.ENABLE_TELEGRAM:
            return
        
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, data=data)
            return response.json()
        except Exception as e:
            print(f"텔레그램 전송 실패: {e}")
    
    def send_start_message(self, investment_amount, balance):
        """시작 메시지"""
        message = f"""
🤖 <b>자동매매 봇 시작!</b>

💰 <b>투자 정보</b>
• 총 원화 잔고: {balance:,.0f}원
• 투자 금액: {investment_amount:,.0f}원
• 예비금: {config.SAFETY_RESERVE:,.0f}원

🪙 <b>거래 코인</b>
• 비트코인 (30%)
• 이더리움 (20%)
• 리플 (20%)
• 솔라나 (20%)
• 카르다노 (10%)

⚙️ <b>설정</b>
• 그리드: {config.GRID_COUNT}개
• 간격: {config.GRID_GAP}%
• 손절: {config.STOP_LOSS}%
• 목표: {config.DAILY_PROFIT_TARGET}%

✅ 24시간 자동 거래를 시작합니다!
        """
        self.send_message(message)
    
    def send_buy_alert(self, coin_name, price, amount, target_price):
        """매수 알림"""
        message = f"""
🔴 <b>매수 완료</b>

🪙 {coin_name}
💵 매수가: {price:,.0f}원
💰 금액: {amount:,.0f}원
🎯 목표가: {target_price:,.0f}원 (+{config.GRID_GAP}%)
        """
        self.send_message(message)
    
    def send_sell_alert(self, coin_name, price, profit, profit_percent):
        """매도 알림"""
        message = f"""
🔵 <b>매도 완료</b>

🪙 {coin_name}
💵 매도가: {price:,.0f}원
💰 수익: {profit:+,.0f}원 ({profit_percent:+.2f}%)
        """
        self.send_message(message)
    
    def send_status(self, total_value, profit, profit_percent, trades, wins):
        """상태 리포트"""
        win_rate = (wins / trades * 100) if trades > 0 else 0
        message = f"""
📊 <b>현재 상태</b>

💵 총 평가액: {total_value:,.0f}원
📈 총 수익: {profit:+,.0f}원 ({profit_percent:+.2f}%)

📊 거래 통계
• 총 거래: {trades}회
• 성공: {wins}회
• 승률: {win_rate:.1f}%
        """
        self.send_message(message)
    
    def send_daily_summary(self, daily_profit, trades, total_value):
        """일일 요약"""
        message = f"""
📅 <b>일일 거래 요약</b>

💰 오늘 수익: {daily_profit:+,.0f}원
📊 거래 횟수: {trades}회
💵 현재 평가액: {total_value:,.0f}원

✨ 내일도 화이팅!
        """
        self.send_message(message)
    
    def send_stop_message(self, reason, final_value, final_profit):
        """중지 메시지"""
        message = f"""
⏸ <b>자동매매 중지</b>

📌 중지 사유: {reason}

📊 최종 결과
• 평가액: {final_value:,.0f}원
• 총 수익: {final_profit:+,.0f}원

모든 포지션이 정리되었습니다.
        """
        self.send_message(message)
    
    def send_error_alert(self, error_message):
        """에러 알림"""
        message = f"""
⚠️ <b>오류 발생</b>

{error_message}

봇이 자동으로 재시작을 시도합니다.
        """
        self.send_message(message)
