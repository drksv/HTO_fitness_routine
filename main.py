import os
from flask import Flask, request, jsonify
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Retrieve API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set. Please check your .env file.")

app = Flask(__name__)

client = Groq(api_key=GROQ_API_KEY)

# Store user preferences
user_preferences = {}

@app.route("/", methods=["GET"])
def home():
    """Health check endpoint to ensure the API is running."""
    return jsonify({"message": "Welcome to the Fitness AI Assistant!"})

@app.route("/chat", methods=["POST"])
def chat():
    """Handles chat requests and generates responses based on user preferences."""
    try:
        data = request.json
        user_id = data.get("user_id", "default")
        user_message = data.get("message", "")

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        # Retrieve user-specific details
        user_info = user_preferences.get(user_id, {"age": "unknown", "gender": "unknown", "activity": "moderate"})

        # Construct a system prompt with user info
        system_prompt = f"You are a fitness assistant. The user is {user_info['age']} years old, {user_info['gender']}, with a {user_info['activity']} activity level. Respond accordingly."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        # Get AI response
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.7,
            max_completion_tokens=1024,
            top_p=1,
            stream=False,
        )

        response_text = completion.choices[0].message.content

        return jsonify({"response": response_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/update_preferences", methods=["POST"])
def update_preferences():
    """Updates user-specific fitness preferences."""
    try:
        data = request.json
        user_id = data.get("user_id", "default")

        # Validate input data
        if not all(k in data for k in ("age", "gender", "activity")):
            return jsonify({"error": "Missing required fields"}), 400

        user_preferences[user_id] = {
            "age": data.get("age"),
            "gender": data.get("gender"),
            "activity": data.get("activity"),
        }

        return jsonify({"message": "User preferences updated successfully!"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Ensure the correct port
    app.run(host="0.0.0.0", port=port)
