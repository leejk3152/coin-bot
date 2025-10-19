# ===== 업비트 API 키 설정 =====
ACCESS_KEY = "your-access-key-here"
SECRET_KEY = "your-secret-key-here"

# ===== 텔레그램 봇 설정 =====
TELEGRAM_BOT_TOKEN = "8292969005:AAGerH-0LmYcCmRgiM-j1eKPFCwkf6C_SJU"  # 나중에 발급받을 것
TELEGRAM_CHAT_ID = "8403612605"  # 나중에 알려드릴 것

# ===== 투자 설정 =====
USE_ALL_BALANCE = True  # 전체 잔고 사용 (True로 고정!)
SAFETY_RESERVE = 10000  # 안전 예비금: 1만원 (수수료 대비)

# ===== 5개 코인 포트폴리오 비율 =====
PORTFOLIO = {
    "KRW-BTC": 0.30,   # 30% - 비트코인
    "KRW-ETH": 0.20,   # 20% - 이더리움
    "KRW-XRP": 0.20,   # 20% - 리플
    "KRW-SOL": 0.20,   # 20% - 솔라나
    "KRW-ADA": 0.10    # 10% - 카르다노
}

# ===== 그리드 트레이딩 설정 =====
GRID_COUNT = 10        # 코인당 그리드 개수
GRID_GAP = 1.5         # 그리드 간격: 1.5%

# ===== 리스크 관리 설정 =====
STOP_LOSS = 8          # 최대 손실: 8%
DAILY_PROFIT_TARGET = 3  # 일일 목표: 3%

# ===== 운영 설정 =====
CHECK_INTERVAL = 20    # 체크 주기: 20초
ENABLE_LOG = True      # 로그 기록
ENABLE_TELEGRAM = True  # 텔레그램 알림
