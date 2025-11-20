import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.1-8b-instant"


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        message = data.get("message")

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": message}],
            max_tokens=700,
            temperature=0.8
        )

        reply = response.choices[0].message["content"]
        return jsonify({"response": reply})

    except Exception as e:
        print("SERVER ERROR:", e)
        return jsonify({"error": "Groq API failed", "details": str(e)}), 500


@app.route("/")
def home():
    return "Fitness API Running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
