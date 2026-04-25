import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = "outilshop2024"
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
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

COMMENT_SYSTEM_PROMPT = """أنت مسوق محترف ترد على تعليقات فيسبوك لمتجر TAWBA.

قواعد صارمة للرد على التعليقات:
- ردك قصير جداً — جملة واحدة فقط
- لا تذكر السعر أبداً في التعليق
- لا تقول "السلام عليكم" أو أي تحية
- لا تقول "ديالك" — قل "تاعك"
- تكلم بالدارجة الجزائرية
- هدفك تحفيز الشخص يراسل في الخاص"""

PRICE_KEYWORDS = ['سعر', 'السعر', 'شحال', 'قداه', 'prix', 'كم', 'بكاش', 'بقداه', 'ثمن', 'الثمن', 'غالي', 'رخيص']

def contains_price_keyword(text):
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in PRICE_KEYWORDS)

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
    print(f"=== WEBHOOK DATA === {data}")

    try:
        for entry in data.get('entry', []):

            # رسائل ماسنجر
            for messaging in entry.get('messaging', []):
                sender_id = messaging['sender']['id']
                message_text = messaging.get('message', {}).get('text')
                if message_text:
                    reply = get_claude_reply(message_text, SYSTEM_PROMPT)
                    send_message(sender_id, reply)

            # تعليقات الصفحة
            for change in entry.get('changes', []):
                value = change.get('value', {})
                print(f"=== CHANGE === field={change.get('field')} item={value.get('item')} verb={value.get('verb')}")

                if value.get('item') == 'comment' and value.get('verb') == 'add':
                    comment_id = value.get('comment_id')
                    commenter_id = value.get('from', {}).get('id')
                    comment_text = value.get('message') or value.get('text') or ''

                    print(f"=== COMMENT === id={comment_id} from={commenter_id} text={comment_text}")

                    if contains_price_keyword(comment_text):
                        if comment_id:
                            reply_to_comment(comment_id, "ردينا عليك في الخاص 👇")
                        if commenter_id:
                            dm_reply = get_claude_reply(comment_text, SYSTEM_PROMPT)
                            send_message(commenter_id, dm_reply)
                    else:
                        if comment_id:
                            comment_reply = get_claude_reply(comment_text, COMMENT_SYSTEM_PROMPT)
                            reply_to_comment(comment_id, comment_reply)
                        if commenter_id:
                            dm_text = comment_text if comment_text else "مرحبا"
                            dm_reply = get_claude_reply(dm_text, SYSTEM_PROMPT)
                            send_message(commenter_id, dm_reply)

    except Exception as e:
        print(f"Error: {e}")
    return jsonify({"status": "ok"}), 200

def get_claude_reply(text, system_prompt):
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
                "system": system_prompt,
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
            f"https://graph.facebook.com/v19.0/{comment_id}/comments",
            params={"access_token": PAGE_ACCESS_TOKEN},
            json={"message": text}
        )
        result = r.json()
        print(f"Comment reply: {result}")
        if 'error' in result:
            r2 = requests.post(
                f"https://graph.facebook.com/v19.0/{comment_id}/comments",
                params={
                    "access_token": PAGE_ACCESS_TOKEN,
                    "message": text
                }
            )
            print(f"Comment reply attempt 2: {r2.json()}")
    except Exception as e:
        print(f"Comment error: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
