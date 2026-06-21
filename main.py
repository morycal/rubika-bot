
import requests, time, random, json, difflib, os

TOKEN = "1597508244:ka5UwETw7QiX-HTltkg5SMNv5MgMBDKC82c"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"
OWNER_ID = 586110315

USERS_FILE = "users.json"
BOT_ENABLED = True
last_update_id = 0

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(data):
    with open(USERS_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False)

users = load_users()
guess_games = {}

def send(chat_id,text,reply_to=None):
    data={"chat_id":chat_id,"text":text}
    if reply_to:
        data["reply_to_message_id"]=reply_to
    requests.post(f"{BASE_URL}/sendMessage",json=data,timeout=15)

def similar(text, words):
    r=difflib.get_close_matches(text.lower(),words,n=1,cutoff=0.6)
    return r[0] if r else text.lower()

challenges=["20 شنا برو","30 درازنشست برو","10 دقیقه مطالعه کن","اتاقت را مرتب کن"]
jokes=["😂 اینترنت کند یعنی فرصت تفکر","🤣 معلم: چرا ننوشتی؟ خودکارم مرخصی بود"]
truths=["بزرگترین ترست چیه؟","آخرین باری که گریه کردی؟"]
dares=["10 بار بپر","یک جوک تعریف کن"]
facts=["خورشید حدود 93 میلیون مایل از زمین فاصله دارد."]
owner_answers={"سلام":"سلام سرورم 😈","خوبی":"فدات ❤️"}

while True:
    try:
        res=requests.get(f"{BASE_URL}/getUpdates",
                         params={"offset":last_update_id+1},
                         timeout=20).json()

        for update in res.get("result",[]):
            last_update_id=update["update_id"]
            if "message" not in update:
                continue

            m=update["message"]
            chat_id=m["chat"]["id"]
            user_id=m["from"]["id"]
            msg_id=m["message_id"]
            text=m.get("text","").strip()

            if not text:
                continue

            users[str(user_id)] = users.get(str(user_id),0)+1
            save_users(users)

            if user_id==OWNER_ID:
                if text=="بخواب":
                    BOT_ENABLED=False
                    send(chat_id,"😴 خاموش شدم",msg_id)
                    continue
                if text=="بیدارشو":
                    BOT_ENABLED=True
                    send(chat_id,"🤖 روشن شدم",msg_id)
                    continue
                if text=="آمار":
                    send(chat_id,f"👥 کاربران: {len(users)}",msg_id)
                    continue

            if not BOT_ENABLED and user_id!=OWNER_ID:
                continue

            cmd=similar(text,[
                "سلام","خوبی","چطوری","چالش","تاس","شیر یا خط",
                "عدد شانسی","حقیقت","جرئت","جوک","دانستنی",
                "حدس عدد","سنگ","کاغذ","قیچی"
            ])

            if text=="حدس عدد":
                guess_games[user_id]=random.randint(1,20)
                send(chat_id,"🎯 عددی بین 1 تا 20 حدس بزن",msg_id)
                continue

            if user_id in guess_games and text.isdigit():
                n=int(text)
                if n==guess_games[user_id]:
                    send(chat_id,"🎉 درست حدس زدی",msg_id)
                    del guess_games[user_id]
                else:
                    send(chat_id,"❌ اشتباه بود",msg_id)
                continue

            if cmd=="چالش":
                send(chat_id,"🎯 "+random.choice(challenges),msg_id); continue
            if cmd=="تاس":
                send(chat_id,f"🎲 {random.randint(1,6)}",msg_id); continue
            if cmd=="شیر یا خط":
                send(chat_id,"🪙 "+random.choice(["شیر","خط"]),msg_id); continue
            if cmd=="عدد شانسی":
                send(chat_id,f"🔢 {random.randint(1,100)}",msg_id); continue
            if cmd=="حقیقت":
                send(chat_id,"🎤 "+random.choice(truths),msg_id); continue
            if cmd=="جرئت":
                send(chat_id,"🔥 "+random.choice(dares),msg_id); continue
            if cmd=="جوک":
                send(chat_id,random.choice(jokes),msg_id); continue
            if cmd=="دانستنی":
                send(chat_id,"📚 "+random.choice(facts),msg_id); continue

            if cmd in ["سنگ","کاغذ","قیچی"]:
                bot=random.choice(["سنگ","کاغذ","قیچی"])
                send(chat_id,f"من: {bot}",msg_id)
                continue

            if user_id==OWNER_ID:
                reply=owner_answers.get(cmd,"چی میگویی سرورم؟ 😈")
            else:
                if text=="/start":
                    reply="سلام 👋\nدستورات:\nچالش\nجوک\nدانستنی\nحقیقت\nجرئت\nتاس\nشیر یا خط\nعدد شانسی\nحدس عدد"
                elif cmd=="سلام":
                    reply=random.choice(["سلام 👋","درود 🌹","سلام رفیق 😎"])
                elif cmd=="خوبی":
                    reply="خوبم 😊"
                else:
                    reply="هااان؟ 🤔"

            send(chat_id,reply,msg_id)

        time.sleep(1)

    except Exception as e:
        print("ERROR",e)
        time.sleep(5)
