import boto3
import os

# ===== AWS SSM 설정 =====
# 파라미터가 저장된 리전(eu-north-1)으로 설정
AWS_REGION = os.getenv("AWS_REGION", "eu-north-1")
ssm = boto3.client("ssm", region_name=AWS_REGION)

def get_ssm(name):
    """SSM Parameter Store에서 SecureString 파라미터 가져오기"""
    resp = ssm.get_parameter(Name=name, WithDecryption=True)
    return resp["Parameter"]["Value"]

# ===== 업비트 API 키 설정 =====
ACCESS_KEY = get_ssm("/coin-bot/upbit/access_key")
SECRET_KEY = get_ssm("/coin-bot/upbit/secret_key")

# ===== 텔레그램 봇 설정 =====
TELEGRAM_BOT_TOKEN = "8292969005:AAGerH-0LmYcCmRgiM-j1eKPFCwkf6C_SJU"
TELEGRAM_CHAT_ID    = "8403612605"

# ===== 투자 설정 =====
USE_ALL_BALANCE = True
SAFETY_RESERVE  = 10000

# ===== 5개 코인 포트폴리오 비율 =====
PORTFOLIO = {
    "KRW-BTC": 0.30,
    "KRW-ETH": 0.20,
    "KRW-XRP": 0.20,
    "KRW-SOL": 0.20,
    "KRW-ADA": 0.10
}

# ===== 그리드 트레이딩 설정 =====
GRID_COUNT = 10
GRID_GAP   = 1.5

# ===== 리스크 관리 설정 =====
STOP_LOSS           = 8
DAILY_PROFIT_TARGET = 3

# ===== 운영 설정 =====
CHECK_INTERVAL  = 20
ENABLE_LOG      = True
ENABLE_TELEGRAM = True

