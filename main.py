# -*- coding: utf-8 -*-
import asyncio
import re
import httpx
from bs4 import BeautifulSoup
import json
import os
import traceback
from urllib.parse import urljoin
from datetime import datetime, timedelta
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

# --- Configuration ---
YOUR_BOT_TOKEN = "8581273737:AAERI2iZwdqVkkj60xk3hvaQIpOXg0OY16o"
ADMIN_CHAT_IDS = ["8410638169"]
INITIAL_CHAT_IDS = ["-1003760844243"]

LOGIN_URL = "https://ivas.tempnum.qzz.io/login"
BASE_URL = "https://ivas.tempnum.qzz.io"
SMS_API_ENDPOINT = "https://ivas.tempnum.qzz.io/portal/sms/received/getsms"

USERNAME = "kumailahmed1947@gmail.com"
PASSWORD = "@Kumail1947"

USERNAME2 = "Mirohev740@gmail.com"
PASSWORD2 = "@Kumail1947"

POLLING_INTERVAL_SECONDS = 2
STATE_FILE = "processed_sms_ids.json"
CHAT_IDS_FILE = "chat_ids.json"

# Global Sessions - One for each account
session_client_1 = httpx.AsyncClient(timeout=20.0, follow_redirects=True)
session_state_1 = {"is_logged_in": False, "csrf_token": ""}

session_client_2 = httpx.AsyncClient(timeout=20.0, follow_redirects=True)
session_state_2 = {"is_logged_in": False, "csrf_token": ""}

message_cache = {}  # Store message data for callback queries
scheduled_deletes = {}  # Track messages scheduled for deletion

# --- Data Tables ---
COUNTRY_FLAGS = {
    "Afghanistan": "🇦🇫", "Albania": "🇦🇱", "Algeria": "🇩🇿", "Andorra": "🇦🇩", "Angola": "🇦🇴",
    "Argentina": "🇦🇷", "Armenia": "🇦🇲", "Australia": "🇦🇺", "Austria": "🇦🇹", "Azerbaijan": "🇦🇿",
    "Bahrain": "🇧🇭", "Bangladesh": "🇧🇩", "Belarus": "🇧🇾", "Belgium": "🇧🇪", "Benin": "🇧🇯",
    "Bhutan": "🇧🇹", "Bolivia": "🇧🇴", "Brazil": "🇧🇷", "Bulgaria": "🇧🇬", "Burkina Faso": "🇧🇫",
    "Cambodia": "🇰🇭", "Cameroon": "🇨🇲", "Canada": "🇨🇦", "Chad": "🇹🇩", "Chile": "🇨🇱",
    "China": "🇨🇳", "Colombia": "🇨🇴", "Congo": "🇨🇬", "Croatia": "🇭🇷", "Cuba": "🇨🇺",
    "Cyprus": "🇨🇾", "Czech Republic": "🇨🇿", "Denmark": "🇩🇰", "Egypt": "🇪🇬", "Estonia": "🇪🇪",
    "Ethiopia": "🇪🇹", "Finland": "🇫🇮", "France": "🇫🇷", "Gabon": "🇬🇦", "Gambia": "🇬🇲",
    "Georgia": "🇬🇪", "Germany": "🇩🇪", "Ghana": "🇬🇭", "Greece": "🇬🇷", "Guatemala": "🇬🇹",
    "Guinea": "🇬🇳", "Haiti": "🇭🇹", "Honduras": "🇭🇳", "Hong Kong": "🇭🇰", "Hungary": "🇭🇺",
    "Iceland": "🇮🇸", "India": "🇮🇳", "Indonesia": "🇮🇩", "Iran": "🇮🇷", "Iraq": "🇮🇶",
    "Ireland": "🇮🇪", "Israel": "🇮🇱", "Italy": "🇮🇹",
    "Ivory Coast": "🇨🇮", "Ivory": "🇨🇮", "Cote D'Ivoire": "🇨🇮", "Côte D'Ivoire": "🇨🇮",
    "Jamaica": "🇯🇲", "Japan": "🇯🇵", "Jordan": "🇯🇴", "Kazakhstan": "🇰🇿", "Kenya": "🇰🇪", "Kuwait": "🇰🇼",
    "Kyrgyzstan": "🇰🇬", "Laos": "🇱🇦", "Latvia": "🇱🇻", "Lebanon": "🇱🇧", "Liberia": "🇱🇷",
    "Libya": "🇱🇾", "Lithuania": "🇱🇹", "Luxembourg": "🇱🇺", "Madagascar": "🇲🇬", "Malaysia": "🇲🇾",
    "Mali": "🇲🇱", "Malta": "🇲🇹", "Mexico": "🇲🇽", "Moldova": "🇲🇩", "Monaco": "🇲🇨",
    "Mongolia": "🇲🇳", "Montenegro": "🇲🇪", "Morocco": "🇲🇦", "Mozambique": "🇲🇿", "Myanmar": "🇲🇲",
    "Namibia": "🇳🇦", "Nepal": "🇳🇵", "Netherlands": "🇳🇱", "New Zealand": "🇳🇿", "Nicaragua": "🇳🇮",
    "Niger": "🇳🇪", "Nigeria": "🇳🇬", "North Korea": "🇰🇵", "North Macedonia": "🇲🇰", "Norway": "🇳🇴",
    "Oman": "🇴🇲", "Pakistan": "🇵🇰", "Panama": "🇵🇦", "Paraguay": "🇵🇾", "Peru": "🇵🇪",
    "Philippines": "🇵🇭", "Poland": "🇵🇱", "Portugal": "🇵🇹", "Qatar": "🇶🇦", "Romania": "🇷🇴",
    "Russia": "🇷🇺", "Rwanda": "🇷🇼", "Saudi Arabia": "🇸🇦", "Senegal": "🇸🇳", "Serbia": "🇷🇸",
    "Sierra Leone": "🇸🇱", "Singapore": "🇸🇬", "Slovakia": "🇸🇰", "Slovenia": "🇸🇮", "Somalia": "🇸🇴",
    "South Africa": "🇿🇦", "South Korea": "🇰🇷", "Spain": "🇪🇸", "Sri Lanka": "🇱🇰", "Sudan": "🇸🇩",
    "Sweden": "🇸🇪", "Switzerland": "🇨🇭", "Syria": "🇸🇾", "Taiwan": "🇹🇼", "Tajikistan": "🇹🇯",
    "Tanzania": "🇹🇿", "Thailand": "🇹🇭", "Togo": "🇹🇬", "Tunisia": "🇹🇳", "Turkey": "🇹🇷",
    "Turkmenistan": "🇹🇲", "Uganda": "🇺🇬", "Ukraine": "🇺🇦", "United Arab Emirates": "🇦🇪", "United Kingdom": "🇬🇧",
    "United States": "🇺🇸", "Uruguay": "🇺🇾", "Uzbekistan": "🇺🇿", "Venezuela": "🇻🇪", "Vietnam": "🇻🇳",
    "Yemen": "🇾🇪", "Zambia": "🇿🇲", "Zimbabwe": "🇿🇼", "Unknown Country": "🏴‍☠️"
}

