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
BOT_TOKEN = "8957580304:AAG3VsYFF0QT8--W-FF3kcB-2irhDwPHUeU"
MINO_API_KEY = "api_key_by_mino"   # 👈 আপনার Mino API Key বসান
TARGET_GROUP = -1003920219065      # গ্রুপ আইডি
DEV_URL = "https://t.me/NETBOLDNETMAIR0"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
MINO_CONSOLE_URL = f"https://minosms.com/console?api_key={MINO_API_KEY}"

seen_sms_cache = deque(maxlen=5000)
is_first_fetch = True

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

# UI ও হেডার প্রিমিয়াম ইমোজি
EMO_ACTIVE   = tg_e('✅', '5224607267797606837')
EMO_COUNTRY  = tg_e('🌍', '5224450179368767019')
EMO_RANGE    = tg_e('📶', '6289791863381563934')
EMO_SERVICE  = tg_e('📱', '6289813338218042779')
EMO_SMS      = tg_e('📩', '5472239203590888751')
EMO_DEFAULT  = tg_e('💎', '6291877744313635378')
EMO_DEV_ID   = '5251297255431892241' # 👈 Developer Premium Custom Emoji ID
EMO_DEV      = tg_e('👨‍💻', EMO_DEV_ID)

# স্ট্যাটাস ইমোজি
E_STATS      = tg_e('📊', '5231200819986047254')
E_PIN        = tg_e('📌', '5397782960512444700')
E_SHIELD     = tg_e('🛡', '5251203410396458957')
E_ARROW      = tg_e('✈️', '5271801931814165886')
E_CHECK      = tg_e('✔️', '5206607081334906820')
E_CROSS      = tg_e('❌', '5210952531676504517')

