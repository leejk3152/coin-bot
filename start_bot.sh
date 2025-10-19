#!/bin/bash
cd ~/coin-bot
nohup bash -c "yes yes | python3 auto_trade_bot.py" > bot.log 2>&1 &

