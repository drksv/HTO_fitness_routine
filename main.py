import os
from flask import Flask, requests, jsonify, render_template
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

HF_API_TOKEN = os.getenv("HF_API_KEY")
HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"


app = Flask(__name__)
CORS(app)

# Store user preferences
user_preferences = {}

# Headers for Hugging Face API
headers = {
    "Authorization": f"Bearer {HF_API_TOKEN}",
    "Content-Type": "application/json"
}

@app.route('/update_preferences', methods=['POST'])
def update_preferences():
    data = request.json
    user_id = data.get("user_id", "default")
    user_preferences[user_id] = {
        "age": data.get("age", "unknown"),
        "gender": data.get("gender", "unknown"),
        "activity": data.get("activity", "moderate"),
    }
    return jsonify({"message": "User preferences updated successfully!"})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_id = data.get("user_id", "default")
    user_message = data.get("message", "")
    
    user_info = user_preferences.get(user_id, {"age": "unknown", "gender": "unknown", "activity": "moderate"})

    system_prompt = f"You are a fitness assistant. The user is {user_info['age']} years old, {user_info['gender']}, with a {user_info['activity']} activity level. Respond accordingly."

    full_prompt = f"{system_prompt}\nUser: {user_message}\nAssistant:"

    payload = {
        "inputs": full_prompt,
        "parameters": {
            "max_new_tokens": 200,
            "temperature": 0.7,
            "top_p": 0.95,
            "return_full_text": False
        }
    }

    response = requests.post(HF_API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        output_text = response.json()[0]['generated_text']
        return jsonify({"response": output_text})
    else:
        return jsonify({"error": "Failed to get response from Hugging Face API", "details": response.text}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
