import os
import logging
from flask import Flask
from threading import Thread
import asyncio

app = Flask(__name__)

# Désactiver les logs verbeux
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Vérifier si on est sur Render
ON_RENDER = os.environ.get('RENDER', '').lower() == 'true'

def run_bot():
    """Fonction pour lancer le bot"""
    try:
        if ON_RENDER:
            logger.info("🛡️ Mode RENDER - Bot démarré")
            # Sur Render, on utilise polling simple
            from crypto_bot import main
            main()
        else:
            logger.info("🛡️ Mode LOCAL - Bot démarré")
            from crypto_bot import main
            main()
    except Exception as e:
        logger.error(f"❌ Erreur bot: {e}")

@app.route('/')
def home():
    return '🛡️ Crypto Sentinel Bot - En ligne!'

@app.route('/health')
def health():
    return 'OK', 200

if __name__ == '__main__':
    # Lancer le bot dans un thread séparé
    if ON_RENDER:
        logger.info("✅ Configuration Render détectée")
        # Sur Render, on démarre le bot
        bot_thread = Thread(target=run_bot, daemon=True)
        bot_thread.start()
    
    # Port pour Render
    port = int(os.environ.get('PORT', 10000))
    
    # Démarrer Flask
    if ON_RENDER:
        # Sur Render, pas de bot en local
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        # En local, démarrer le bot aussi
        bot_thread = Thread(target=run_bot, daemon=True)
        bot_thread.start()
        logger.info("🌐 Serveur web: http://localhost:{}".format(port))
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)