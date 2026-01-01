from flask import Flask
import os
import logging
from threading import Thread
import time
import sys

# CRUCIAL : Crée l'application Flask AU DÉBUT
app = Flask(__name__)

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    return '''
    <html>
        <head><title>Crypto Sentinel Bot</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1>🛡️ Crypto Sentinel Bot</h1>
            <p>Votre bot Telegram crypto est en ligne !</p>
            <p>Ouvrez Telegram et utilisez /start</p>
            <p>Statut: <span style="color: green;">● En ligne</span></p>
        </body>
    </html>
    '''

@app.route('/health')
def health():
    return 'OK', 200

def run_bot():
    """Lance le bot Telegram"""
    try:
        print("🤖 Importation du bot...")
        from crypto_bot import start_bot
        print("🤖 Démarrage du bot...")
        start_bot()
    except Exception as e:
        print(f"❌ Erreur dans le bot: {e}")
        import traceback
        traceback.print_exc()
        time.sleep(10)
        run_bot()  # Redémarre

def keep_alive():
    """Auto-ping pour éviter la mise en veille"""
    import threading
    import requests
    
    def ping_server():
        while True:
            try:
                time.sleep(300)  # 5 minutes
                render_url = os.environ.get('RENDER_EXTERNAL_URL', 'https://crypto-bot-9qtg.onrender.com')
                response = requests.get(f"{render_url}/health", timeout=10)
                print(f"✅ Ping: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Ping échoué: {e}")
    
    thread = threading.Thread(target=ping_server, daemon=True)
    thread.start()
    print("🔄 Auto-ping activé")

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 CRYPTO SENTINEL BOT - RENDER")
    print("=" * 50)
    
    # Vérifier le token
    token = os.environ.get('TELEGRAM_TOKEN')
    if token and token != 'TON_TOKEN_ICI':
        print("✅ Token configuré")
    else:
        print("⚠️ Token non configuré")
    
    # Démarrer le bot dans un thread
    print("🤖 Lancement du bot Telegram...")
    bot_thread = Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Auto-ping sur Render
    if os.environ.get('RENDER'):
        keep_alive()
        print("🌐 Mode Render - En ligne")
    
    print("\n✅ Serveur web démarré")
    print("📱 Testez sur Telegram avec /start")
    print("=" * 50)
    
    # Démarrer Flask
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
