import os
from flask import Flask
import asyncio
from threading import Thread
from crypto_bot import main as run_bot

app = Flask(__name__)

@app.route('/')
def home():
    return '🛡️ Crypto Sentinel Bot - En ligne!'

@app.route('/health')
def health():
    return 'OK', 200

def run_telegram_bot():
    """Lance le bot Telegram dans un thread séparé"""
    asyncio.run(run_bot())

if __name__ == '__main__':
    # Lance le bot Telegram dans un thread
    bot_thread = Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    # Lance Flask
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)