SERVICE_KEYWORDS = {
    "Facebook": ["facebook"], "Google": ["google", "gmail"], "WhatsApp": ["whatsapp"],
    "Telegram": ["telegram"], "Instagram": ["instagram"], "Amazon": ["amazon"],
    "Netflix": ["netflix"], "LinkedIn": ["linkedin"], "Microsoft": ["microsoft", "outlook", "live.com"],
    "Apple": ["apple", "icloud"], "Twitter": ["twitter"], "Snapchat": ["snapchat"],
    "TikTok": ["tiktok"], "Discord": ["discord"], "Signal": ["signal"],
    "Viber": ["viber"], "IMO": ["imo"], "PayPal": ["paypal"], "Binance": ["binance"],
    "Uber": ["uber"], "Bolt": ["bolt"], "Airbnb": ["airbnb"], "Yahoo": ["yahoo"],
    "Steam": ["steam"], "Blizzard": ["blizzard"], "Foodpanda": ["foodpanda"],
    "Pathao": ["pathao"], "Messenger": ["messenger", "meta"], "YouTube": ["youtube"],
    "X": ["x", "twitter"], "eBay": ["ebay"], "AliExpress": ["aliexpress"],
    "Alibaba": ["alibaba"], "Flipkart": ["flipkart"], "Spotify": ["spotify"],
    "Stripe": ["stripe"], "Cash App": ["cash app"], "Venmo": ["venmo"],
    "Wise": ["wise"], "Coinbase": ["coinbase"], "KuCoin": ["kucoin"],
    "Bybit": ["bybit"], "OKX": ["okx"], "Huobi": ["huobi"], "Kraken": ["kraken"],
    "MetaMask": ["metamask"], "Epic Games": ["epic games"], "PlayStation": ["playstation"],
    "Xbox": ["xbox"], "Twitch": ["twitch"], "Reddit": ["reddit"], "ProtonMail": ["protonmail"],
    "Zoho": ["zoho"], "Quora": ["quora"], "StackOverflow": ["stackoverflow"],
    "Indeed": ["indeed"], "Upwork": ["upwork"], "Fiverr": ["fiverr"],
    "Glassdoor": ["glassdoor"], "Booking.com": ["booking.com"], "Careem": ["careem"],
    "Swiggy": ["swiggy"], "Zomato": ["zomato"], "McDonald's": ["mcdonalds"],
    "KFC": ["kfc"], "Nike": ["nike"], "Adidas": ["adidas"], "Shein": ["shein"],
    "OnlyFans": ["onlyfans"], "Tinder": ["tinder"], "Bumble": ["bumble"],
    "Grindr": ["grindr"], "Line": ["line"], "WeChat": ["wechat"], "VK": ["vk"]
}

