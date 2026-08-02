import telebot
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import threading
import os

# الإعدادات الأساسية
TOKEN = "8662213304:AAFtfPDot3NYCEQZ5GXrVK25REUMmqvq254"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
CORS(app)

# إعداد قاعدة البيانات
def get_db_connection():
    # السماح باستخدام الاتصال بسلاسة عبر Render
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
    else:
        welcome_msg = f"أهلاً بعودتك! 👋\n🔑 كود الدخول الخاص بك هو:\n`{user[1]}`"
        bot.reply_to(message, welcome_msg, parse_mode="Markdown")
    conn.close()

@bot.message_handler(commands=['upgrade'])
def upgrade_user(message):
    try:
        target_token = message.text.split()[1]
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE users SET is_premium=1 WHERE token=?", (target_token,))
        if c.rowcount > 0:
            bot.reply_to(message, f"✅ تم تفعيل حساب {target_token} إلى PRO بنجاح!")
        else:
            bot.reply_to(message, "❌ لم يتم العثور على هذا الكود.")
        conn.commit()
        conn.close()
    except:
        bot.reply_to(message, "الاستخدام الصحيح: /upgrade TG-XXXXX")

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

def run_bot():
    bot.infinity_polling()

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    # ضبط المنفذ الديناميكي الخاص بمنصة Render
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    # ... (باقي الكود في الأعلى كما هو بدون تغيير)

def run_bot():
    bot.infinity_polling()

# التعديل هنا: أخرجنا أمر التشغيل لكي يبدأ تلقائياً مع السيرفر
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    # ==========================================
# 5. تشغيل السيرفر والبوت معاً
# ==========================================
def run_bot():
    bot.infinity_polling()

# هذا السطر يجب أن يكون خارج (فوق) جملة if __name__ لكي يقرأه السيرفر
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == '__main__':
    # تشغيل سيرفر الـ API
    print("🚀 Server is running...")
    app.run(host='0.0.0.0', port=5000)
