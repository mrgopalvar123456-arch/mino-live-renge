import os
import time
import html
import re
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import deque
import requests
import telebot
from telebot import types

# ================= কনফিগারেশন =================
BOT_TOKEN = "8957580304:AAHUCJVN14EZMIZIFPHFn_8PnbYA3H4y7rE"
MINO_API_KEY = "api_key_by_mino"   # 👈 আপনার Mino API Key বসান
TARGET_GROUP = -1003920219065      # আপনার গ্রুপ আইডি
DEV_URL = "https://t.me/NETBOLDNETMAIR0"  # 👈 ডেভেলপার লিংক

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
MINO_CONSOLE_URL = f"https://minosms.com/console?api_key={MINO_API_KEY}"

seen_sms_cache = deque(maxlen=2500)

# --- প্রিমিয়াম ইমোজি হেল্পার ফাংশন ---
def tg_e(emoji, eid):
    return f'<tg-emoji emoji-id="{eid}">{emoji}</tg-emoji>'

# UI থিম ইমোজি
EMO_ACTIVE   = tg_e('✅', '5224607267797606837')
EMO_COUNTRY  = tg_e('🌍', '5224450179368767019')
EMO_RANGE    = tg_e('📶', '6289791863381563934')
EMO_SERVICE  = tg_e('📱', '6289813338218042779')
EMO_SMS      = tg_e('📩', '5472239203590888751')
EMO_DEFAULT  = tg_e('💎', '6291877744313635378')
E_STATS      = tg_e('📊', '5231200819986047254')
E_PIN        = tg_e('📌', '5397782960512444700')
E_SHIELD     = tg_e('🛡', '5251203410396458957')
E_ARROW      = tg_e('✈️', '5271801931814165886')

