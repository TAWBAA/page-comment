import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = "outilshop2024"
PAGE_ACCESS_TOKEN = "EAAU5UaV3N3cBRQk59GCJRFgZCgro0Uxkz11ysJ9ZCDFPyUy6msWCYRUwv4XNmVhDrJ8Aguwb74PZAjzbhC2eVNMaObciEeNZCOzYNUlT1kLjkUnmm6eviIYpACQ1f2ajAp6KJRL9oIzf6m5s41y2CBdsCmWd5J0gOZBxu8hHCmZCGynM3qsSYn2SZBPjMiXJYjJDRaDqW4q6f8pt2Uuf9yvKgZDZD"
CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

SYSTEM_PROMPT = """أنت مسوق محترف تبيع بطاقة NFC TAWBA للزبائن الجزائريين عبر الماسنجر.

قواعد صارمة:
- لا تقول "السلام عليكم" أبداً إلا في أول رسالة فقط
- لا تقول "يالحاج" أو أي لقب
- لا تقول "ديالك" — قل "تاعك" دائماً
- ردودك قصيرة ومباشرة — جملة أو جملتين كافيين
- لا تكرر معلومات قالها الزبون
- لا تبدأ كل رد بتحية
- تكلم بالدارجة الجزائرية الحقيقية

معلومات المنتج:
- الاسم: بطاقة NFC TAWBA
- السعر: 1900 دج
- كيفاش تخدم: تلمس بيها الهاتف وتشغل القرآن مباشرة
- الدفع: عند الاستلام
- التوصيل: لجميع ولايات الجزائر

أسلوب البيع:
- جاوب على السؤال مباشرة بدون مقدمات
- إذا الزبون مهتم حفزه يطلب بجملة واحدة
- إذا قال "نطلب" أو "بغيت" اطلب منه: الاسم الكامل، رقم الهاتف، الولاية
- إذا قال غالي قله القيمة تستاهل وعند الاستلام تشوف بعينيك"""

COMMENT_REPLY = "راسلنا في DM باش نجاوبوك على كل أسئلتك 👇"

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
            # رسائل ماسنجر
            for messaging in entry.get('messaging', []):
                sender_id = messaging['sender']['id']
                message_text = messaging.get('message', {}).get('text')
                if message_text:
                    reply = get_claude_reply(message_text)
                    send_message(sender_id, reply)

            # تعليقات الصفحة
            for change in entry.get('changes', []):
                value = change.get('value', {})
                if value.get('item') == 'comment' and value.get('verb') == 'add':
                    comment_id = value.get('comment_id')
                    commenter_id = value.get('from', {}).get('id')
                    comment_text = value.get('message', '')

                    # رد في التعليق
                    reply_to_comment(comment_id, COMMENT_REPLY)

                    # إرسال DM بالذكاء الاصطناعي
                    if commenter_id and comment_text:
                        dm_reply = get_claude_reply(comment_text)
                        send_message(commenter_id, dm_reply)

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
        return "راسلنا في DM باش نجاوبوك 👇"

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

def reply_to_comment(comment_id, text):
    try:
        r = requests.post(
            f"https://graph.facebook.com/v19.0/{comment_id}/comments?access_token={PAGE_ACCESS_TOKEN}",
            json={"message": text}
        )
        print(f"Comment reply: {r.json()}")
    except Exception as e:
        print(f"Comment error: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
