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
TARGET_GROUP = -1003920219065      # গ্রুপ আইডি
DEV_URL = "https://t.me/NETBOLDNETMAIR0"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
MINO_CONSOLE_URL = f"https://minosms.com/console?api_key={MINO_API_KEY}"

seen_sms_cache = deque(maxlen=3000)
system_stats = {
    "total_processed": 0,
    "last_fetch_count": 0,
    "last_error": "None",
    "services": {},
    "ranges": {}
}

# --- প্রিমিয়াম ইমোজি হেল্পার ফাংশন ---
def tg_e(emoji, eid):
    return f'<tg-emoji emoji-id="{eid}">{emoji}</tg-emoji>'

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
E_CHECK      = tg_e('✔️', '5206607081334906820')
E_CROSS      = tg_e('❌', '5210952531676504517')

# ================= বিশ্বের ২৪০+ দেশের কান্ট্রি ডাটাবেস =================
COUNTRIES = {
    "245": ("Guinea-Bissau", tg_e('🇬🇼', '5224705704153066489'), '🇬🇼'),
    "224": ("Guinea", tg_e('🇬🇳', '5222337588035073000'), '🇬🇳'),
    "220": ("Gambia", tg_e('🇬🇲', '5221949872747330159'), '🇬🇲'),
    "221": ("Senegal", tg_e('🇸🇳', '5224358988623130949'), '🇸🇳'),
    "222": ("Mauritania", '🇲🇷', '🇲🇷'),
    "223": ("Mali", tg_e('🇲🇱', '5224322352552096671'), '🇲🇱'),
    "225": ("Ivory Coast", '🇨🇮', '🇨🇮'),
    "226": ("Burkina Faso", tg_e('🇧🇫', '5222356541725749790'), '🇧🇫'),
    "227": ("Niger", tg_e('🇳🇪', '5222099049846420864'), '🇳🇪'),
    "228": ("Togo", tg_e('🇹🇬', '5222408051268532030'), '🇹🇬'),
    "229": ("Benin", tg_e('🇧🇯', '5222024115552009151'), '🇧🇯'),
    "231": ("Liberia", tg_e('🇱🇷', '5221998371518034740'), '🇱🇷'),
    "232": ("Sierra Leone", tg_e('🇸🇱', '5224420995065983217'), '🇸🇱'),
    "233": ("Ghana", tg_e('🇬🇭', '5224511339703056124'), '🇬🇭'),
    "234": ("Nigeria", tg_e('🇳🇬', '5224723614166691638'), '🇳🇬'),
    "235": ("Chad", '🇹🇩', '🇹🇩'),
    "236": ("Central African Republic", '🇨🇫', '🇨🇫'),
    "237": ("Cameroon", tg_e('🇨🇲', '5222270788408717651'), '🇨🇲'),
    "238": ("Cape Verde", '🇨🇻', '🇨🇻'),
    "240": ("Equatorial Guinea", tg_e('🇬🇶', '5222172811614762423'), '🇬🇶'),
    "241": ("Gabon", tg_e('🇬🇦', '5224669733801963467'), '🇬🇦'),
    "242": ("Republic of Congo", tg_e('🇨🇬', '5222104268231684600'), '🇨🇬'),
    "243": ("DR Congo", tg_e('🇨🇩', '5224398158724871677'), '🇨🇩'),
    "244": ("Angola", tg_e('🇦🇴', '5224379767674907895'), '🇦🇴'),
    "261": ("Madagascar", tg_e('🇲🇬', '5222042605386217334'), '🇲🇬'),
    "255": ("Tanzania", tg_e('🇹🇿', '5224397364155923150'), '🇹🇿'),
    "254": ("Kenya", tg_e('🇰🇪', '5222089648163009103'), '🇰🇪'),
    "256": ("Uganda", tg_e('🇺🇬', '5222464040462200940'), '🇺🇬'),
    "251": ("Ethiopia", tg_e('🇪🇹', '5224467805914542024'), '🇪🇹'),
    "260": ("Zambia", tg_e('🇿🇲', '5224646626877911277'), '🇿🇲'),
    "263": ("Zimbabwe", tg_e('🇿🇼', '5222060442385397848'), '🇿🇼'),
    "258": ("Mozambique", tg_e('🇲🇿', '5222470388423864826'), '🇲🇿'),
    "250": ("Rwanda", tg_e('🇷🇼', '5222449197055227754'), '🇷🇼'),
    "27":  ("South Africa", tg_e('🇿🇦', '5224696216570309138'), '🇿🇦'),
    "880": ("Bangladesh", tg_e('🇧🇩', '5224407289825340729'), '🇧🇩'),
    "91":  ("India", tg_e('🇮🇳', '5222300011366200403'), '🇮🇳'),
    "92":  ("Pakistan", tg_e('🇵🇰', '5224637061985742245'), '🇵🇰'),
    "62":  ("Indonesia", tg_e('🇮🇩', '5224405893960969756'), '🇮🇩'),
    "63":  ("Philippines", tg_e('🇵🇭', '5222065042295376892'), '🇵🇭'),
    "84":  ("Vietnam", tg_e('🇻🇳', '5222359651282071925'), '🇻🇳'),
    "66":  ("Thailand", tg_e('🇹🇭', '5224638530864556281'), '🇹🇭'),
    "60":  ("Malaysia", tg_e('🇲🇾', '5224312886444174057'), '🇲🇾'),
    "977": ("Nepal", tg_e('🇳🇵', '5222444378101925267'), '🇳🇵'),
    "94":  ("Sri Lanka", tg_e('🇱🇰', '5224277294050192388'), '🇱🇰'),
    "86":  ("China", tg_e('🇨🇳', '5224435456220868088'), '🇨🇳'),
    "81":  ("Japan", tg_e('🇯🇵', '5222390089715299207'), '🇯🇵'),
    "82":  ("South Korea", tg_e('🇰🇷', '5222345550904439270'), '🇰🇷'),
    "998": ("Uzbekistan", tg_e('🇺🇿', '5222404546575219535'), '🇺🇿'),
    "964": ("Iraq", tg_e('🇮🇶', '5221980268230882832'), '🇮🇶'),
    "98":  ("Iran", tg_e('🇮🇷', '5224374154152653367'), '🇮🇷'),
    "966": ("Saudi Arabia", tg_e('🇸🇦', '5224698145010624573'), '🇸🇦'),
    "971": ("UAE", tg_e('🇦🇪', '5224565851427976312'), '🇦🇪'),
    "20":  ("Egypt", tg_e('🇪🇬', '5222161185138292290'), '🇪🇬'),
    "90":  ("Turkey", tg_e('🇹🇷', '5224601903383457698'), '🇹🇷'),
    "212": ("Morocco", tg_e('🇲🇦', '5224530035695693965'), '🇲🇦'),
    "213": ("Algeria", tg_e('🇩🇿', '5224260376174015500'), '🇩🇿'),
    "216": ("Tunisia", tg_e('🇹🇳', '5221991375016310330'), '🇹🇳'),
    "1":   ("United States / Canada", tg_e('🇺🇸', '5224321781321442532'), '🇺🇸'),
    "44":  ("United Kingdom", tg_e('🇬🇧', '5224518800061245598'), '🇬🇧'),
    "7":   ("Russia / Kazakhstan", tg_e('🇷🇺', '5280582975270963511'), '🇷🇺'),
    "55":  ("Brazil", tg_e('🇧🇷', '5224688610183228070'), '🇧🇷'),
    "57":  ("Colombia", tg_e('🇨🇴', '5224455152940886669'), '🇨🇴'),
    "52":  ("Mexico", tg_e('🇲🇽', '5221971386238514431'), '🇲🇽'),
    "380": ("Ukraine", tg_e('🇺🇦', '5222250679371839695'), '🇺🇦'),
    "48":  ("Poland", tg_e('🇵🇱', '5224670399521892983'), '🇵🇱'),
    "49":  ("Germany", tg_e('🇩🇪', '5222165617544542414'), '🇩🇪'),
    "33":  ("France", tg_e('🇫🇷', '5222029789203804982'), '🇫🇷'),
    "39":  ("Italy", tg_e('🇮🇹', '5222460101977190141'), '🇮🇹'),
    "34":  ("Spain", tg_e('🇪🇸', '5222024776976970940'), '🇪🇸'),
    "31":  ("Netherlands", tg_e('🇳🇱', '5224516489368841614'), '🇳🇱')
}