# ================= কান্ট্রি ডাটাবেস =================
COUNTRIES = {
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
    "237": ("Cameroon", tg_e('🇨🇲', '5222270788408717651')),
    "240": ("Equatorial Guinea", tg_e('🇬🇶', '5222172811614762423')),
    "241": ("Gabon", tg_e('🇬🇦', '5224669733801963467')),
    "242": ("Republic of Congo", tg_e('🇨🇬', '5222104268231684600')),
    "243": ("DR Congo", tg_e('🇨🇩', '5224398158724871677')),
    "244": ("Angola", tg_e('🇦🇴', '5224379767674907895')),
    "261": ("Madagascar", tg_e('🇲🇬', '5222042605386217334')),
    "255": ("Tanzania", tg_e('🇹ℤ', '5224397364155923150')),
    "254": ("Kenya", tg_e('🇰🇪', '5222089648163009103')),
    "256": ("Uganda", tg_e('🇺🇬', '5222464040462200940')),
    "251": ("Ethiopia", tg_e('🇪🇹', '5224467805914542024')),
    "260": ("Zambia", tg_e('🇿🇲', '5224646626877911277')),
    "263": ("Zimbabwe", tg_e('🇿🇼', '5222060442385397848')),
    "258": ("Mozambique", tg_e('🇲ℤ', '5222470388423864826')),
    "250": ("Rwanda", tg_e('🇷🇼', '5222449197055227754')),
    "27":  ("South Africa", tg_e('🇿🇦', '5224696216570309138')),
    "880": ("Bangladesh", tg_e('🇧🇩', '5224407289825340729')),
    "91":  ("India", tg_e('🇮🇳', '5222300011366200403')),
    "92":  ("Pakistan", tg_e('🇵🇰', '5224637061985742245')),
    "62":  ("Indonesia", tg_e('🇮🇩', '5224405893960969756')),
    "63":  ("Philippines", tg_e('🇵🇭', '5222065042295376892')),
    "84":  ("Vietnam", tg_e('🇻🇳', '5222359651282071925')),
    "66":  ("Thailand", tg_e('🇹🇭', '5224638530864556281')),
    "60":  ("Malaysia", tg_e('🇲🇾', '5224312886444174057')),
    "977": ("Nepal", tg_e('🇳🇵', '5222444378101925267')),
    "94":  ("Sri Lanka", tg_e('🇱🇰', '5224277294050192388')),
    "86":  ("China", tg_e('🇨🇳', '5224435456220868088')),
    "81":  ("Japan", tg_e('🇯🇵', '5222390089715299207')),
    "82":  ("South Korea", tg_e('🇰🇷', '5222345550904439270')),
    "998": ("Uzbekistan", tg_e('🇺🇿', '5222404546575219535')),
    "964": ("Iraq", tg_e('🇮🇶', '5221980268230882832')),
    "98":  ("Iran", tg_e('🇮🇷', '5224374154152653367')),
    "966": ("Saudi Arabia", tg_e('🇸🇦', '5224698145010624573')),
    "971": ("UAE", tg_e('🇦🇪', '5224565851427976312')),
    "20":  ("Egypt", tg_e('🇪🇬', '5222161185138292290')),
    "90":  ("Turkey", tg_e('🇹🇷', '5224601903383457698')),
    "212": ("Morocco", tg_e('🇲🇦', '5224530035695693965')),
    "213": ("Algeria", tg_e('🇩🇿', '5224260376174015500')),
    "216": ("Tunisia", tg_e('🇹🇳', '5221991375016310330')),
    "1":   ("United States / Canada", tg_e('🇺🇸', '5224321781321442532')),
    "44":  ("United Kingdom", tg_e('🇬🇧', '5224518800061245598')),
    "7":   ("Russia / Kazakhstan", tg_e('🇷🇺', '5280582975270963511')),
    "55":  ("Brazil", tg_e('🇧🇷', '5224688610183228070')),
    "57":  ("Colombia", tg_e('🇨🇴', '5224455152940886669')),
    "52":  ("Mexico", tg_e('🇲🇽', '5221971386238514431')),
    "380": ("Ukraine", tg_e('🇺🇦', '5222250679371839695')),
    "382": ("Montenegro", tg_e('🇲🇪', '5224378127014177579')), # 👈 Montenegro যুক্ত করা হয়েছে
    "48":  ("Poland", tg_e('🇵🇱', '5224670399521892983')),
    "49":  ("Germany", tg_e('🇩🇪', '5222165617544542414')),
    "33":  ("France", tg_e('🇫🇷', '5222029789203804982')),
    "39":  ("Italy", tg_e('🇮🇹', '5222460101977190141')),
    "34":  ("Spain", tg_e('🇪🇸', '5222024776976970940')),
    "31":  ("Netherlands", tg_e('🇳🇱', '5224516489368841614'))
}

# ================= সার্ভিস ডাটাবেস (প্রিমিয়াম ইমোজি সহ) =================
SERVICES = {
    "whatsapp": ("WhatsApp", tg_e('🟢', '6285030020255587142')),
    "telegram": ("Telegram", tg_e('✈️', '6253419950015258099')),
    "facebook": ("Facebook", tg_e('📘', '6253285023617654178')),
    "fb": ("Facebook", tg_e('📘', '6253285023617654178')),
    "instagram": ("Instagram", tg_e('📸', '6253293974329499654')),
    "ig": ("Instagram", tg_e('📸', '6253293974329499654')),
    "google": ("Google", tg_e('🌐', '6253583949046489451')),
    "tiktok": ("TikTok", tg_e('🎵', '6253681852826002272')),
    "twitter": ("Twitter (X)", tg_e('🐦', '6282955009885741957')),
    "imo": ("imo", tg_e('💬', '6217345690767466648')),
    "discord": ("Discord", tg_e('👾', '6253615667379970369')),
    "binance": ("Binance", tg_e('🟡', '6253780203282113440')),
    "bybit": ("Bybit", tg_e('📈', '6253544882023964945')),
    "okx": ("OKX", tg_e('💹', '6253774452320903309')),
    "paypal": ("PayPal", tg_e('🅿️', '6296578985451071487')),
    "netflix": ("Netflix", tg_e('🎬', '6253485220633258832'))
}

