# ===== 업비트 API 키 설정 =====
import os

ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY")
SECRET_KEY = os.getenv("UPBIT_SECRET_KEY")

# ===== 텔레그램 봇 설정 =====
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID    = os.getenv("TELEGRAM_CHAT_ID")

# ===== 투자 설정 =====
# 전체 잔고 사용 여부 (True: 전체, False: 안전 예비금 제외)
USE_ALL_BALANCE = True
# 안전 예비금 (원화 최소 보유 금액, 매수 수수료 대비)
SAFETY_RESERVE  = 10000

# ===== 5개 코인 포트폴리오 비율 =====
PORTFOLIO = {
    "KRW-BTC": 0.30,   # 비트코인 30%
    "KRW-ETH": 0.20,   # 이더리움 20%
    "KRW-XRP": 0.20,   # 리플 20%
    "KRW-SOL": 0.20,   # 솔라나 20%
    "KRW-ADA": 0.10    # 카르다노 10%
}

# ===== 그리드 트레이딩 설정 =====
GRID_COUNT = 10      # 코인당 그리드 개수
GRID_GAP   = 1.5     # 그리드 간격(%)

# ===== 리스크 관리 설정 =====
STOP_LOSS         = 8   # 최대 손실(%)
DAILY_PROFIT_TARGET = 3 # 일일 목표(%)

# ===== 운영 설정 =====
CHECK_INTERVAL  = 20   # 체크 주기(초)
ENABLE_LOG      = True # 로그 기록 여부
ENABLE_TELEGRAM = True # 텔레그램 알림 여부

