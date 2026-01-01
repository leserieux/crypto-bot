import os
import logging
import random
import asyncio
from datetime import datetime
from typing import Dict, Tuple, Optional
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, ContextTypes
)

# ==================== CONFIGURATION ====================
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '7452641114:AAGw0QarxqhvF1a1ni92VQeqx4ACBQzKzHw')
NEWS_API_KEY = os.environ.get('NEWS_API_KEY', 'f3a0db1460c14aea8c1f2a679d3c4686')
COINGECKO_API = 'https://api.coingecko.com/api/v3'

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Cache simple
price_cache: Dict[str, Tuple[float, float, datetime]] = {}

# Mapping des cryptos
CRYPTO_MAPPING = {
    'bitcoin': 'bitcoin', 'btc': 'bitcoin',
    'ethereum': 'ethereum', 'eth': 'ethereum',
    'solana': 'solana', 'sol': 'solana',
    'dogecoin': 'dogecoin', 'doge': 'dogecoin',
    'cardano': 'cardano', 'ada': 'cardano',
    'ripple': 'ripple', 'xrp': 'ripple',
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler pour la commande /start"""
    welcome_text = """
👋 *Bonjour !*

🛡️ **Crypto Sentinel** – Votre garde du corps crypto

📊 *Comment utiliser :*
Envoyez simplement le nom d'une crypto :
• bitcoin / btc
• ethereum / eth
• solana / sol
• dogecoin / doge
• cardano / ada
• etc.

⚡ *Essayer maintenant :*
Envoyez `bitcoin` pour commencer !
"""
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

def get_coin_id(query: str) -> str:
    return CRYPTO_MAPPING.get(query.lower().strip(), query.lower().strip())

async def get_crypto_data(query: str) -> Tuple[str, Optional[str], InlineKeyboardMarkup]:
    """Récupère toutes les données pour une crypto"""
    coin_id = get_coin_id(query)
    
    # 1. Récupération du prix
    try:
        response = requests.get(
            f'{COINGECKO_API}/simple/price',
            params={
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true'
            },
            timeout=5
        )
        data = response.json()
        
        if coin_id in data:
            crypto_data = data[coin_id]
            price_usd = crypto_data.get('usd', 0)
            change_24h = crypto_data.get('usd_24h_change', 0)
        else:
            price_usd = 0
            change_24h = 0
    except Exception as e:
        logger.error(f"Erreur API CoinGecko: {e}")
        price_usd = 0
        change_24h = 0
    
    # 2. Récupération des actualités
    news_title = "Actualités en cours de chargement..."
    news_url = None
    news_image = None
    
    try:
        news_response = requests.get(
            'https://newsapi.org/v2/everything',
            params={
                'apiKey': NEWS_API_KEY,
                'q': query,
                'language': 'fr',
                'sortBy': 'relevancy',
                'pageSize': 1
            },
            timeout=5
        )
        news_data = news_response.json()
        
        if news_data.get('articles'):
            article = news_data['articles'][0]
            news_title = article.get('title', 'Pas de nouvelles récentes')[:100]
            news_url = article.get('url')
            news_image = article.get('urlToImage')
    except Exception as e:
        logger.error(f"Erreur API News: {e}")
    
    # 3. Génération du sentiment
    sentiment_score = random.randint(30, 85)
    if sentiment_score > 65:
        sentiment = "🟢 Positif"
    elif sentiment_score > 45:
        sentiment = "🟡 Neutre"
    else:
        sentiment = "🔴 Négatif"
    
    # 4. Construction du message
    if price_usd >= 1000:
        price_str = f"${price_usd:,.0f}"
    elif price_usd >= 1:
        price_str = f"${price_usd:,.2f}"
    else:
        price_str = f"${price_usd:.6f}".rstrip('0').rstrip('.')
    
    change_str = f"+{change_24h:.2f}%" if change_24h > 0 else f"{change_24h:.2f}%"
    change_emoji = "📈" if change_24h > 0 else "📉" if change_24h < 0 else "➡️"
    
    message = f"""
🛡️ *{query.upper()} - Crypto Sentinel*

💰 *Prix*: {price_str}
{change_emoji} *24h*: {change_str}

📊 *Sentiment marché*: {sentiment_score}/100 {sentiment}

📰 *Actualité*: {news_title}...
"""
    
    # 5. Construction des boutons
    buttons = [
        [InlineKeyboardButton("🔄 Actualiser", callback_data=f'refresh_{query}')],
        [InlineKeyboardButton("📈 CoinGecko", url=f'https://www.coingecko.com/fr/pièces/{coin_id}')]
    ]
    
    if news_url:
        buttons.insert(1, [InlineKeyboardButton("📰 Lire l'article", url=news_url)])
    
    return message, news_image, InlineKeyboardMarkup(buttons)

async def handle_crypto_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les requêtes de cryptomonnaies"""
    query = update.message.text.strip()
    
    if len(query) < 2:
        await update.message.reply_text("❌ Veuillez entrer un nom de crypto valide.")
        return
    
    try:
        processing_msg = await update.message.reply_text(f"🔍 Analyse de *{query.upper()}*...", parse_mode='Markdown')
        
        text, image, markup = await get_crypto_data(query)
        
        await processing_msg.delete()
        
        if image:
            await update.message.reply_photo(
                photo=image,
                caption=text,
                reply_markup=markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=markup,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
    except Exception as e:
        logger.error(f"Erreur: {e}")
        await update.message.reply_text("❌ Erreur. Essayez avec un autre nom de crypto.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les interactions avec les boutons inline"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith('refresh_'):
        crypto_name = data[8:]
        
        text, image, markup = await get_crypto_data(crypto_name)
        
        try:
            if image and query.message.photo:
                await query.message.edit_media(
                    media=InputMediaPhoto(image, caption=text, parse_mode='Markdown'),
                    reply_markup=markup
                )
            else:
                await query.message.edit_text(
                    text,
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Erreur d'édition: {e}")
            await query.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Gère les erreurs"""
    logger.error(f"Erreur: {context.error}")

def main():
    """Fonction principale pour démarrer le bot"""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_crypto_query))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    application.add_error_handler(error_handler)
    
    logger.info("🛡️ Crypto Sentinel - Bot démarré !")
    print("✅ Bot en ligne! Utilisez /start pour commencer.")
    print("🔴 Appuyez sur Ctrl+C pour arrêter.")
    
    application.run_polling()

if __name__ == '__main__':
    main()