SERVICE_EMOJIS = {
    "Telegram": "📩", "WhatsApp": "🟢", "Facebook": "📘", "Instagram": "📸", "Messenger": "💬",
    "Google": "🔍", "Gmail": "✉️", "YouTube": "▶️", "Twitter": "🐦", "X": "❌",
    "TikTok": "🎵", "Snapchat": "👻", "Amazon": "🛒", "eBay": "📦", "AliExpress": "📦",
    "Alibaba": "🏭", "Flipkart": "📦", "Microsoft": "🪟", "Outlook": "📧", "Skype": "📞",
    "Netflix": "🎬", "Spotify": "🎶", "Apple": "🍏", "iCloud": "☁️", "PayPal": "💰",
    "Stripe": "💳", "Cash App": "💵", "Venmo": "💸", "Zelle": "🏦", "Wise": "🌐",
    "Binance": "🪙", "Coinbase": "🪙", "KuCoin": "🪙", "Bybit": "📈", "OKX": "🟠",
    "Huobi": "🔥", "Kraken": "🐙", "MetaMask": "🦊", "Discord": "🗨️", "Steam": "🎮",
    "Epic Games": "🕹️", "PlayStation": "🎮", "Xbox": "🎮", "Twitch": "📺", "Reddit": "👽",
    "Yahoo": "🟣", "ProtonMail": "🔐", "Zoho": "📬", "Quora": "❓", "StackOverflow": "🧑‍💻",
    "LinkedIn": "💼", "Indeed": "📋", "Upwork": "🧑‍💻", "Fiverr": "💻", "Glassdoor": "🔎",
    "Airbnb": "🏠", "Booking.com": "🛏️", "Uber": "🚗", "Lyft": "🚕", "Bolt": "🚖",
    "Careem": "🚗", "Swiggy": "🍔", "Zomato": "🍽️", "Foodpanda": "🍱",
    "McDonald's": "🍟", "KFC": "🍗", "Nike": "👟", "Adidas": "👟", "Shein": "👗",
    "OnlyFans": "🔞", "Tinder": "🔥", "Bumble": "🐝", "Grindr": "😈", "Signal": "🔐",
    "Viber": "📞", "Line": "💬", "WeChat": "💬", "VK": "🌐", "Unknown": "❓"
}

# --- Helper Functions ---
def load_chat_ids():
    if not os.path.exists(CHAT_IDS_FILE):
        with open(CHAT_IDS_FILE, 'w') as f: json.dump(INITIAL_CHAT_IDS, f)
        return INITIAL_CHAT_IDS
    try:
        with open(CHAT_IDS_FILE, 'r') as f: return json.load(f)
    except: return INITIAL_CHAT_IDS

def save_chat_ids(chat_ids):
    with open(CHAT_IDS_FILE, 'w') as f: json.dump(chat_ids, f, indent=4)

def load_processed_ids():
    if not os.path.exists(STATE_FILE): return set()
    try:
        with open(STATE_FILE, 'r') as f: return set(json.load(f))
    except: return set()

def save_processed_id(sms_id):
    processed_ids = load_processed_ids()
    processed_ids.add(sms_id)
    with open(STATE_FILE, 'w') as f: json.dump(list(processed_ids), f)

def escape_markdown(text):
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))

def mask_phone_number(phone):
    """Mask phone number to show only first 6 and last 3 digits with INF in middle"""
    phone = str(phone).strip()
    if len(phone) <= 9:
        return phone
    # Show first 6 digits + INF + last 3 digits
    return f"{phone[:6]}INF{phone[-3:]}"