SERVICES = {
    "whatsapp": ("WhatsApp", tg_e('🟢', '6285030020255587142')),
    "telegram": ("Telegram", tg_e('✈️', '6253419950015258099')),
    "facebook": ("Facebook", tg_e('📘', '6253285023617654178')),
    "instagram": ("Instagram", tg_e('📸', '6253293974329499654')),
    "google": ("Google", tg_e('🌐', '6253583949046489451')),
    "tiktok": ("TikTok", tg_e('🎵', '6253681852826002272')),
    "twitter": ("Twitter (X)", tg_e('🐦', '6282955009885741957')),
    "imo": ("imo", tg_e('💬', '6217345690767466648')),
    "discord": ("Discord", tg_e('👾', '6253615667379970369')),
    "binance": ("Binance", tg_e('🟡', '6253780203282113440')),
    "bybit": ("Bybit", tg_e('📈', '6253544882023964945')),
    "okx": ("OKX", tg_e('💹', '6253774452320903309'))
}

STOP_WORDS = {"your", "use", "is", "dear", "the", "for", "code", "otp", "to", "account", "verification", "login", "password"}

# কান্ট্রি ডিটেকশন
def detect_country(num, raw_c=""):
    clean = re.sub(r'\D', '', str(num))
    if clean.startswith("00"):
        clean = clean[2:]

    for code in sorted(COUNTRIES.keys(), key=len, reverse=True):
        if clean.startswith(code):
            return COUNTRIES[code][0], COUNTRIES[code][1], COUNTRIES[code][2], f"+{code}"

    if raw_c:
        rc = raw_c.lower().strip()
        if "bissau" in rc or rc == "gw":
            return COUNTRIES["245"][0], COUNTRIES["245"][1], COUNTRIES["245"][2], "+245"
        for code, data in COUNTRIES.items():
            if rc == data[0].lower() or rc in data[0].lower():
                return data[0], data[1], data[2], f"+{code}"

    return "Global Region", tg_e('🌐', '5433880764770957207'), "🌐", ""