STOP_WORDS = {"your", "use", "is", "dear", "the", "for", "code", "otp", "to", "account", "verification", "login", "password"}

# রেঞ্জ ডিটেক্টর
def extract_and_format_range(raw_val, sms_text):
    clean_raw = str(raw_val).strip()

    masked_match = re.search(r'(\d{4,9})[xX*]{2,5}', clean_raw)
    if masked_match:
        digits = masked_match.group(1)
        return digits, digits + "XXX"

    digits = re.sub(r'\D', '', clean_raw)

    if len(digits) < 4:
        sms_matches = re.findall(r'(?:\+|00)?\s*([1-9][0-9\s\-]{6,15}[0-9])', sms_text)
        for cand in sms_matches:
            c_digits = re.sub(r'\D', '', cand)
            if 7 <= len(c_digits) <= 15:
                digits = c_digits
                break

    if len(digits) >= 6:
        return digits, digits[:6] + "XXX"
    elif len(digits) == 5:
        return digits, digits[:5] + "XXX"
    elif len(digits) == 4:
        return digits, digits[:4] + "XXX"

    return "", "Unknown"

# কান্ট্রি ডিটেকশন
def detect_country(num, raw_c=""):
    clean = re.sub(r'\D', '', str(num))
    if clean.startswith("00"): clean = clean[2:]
    for code in sorted(COUNTRIES.keys(), key=len, reverse=True):
        if clean.startswith(code):
            return COUNTRIES[code][0], COUNTRIES[code][1], f"+{code}"
    if raw_c:
        rc = raw_c.lower().strip()
        if "bissau" in rc or rc == "gw":
            return COUNTRIES["245"][0], COUNTRIES["245"][1], "+245"
        for code, data in COUNTRIES.items():
            if rc == data[0].lower() or rc in data[0].lower():
                return data[0], data[1], f"+{code}"
    return "Global Region", tg_e('🌐', '5433880764770957207'), ""

# নির্ভুল সার্ভিস ডিটেকশন (প্রিমিয়াম ইমোজি সহ)
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

def fetch_logs():
    headers = {"User-Agent": "Mozilla/5.0", "X-MINO-API-KEY": MINO_API_KEY}
    try:
        res = requests.get(MINO_CONSOLE_URL, headers=headers, timeout=10)
        if res.status_code != 200:
            system_stats["last_error"] = f"Mino HTTP {res.status_code}"
            return []
        try:
            data = res.json()
            if isinstance(data, list): return data
            elif isinstance(data, dict):
                for k in ["data", "logs", "messages", "result", "items"]:
                    if k in data and isinstance(data[k], list):
                        return data[k]
                return [data]
        except Exception:
            pass

        logs = []
        for line in res.text.splitlines():
            line = line.strip()
            if not line or line.startswith("<"): continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                logs.append({"phone": parts[0], "service": parts[1], "message": "|".join(parts[2:])})
            elif len(parts) == 2:
                logs.append({"phone": parts[0], "message": parts[1]})
            else:
                logs.append({"message": line})
        return logs
    except Exception as e:
        system_stats["last_error"] = str(e)
        return []

