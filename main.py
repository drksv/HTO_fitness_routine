import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
import os
import psycopg2



app = Flask(__name__)

# Wide-open CORS for testing + preflight support
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

DATABASE_URL = os.getenv("DATABASE_URL")

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

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def save_routine(user_id, prompt, routine):

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO fitness_routines
        (user_id, prompt, routine)
        VALUES (%s, %s, %s)
        """,
        (
            user_id,
            prompt,
            routine
        )
    )

    conn.commit()

    cur.close()
    conn.close()

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
            max_tokens=2000,
            temperature=0.7
        )

        reply = groq_response.choices[0].message.content

        save_routine(
            user_id,
            message,
            reply
        )
        
        return jsonify({
            "response": reply
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": "Groq API failed", "details": str(e)}), 500

@app.route("/routines/<user_id>", methods=["GET"])
def get_routines(user_id):

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id,prompt,routine,created_at
        FROM fitness_routines
        WHERE user_id=%s
        ORDER BY created_at DESC
        """,
        (user_id,)
    )

    rows = cur.fetchall()

    results = []

    for row in rows:
        results.append({
            "id": row[0],
            "prompt": row[1],
            "routine": row[2],
            "created_at": str(row[3])
        })

    cur.close()
    conn.close()

    return jsonify(results)

@app.route("/")
def home():
    return "Fitness API Running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
