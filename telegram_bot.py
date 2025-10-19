import requests
import config

class TelegramBot:
    def __init__(self):
        self.token    = config.TELEGRAM_BOT_TOKEN
        self.chat_id  = config.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.offset   = None

    def _post(self, method, payload):
        requests.post(f"{self.base_url}/{method}", data=payload)

    def send_message(self, text):
        self._post("sendMessage", {"chat_id": self.chat_id, "text": text})

    def send_help(self):
        help_text = (
            "🤖 사용 가능한 명령어:\n"
            "/help    – 이 도움말 표시\n"
            "/status  – 평가액·수익 현황\n"
            "/pause   – 자동매매 일시 중지\n"
            "/resume  – 자동매매 재개\n"
            "/stop    – 봇 완전 중지\n"
        )
        self.send_message(help_text)

    def send_start_message(self, invest_amt, init_bal, balances):
        lines = [
            f"{coin}: 수량 {amt:,.2f}, 평가액 {amt*price:,.2f}원"
            for coin,(amt,price) in balances.items()
        ]
        balance_text = "\n".join(lines)
        text = (
            f"🚀 자동매매 시작\n"
            f"투자금: {invest_amt:,.2f}원\n"
            f"초기잔고: {init_bal:,.2f}원\n\n"
            f"📊 초기 보유 자산:\n{balance_text}"
        )
        self.send_message(text)

    def send_status(self, total, profit, pct, trades, wins, balances):
        # 수익률이 위에
        lines = []
        for coin in ["KRW-BTC","KRW-ETH","KRW-XRP","KRW-SOL","KRW-ADA","KRW"]:
            if coin in balances:
                amt,price = balances[coin]
                lines.append(f"{coin}: {amt:,.2f}개 ({amt*price:,.2f}원)")
        balance_text = "\n".join(lines)
        text = (
            f"📊 수익: {profit:+,.2f}원 ({pct:+.2f}%)\n"
            f"평가액: {total:,.2f}원\n\n"
            f"💰 보유 자산:\n{balance_text}\n\n"
            f"📈 총거래: {trades}회 | 승리: {wins}회"
        )
        self.send_message(text)

    def send_final_result(self, final_bal, init_bal, profit, pct, trades, wins, duration, balances):
        lines = [
            f"{coin}: 수량 {amt:,.2f}, 평가액 {amt*price:,.2f}원"
            for coin,(amt,price) in balances.items()
        ]
        balance_text = "\n".join(lines)
        text = (
            f"🏁 자동매매 최종 결과 ({duration})\n"
            f"초기잔고: {init_bal:,.2f}원 → 최종평가액: {final_bal:,.2f}원\n"
            f"순수익: {profit:+,.2f}원 ({pct:+.2f}%)\n"
            f"총거래: {trades}회 | 승리: {wins}회\n\n"
            f"📊 최종 보유 자산:\n{balance_text}"
        )
        self.send_message(text)

    def send_buy_alert(self, coin, price, amount, target):
        text = (
            f"🔴 매수 알림\n"
            f"코인: {coin}\n"
            f"매수가: {price:,.2f}원\n"
            f"투자금: {amount:,.2f}원\n"
            f"목표가: {target:,.2f}원"
        )
        self.send_message(text)

    def send_sell_alert(self, coin, price, profit, pct):
        text = (
            f"🔵 매도 알림\n"
            f"코인: {coin}\n"
            f"매도가: {price:,.2f}원\n"
            f"수익: {profit:+,.2f}원 ({pct:.2f}%)"
        )
        self.send_message(text)

    def send_error_alert(self, err):
        self.send_message(f"⚠️ 오류 발생: {err}")

    def send_stop_message(self, reason, total, profit):
        text = (
            f"🚫 자동매매 중지\n"
            f"사유: {reason}\n"
            f"최종평가액: {total:,.2f}원\n"
            f"최종수익: {profit:+,.2f}원"
        )
        self.send_message(text)

    def get_updates(self):
        params = {"timeout": 10}
        if self.offset:
            params["offset"] = self.offset
        resp = requests.get(f"{self.base_url}/getUpdates", params=params).json()
        updates = resp.get("result", [])
        if updates:
            self.offset = updates[-1]["update_id"] + 1
        return updates