def get_service_abbr(service):
    """Get service abbreviation without escaping"""
    service_map = {
        "WhatsApp": "WS", "Facebook": "FB", "Instagram": "IG", "Telegram": "TG",
        "Google": "GO", "Gmail": "GM", "Twitter": "TW", "X": "TW",
        "TikTok": "TK", "Snapchat": "SC", "Discord": "DC", "Microsoft": "MS",
        "Apple": "AP", "Amazon": "AM", "Netflix": "NF", "LinkedIn": "LI",
        "YouTube": "YT", "PayPal": "PP", "Binance": "BN", "Coinbase": "CB",
        "Uber": "UB", "Messenger": "ME", "Signal": "SG", "Viber": "VB",
        "WeChat": "WC", "Line": "LN", "Steam": "ST", "PlayStation": "PS",
        "Xbox": "XB", "Epic Games": "EG", "Reddit": "RD", "Twitch": "TC",
        "Spotify": "SP", "Unknown": "UN"
    }
    return service_map.get(service, service[:2].upper())

def get_language_name(language_tag):
    """Extract language name from escaped tag"""
    # Remove the escape characters and # sign
    return language_tag.replace('\\#', '').replace('#', '')

def detect_language(text):
    """Detect language from SMS text based on character patterns"""
    text = str(text).strip()
    text_lower = text.lower()
    
    # Arabic script (Arabic, Urdu, Persian, etc.)
    if re.search(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text):
        # Check for specific Urdu words
        if re.search(r'(کوڈ|واٹس|ایپ|نمبر|تصدیق)', text):
            return "Urdu"
        # Check for Arabic
        elif re.search(r'(رمز|كود|واتس|تطبيق)', text):
            return "Arabic"
        # Check for Persian
        elif re.search(r'(کد|واتساپ|برنامه)', text):
            return "Persian"
        else:
            return "Arabic"  # Default for Arabic script
    
    # Chinese
    elif re.search(r'[\u4e00-\u9fff]', text):
        return "Chinese"
    
    # Japanese
    elif re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):
        return "Japanese"
    
    # Korean
    elif re.search(r'[\uac00-\ud7af\u1100-\u11ff]', text):
        return "Korean"
    
    # Hindi/Devanagari
    elif re.search(r'[\u0900-\u097F]', text):
        return "Hindi"
    
    # Bengali
    elif re.search(r'[\u0980-\u09FF]', text):
        return "Bengali"
    
    # Thai
    elif re.search(r'[\u0E00-\u0E7F]', text):
        return "Thai"
    
    # Hebrew
    elif re.search(r'[\u0590-\u05FF]', text):
        return "Hebrew"
    
    # Russian/Cyrillic
    elif re.search(r'[\u0400-\u04FF]', text):
        return "Russian"
    
    # Greek
    elif re.search(r'[\u0370-\u03FF]', text):
        return "Greek"
    
    # Vietnamese (has special characters)
    elif re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', text, re.IGNORECASE):
        return "Vietnamese"
    
    # For Latin script languages, check English FIRST with strong indicators
    elif re.search(r'\b(your|verification|account|security|confirm|authenticate|login|sign|register|password|otp|whatsapp|telegram|facebook|google|instagram)\b', text_lower):
        return "English"
    
    # Spanish (more specific words that don't overlap with English)
    elif re.search(r'\b(código|tu|verificación|cuenta|contraseña|autenticar|iniciar)\b', text_lower):
        return "Spanish"
    
    # French (more specific French words)
    elif re.search(r'\b(votre|vérification|compte|mot de passe|authentifier|connexion)\b', text_lower):
        return "French"
    
    # Portuguese (more specific)
    elif re.search(r'\b(código|seu|verificação|conta|senha|autenticar)\b', text_lower):
        return "Portuguese"
    
    # German (more specific)
    elif re.search(r'\b(ihr|verifizierung|konto|passwort|bestätigen|anmelden)\b', text_lower):
        return "German"
    
    # Italian (more specific)
    elif re.search(r'\b(codice|tuo|verifica|account|password|autenticare)\b', text_lower):
        return "Italian"
    
    # Turkish
    elif re.search(r'\b(kod|sizin|doğrulama|hesap|şifre|oturum)\b', text_lower):
        return "Turkish"
    
    # Indonesian/Malay
    elif re.search(r'\b(kode|anda|verifikasi|akun|kata sandi|masuk)\b', text_lower):
        return "Indonesian"
    
    # Polish
    elif re.search(r'\b(kod|twój|weryfikacja|konto|hasło|zaloguj)\b', text_lower):
        return "Polish"
    
    # Dutch
    elif re.search(r'\b(jouw|verificatie|account|wachtwoord|inloggen)\b', text_lower):
        return "Dutch"
    
    # Swedish
    elif re.search(r'\b(din|verifiering|konto|lösenord|logga)\b', text_lower):
        return "Swedish"
    
    # Default to English for Latin script
    else:
        return "English"