# --- অটো ফরোয়ার্ডার (২৫ সেকেন্ড সেফটি লুপ) ---
def forwarder_worker():
    global is_first_fetch
    print("🚀 Mino Forwarder Worker Started...")

    while True:
        try:
            logs = fetch_logs()
            system_stats["last_fetch_count"] = len(logs)

            if is_first_fetch:
                for item in logs:
                    sms = str(item.get("message") or item.get("sms") or "").strip()
                    raw_val = str(item.get("range") or item.get("number") or item.get("phone") or "").strip()
                    if sms:
                        seen_sms_cache.append(f"{raw_val}_{sms}")
                is_first_fetch = False
                print(f"[Initial Warmup] Cached {len(seen_sms_cache)} historical SMS.")
                time.sleep(25)
                continue

            for item in logs:
                sms = ""
                raw_val = ""
                raw_c = ""

                if isinstance(item, dict):
                    sms = str(item.get("message") or item.get("sms") or item.get("text") or "").strip()
                    raw_val = str(item.get("range") or item.get("number") or item.get("phone") or "").strip()
                    raw_c = str(item.get("country") or item.get("country_code") or "").strip()
                elif isinstance(item, str):
                    sms = item.strip()

                if not sms: continue

                msg_hash = f"{raw_val}_{sms}"
                if msg_hash in seen_sms_cache: continue
                seen_sms_cache.append(msg_hash)

                num_digits, display_range = extract_and_format_range(raw_val, sms)
                c_name, c_flag, c_prefix = detect_country(num_digits, raw_c)
                s_name, s_icon = detect_service(sms)
                safe_sms = html.escape(sms)

                system_stats["total_processed"] += 1
                system_stats["services"][s_name] = system_stats["services"].get(s_name, 0) + 1
                if display_range != "Unknown":
                    if s_name not in system_stats["ranges"]:
                        system_stats["ranges"][s_name] = []
                    system_stats["ranges"][s_name].append(display_range)

                country_text = f"{c_name} ({c_prefix})" if c_prefix else c_name

                # ================= আধুনিক ও স্লিক প্রিমিয়াম ডিজাইন =================
                msg = (
                    f"<blockquote>{EMO_ACTIVE} <b>MINO ACTIVE OTP STREAM</b> {EMO_ACTIVE}</blockquote>\n"
                    f"<blockquote>{EMO_COUNTRY} <b>Country:</b> {c_flag} {country_text}\n"
                    f"{EMO_RANGE} <b>Range:</b> <code>{display_range}</code>\n"
                    f"{s_icon} <b>Service:</b> <b>{s_name}</b></blockquote>\n"
                    f"<blockquote>{EMO_SMS} <b>Live SMS Content:</b>\n"
                    f"<code>{safe_sms}</code></blockquote>"
                )

                kb = types.InlineKeyboardMarkup(row_width=2)
                try:
                    btn_dev = types.InlineKeyboardButton("Developer", url=DEV_URL, icon_custom_emoji_id=EMO_DEV_ID)
                except TypeError:
                    btn_dev = types.InlineKeyboardButton("👨‍💻 Developer", url=DEV_URL)

                try:
                    btn_copy = types.InlineKeyboardButton("📋 Copy Range", copy_text=types.CopyTextButton(text=display_range))
                except:
                    btn_copy = types.InlineKeyboardButton("📋 Copy Range", callback_data=f"copy_{display_range}")
                kb.add(btn_dev, btn_copy)

                sent = False
                while not sent:
                    try:
                        bot.send_message(TARGET_GROUP, msg, reply_markup=kb, disable_web_page_preview=True)
                        print(f"[Sent] {c_name} | {display_range} | {s_name}")
                        system_stats["last_error"] = "None"
                        sent = True
                        time.sleep(2.5)
                    except telebot.apihelper.ApiTelegramException as api_err:
                        if api_err.error_code == 429:
                            retry_sec = api_err.result_json.get("parameters", {}).get("retry_after", 15)
                            print(f"⚠️ [Telegram 429] Paused for {retry_sec + 2}s...")
                            system_stats["last_error"] = f"Telegram 429: Paused for {retry_sec}s"
                            time.sleep(retry_sec + 2)
                        else:
                            print(f"[Telegram Error] {api_err}")
                            system_stats["last_error"] = str(api_err)
                            break
                    except Exception as e:
                        print(f"[Send Error] {e}")
                        system_stats["last_error"] = str(e)
                        break

        except Exception as loop_err:
            print(f"[Worker Error] {loop_err}")
            system_stats["last_error"] = str(loop_err)

        time.sleep(25)

