from dotenv import load_dotenv
from openai import OpenAI
import os
from flask import Flask, render_template, request, jsonify
from datetime import datetime

load_dotenv()

app = Flask(__name__)
file_path = "airpods.txt"
log_file = "interaction_log.txt"  

with open(file_path, "r", encoding="utf-8") as file:
    airpods_content = file.read()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def log_interaction(user_input, response):
    """Log user input and response to a text file."""
    with open(log_file, "a", encoding="utf-8") as file:
        file.write(f"Timestamp: {datetime.now()}\n")
        file.write(f"User Input: {user_input}\n")
        file.write(f"Response: {response}\n")
        file.write("="*50 + "\n")  # Separator for readability

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api', methods=['POST'])
def api_call():
    user_input = request.json.get('text')
    chat_completion = client.chat.completions.create(
    messages=[
        {"role": "system", "content": airpods_content},
        {"role": "user", "content": user_input},
    ],
    model="gpt-3.5-turbo",
)
    response = chat_completion.choices[0].message.content
    log_interaction(user_input, response)  # Log input and output
    return jsonify({"response": response})  # Wrap response in JSON

if __name__ == '__main__':
    app.run(debug=True)

