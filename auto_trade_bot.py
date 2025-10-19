import pyupbit, time, logging
from datetime import datetime
import config
from telegram_bot import TelegramBot

logging.basicConfig(level=logging.DEBUG)

class AutoTradingBot:
    def __init__(self):
        self.upbit = pyupbit.Upbit(config.ACCESS_KEY, config.SECRET_KEY)
        self.telegram = TelegramBot()
        self.portfolio = config.PORTFOLIO
        self.is_paused = False
        self.should_stop = False
        self.total_trades = 0
        self.winning_trades = 0
        self.total_profit = 0
        self.initial_balance = 0
        self.investment_amount = 0

    def get_balance(self, ticker="KRW"):
        try:
            return self.upbit.get_balance("KRW") if ticker=="KRW" else self.upbit.get_balance(ticker.replace("KRW-",""))
        except:
            return 0

    def get_current_price(self, coin):
        return pyupbit.get_current_price(coin) or 0

    def calculate_investment(self):
        krw = self.get_balance("KRW")
        avail = krw - config.SAFETY_RESERVE
        return avail if avail>=50000 else 0

    def calculate_total_value(self):
        krw = self.get_balance("KRW")
        val = sum(self.get_balance(c)*self.get_current_price(c) for c in self.portfolio)
        return krw + val

    def get_current_balances(self):
        bals = {"KRW": (self.get_balance("KRW"), 1)}
        for coin in self.portfolio:
            amt = self.get_balance(coin)
            bals[coin] = (amt, self.get_current_price(coin))
        return bals

    def setup_all(self):
        self.investment_amount = self.calculate_investment()
        if not self.investment_amount:
            return False
        self.initial_balance = self.calculate_total_value()
        bals = self.get_current_balances()
        self.telegram.send_start_message(self.investment_amount, self.initial_balance, bals)
        return True

    def check_all_signals(self):
        # 기존 매매 로직 삽입
        pass

    def check_risk_limits(self):
        total = self.calculate_total_value()
        pct = (total-self.initial_balance)/self.initial_balance*100 if self.initial_balance else 0
        if pct < -config.STOP_LOSS:
            self.telegram.send_stop_message(f"손실 한도 초과 ({pct:.2f}%)", total, total-self.initial_balance)
            return False
        if pct >= config.DAILY_PROFIT_TARGET:
            self.telegram.send_stop_message(f"목표 달성 ({pct:.2f}%)", total, total-self.initial_balance)
            return False
        return True

    def run(self):
        start_time = datetime.now()
        if not self.setup_all():
            return
        loop = 0

        while not self.should_stop:
            # ① 명령 처리
            for upd in self.telegram.get_updates():
                txt = upd.get("message",{}).get("text","")
                if txt == "/help":
                    self.telegram.send_help()
                elif txt == "/status":
                    total = self.calculate_total_value()
                    profit = total - self.initial_balance
                    pct = profit / self.initial_balance * 100
                    bals = self.get_current_balances()
                    self.telegram.send_status(total, profit, pct, self.total_trades, self.winning_trades, bals)
                elif txt == "/pause":
                    self.is_paused = True
                    self.telegram.send_message("⏸️ 자동매매 일시 중지")
                elif txt == "/resume":
                    self.is_paused = False
                    self.telegram.send_message("▶️ 자동매매 재개")
                elif txt == "/stop":
                    self.should_stop = True
                    break

            # ② 일시중지
            if self.is_paused:
                time.sleep(config.CHECK_INTERVAL)
                continue

            # ③ 매매 로직
            self.check_all_signals()
            if not self.check_risk_limits():
                break

            # ④ 1분마다 상태 알림
            if loop % (60//config.CHECK_INTERVAL) == 0:
                total = self.calculate_total_value()
                profit = total - self.initial_balance
                pct = profit / self.initial_balance * 100
                bals = self.get_current_balances()
                self.telegram.send_status(total, profit, pct, self.total_trades, self.winning_trades, bals)

            loop += 1
            time.sleep(config.CHECK_INTERVAL)

        # 종료 결과
        duration = str(datetime.now() - start_time).split('.')[0]
        final = self.calculate_total_value()
        profit = final - self.initial_balance
        pct = profit / self.initial_balance * 100
        bals = self.get_current_balances()
        self.telegram.send_final_result(final, self.initial_balance, profit, pct, self.total_trades, self.winning_trades, duration, bals)

if __name__ == "__main__":
    AutoTradingBot().run()