# ================= বিশ্বের ২৪০+ দেশের কান্ট্রি ডাটাবেস =================
COUNTRIES = {
    # West & Central Africa
    "245": ("Guinea-Bissau", tg_e('🇬🇼', '5224705704153066489')),
    "224": ("Guinea", tg_e('🇬🇳', '5222337588035073000')),
    "220": ("Gambia", tg_e('🇬🇲', '5221949872747330159')),
    "221": ("Senegal", tg_e('🇸🇳', '5224358988623130949')),
    "222": ("Mauritania", '🇲🇷'),
    "223": ("Mali", tg_e('🇲🇱', '5224322352552096671')),
    "225": ("Ivory Coast", '🇨🇮'),
    "226": ("Burkina Faso", tg_e('🇧🇫', '5222356541725749790')),
    "227": ("Niger", tg_e('🇳🇪', '5222099049846420864')),
    "228": ("Togo", tg_e('🇹🇬', '5222408051268532030')),
    "229": ("Benin", tg_e('🇧🇯', '5222024115552009151')),
    "231": ("Liberia", tg_e('🇱🇷', '5221998371518034740')),
    "232": ("Sierra Leone", tg_e('🇸🇱', '5224420995065983217')),
    "233": ("Ghana", tg_e('🇬🇭', '5224511339703056124')),
    "234": ("Nigeria", tg_e('🇳🇬', '5224723614166691638')),
    "235": ("Chad", '🇹🇩'),
    "236": ("Central African Republic", '🇨🇫'),
    "237": ("Cameroon", tg_e('🇨🇲', '5222270788408717651')),
    "238": ("Cape Verde", '🇨🇻'),
    "239": ("Sao Tome and Principe", '🇸🇹'),
    "240": ("Equatorial Guinea", tg_e('🇬🇶', '5222172811614762423')),
    "241": ("Gabon", tg_e('🇬🇦', '5224669733801963467')),
    "242": ("Republic of Congo", tg_e('🇨🇬', '5222104268231684600')),
    "243": ("DR Congo", tg_e('🇨🇩', '5224398158724871677')),
    "244": ("Angola", tg_e('🇦🇴', '5224379767674907895')),

    # East & Southern Africa
    "261": ("Madagascar", tg_e('🇲🇬', '5222042605386217334')),
    "255": ("Tanzania", tg_e('🇹🇿', '5224397364155923150')),
    "254": ("Kenya", tg_e('🇰🇪', '5222089648163009103')),
    "256": ("Uganda", tg_e('🇺🇬', '5222464040462200940')),
    "251": ("Ethiopia", tg_e('🇪🇹', '5224467805914542024')),
    "260": ("Zambia", tg_e('🇿🇲', '5224646626877911277')),
    "263": ("Zimbabwe", tg_e('🇿🇼', '5222060442385397848')),
    "258": ("Mozambique", tg_e('🇲🇿', '5222470388423864826')),
    "250": ("Rwanda", tg_e('🇷🇼', '5222449197055227754')),
    "257": ("Burundi", '🇧🇮'),
    "265": ("Malawi", '🇲🇼'),
    "264": ("Namibia", '🇳🇦'),
    "267": ("Botswana", '🇧🇼'),
    "268": ("Eswatini", '🇸🇿'),
    "266": ("Lesotho", '🇱🇸'),
    "269": ("Comoros", '🇰🇲'),
    "248": ("Seychelles", '🇸🇨'),
    "230": ("Mauritius", '🇲🇺'),
    "27":  ("South Africa", tg_e('🇿🇦', '5224696216570309138')),

    # North Africa & Middle East
    "20":  ("Egypt", tg_e('🇪🇬', '5222161185138292290')),
    "212": ("Morocco", tg_e('🇲🇦', '5224530035695693965')),
    "213": ("Algeria", tg_e('🇩🇿', '5224260376174015500')),
    "216": ("Tunisia", tg_e('🇹🇳', '5221991375016310330')),
    "218": ("Libya", '🇱🇾'),
    "249": ("Sudan", tg_e('🇸🇩', '5224372990216514135')),
    "211": ("South Sudan", tg_e('🇸🇸', '5224618146949773268')),
    "252": ("Somalia", tg_e('🇸🇴', '5222370504664428325')),
    "253": ("Djibouti", '🇩🇯'),
    "966": ("Saudi Arabia", tg_e('🇸🇦', '5224698145010624573')),
    "971": ("UAE", tg_e('🇦🇪', '5224565851427976312')),
    "968": ("Oman", tg_e('🇴🇲', '5222396686785066306')),
    "974": ("Qatar", tg_e('🇶🇦', '5222225596762830469')),
    "965": ("Kuwait", tg_e('🇰🇼', '5221949726718442491')),
    "973": ("Bahrain", '🇧🇭'),
    "962": ("Jordan", '🇯🇴'),
    "961": ("Lebanon", '🇱🇧'),
    "963": ("Syria", '🇸🇾'),
    "964": ("Iraq", tg_e('🇮🇶', '5221980268230882832')),
    "967": ("Yemen", tg_e('🇾🇪', '5222300655611294950')),
    "972": ("Israel", tg_e('🇮🇱', '5224720599099648709')),
    "970": ("Palestine", '🇵🇸'),
    "98":  ("Iran", tg_e('🇮🇷', '5224374154152653367')),
    "90":  ("Turkey", tg_e('🇹🇷', '5224601903383457698')),

    # South & Central Asia
    "880": ("Bangladesh", tg_e('🇧🇩', '5224407289825340729')),
    "91":  ("India", tg_e('🇮🇳', '5222300011366200403')),
    "92":  ("Pakistan", tg_e('🇵🇰', '5224637061985742245')),
    "93":  ("Afghanistan", '🇦🇫'),
    "94":  ("Sri Lanka", tg_e('🇱🇰', '5224277294050192388')),
    "977": ("Nepal", tg_e('🇳🇵', '5222444378101925267')),
    "975": ("Bhutan", '🇧🇹'),
    "960": ("Maldives", '🇲🇻'),
    "998": ("Uzbekistan", tg_e('🇺🇿', '5222404546575219535')),
    "992": ("Tajikistan", tg_e('🇹🇯', '5222217865821696536')),
    "993": ("Turkmenistan", tg_e('🇹🇲', '5224256935905208951')),
    "996": ("Kyrgyzstan", tg_e('🇰🇬', '5224388147156102493')),
    "994": ("Azerbaijan", tg_e('🇦🇿', '5224426544163728284')),
    "374": ("Armenia", tg_e('🇦🇲', '5224369957969603463')),
    "995": ("Georgia", tg_e('🇬🇪', '5222152195771742239')),
    "7":   ("Russia / Kazakhstan", tg_e('🇷🇺', '5280582975270963511')),

    # East & Southeast Asia
    "86":  ("China", tg_e('🇨🇳', '5224435456220868088')),
    "81":  ("Japan", tg_e('🇯🇵', '5222390089715299207')),
    "82":  ("South Korea", tg_e('🇰🇷', '5222345550904439270')),
    "850": ("North Korea", '🇰🇵'),
    "886": ("Taiwan", '🇹🇼'),
    "852": ("Hong Kong", '🇭🇰'),
    "853": ("Macau", '🇲🇴'),
    "976": ("Mongolia", tg_e('🇲🇳', '5224192257992701543')),
    "62":  ("Indonesia", tg_e('🇮🇩', '5224405893960969756')),
    "63":  ("Philippines", tg_e('🇵🇭', '5222065042295376892')),
    "84":  ("Vietnam", tg_e('🇻🇳', '5222359651282071925')),
    "66":  ("Thailand", tg_e('🇹🇭', '5224638530864556281')),
    "60":  ("Malaysia", tg_e('🇲🇾', '5224312886444174057')),
    "65":  ("Singapore", tg_e('🇸🇬', '5224194023224257181')),
    "95":  ("Myanmar", '🇲🇲'),
    "855": ("Cambodia", tg_e('🇰🇭', '5224189882875785448')),
    "856": ("Laos", '🇱🇦'),
    "673": ("Brunei", '🇧🇳'),
    "670": ("East Timor", '🇹🇱'),

    # Americas & Caribbean
    "1":   ("United States / Canada", tg_e('🇺🇸', '5224321781321442532')),
    "52":  ("Mexico", tg_e('🇲🇽', '5221971386238514431')),
    "55":  ("Brazil", tg_e('🇧🇷', '5224688610183228070')),
    "57":  ("Colombia", tg_e('🇨🇴', '5224455152940886669')),
    "54":  ("Argentina", tg_e('🇦🇷', '5221980461504411710')),
    "56":  ("Chile", tg_e('🇨🇱', '5222350726340032308')),
    "51":  ("Peru", tg_e('🇵🇪', '5224482026551258766')),
    "58":  ("Venezuela", '🇻🇪'),
    "593": ("Ecuador", '🇪🇨'),
    "591": ("Bolivia", '🇧🇴'),
    "595": ("Paraguay", tg_e('🇵🇾', '5222152565138929235')),
    "598": ("Uruguay", tg_e('🇺🇾', '5222466849370813232')),
    "507": ("Panama", tg_e('🇵🇦', '5222111719999945107')),
    "506": ("Costa Rica", '🇨🇷'),
    "504": ("Honduras", '🇭🇳'),
    "503": ("El Salvador", '🇸🇻'),
    "502": ("Guatemala", '🇬🇹'),
    "505": ("Nicaragua", '🇳🇮'),
    "501": ("Belize", '🇧🇿'),
    "509": ("Haiti", '🇭🇹'),
    "53":  ("Cuba", '🇨🇺'),
    "592": ("Guyana", '🇬🇾'),
    "597": ("Suriname", '🇸🇷'),

    # Europe & Oceania
    "44":  ("United Kingdom", tg_e('🇬🇧', '5224518800061245598')),
    "49":  ("Germany", tg_e('🇩🇪', '5222165617544542414')),
    "33":  ("France", tg_e('🇫🇷', '5222029789203804982')),
    "39":  ("Italy", tg_e('🇮🇹', '5222460101977190141')),
    "34":  ("Spain", tg_e('🇪🇸', '5222024776976970940')),
    "351": ("Portugal", tg_e('🇵🇹', '5224404094369672274')),
    "31":  ("Netherlands", tg_e('🇳🇱', '5224516489368841614')),
    "32":  ("Belgium", '🇧🇪'),
    "41":  ("Switzerland", tg_e('🇨🇭', '5224707263226194753')),
    "43":  ("Austria", '🇦🇹'),
    "46":  ("Sweden", tg_e('🇸🇪', '5222201098269373561')),
    "47":  ("Norway", tg_e('🇳🇴', '5224465228934163949')),
    "45":  ("Denmark", '🇩🇰'),
    "358": ("Finland", '🇫🇮'),
    "353": ("Ireland", '🇮🇪'),
    "30":  ("Greece", '🇬🇷'),
    "48":  ("Poland", tg_e('🇵🇱', '5224670399521892983')),
    "380": ("Ukraine", tg_e('🇺🇦', '5222250679371839695')),
    "375": ("Belarus", tg_e('🇧🇾', '5222398507851199882')),
    "420": ("Czech Republic", '🇨🇿'),
    "421": ("Slovakia", '🇸🇰'),
    "36":  ("Hungary", '🇭🇺'),
    "40":  ("Romania", tg_e('🇷🇴', '5222273794885826118')),
    "359": ("Bulgaria", '🇧🇬'),
    "381": ("Serbia", tg_e('🇷🇸', '5222145396838512729')),
    "385": ("Croatia", '🇭🇷'),
    "386": ("Slovenia", '🇸🇮'),
    "387": ("Bosnia", '🇧🇦'),
    "370": ("Lithuania", '🇱🇹'),
    "371": ("Latvia", '🇱🇻'),
    "372": ("Estonia", '🇪🇪'),
    "373": ("Moldova", tg_e('🇲🇩', '5224216473018314447')),
    "356": ("Malta", '🇲🇹'),
    "357": ("Cyprus", '🇨🇾'),
    "61":  ("Australia", tg_e('🇦🇺', '5224659803837574114')),
    "64":  ("New Zealand", '🇳🇿'),
    "679": ("Fiji", '🇫🇯'),
    "675": ("Papua New Guinea", '🇵🇬')
}

