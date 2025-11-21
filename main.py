import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

# ----------------- FIX 1: DEFINE THE DICTIONARY (IN-MEMORY FIX) -----------------
user_preferences = {}

app = Flask(__name__)
CORS(app)

# ----------------- CHECK API KEY AVAILABILITY -----------------
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("WARNING: GROQ_API_KEY environment variable is not set. API calls may fail.")

# Attempt to initialize client with the key (may be None)
# In a robust app, this would also be wrapped in a try/except.
client = Groq(api_key=api_key)

MODEL = "llama-3.1-8b-instant"


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message")
    user_id = data.get("user_id", "default_user_123")

    if not message:
        return jsonify({"error": "No message provided"}), 400

    prefs = user_preferences.get(
        user_id,
        {"age": "unknown", "gender": "unknown", "activity": "moderate"}
    )

    # Note: Storing defaults back into the dict is fine for an in-memory solution
    user_preferences[user_id] = prefs

    system_message = (
        f"You are a certified fitness expert. The user is {prefs['age']} years old, "
        f"{prefs['gender']}, with a {prefs['activity']} activity level. "
        f"Give workout routines with reps, sets, timing, posture corrections. "
        f"Keep it concise and action-oriented."
    )

    try:
        groq_response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": message}
            ],
            max_tokens=500,
            temperature=0.7
        )

        # ------------------- CRITICAL FIX: Use dot notation -------------------
        reply = groq_response.choices[0].message.content 

        return jsonify({"response": reply})

    except Exception as e:
        print(f"ERROR processing Groq API request: {e}")
        # Return a 500 error if the API call fails
        return jsonify({"error": "Groq API failed", "details": str(e)}), 500


@app.route("/")
def home():
    return "Fitness API Running"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