# --- Admin Commands ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.from_user.id) in ADMIN_CHAT_IDS:
        await update.message.reply_text("👋 Admin Active!\n\n/add_chat <id>\n/remove_chat <id>\n/list_chats\n/test - Test SMS fetch now\n/clear - Clear processed IDs (resend all)")
    else:
        await update.message.reply_text("❌ Not Authorized.")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual test to check SMS fetching"""
    if str(update.message.from_user.id) not in ADMIN_CHAT_IDS: 
        await update.message.reply_text("❌ Not Authorized.")
        return
    
    await update.message.reply_text("🔍 Testing SMS fetch from both accounts...")
    await check_sms_job(context)
    await update.message.reply_text("✅ Test completed! Check console logs.")

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear all processed message IDs to resend all messages"""
    if str(update.message.from_user.id) not in ADMIN_CHAT_IDS: 
        await update.message.reply_text("❌ Not Authorized.")
        return
    
    try:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
            await update.message.reply_text("✅ Cleared all processed IDs! All messages will be resent on next check.")
        else:
            await update.message.reply_text("⚠️ No processed IDs file found.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def add_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.from_user.id) not in ADMIN_CHAT_IDS: return
    try:
        cid = context.args[0]
        chats = load_chat_ids()
        if cid not in chats:
            chats.append(cid)
            save_chat_ids(chats)
            await update.message.reply_text(f"✅ Added: {cid}")
        else:
            await update.message.reply_text("⚠️ Exists.")
    except: await update.message.reply_text("❌ Use: /add_chat <id>")

async def remove_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.from_user.id) not in ADMIN_CHAT_IDS: return
    try:
        cid = context.args[0]
        chats = load_chat_ids()
        if cid in chats:
            chats.remove(cid)
            save_chat_ids(chats)
            await update.message.reply_text(f"🗑️ Removed: {cid}")
    except: await update.message.reply_text("❌ Use: /remove_chat <id>")

async def list_chats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.from_user.id) not in ADMIN_CHAT_IDS: return
    chats = load_chat_ids()
    await update.message.reply_text("📜 Chats:\n" + "\n".join(chats) if chats else "Empty")

# --- Button Callback Handler ---
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if query.data.startswith("copy_"):
        code = query.data.replace("copy_", "")
        # Show code in popup alert - user can manually select and copy
        await query.answer(text=code, show_alert=True)

# --- Auto Delete Function ---
async def auto_delete_message(context: ContextTypes.DEFAULT_TYPE):
    """Delete message after 15 minutes"""
    job = context.job
    try:
        await context.bot.delete_message(chat_id=job.chat_id, message_id=job.data['message_id'])
        print(f"✅ Deleted message {job.data['message_id']} from chat {job.chat_id}")
    except Exception as e:
        print(f"❌ Failed to delete message: {e}")