SERVICES = {
    "whatsapp": "WhatsApp", "telegram": "Telegram", "facebook": "Facebook",
    "instagram": "Instagram", "google": "Google", "tiktok": "TikTok",
    "twitter": "Twitter", "imo": "imo", "discord": "Discord", "binance": "Binance",
    "bybit": "Bybit", "okx": "OKX", "apple": "Apple", "amazon": "Amazon",
    "netflix": "Netflix", "uber": "Uber", "viber": "Viber", "paypal": "PayPal"
}

STOP_WORDS = {"your", "use", "is", "dear", "the", "for", "code", "otp", "to", "account", "verification", "login", "password"}

# কান্ট্রি ও ডায়াল প্রিফিক্স ডিটেকশন
def detect_country(num, raw_c=""):
    clean = re.sub(r'\D', '', str(num))
    if clean.startswith("00"):
        clean = clean[2:]

    # নম্বরের প্রিফিক্স দিয়ে নিখুঁত ম্যাচিং
    for code in sorted(COUNTRIES.keys(), key=len, reverse=True):
        if clean.startswith(code):
            return COUNTRIES[code][0], COUNTRIES[code][1], f"+{code}"

    # API কান্ট্রি স্ট্রিং চেক
    if raw_c:
        rc = raw_c.lower().strip()
        if "bissau" in rc or rc == "gw":
            return COUNTRIES["245"][0], COUNTRIES["245"][1], "+245"
        for code, data in COUNTRIES.items():
            if rc == data[0].lower() or rc in data[0].lower():
                return data[0], data[1], f"+{code}"

    return "Global Region", tg_e('🌐', '5433880764770957207'), ""