# ================= বট কমান্ড ও স্ট্যাটাস =================

@bot.message_handler(commands=['start'])
def start_handler(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📊 Status"))
    welcome = (
        f"{EMO_ACTIVE} <b>Mino Live Stream Engine Online!</b>\n\n"
        f"✅ লাইভ ওটিপি স্ট্রিম স্বয়ংক্রিয়ভাবে গ্রুপে ফরওয়ার্ড হচ্ছে।\n"
        f"{EMO_DEV} <b>Developer:</b> <a href=\"{DEV_URL}\">@NETBOLDNETMAIR0</a>\n\n"
        f"📊 লাইভ স্ট্যাটাস দেখতে নিচে <b>📊 Status</b> চাপুন।"
    )
    bot.send_message(message.chat.id, welcome, reply_markup=markup, disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("copy_"))
def copy_callback(call):
    r_val = call.data.replace("copy_", "")
    bot.answer_callback_query(call.id, f"Range: {r_val}", show_alert=True)

@bot.message_handler(func=lambda msg: msg.text in ["📊 Status", "/status"])
def status_handler(message):
    wait_msg = bot.send_message(message.chat.id, "<i>⏳ Fetching real-time system analytics...</i>")
    try:
        total = system_stats["total_processed"]
        last_logs = system_stats["last_fetch_count"]
        last_err = system_stats["last_error"]
        svc_counts = system_stats["services"]

        out = f"<blockquote>{E_STATS} <b>Mino Smart SMS Analytics</b> {E_STATS}\n"
        out += f"{E_PIN} <b>Total Streamed SMS:</b> {total}\n"
        out += f"{EMO_RANGE} <b>Last API Fetch:</b> {last_logs} entries\n"
        out += f"{E_SHIELD} <b>Target Group:</b> <code>{TARGET_GROUP}</code>\n"
        out += f"{EMO_DEV} <b>Developer:</b> <a href=\"{DEV_URL}\">@NETBOLDNETMAIR0</a>\n"
        out += f"{E_CHECK} <b>System Health:</b> {'Operational' if last_err == 'None' else 'Active (Protected)'}</blockquote>\n"
        out += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"

        if svc_counts:
            top_services = sorted(svc_counts.items(), key=lambda x: x[1], reverse=True)[:6]
            for s_name, hits in top_services:
                percent = (hits / total) * 100 if total > 0 else 0
                s_icon = SERVICES.get(s_name.lower(), (s_name, EMO_DEFAULT))[1]
                out += f"{s_icon} <b>{s_name}</b> {E_ARROW} <b>{hits} Hits</b> ({percent:.1f}%)\n"

                ranges = system_stats["ranges"].get(s_name, [])
                rc = {}
                for r in ranges:
                    rc[r] = rc.get(r, 0) + 1
                top_r = sorted(rc.items(), key=lambda x: x[1], reverse=True)[:3]
                for r_code, count in top_r:
                    out += f"  └ {E_SHIELD} Range: <code>{r_code}</code> {E_ARROW} <b>{count} Hits</b>\n"
                out += "\n"
        else:
            out += "<i>⏳ Monitoring stream for new live OTPs...</i>\n\n"

        if last_err != "None":
            out += f"⚠️ <b>Last Error Log:</b> <code>{html.escape(last_err)}</code>\n"

        out += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        out += f"{E_CHECK} <i>Live monitoring is active and rate-limited safely.</i>"

        bot.edit_message_text(out, message.chat.id, wait_msg.message_id, disable_web_page_preview=True)

    except Exception as ex:
        bot.edit_message_text(f"{E_CROSS} Status Error: <code>{str(ex)}</code>", message.chat.id, wait_msg.message_id)

# --- Render-এর জন্য Web Server ---
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Mino Stream Bot Live 24/7!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    threading.Thread(target=forwarder_worker, daemon=True).start()
    bot.infinity_polling()