# --- Scraper ---
async def fetch_sms_from_api(client, headers, csrf_token):
    all_messages = []
    try:
        today = datetime.utcnow()
        from_date = (today - timedelta(days=1)).strftime('%m/%d/%Y')
        to_date = today.strftime('%m/%d/%Y')

        payload = {'from': from_date, 'to': to_date, '_token': csrf_token}
        res = await client.post(SMS_API_ENDPOINT, data=payload, headers=headers)
        print(f"📡 API Response Status: {res.status_code}")

        soup = BeautifulSoup(res.text, 'html.parser')
        groups = soup.find_all('div', {'class': 'pointer'})
        print(f"🌍 Found {len(groups)} country groups")

        if len(groups) == 0:
            print("⚠️ WARNING: No country groups found!")
            print(f"📄 Response preview: {res.text[:500]}")
            return []

        processed = load_processed_ids()

        # ── Helper: fetch all SMS for one phone number ──────────────────────
        async def fetch_number_sms(phone, group_id, country_norm, flag):
            results = []
            try:
                sms_url = urljoin(BASE_URL, "portal/sms/received/getsms/number/sms")
                sms_res = await client.post(
                    sms_url,
                    data={'start': from_date, 'end': to_date, 'Number': phone, 'Range': group_id, '_token': csrf_token},
                    headers=headers
                )
                sms_soup = BeautifulSoup(sms_res.text, 'html.parser')
                cards = sms_soup.find_all('div', class_='card-body')
                for card in cards:
                    p_tag = card.find('p', class_='mb-0')
                    if not p_tag:
                        continue
                    txt = p_tag.get_text(separator='\n').strip()
                    msg_id = f"{phone}-{txt[:30]}"
                    if msg_id in processed:
                        continue
                    service = "Unknown"
                    for s, keys in SERVICE_KEYWORDS.items():
                        if any(k in txt.lower() for k in keys):
                            service = s; break
                    code = "N/A"
                    hyphen_match = re.search(r'(\d{3}-\d{3})', txt)
                    if hyphen_match:
                        code = hyphen_match.group(1)
                    else:
                        c_match = re.search(r'\b(\d{4,8})\b', txt)
                        if c_match:
                            code = c_match.group(1)
                    language = detect_language(txt)
                    results.append({
                        "id": msg_id, "number": phone, "country": country_norm,
                        "flag": flag, "service": service, "code": code, "full_sms": txt,
                        "time": datetime.now().strftime('%H:%M:%S'), "language": language
                    })
            except Exception as e:
                print(f"❌ Error fetching SMS for {phone}: {e}")
            return results

        # ── Helper: fetch all numbers for one country group ─────────────────
        async def fetch_country_group(div):
            results = []
            try:
                onclick = div.get('onclick', '')
                match = re.search(r"getDetials\('(.+?)'\)", onclick)
                if not match:
                    return []
                group_id = match.group(1)

                # Resolve country name — try longest match first
                country_norm = group_id.strip().title()
                flag = "🏳️"
                matched_country = country_norm
                words = country_norm.split()
                for i in range(len(words), 0, -1):
                    candidate = " ".join(words[:i])
                    if candidate in COUNTRY_FLAGS:
                        flag = COUNTRY_FLAGS[candidate]
                        matched_country = candidate
                        break
                country_norm = matched_country

                num_url = urljoin(BASE_URL, "portal/sms/received/getsms/number")
                num_res = await client.post(
                    num_url,
                    data={'start': from_date, 'end': to_date, 'range': group_id, '_token': csrf_token},
                    headers=headers
                )
                num_soup = BeautifulSoup(num_res.text, 'html.parser')
                num_divs = num_soup.select("div[onclick*='getDetialsNumber']")
                phones = [n.text.strip() for n in num_divs]

                # ⚡ Fetch all phone numbers in this country IN PARALLEL
                tasks = [fetch_number_sms(phone, group_id, country_norm, flag) for phone in phones]
                phone_results = await asyncio.gather(*tasks, return_exceptions=True)
                for pr in phone_results:
                    if isinstance(pr, list):
                        results.extend(pr)
            except Exception as e:
                print(f"❌ Error fetching country group: {e}")
            return results

        # ⚡ Fetch ALL country groups IN PARALLEL
        country_tasks = [fetch_country_group(div) for div in groups]
        country_results = await asyncio.gather(*country_tasks, return_exceptions=True)
        for cr in country_results:
            if isinstance(cr, list):
                all_messages.extend(cr)

        print(f"📦 Total NEW messages collected: {len(all_messages)}")
        return all_messages

    except Exception as e:
        print(f"❌ Error in fetch_sms_from_api: {e}")
        traceback.print_exc()
        return []

