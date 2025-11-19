import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

client = Groq(api_key=os.getenv("hto_fitness_routine"))
MODEL = "llama-3.1-8b-instant"


user_preferences = {}


@app.route("/update_preferences", methods=["POST"])
def update_preferences():
    data = request.json
    user_id = data.get("user_id", "default")
    user_preferences[user_id] = {
        "age": data.get("age"),
        "gender": data.get("gender"),
        "activity": data.get("activity")
    }
    return jsonify({"message": "Preferences updated"})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_id = data.get("user_id", "default")
    message = data.get("message")

    prefs = user_preferences.get(
        user_id,
        {"age": "unknown", "gender": "unknown", "activity": "moderate"}
    )

    system = (
        f"You are a certified fitness expert. The user is {prefs['age']} years old, "
        f"{prefs['gender']}, and has a {prefs['activity']} activity level. "
        f"Give clear workout routines, reps, timings, safety corrections."
    )

    reply = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": message}
        ],
        max_tokens=250,
        temperature=0.7
    ).choices[0].message["content"]

    return jsonify({"response": reply})


@app.route("/", methods=["GET"])
def home():
    return "Fitness API Running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