# নির্ভুল সার্ভিস ফাইন্ডার
def detect_service(sms):
    t = sms.lower()
    for k, v in SERVICES.items():
        if re.search(rf'\b{re.escape(k)}\b', t):
            return v
    words = re.findall(r'[A-Za-z0-9]+', sms)
    for w in words:
        if w.lower() not in STOP_WORDS and len(w) > 2 and not w.isdigit():
            return w.capitalize()
    return "Service"

# Mino API থেকে ডাটা ফেচ
def fetch_logs():
    headers = {"User-Agent": "Mozilla/5.0", "X-MINO-API-KEY": MINO_API_KEY}
    try:
        res = requests.get(MINO_CONSOLE_URL, headers=headers, timeout=8)
        data = res.json()
        return data if isinstance(data, list) else [data]
    except:
        return []

# অটো ওটিপি ফরওয়ার্ডার
def forwarder_worker():
    while True:
        try:
            logs = fetch_logs()
            for item in logs:
                sms = str(item.get("message") or item.get("sms") or "").strip()
                raw_num = str(item.get("number") or item.get("phone") or item.get("range") or "").strip()
                raw_c = str(item.get("country") or "").strip()
                if not sms:
                    continue

                msg_hash = f"{raw_num}_{sms}"
                if msg_hash in seen_sms_cache:
                    continue
                seen_sms_cache.append(msg_hash)

                num = re.sub(r'\D', '', raw_num)
                if not num:
                    m = re.findall(r'\+?(\d{8,15})', sms)
                    if m: num = m[0]

                c_name, c_flag, c_prefix = detect_country(num, raw_c)
                country_text = f"{c_name} ({c_prefix})" if c_prefix else c_name
                s_name = detect_service(sms)
                display_range = num[:6] + "XXX" if len(num) >= 6 else "Unknown"
                safe_sms = html.escape(sms)

                msg = (
                    f"<blockquote>{EMO_ACTIVE} <b>New Active Range</b> {EMO_ACTIVE}</blockquote>\n"
                    f"<blockquote>{EMO_COUNTRY} <b>Country:</b> {c_flag} {country_text}</blockquote>\n"
                    f"<blockquote>{EMO_RANGE} <b>Range:</b> <code>{display_range}</code></blockquote>\n"
                    f"<blockquote>{EMO_SERVICE} <b>Service:</b> {EMO_DEFAULT} {s_name}</blockquote>\n"
                    f"<blockquote>{EMO_SMS} <b>Full SMS:</b> <code>{safe_sms}</code></blockquote>"
                )

                # প্রিমিয়াম ইনলাইন বাটন
                kb = types.InlineKeyboardMarkup(row_width=2)
                btn_dev = types.InlineKeyboardButton("👨‍💻 Developer", url=DEV_URL)
                try:
                    btn_copy = types.InlineKeyboardButton("📋 Copy Range", copy_text=types.CopyTextButton(text=display_range))
                except:
                    btn_copy = types.InlineKeyboardButton("📋 Copy Range", callback_data=f"copy_{display_range}")

                kb.add(btn_dev, btn_copy)
                bot.send_message(TARGET_GROUP, msg, reply_markup=kb)
        except Exception:
            time.sleep(3)
        time.sleep(3)

# বট কমান্ড
@bot.message_handler(commands=['start'])
def start(m):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("📊 Status"))
    bot.send_message(m.chat.id, f"{EMO_ACTIVE} <b>Mino Live Stream Bot Active!</b>", reply_markup=kb)

@bot.message_handler(func=lambda msg: msg.text in ["📊 Status", "/status"])
def status(m):
    bot.send_message(m.chat.id, f"<blockquote>{E_STATS} <b>Mino Live System Online</b>\n{E_SHIELD} <b>Target Group:</b> <code>{TARGET_GROUP}</code></blockquote>")

# --- Render-এর জন্য Keep-Alive Web Server ---
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running 24/7!")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

if __name__ == "__main__":
    # Render পোর্ট ওপেন রাখা
    threading.Thread(target=run_server, daemon=True).start()
    # ব্যাকগ্রাউন্ড SMS ফেচিং চালু
    threading.Thread(target=forwarder_worker, daemon=True).start()
    # বট পোলিং
    bot.infinity_polling()