async def send_telegram_message(context: ContextTypes.DEFAULT_TYPE, chat_id: str, data: dict):
    try:
        global message_cache
        
        # Store message data in cache for button callbacks
        message_cache[data['id']] = data
        
        # Country code map (country name -> dial code)
        COUNTRY_CODES = {
            "Afghanistan": "93", "Albania": "355", "Algeria": "213", "Argentina": "54",
            "Armenia": "374", "Australia": "61", "Austria": "43", "Azerbaijan": "994",
            "Bahrain": "973", "Bangladesh": "880", "Belarus": "375", "Belgium": "32",
            "Benin": "229", "Bhutan": "975", "Bolivia": "591", "Brazil": "55",
            "Bulgaria": "359", "Burkina Faso": "226", "Cambodia": "855",
            "Cameroon": "237", "Canada": "1", "Chad": "235", "Chile": "56", "China": "86",
            "Colombia": "57", "Congo": "242", "Croatia": "385", "Cuba": "53", "Cyprus": "357",
            "Czech Republic": "420", "Denmark": "45", "Egypt": "20", "Estonia": "372",
            "Ethiopia": "251", "Finland": "358", "France": "33", "Gabon": "241",
            "Gambia": "220", "Georgia": "995", "Germany": "49", "Ghana": "233",
            "Greece": "30", "Guatemala": "502", "Guinea": "224", "Haiti": "509",
            "Honduras": "504", "Hong Kong": "852", "Hungary": "36", "Iceland": "354",
            "India": "91", "Indonesia": "62", "Iran": "98", "Iraq": "964",
            "Ireland": "353", "Israel": "972", "Italy": "39",
            "Ivory Coast": "225", "Ivory": "225", "Cote D'Ivoire": "225", "Côte D'Ivoire": "225",
            "Jamaica": "1876", "Japan": "81", "Jordan": "962", "Kazakhstan": "7",
            "Kenya": "254", "Kuwait": "965", "Kyrgyzstan": "996", "Laos": "856",
            "Latvia": "371", "Lebanon": "961", "Liberia": "231", "Libya": "218",
            "Lithuania": "370", "Luxembourg": "352", "Madagascar": "261", "Malaysia": "60",
            "Mali": "223", "Malta": "356", "Mexico": "52", "Moldova": "373",
            "Monaco": "377", "Mongolia": "976", "Montenegro": "382", "Morocco": "212",
            "Mozambique": "258", "Myanmar": "95", "Namibia": "264", "Nepal": "977",
            "Netherlands": "31", "New Zealand": "64", "Nicaragua": "505", "Niger": "227",
            "Nigeria": "234", "North Korea": "850", "North Macedonia": "389", "Norway": "47",
            "Oman": "968", "Pakistan": "92", "Panama": "507", "Paraguay": "595",
            "Peru": "51", "Philippines": "63", "Poland": "48", "Portugal": "351",
            "Qatar": "974", "Romania": "40", "Russia": "7", "Rwanda": "250",
            "Saudi Arabia": "966", "Senegal": "221", "Serbia": "381", "Sierra Leone": "232",
            "Singapore": "65", "Slovakia": "421", "Slovenia": "386", "Somalia": "252",
            "South Africa": "27", "South Korea": "82", "Spain": "34", "Sri Lanka": "94",
            "Sudan": "249", "Sweden": "46", "Switzerland": "41", "Syria": "963",
            "Taiwan": "886", "Tajikistan": "992", "Tanzania": "255", "Thailand": "66",
            "Togo": "228", "Tunisia": "216", "Turkey": "90", "Turkmenistan": "993",
            "Uganda": "256", "Ukraine": "380", "United Arab Emirates": "971",
            "United Kingdom": "44", "United States": "1", "Uruguay": "598",
            "Uzbekistan": "998", "Venezuela": "58", "Vietnam": "84",
            "Yemen": "967", "Zambia": "260", "Zimbabwe": "263"
        }

        # Get real country code — check exact match first, then partial
        country_code = COUNTRY_CODES.get(data['country'], COUNTRY_CODES.get(data['country'].split()[0], "0"))

        # Phone format: +[countrycode]-PKOTP-[last 5 digits]
        phone = str(data['number']).strip()
        last_digits = phone[-5:] if len(phone) >= 5 else phone
        masked_phone = f"+{country_code}-PKOTP-{last_digits}"

        # Build hashtags
        service_abbr = get_service_abbr(data['service'])
        country_abbr = data['country'][:2].upper()
        language = get_language_name(data.get('language', 'English'))

        # Message body — NO "PK OTP" or "THE REAL" header
        msg = (
            f"<b>#{service_abbr} #{country_abbr}{data['flag']}</b> {masked_phone}\n"
            f"<b>#{language}</b>"
        )

        # Inline keyboard — NO key emoji, just OTP copy button + links
        try:
            from telegram import CopyTextButton as CTB
            otp_row = [
                InlineKeyboardButton(f"🔑 {data['code']}", copy_text=CTB(text=data['code'])),
            ]
        except ImportError:
            otp_row = [
                InlineKeyboardButton(f"🔑 {data['code']}", callback_data=f"copy_{data['code']}"),
            ]

        keyboard = [
            otp_row,
            [
                InlineKeyboardButton("📞 Numbers ↗", url="https://t.me/PKNUMBERS1"),
                InlineKeyboardButton("💬 Chat ↗",    url="https://t.me/PKOTPDISCUSSION"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send with HTML parse mode
        sent_message = await context.bot.send_message(
            chat_id=chat_id,
            text=msg,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

        # Schedule auto-deletion after 15 minutes
        if context.job_queue:
            context.job_queue.run_once(
                auto_delete_message,
                when=900,
                chat_id=chat_id,
                data={'message_id': sent_message.message_id}
            )
            print(f"📤 Sent message {sent_message.message_id} - will delete in 15 min")
        else:
            print(f"📤 Sent message {sent_message.message_id}")

    except Exception as e:
        print(f"Error sending message: {e}")

async def check_sms_job(context: ContextTypes.DEFAULT_TYPE):
    global session_client_1, session_state_1, session_client_2, session_state_2
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    
    try:
        print(f"🔍 [DEBUG] Starting SMS check at {datetime.now().strftime('%H:%M:%S')}")
        
        all_messages = []
        
        # --- LOGIN BOTH ACCOUNTS FIRST (parallel) ---
        async def ensure_login(client, state, username, password, label):
            if not state["is_logged_in"]:
                print(f"🔐 Attempting login for {label}...")
                try:
                    l_page = await client.get(LOGIN_URL)
                    token = BeautifulSoup(l_page.text, 'html.parser').find('input', {'name': '_token'})['value']
                    auth = await client.post(LOGIN_URL, data={'email': username, 'password': password, '_token': token})
                    if "login" not in str(auth.url):
                        state["is_logged_in"] = True
                        state["csrf_token"] = BeautifulSoup(auth.text, 'html.parser').find('meta', {'name': 'csrf-token'})['content']
                        print(f"✅ {label} Logged In Successfully")
                    else:
                        print(f"❌ {label} Login Failed")
                except Exception as e:
                    print(f"❌ {label} Login Error: {e}")

        await asyncio.gather(
            ensure_login(session_client_1, session_state_1, USERNAME, PASSWORD, "Account 1"),
            ensure_login(session_client_2, session_state_2, USERNAME2, PASSWORD2, "Account 2"),
        )

        # --- FETCH FROM BOTH ACCOUNTS IN PARALLEL ---
        async def fetch_account(client, state, label):
            if not state["is_logged_in"]:
                return []
            print(f"📡 Fetching SMS from {label}...")
            msgs = await fetch_sms_from_api(client, headers, state["csrf_token"])
            print(f"📨 {label}: Found {len(msgs)} new messages")
            return msgs

        results = await asyncio.gather(
            fetch_account(session_client_1, session_state_1, "Account 1"),
            fetch_account(session_client_2, session_state_2, "Account 2"),
        )
        for r in results:
            all_messages.extend(r)
        
        # --- PROCESS ALL MESSAGES FROM BOTH ACCOUNTS ---
        print(f"📦 Total messages from both accounts: {len(all_messages)}")
        
        processed = load_processed_ids()
        chats = load_chat_ids()
        print(f"📋 Loaded {len(processed)} processed IDs")
        print(f"💬 Sending to {len(chats)} chat(s): {chats}")

        new_messages = 0
        for m in reversed(all_messages):
            if m["id"] not in processed:
                print(f"🆕 New message: {m['code']} from {m['country']} - {m['service']}")
                try:
                    # Send to all chats
                    await asyncio.gather(*[send_telegram_message(context, c, m) for c in chats])
                    # Only mark as processed if sending succeeded
                    save_processed_id(m["id"])
                    new_messages += 1
                    print(f"✅ Successfully sent and marked as processed: {m['id']}")
                except Exception as send_error:
                    print(f"❌ Failed to send message {m['id']}: {send_error}")
                    # Don't mark as processed if sending failed
        
        if new_messages == 0:
            print("✔️ No new messages from both accounts")
        else:
            print(f"✅ Sent {new_messages} new message(s) from both accounts")
            
    except Exception as e:
        print(f"❌ Error in check_sms_job: {e}")
        traceback.print_exc()
        session_state_1["is_logged_in"] = False
        session_state_2["is_logged_in"] = False

def main():
    # Build application with job queue enabled
    app = Application.builder().token(YOUR_BOT_TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("add_chat", add_chat_command))
    app.add_handler(CommandHandler("remove_chat", remove_chat_command))
    app.add_handler(CommandHandler("list_chats", list_chats_command))
    app.add_handler(CommandHandler("test", test_command))  # Added test command
    app.add_handler(CommandHandler("clear", clear_command))  # Added clear command
    
    # Add callback query handler for button clicks
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Check if job_queue is available
    if app.job_queue is not None:
        # Add the repeating job
        app.job_queue.run_repeating(check_sms_job, interval=POLLING_INTERVAL_SECONDS, first=1)
        print("🤖 Bot is Online with JobQueue...")
    else:
        print("⚠️ JobQueue not available. Running with alternative polling method...")
        print("🤖 Bot is Online (using asyncio background task)...")
        
        # Alternative: Create background task for SMS checking
        async def background_sms_checker():
            """Background task to check SMS when JobQueue is not available"""
            await asyncio.sleep(1)  # Wait for app to initialize
            while True:
                try:
                    # Create a fake context for check_sms_job
                    class FakeContext:
                        bot = app.bot
                    await check_sms_job(FakeContext())
                except Exception as e:
                    print(f"❌ Background checker error: {e}")
                await asyncio.sleep(POLLING_INTERVAL_SECONDS)
        
        # Use post_init to start background task
        async def post_init(application):
            asyncio.create_task(background_sms_checker())
        
        app.post_init = post_init
    
    app.run_polling()

if __name__ == "__main__":
    main()
