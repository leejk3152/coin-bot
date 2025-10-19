import pyupbit
import time
import logging
from datetime import datetime
import config
from telegram_bot import TelegramBot

logging.basicConfig(level=logging.DEBUG)

class AutoTradingBot:
    def __init__(self):
        print("\n" + "="*90)
        print("🚀 전액 투자 자동매매 봇 v3.0 (AWS + 텔레그램)")
        print("="*90)

        self.upbit = pyupbit.Upbit(config.ACCESS_KEY, config.SECRET_KEY)
        self.telegram = TelegramBot()
        self.portfolio = config.PORTFOLIO
        self.coin_bots = {}

        self.is_paused = False
        self.should_stop = False
        self.total_trades = 0
        self.winning_trades = 0
        self.total_profit = 0
        self.initial_balance = 0
        self.investment_amount = 0

        self.coin_names = {
            "KRW-BTC": "비트코인",
            "KRW-ETH": "이더리움", 
            "KRW-XRP": "리플",
            "KRW-SOL": "솔라나",
            "KRW-ADA": "카르다노"
        }

    def log(self, message, level="INFO", coin=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        icons = {"INFO":"ℹ️","BUY":"🔴","SELL":"🔵","SUCCESS":"✅","WARNING":"⚠️","ERROR":"❌"}
        icon = icons.get(level,"📝")
        tag = f"[{self.coin_names.get(coin,coin)}]" if coin else ""
        msg = f"[{timestamp}] {icon} {tag} {message}"
        print(msg)
        if config.ENABLE_LOG:
            with open("trading_log.txt","a",encoding="utf-8") as f:
                f.write(msg+"\n")

    def get_balance(self, ticker="KRW"):
        try:
            if ticker=="KRW":
                return self.upbit.get_balance("KRW")
            return self.upbit.get_balance(ticker.replace("KRW-",""))
        except Exception as e:
            self.log(f"잔고 조회 실패: {e}","ERROR")
            return 0

    def get_current_price(self, coin):
        try:
            return pyupbit.get_current_price(coin) or 0
        except:
            return 0

    def calculate_investment(self):
        total_krw = self.get_balance("KRW")
        avail = total_krw - config.SAFETY_RESERVE
        if avail<50000:
            self.log(f"투자 가능 금액 부족: {avail:,.0f}원","ERROR")
            return 0
        self.log(f"총 원화 잔고: {total_krw:,.0f}원","INFO")
        self.log(f"투자 금액: {avail:,.0f}원 (예비금 {config.SAFETY_RESERVE:,.0f}원 제외)","SUCCESS")
        return avail

    def setup_coin_grids(self, coin, invest_amt):
        price = self.get_current_price(coin)
        if price==0:
            return False
        per_grid = invest_amt / config.GRID_COUNT
        grids=[]
        for i in range(1,config.GRID_COUNT+1):
            buy_p  = price*(1-config.GRID_GAP*i/100)
            sell_p = buy_p*(1+config.GRID_GAP/100)
            grids.append({'id':i,'buy_price':buy_p,'sell_price':sell_p,'amount':per_grid,'status':'waiting','volume':0})
        self.coin_bots[coin]={'grids':grids,'positions':[],'investment':invest_amt,'trades':0,'wins':0,'profit':0}
        self.log(f"그리드 설정 | {invest_amt:,.0f}원 | 현재가: {price:,.0f}원","SUCCESS",coin)
        return True

    def setup_all_grids(self):
        self.investment_amount=self.calculate_investment()
        if not self.investment_amount:
            return False
        self.initial_balance=self.calculate_total_value()
        print(f"\n📊 포트폴리오 배분 (총 {self.investment_amount:,.0f}원)")
        print("-"*90)
        for coin,ratio in self.portfolio.items():
            amt=self.investment_amount*ratio
            print(f"   {self.coin_names.get(coin,coin):8s} | {amt:>12,.0f}원 ({ratio*100:>5.1f}%)")
            if not self.setup_coin_grids(coin,amt):
                return False
            time.sleep(0.1)
        print("-"*90)
        
        # 초기 잔고 수집
        balances = {"KRW": (self.get_balance("KRW"), 1)}
        for coin in self.portfolio:
            amt = self.get_balance(coin)
            if amt>0:
                balances[coin] = (amt, self.get_current_price(coin))
        
        self.telegram.send_start_message(self.investment_amount, self.initial_balance, balances)
        return True

    def execute_buy(self, coin, grid):
        if self.get_balance("KRW")<grid['amount']:
            return False
        try:
            res=self.upbit.buy_market_order(coin,grid['amount'])
            logging.debug("매수 결과:%s",res)
            if res and 'uuid' in res:
                vol=float(res.get('executed_volume',0))
                grid['status'],grid['volume']='bought',vol
                self.coin_bots[coin]['positions'].append({'grid_id':grid['id'],'buy_price':grid['buy_price'],'sell_price':grid['sell_price'],'volume':vol,'buy_time':datetime.now()})
                self.log(f"매수 | Lv.{grid['id']} | {grid['buy_price']:,.0f}원","BUY",coin)
                self.telegram.send_buy_alert(self.coin_names[coin],grid['buy_price'],grid['amount'],grid['sell_price'])
                return True
        except Exception as e:
            self.log(f"매수 오류: {e}","ERROR",coin)
        return False

    def execute_sell(self, coin, pos):
        try:
            res=self.upbit.sell_market_order(coin,pos['volume'])
            logging.debug("매도 결과:%s",res)
            if res and 'uuid' in res:
                prof=(pos['sell_price']-pos['buy_price'])*pos['volume']
                self.total_trades+=1
                self.total_profit+=prof
                if prof>0:
                    self.winning_trades+=1
                for g in self.coin_bots[coin]['grids']:
                    if g['id']==pos['grid_id']:
                        g['status'],g['volume']='waiting',0
                self.log(f"매도 | Lv.{pos['grid_id']} | {prof:+,.0f}원","SELL",coin)
                self.telegram.send_sell_alert(self.coin_names[coin],pos['sell_price'],prof,prof/pos['buy_price']*100)
                self.coin_bots[coin]['positions'].remove(pos)
                return True
        except Exception as e:
            self.log(f"매도 오류: {e}","ERROR",coin)
        return False

    def check_all_signals(self):
        for coin in self.portfolio:
            price=self.get_current_price(coin)
            if price==0: continue
            for g in self.coin_bots[coin]['grids']:
                if g['status']=="waiting" and price<=g['buy_price']:
                    self.execute_buy(coin,g); time.sleep(0.1)
            for p in list(self.coin_bots[coin]['positions']):
                if price>=p['sell_price']:
                    self.execute_sell(coin,p); time.sleep(0.1)

    def calculate_total_value(self):
        krw=self.get_balance("KRW")
        coin_val=0
        for coin in self.portfolio:
            bal=self.get_balance(coin)
            if bal:
                coin_val+=bal*self.get_current_price(coin)
        return krw+coin_val

    def get_current_balances(self):
        """현재 모든 자산의 수량과 가격 반환"""
        balances = {}
        balances["KRW"] = (self.get_balance("KRW"), 1)
        for coin in self.portfolio:
            amt = self.get_balance(coin)
            price = self.get_current_price(coin)
            balances[coin] = (amt, price)
        return balances

    def check_risk_limits(self):
        total=self.calculate_total_value()
        pct=(total-self.initial_balance)/self.initial_balance*100 if self.initial_balance else 0
        if pct< -config.STOP_LOSS:
            self.telegram.send_stop_message(f"손실 한도 초과({pct:.2f}%)",total,total-self.initial_balance)
            return False
        if pct>=config.DAILY_PROFIT_TARGET:
            self.telegram.send_stop_message(f"목표 달성({pct:.2f}%)",total,total-self.initial_balance)
            return False
        return True

    def show_status(self):
        total=self.calculate_total_value()
        prof=total-self.initial_balance
        pct=prof/self.initial_balance*100 if self.initial_balance else 0
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 평가액: {total:,.0f}원 | 수익: {prof:+,.0f}원 ({pct:+.2f}%) | 거래: {self.total_trades}회")

    def run(self):
        print("\n⚠️  업비트 잔고 전액을 투자합니다.")
        if input("계속하시겠습니까? (yes 입력): ").lower()!="yes":
            print("봇을 종료합니다."); return

        if not self.setup_all_grids():
            self.log("그리드 설정 실패","ERROR"); return

        self.log("🚀 자동매매 시작","SUCCESS")
        start_time = datetime.now()
        loop=0
        
        try:
            while not self.should_stop:
                # Telegram 명령 처리
                for upd in self.telegram.get_updates():
                    txt=upd.get("message",{}).get("text","")
                    if txt=="/help":
                        self.telegram.send_help()
                    elif txt=="/status":
                        total = self.calculate_total_value()
                        profit = total-self.initial_balance
                        pct = profit/self.initial_balance*100 if self.initial_balance else 0
                        balances = self.get_current_balances()
                        self.telegram.send_status(total,profit,pct,self.total_trades,self.winning_trades,balances)
                    elif txt=="/pause":
                        self.is_paused = True
                        self.telegram.send_message("⏸️ 자동매매가 일시 중지되었습니다.")
                    elif txt=="/resume":
                        self.is_paused = False
                        self.telegram.send_message("▶️ 자동매매가 재개되었습니다.")
                    elif txt=="/stop":
                        self.should_stop = True
                        break

                # 일시 중지 상태
                if self.is_paused:
                    time.sleep(config.CHECK_INTERVAL)
                    continue

                # 매매 로직
                self.check_all_signals()
                if not self.check_risk_limits(): 
                    break

                # 1분마다 텔레그램 상태 알림 (수익률 + 각 코인 수량/금액)
                if loop%(60//config.CHECK_INTERVAL)==0:
                    total = self.calculate_total_value()
                    profit = total-self.initial_balance
                    pct = profit/self.initial_balance*100 if self.initial_balance else 0
                    balances = self.get_current_balances()
                    self.telegram.send_status(total,profit,pct,self.total_trades,self.winning_trades,balances)

                # 10분마다 콘솔 출력
                if loop%(600//config.CHECK_INTERVAL)==0:
                    self.show_status()

                loop+=1
                time.sleep(config.CHECK_INTERVAL)

        except KeyboardInterrupt:
            self.log("사용자 중지","WARNING")
        except Exception as e:
            self.log(f"오류: {e}","ERROR")
            self.telegram.send_error_alert(str(e))
        finally:
            end_time = datetime.now()
            duration = str(end_time-start_time).split('.')[0]
            final=self.calculate_total_value()
            profit=final-self.initial_balance
            pct=profit/self.initial_balance*100 if self.initial_balance else 0
            balances = self.get_current_balances()
            self.telegram.send_final_result(
                final, self.initial_balance, profit, pct,
                self.total_trades, self.winning_trades,
                duration, balances
            )

if __name__=="__main__":
    AutoTradingBot().run()

