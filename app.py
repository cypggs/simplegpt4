from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import openai
import os
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.String, nullable=False)
    user_text = db.Column(db.String, nullable=False)
    assistant_text = db.Column(db.String, nullable=False)

with app.app_context():
    db.create_all()

# 初始化 openai 库
openai.api_type = "azure"
openai.api_base = os.getenv("OPENAI_API_BASE")
openai.api_version = "2023-03-15-preview"
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/send_message", methods=["POST"])
def send_message():
    user_input = request.json.get("user_input")
    if not user_input:
        return jsonify({"error": "Please provide user_input"}), 400

    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    for chat in Chat.query.all():
        messages.append({"role": "user", "content": chat.user_text})
        messages.append({"role": "assistant", "content": chat.assistant_text})
    messages.append({"role": "user", "content": user_input})

    response = openai.ChatCompletion.create(
        engine="gpt-4-8k",
        messages=messages,
    )

    assistant_response = response.choices[0].message['content']
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    chat = Chat(timestamp=timestamp, user_text=user_input, assistant_text=assistant_response)
    db.session.add(chat)
    db.session.commit()

    return jsonify({"timestamp": timestamp, "assistant_response": assistant_response})

@app.route("/get_history", methods=["GET"])
def get_history():
    history = []
    for chat in Chat.query.all():
        history.append({"timestamp": chat.timestamp, "user_text": chat.user_text, "assistant_text": chat.assistant_text})
    return jsonify(history)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=44)