# সার্ভিস ডিটেকশন
def detect_service(sms):
    t = sms.lower()
    for k, v in SERVICES.items():
        if re.search(rf'\b{re.escape(k)}\b', t):
            return v[0], v[1]
    words = re.findall(r'[A-Za-z0-9]+', sms)
    for w in words:
        if w.lower() not in STOP_WORDS and len(w) > 2 and not w.isdigit():
            return w.capitalize(), EMO_DEFAULT
    return "Service", EMO_DEFAULT

# সম্পূর্ণ এরর-মুক্ত Mino API ফেচার
def fetch_logs():
    headers = {"User-Agent": "Mozilla/5.0", "X-MINO-API-KEY": MINO_API_KEY}
    try:
        res = requests.get(MINO_CONSOLE_URL, headers=headers, timeout=10)
        if res.status_code != 200:
            print(f"[Mino API Error] Status Code: {res.status_code}, Response: {res.text[:120]}")
            system_stats["last_error"] = f"Mino HTTP {res.status_code}"
            return []

        # ১. JSON রেসপন্স টেস্ট
        try:
            data = res.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                for k in ["data", "logs", "messages", "result", "items"]:
                    if k in data and isinstance(data[k], list):
                        return data[k]
                return [data]
        except Exception:
            pass

        # ২. প্লেইন টেক্সট বা পাইপ (|) টেস্ট
        logs = []
        for line in res.text.splitlines():
            line = line.strip()
            if not line or line.startswith("<"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                logs.append({"phone": parts[0], "service": parts[1], "message": "|".join(parts[2:])})
            elif len(parts) == 2:
                logs.append({"phone": parts[0], "message": parts[1]})
            else:
                logs.append({"message": line})
        return logs

    except Exception as e:
        print(f"[Fetch Exception] {e}")
        system_stats["last_error"] = str(e)
        return []

# অটো ওটিপি ফরোয়ার্ডার
def forwarder_worker():
    print("🚀 Mino Forwarder Worker Started...")
    while True:
        try:
            logs = fetch_logs()
            system_stats["last_fetch_count"] = len(logs)

            if logs:
                print(f"[Mino Poll] Fetched {len(logs)} logs from console.")

            for item in logs:
                sms = ""
                raw_num = ""
                raw_c = ""

                if isinstance(item, dict):
                    sms = str(item.get("message") or item.get("sms") or item.get("text") or "").strip()
                    raw_num = str(item.get("number") or item.get("phone") or item.get("range") or "").strip()
                    raw_c = str(item.get("country") or "").strip()
                elif isinstance(item, str):
                    sms = item.strip()

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

                c_name, c_flag_prem, c_flag_std, c_prefix = detect_country(num, raw_c)
                s_name, s_icon = detect_service(sms)
                display_range = num[:6] + "XXX" if len(num) >= 6 else "Unknown"
                safe_sms = html.escape(sms)

                # স্ট্যাটাস ট্র্যাকার আপডেট
                system_stats["total_processed"] += 1
                system_stats["services"][s_name] = system_stats["services"].get(s_name, 0) + 1
                if display_range != "Unknown":
                    if s_name not in system_stats["ranges"]:
                        system_stats["ranges"][s_name] = []
                    system_stats["ranges"][s_name].append(display_range)

                country_text = f"{c_name} ({c_prefix})" if c_prefix else c_name

                # প্রিমিয়াম মেসেজ টেমপ্লেট
                msg = (
                    f"<blockquote>{EMO_ACTIVE} <b>New Active Range</b> {EMO_ACTIVE}</blockquote>\n"
                    f"<blockquote>{EMO_COUNTRY} <b>Country:</b> {c_flag_prem} {country_text}</blockquote>\n"
                    f"<blockquote>{EMO_RANGE} <b>Range:</b> <code>{display_range}</code></blockquote>\n"
                    f"<blockquote>{EMO_SERVICE} <b>Service:</b> {s_icon} {s_name}</blockquote>\n"
                    f"<blockquote>{EMO_SMS} <b>Full SMS:</b> <code>{safe_sms}</code></blockquote>"
                )

                kb = types.InlineKeyboardMarkup(row_width=2)
                btn_dev = types.InlineKeyboardButton("👨‍💻 Developer", url=DEV_URL)
                try:
                    btn_copy = types.InlineKeyboardButton("📋 Copy Range", copy_text=types.CopyTextButton(text=display_range))
                except:
                    btn_copy = types.InlineKeyboardButton("📋 Copy Range", callback_data=f"copy_{display_range}")
                kb.add(btn_dev, btn_copy)

                # মেসেজ পাঠানো (প্রিমিয়াম ফেইল করলে সাধারণ ইমোজি ব্যাকআপ)
                try:
                    bot.send_message(TARGET_GROUP, msg, reply_markup=kb)
                    print(f"[Sent Successfully] {c_name} | {display_range} | {s_name}")
                except Exception as tg_err:
                    print(f"⚠️ [Telegram Send Error] {tg_err}")
                    system_stats["last_error"] = str(tg_err)
                    # ফলব্যাক সেন্ডার
                    try:
                        fallback_msg = (
                            f"✅ <b>New Active Range</b> ✅\n"
                            f"🌍 <b>Country:</b> {c_flag_std} {country_text}\n"
                            f"📶 <b>Range:</b> <code>{display_range}</code>\n"
                            f"📱 <b>Service:</b> {s_name}\n"
                            f"📩 <b>Full SMS:</b> <code>{safe_sms}</code>"
                        )
                        bot.send_message(TARGET_GROUP, fallback_msg, reply_markup=kb)
                        print(f"[Sent via Fallback] {c_name} | {display_range}")
                    except Exception as fb_err:
                        print(f"❌ [Critical Send Error to Group] {fb_err}")
                        system_stats["last_error"] = f"Group Send Failed: {fb_err}"

        except Exception as loop_err:
            print(f"[Worker Exception] {loop_err}")
            system_stats["last_error"] = str(loop_err)

        time.sleep(3)

# ================= বট কমান্ড ও ডাইনামিক স্ট্যাটাস =================

@bot.message_handler(commands=['start'])
def start_handler(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📊 Status"))
    welcome = (
        f"{EMO_ACTIVE} <b>Mino Live Stream Bot is Active!</b>\n\n"
        f"✅ লাইভ ওটিপি স্ট্রিম গ্রুপে স্বয়ংক্রিয়ভাবে ফরওয়ার্ড হচ্ছে।\n"
        f"📊 লাইভ ডাটা ও অ্যানালিটিক্স দেখতে নিচে <b>📊 Status</b> বাটনে চাপ দিন।"
    )
    bot.send_message(message.chat.id, welcome, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("copy_"))
def copy_callback(call):
    r_val = call.data.replace("copy_", "")
    bot.answer_callback_query(call.id, f"Range: {r_val}", show_alert=True)

@bot.message_handler(func=lambda msg: msg.text in ["📊 Status", "/status"])
def status_handler(message):
    wait_msg = bot.send_message(message.chat.id, "<i>⏳ Fetching real-time Mino system analytics...</i>")
    try:
        total = system_stats["total_processed"]
        last_logs = system_stats["last_fetch_count"]
        last_err = system_stats["last_error"]
        svc_counts = system_stats["services"]

        out = f"<blockquote>{E_STATS} <b>Mino Smart SMS Analytics</b> {E_STATS}\n"
        out += f"{E_PIN} <b>Total Streamed SMS:</b> {total}\n"
        out += f"{EMO_RANGE} <b>Last API Fetch:</b> {last_logs} entries\n"
        out += f"{E_SHIELD} <b>Target Group:</b> <code>{TARGET_GROUP}</code>\n"
        out += f"{E_CHECK} <b>System Health:</b> {'Operational' if last_err == 'None' else 'Error Encountered'}</blockquote>\n"
        out += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"

        if svc_counts:
            top_services = sorted(svc_counts.items(), key=lambda x: x[1], reverse=True)[:6]
            for s_name, hits in top_services:
                percent = (hits / total) * 100 if total > 0 else 0
                out += f"📱 <b>{s_name}</b> {E_ARROW} <b>{hits} Hits</b> ({percent:.1f}%)\n"

                ranges = system_stats["ranges"].get(s_name, [])
                rc = {}
                for r in ranges:
                    rc[r] = rc.get(r, 0) + 1
                top_r = sorted(rc.items(), key=lambda x: x[1], reverse=True)[:3]
                for r_code, count in top_r:
                    out += f"  └ {E_SHIELD} Range: <code>{r_code}</code> {E_ARROW} <b>{count} Hits</b>\n"
                out += "\n"
        else:
            out += "<i>⏳ No active SMS forwarded yet. Monitoring stream...</i>\n\n"

        if last_err != "None":
            out += f"⚠️ <b>Last Error Log:</b> <code>{html.escape(last_err)}</code>\n"

        out += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        out += f"{E_CHECK} <i>Live monitoring is active and healthy.</i>"

        bot.edit_message_text(out, message.chat.id, wait_msg.message_id)

    except Exception as ex:
        bot.edit_message_text(f"{E_CROSS} Status Error: <code>{str(ex)}</code>", message.chat.id, wait_msg.message_id)

# --- Render-এর জন্য Keep-Alive Server ---
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Mino Stream Bot Live 24/7!")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    threading.Thread(target=forwarder_worker, daemon=True).start()
    bot.infinity_polling()
