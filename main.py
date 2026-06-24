import os
import psycopg2

from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from supabase import create_client

app = Flask(__name__)

CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True
)

# ----------------------------------
# ENV VARIABLES
# ----------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ----------------------------------
# CLIENTS
# ----------------------------------

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

client = Groq(
    api_key=GROQ_API_KEY
)

MODEL = "llama-3.1-8b-instant"

# ----------------------------------
# CORS HEADERS
# ----------------------------------

@app.after_request
def after_request(response):

    response.headers.add(
        "Access-Control-Allow-Origin",
        "*"
    )

    response.headers.add(
        "Access-Control-Allow-Headers",
        "Content-Type,Authorization"
    )

    response.headers.add(
        "Access-Control-Allow-Methods",
        "GET,POST,OPTIONS"
    )

    return response

# ----------------------------------
# IN-MEMORY USER PREFS
# ----------------------------------

user_preferences = {}

# ----------------------------------
# DATABASE HELPERS
# ----------------------------------

def get_db_connection():

    return psycopg2.connect(DATABASE_URL)

def save_routine(user_id, prompt, routine):

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO fitness_routines
        (user_id,prompt,routine)
        VALUES (%s,%s,%s)
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

# ----------------------------------
# HOME
# ----------------------------------

@app.route("/")
def home():

    return jsonify({
        "status": "running",
        "service": "Health Timeout Fitness API"
    })

# ----------------------------------
# SIGNUP
# ----------------------------------

@app.route("/signup", methods=["POST", "OPTIONS"])
def signup():

    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:

        data = request.json

        email = data.get("email")
        password = data.get("password")

        if not email or not password:

            return jsonify({
                "success": False,
                "error": "Email and password required"
            }), 400

        result = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        return jsonify({
            "success": True,
            "message": "Account created"
        })

    except Exception as e:

        print("SIGNUP ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

# ----------------------------------
# LOGIN
# ----------------------------------

@app.route("/login", methods=["POST", "OPTIONS"])
def login():

    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:

        data = request.json

        email = data.get("email")
        password = data.get("password")

        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        return jsonify({
            "success": True,
            "user_id": result.user.id,
            "email": result.user.email
        })

    except Exception as e:

        print("LOGIN ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 401

# ----------------------------------
# UPDATE PREFERENCES
# ----------------------------------

@app.route("/update_preferences", methods=["POST", "OPTIONS"])
def update_preferences():

    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.json

    user_id = data.get(
        "user_id",
        "default_user"
    )

    user_preferences[user_id] = {

        "age": data.get("age"),

        "gender": data.get("gender"),

        "activity": data.get("activity")
    }

    return jsonify({
        "message": "Preferences updated"
    })

# ----------------------------------
# CHAT
# ----------------------------------

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():

    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:

        data = request.json

        message = data.get("message")

        user_id = data.get(
            "user_id",
            "default_user"
        )

        prefs = user_preferences.get(
            user_id,
            {
                "age": "unknown",
                "gender": "unknown",
                "activity": "moderate"
            }
        )

        system_message = (
            f"You are a certified fitness expert. "
            f"The user is {prefs['age']} years old, "
            f"{prefs['gender']}, "
            f"with a {prefs['activity']} activity level. "
            f"Provide specific workout routines with "
            f"sets, reps, timings and safety guidance."
        )

        groq_response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": message
                }
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
            "response": reply,
            "saved": True
        })

    except Exception as e:

        print("CHAT ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ----------------------------------
# GET ROUTINES
# ----------------------------------

@app.route(
    "/routines/<user_id>",
    methods=["GET"]
)
def get_routines(user_id):

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                id,
                prompt,
                routine,
                created_at
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

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ----------------------------------
# RUN
# ----------------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5001
    )
