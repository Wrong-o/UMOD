from dotenv import load_dotenv
from openai import OpenAI
import os
load_dotenv()
from flask import Flask, render_template, request, jsonify


app = Flask(__name__)
file_path = "airpods.txt"

with open(file_path, "r", encoding="utf-8") as file:
    airpods_content = file.read()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)


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
    return jsonify({"response": response})  # Wrap response in JSON

if __name__ == '__main__':
    app.run(debug=True)

