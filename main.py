import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)

# Wide-open CORS for testing + preflight support
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    return response

# Memory store
user_preferences = {}

# Groq client
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)
MODEL = "llama-3.1-8b-instant"


@app.route("/update_preferences", methods=["POST", "OPTIONS"])
def update_preferences():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.json
    user_id = data.get("user_id", "default_user_123")

    user_preferences[user_id] = {
        "age": data.get("age"),
        "gender": data.get("gender"),
        "activity": data.get("activity")
    }

    return jsonify({"message": "Preferences updated"})


@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.json
    message = data.get("message")
    user_id = data.get("user_id", "default_user_123")

    prefs = user_preferences.get(
        user_id,
        {"age": "unknown", "gender": "unknown", "activity": "moderate"}
    )

    system_message = (
        f"You are a certified fitness expert. The user is {prefs['age']} years old, "
        f"{prefs['gender']}, and has a {prefs['activity']} activity level. "
        f"Provide specific workout routines with reps, sets, timings, and safety corrections."
    )

    try:
        groq_response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": message}
            ],
            max_tokens=250,
            temperature=0.7
        )

        reply = groq_response.choices[0].message.content

        return jsonify({"response": reply})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": "Groq API failed", "details": str(e)}), 500


@app.route("/")
def home():
    return "Fitness API Running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
