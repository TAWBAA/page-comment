import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = "outilshop2024"
PAGE_ACCESS_TOKEN = "EAAU5UaV3N3cBRSZBlbNbUD8tbFpQA5cEQrfv5qZAuKWq0k8u6UQGCqpcehk8UrdyRRCoRtBoxN0y7E3g1GSU63wDpgJ9LZCdCCjZBcomv4pxOp3yAVQNvTZCH7RPP1XS9i9S8R9AcXRZB4mZCcRUbZAXT3tIhRNm0dymaDTBpYrKJflAt4D83a628NKfOMaFLwKZBcfCvuljZA5eRqEQ5ZA06bKUQZDZD"
CLAUDE_API_KEY = "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"

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
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-haiku-4-5",
            "max_tokens": 500,
            "system": "أنت مساعد لمتجر TAWBA. المنتج الرئيسي: بطاقة NFC TAWBA بسعر 1900 دج. رد بالدارجة الجزائرية دائماً بشكل مختصر وواضح.",
            "messages": [{"role": "user", "content": text}]
        }
    )
    return response.json()['content'][0]['text']

def send_message(recipient_id, text):
    requests.post(
        f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}",
        json={
            "recipient": {"id": recipient_id},
            "message": {"text": text}
        }
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
