import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = "outilshop2024"
PAGE_ACCESS_TOKEN = "EAAU5UaV3N3cBRQk59GCJRFgZCgro0Uxkz11ysJ9ZCDFPyUy6msWCYRUwv4XNmVhDrJ8Aguwb74PZAjzbhC2eVNMaObciEeNZCOzYNUlT1kLjkUnmm6eviIYpACQ1f2ajAp6KJRL9oIzf6m5s41y2CBdsCmWd5J0gOZBxu8hHCmZCGynM3qsSYn2SZBPjMiXJYjJDRaDqW4q6f8pt2Uuf9yvKgZDZD"
CLAUDE_API_KEY = "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"

SYSTEM_PROMPT = """أنت مساعد بيع ذكي لمتجر TAWBA الجزائري. ردك دائماً بالدارجة الجزائرية.
معلومات المنتج:
- الاسم: بطاقة NFC TAWBA
- السعر: 1900 دج
- طريقة الاستخدام: تلمس الهاتف بالبطاقة وتشغل القرآن مباشرة
- الدفع: عند الاستلام COD
- التوصيل: لجميع ولايات الجزائر
مهمتك:
1. رد على أسئلة الزبائن بشكل واضح ومختصر
2. حفز الزبون على الطلب
3. إذا أراد الزبون يطلب اطلب منه الاسم الكامل ورقم الهاتف والعنوان
4. كن ودود ومحترف دائماً"""

@app.route('/webhook', methods=['GET'])
def verify():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        return challenge, 200
    return 'Forbidden', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    try:
        for entry in data.get('entry', []):
            for messaging in entry.get('messaging', []):
                sender_id = messaging['sender']['id']
                message_text = messaging.get('message', {}).get('text')
                if message_text:
                    reply = get_claude_reply(message_text)
                    send_message(sender_id, reply)
    except Exception as e:
        print(f"Error: {e}")
    return jsonify({"status": "ok"}), 200

def get_claude_reply(text):
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 500,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": text}]
            }
        )
        data = response.json()
        print(f"Claude response: {data}")
        return data['content'][0]['text']
    except Exception as e:
        print(f"Claude error: {e}")
        return "عندنا مشكلة تقنية، حاول مرة أخرى"

def send_message(recipient_id, text):
    try:
        r = requests.post(
            f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}",
            json={
                "recipient": {"id": recipient_id},
                "message": {"text": text}
            }
        )
        print(f"FB response: {r.json()}")
    except Exception as e:
        print(f"FB error: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
