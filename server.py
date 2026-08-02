import telebot
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import time

# ==========================================
# ⚠️ الإعدادات الأساسية ⚠️
# ==========================================
# ضع التوكن الجديد الخاص بك بين علامتي التنصيص هنا
TOKEN = "8662213304:AAFtfPDot3NYCEQZ5GXrVK25REUMmqvg254" 
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)
CORS(app)

# ==========================================
# إعداد قاعدة البيانات
# ==========================================
def get_db_connection():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (chat_id TEXT PRIMARY KEY, token TEXT, trials_left INTEGER, is_premium INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# أوامر بوت التلجرام
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        print("▶️ تم استدعاء أمر /start بنجاح داخل السيرفر!")
        chat_id = str(message.chat.id)
        access_token = f"TG-{chat_id}"
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE chat_id=?", (chat_id,))
        user = c.fetchone()
        
        if not user:
            c.execute("INSERT INTO users (chat_id, token, trials_left, is_premium) VALUES (?, ?, ?, ?)",
                      (chat_id, access_token, 3, 0))
            conn.commit()
            welcome_msg = (
                "مرحباً بك في أداة TikTok Crisp PRO! 🚀\n\n"
                "لقد حصلت على 3 محاولات مجانية لرفع الفيديوهات بأعلى جودة.\n"
                f"🔑 كود الدخول الخاص بك هو:\n`{access_token}`\n\n"
                "قم بنسخه ولصقه في الإضافة للبدء."
            )
            bot.reply_to(message, welcome_msg, parse_mode="Markdown")
            print("✅ تم الرد بنجاح على مستخدم جديد!")
        else:
            welcome_msg = f"أهلاً بعودتك! 👋\n🔑 كود الدخول الخاص بك هو:\n`{user[1]}`"
            bot.reply_to(message, welcome_msg, parse_mode="Markdown")
            print("✅ تم الرد بنجاح على مستخدم قديم!")
        conn.close()
    except Exception as e:
        print(f"❌ خطأ داخلي أثناء الرد على /start: {str(e)}")

# ==========================================
# مسارات الـ API (للاتصال بالإضافة)
# ==========================================
@app.route('/api/login', methods=['GET'])
def api_login():
    token = request.args.get('token')
    if not token:
        return jsonify({"valid": False, "error": "Missing token"}), 400
        
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT trials_left, is_premium FROM users WHERE token=?", (token,))
    user = c.fetchone()
    conn.close()
    
    if user:
        return jsonify({"valid": True, "trialsLeft": user[0], "isPremium": bool(user[1])})
    else:
        return jsonify({"valid": False, "error": "Invalid token"}), 404

@app.route('/api/use_tool', methods=['GET'])
def api_use_tool():
    token = request.args.get('token')
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT trials_left, is_premium FROM users WHERE token=?", (token,))
    user = c.fetchone()
    
    if not user:
        conn.close()
        return jsonify({"allowed": False, "error": "Invalid token"}), 404
        
    trials_left, is_premium = user[0], user[1]
    
    if is_premium:
        conn.close()
        return jsonify({"allowed": True, "message": "Premium user"})
        
    if trials_left > 0:
        c.execute("UPDATE users SET trials_left = trials_left - 1 WHERE token=?", (token,))
        conn.commit()
        conn.close()
        return jsonify({"allowed": True, "trialsLeft": trials_left - 1})
    else:
        conn.close()
        return jsonify({"allowed": False, "error": "No trials left"})

# ==========================================
# نظام Webhook لربط التلجرام بالسيرفر
# ==========================================
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    try:
        json_string = request.get_data().decode('utf-8')
        print("📩 السيرفر استلم رسالة من تلجرام للتو!")
        
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    except Exception as e:
        print(f"❌ خطأ في معالجة الويب هوك: {str(e)}")
        return "!", 500

@app.route('/setup_webhook')
def setup_webhook():
    try:
        bot.remove_webhook()
        time.sleep(1) 
        bot.set_webhook(url='https://tiktok-crisp-backend.onrender.com/' + TOKEN)
        return "✅ تم تفعيل البوت بنجاح! يمكنك الآن الذهاب للتلجرام والضغط على /start", 200
    except Exception as e:
        return f"❌ فشل الاتصال بتلجرام، السبب: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
