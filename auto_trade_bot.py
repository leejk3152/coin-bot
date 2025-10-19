import pyupbit
import time
from datetime import datetime
import config
from telegram_bot import TelegramBot

class AutoTradingBot:
    def __init__(self):
        """전액 투자 자동매매 봇"""
        print("\n" + "=" * 90)
        print("🚀 전액 투자 자동매매 봇 v3.0 (AWS + 텔레그램)")
        print("=" * 90)
        
        # 업비트 연결
        self.upbit = pyupbit.Upbit(config.ACCESS_KEY, config.SECRET_KEY)
        
        # 텔레그램 봇
        self.telegram = TelegramBot()
        
        # 포트폴리오
        self.portfolio = config.PORTFOLIO
        self.coin_bots = {}
        
        # 통계
        self.total_trades = 0
        self.winning_trades = 0
        self.total_profit = 0
        self.initial_balance = 0
        self.investment_amount = 0
        
        # 코인 이름
        self.coin_names = {
            "KRW-BTC": "비트코인",
            "KRW-ETH": "이더리움",
            "KRW-XRP": "리플",
            "KRW-SOL": "솔라나",
            "KRW-ADA": "카르다노"
        }
    
    def log(self, message, level="INFO", coin=None):
        """로그 기록"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        icons = {
            "INFO": "ℹ️",
            "BUY": "🔴",
            "SELL": "🔵",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌"
        }
        icon = icons.get(level, "📝")
        
        if coin:
            coin_name = self.coin_names.get(coin, coin)
            coin_tag = f"[{coin_name}]"
        else:
            coin_tag = ""
        
        log_msg = f"[{timestamp}] {icon} {coin_tag} {message}"
        print(log_msg)
        
        if config.ENABLE_LOG:
            with open("trading_log.txt", "a", encoding="utf-8") as f:
                f.write(log_msg + "\n")
    
    def get_balance(self, ticker="KRW"):
        """잔고 조회"""
        try:
            if ticker == "KRW":
                return self.upbit.get_balance("KRW")
            else:
                return self.upbit.get_balance(ticker.replace("KRW-", ""))
        except Exception as e:
            self.log(f"잔고 조회 실패: {e}", "ERROR")
            return 0
    
    def get_current_price(self, coin):
        """현재가 조회"""
        try:
            price = pyupbit.get_current_price(coin)
            return price if price else 0
        except:
            return 0
    
    def calculate_investment(self):
        """투자 금액 계산 (전액)"""
        total_krw = self.get_balance("KRW")
        
        # 안전 예비금 제외
        available = total_krw - config.SAFETY_RESERVE
        
        if available < 50000:
            self.log(f"투자 가능 금액 부족: {available:,.0f}원", "ERROR")
            return 0
        
        self.log(f"총 원화 잔고: {total_krw:,.0f}원", "INFO")
        self.log(f"투자 금액: {available:,.0f}원 (예비금 {config.SAFETY_RESERVE:,.0f}원 제외)", "SUCCESS")
        
        return available
    
    def setup_coin_grids(self, coin, investment_amount):
        """코인별 그리드 설정"""
        current_price = self.get_current_price(coin)
        
        if current_price == 0:
            return False
        
        amount_per_grid = investment_amount / config.GRID_COUNT
        
        grids = []
        for i in range(1, config.GRID_COUNT + 1):
            buy_price = current_price * (1 - config.GRID_GAP * i / 100)
            sell_price = buy_price * (1 + config.GRID_GAP / 100)
            
            grids.append({
                'id': i,
                'buy_price': buy_price,
                'sell_price': sell_price,
                'amount': amount_per_grid,
                'status': 'waiting',
                'volume': 0
            })
        
        self.coin_bots[coin] = {
            'grids': grids,
            'positions': [],
            'investment': investment_amount,
            'trades': 0,
            'wins': 0,
            'profit': 0
        }
        
        self.log(f"그리드 설정 | {investment_amount:,.0f}원 | 현재가: {current_price:,.0f}원", "SUCCESS", coin)
        return True
    
    def setup_all_grids(self):
        """전체 그리드 설정"""
        # 전액 계산
        self.investment_amount = self.calculate_investment()
        
        if self.investment_amount == 0:
            return False
        
        self.initial_balance = self.get_balance("KRW")
        
        print(f"\n📊 포트폴리오 배분 (총 {self.investment_amount:,.0f}원)")
        print("-" * 90)
        
        for coin, ratio in self.portfolio.items():
            investment = self.investment_amount * ratio
            coin_name = self.coin_names.get(coin, coin)
            
            print(f"   {coin_name:8s} | {investment:>12,.0f}원 ({ratio*100:>5.1f}%)")
            
            if not self.setup_coin_grids(coin, investment):
                return False
            
            time.sleep(0.1)
        
        print("-" * 90)
        
        # 텔레그램 시작 알림
        self.telegram.send_start_message(self.investment_amount, self.initial_balance)
        
        return True
    
    def execute_buy(self, coin, grid):
        """매수 실행"""
        if self.get_balance("KRW") < grid['amount']:
            return False
        
        try:
            result = self.upbit.buy_market_order(coin, grid['amount'])
            
            if result and 'uuid' in result:
                executed_volume = float(result.get('executed_volume', 0))
                
                grid['status'] = 'bought'
                grid['volume'] = executed_volume
                
                self.coin_bots[coin]['positions'].append({
                    'grid_id': grid['id'],
                    'buy_price': grid['buy_price'],
                    'sell_price': grid['sell_price'],
                    'volume': executed_volume,
                    'buy_time': datetime.now()
                })
                
                self.log(f"매수 | Lv.{grid['id']} | {grid['buy_price']:,.0f}원", "BUY", coin)
                
                # 텔레그램 알림
                coin_name = self.coin_names[coin]
                self.telegram.send_buy_alert(
                    coin_name,
                    grid['buy_price'],
                    grid['amount'],
                    grid['sell_price']
                )
                
                return True
        except Exception as e:
            self.log(f"매수 오류: {e}", "ERROR", coin)
        
        return False
    
    def execute_sell(self, coin, position):
        """매도 실행"""
        try:
            result = self.upbit.sell_market_order(coin, position['volume'])
            
            if result and 'uuid' in result:
                profit_percent = (position['sell_price'] - position['buy_price']) / position['buy_price'] * 100
                profit_krw = (position['sell_price'] - position['buy_price']) * position['volume']
                
                # 통계 업데이트
                self.coin_bots[coin]['trades'] += 1
                self.coin_bots[coin]['profit'] += profit_krw
                self.total_trades += 1
                self.total_profit += profit_krw
                
                if profit_krw > 0:
                    self.coin_bots[coin]['wins'] += 1
                    self.winning_trades += 1
                
                # 그리드 초기화
                for grid in self.coin_bots[coin]['grids']:
                    if grid['id'] == position['grid_id']:
                        grid['status'] = 'waiting'
                        grid['volume'] = 0
                        break
                
                self.log(f"매도 | Lv.{position['grid_id']} | {profit_krw:+,.0f}원 ({profit_percent:+.2f}%)", "SELL", coin)
                
                # 텔레그램 알림
                coin_name = self.coin_names[coin]
                self.telegram.send_sell_alert(
                    coin_name,
                    position['sell_price'],
                    profit_krw,
                    profit_percent
                )
                
                self.coin_bots[coin]['positions'].remove(position)
                return True
        except Exception as e:
            self.log(f"매도 오류: {e}", "ERROR", coin)
        
        return False
    
    def check_coin_signals(self, coin):
        """매매 신호 확인"""
        current_price = self.get_current_price(coin)
        
        if current_price == 0:
            return
        
        bot_data = self.coin_bots[coin]
        
        # 매수
        for grid in bot_data['grids']:
            if grid['status'] == 'waiting' and current_price <= grid['buy_price']:
                if self.execute_buy(coin, grid):
                    time.sleep(0.1)
        
        # 매도
        for position in bot_data['positions'][:]:
            if current_price >= position['sell_price']:
                if self.execute_sell(coin, position):
                    time.sleep(0.1)
    
    def check_all_signals(self):
        """전체 확인"""
        for coin in self.portfolio.keys():
            self.check_coin_signals(coin)
    
    def calculate_total_value(self):
        """총 평가액"""
        krw = self.get_balance("KRW")
        total_coin_value = 0
        
        for coin in self.portfolio.keys():
            balance = self.get_balance(coin)
            price = self.get_current_price(coin)
            
            if balance and price:
                total_coin_value += balance * price
        
        return krw + total_coin_value
    
    def check_risk_limits(self):
        """리스크 체크"""
        if self.initial_balance == 0:
            return True
        
        total_value = self.calculate_total_value()
        profit = total_value - self.initial_balance
        profit_percent = (profit / self.initial_balance) * 100
        
        # 손실 한도
        if profit_percent < -config.STOP_LOSS:
            reason = f"최대 손실 도달 ({profit_percent:.2f}%)"
            self.telegram.send_stop_message(reason, total_value, profit)
            return False
        
        # 목표 달성
        if profit_percent >= config.DAILY_PROFIT_TARGET:
            reason = f"일일 목표 달성 ({profit_percent:.2f}%)"
            self.telegram.send_stop_message(reason, total_value, profit)
            return False
        
        return True
    
    def show_status(self):
        """상태 출력"""
        total_value = self.calculate_total_value()
        profit = total_value - self.initial_balance if self.initial_balance > 0 else 0
        profit_percent = (profit / self.initial_balance * 100) if self.initial_balance > 0 else 0
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] "
              f"평가액: {total_value:,.0f}원 | "
              f"수익: {profit:+,.0f}원 ({profit_percent:+.2f}%) | "
              f"거래: {self.total_trades}회")
    
    def run(self):
        """봇 실행"""
        print(f"\n⚠️  업비트 잔고 전액을 투자합니다.")
        confirm = input("계속하시겠습니까? (yes 입력): ")
        
        if confirm.lower() != 'yes':
            print("봇을 종료합니다.")
            return
        
        # 그리드 설정
        if not self.setup_all_grids():
            self.log("그리드 설정 실패", "ERROR")
            return
        
        self.log("🚀 24시간 자동매매 시작!", "SUCCESS")
        
        loop_count = 0
        
        try:
            while True:
                self.check_all_signals()
                
                if not self.check_risk_limits():
                    break
                
                # 10분마다 상태
                if loop_count % 30 == 0:
                    self.show_status()
                
                # 1시간마다 텔레그램 상태
                if loop_count % 180 == 0 and loop_count > 0:
                    total_value = self.calculate_total_value()
                    profit = total_value - self.initial_balance
                    profit_percent = (profit / self.initial_balance * 100)
                    self.telegram.send_status(
                        total_value,
                        profit,
                        profit_percent,
                        self.total_trades,
                        self.winning_trades
                    )
                
                loop_count += 1
                time.sleep(config.CHECK_INTERVAL)
                
        except KeyboardInterrupt:
            self.log("사용자 중지", "WARNING")
        except Exception as e:
            self.log(f"오류: {e}", "ERROR")
            self.telegram.send_error_alert(str(e))
        finally:
            total_value = self.calculate_total_value()
            profit = total_value - self.initial_balance
            self.log(f"최종 평가액: {total_value:,.0f}원 | 수익: {profit:+,.0f}원", "INFO")

if __name__ == "__main__":
    bot = AutoTradingBot()
    bot.run()
