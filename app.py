import os
import logging
import asyncio
from threading import Thread
import time
import sys
from flask import Flask

# Crée l'application Flask pour Render
app = Flask(__name__)

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
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

@app.route('/ping')
def ping():
    return 'PONG', 200

def run_telegram_bot():
    """Lance le bot Telegram dans un thread séparé"""
    try:
        from crypto_bot import main as run_bot
        asyncio.run(run_bot())
    except ImportError as e:
        logger.error(f"❌ Impossible d'importer crypto_bot: {e}")
    except Exception as e:
        logger.error(f"❌ Erreur dans le bot: {e}")
        time.sleep(5)
        run_telegram_bot()  # Redémarre en cas d'erreur

def keep_alive():
    """Auto-ping pour éviter la mise en veille sur Render"""
    import threading
    import requests
    
    def ping_server():
        while True:
            try:
                time.sleep(60)  # Attendre 1 minute
                
                # URL de notre propre service
                render_url = os.environ.get('RENDER_EXTERNAL_URL')
                if render_url:
                    response = requests.get(f"{render_url}/health", timeout=10)
                    logger.info(f"✅ Auto-ping réussi: {response.status_code}")
                else:
                    # En développement local
                    logger.info("🔧 Mode développement")
            except Exception as e:
                logger.error(f"❌ Erreur auto-ping: {e}")
            finally:
                time.sleep(240)  # Attendre 4 minutes (total 5 minutes)
    
    thread = threading.Thread(target=ping_server, daemon=True)
    thread.start()
    logger.info("🔄 Auto-ping activé (toutes les 5 minutes)")

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 DÉMARRAGE CRYPTO SENTINEL BOT")
    print("=" * 50)
    
    # Vérifier les variables d'environnement
    token = os.environ.get('TELEGRAM_TOKEN')
    if not token or token == 'TON_TOKEN_ICI':
        print("⚠️ ATTENTION: TELEGRAM_TOKEN non configuré!")
    else:
        print("✅ TELEGRAM_TOKEN configuré")
    
    # Démarrer le bot dans un thread
    print("🤖 Lancement du bot Telegram...")
    bot_thread = Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    # Démarrer l'auto-ping sur Render
    if os.environ.get('RENDER'):
        keep_alive()
        print("🌐 Mode Render - Auto-ping activé")
    else:
        print("💻 Mode développement local")
    
    # Message de confirmation
    print("\n" + "=" * 50)
    print("✅ BOT PRÊT À RECEVOIR DES MESSAGES!")
    print("📱 Ouvrez Telegram et tapez /start")
    print("=" * 50 + "\n")
    
    # Démarrer Flask
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
