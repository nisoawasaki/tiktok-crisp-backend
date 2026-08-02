# ==========================================
# أوامر بوت التلجرام
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        print("▶️ تم استدعاء أمر /start بنجاح داخل السيرفر!") # جهاز استشعار 1
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
        # إذا حدث أي خطأ برمجي هنا، سيتم طباعته بدلاً من التجاهل
        print(f"❌ خطأ داخلي أثناء الرد على /start: {str(e)}")

# ==========================================
# نظام Webhook لربط التلجرام بالسيرفر
# ==========================================
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    try:
        json_string = request.get_data().decode('utf-8')
        print("📩 السيرفر استلم رسالة من تلجرام للتو!") # جهاز استشعار 2
        
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    except Exception as e:
        print(f"❌ خطأ في معالجة الويب هوك: {str(e)}")
        return "!", 500
