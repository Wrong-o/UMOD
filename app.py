from dotenv import load_dotenv
from openai import OpenAI
import os
from flask import Flask, render_template, request, jsonify
from datetime import datetime
from database_manager import DatabaseManager


load_dotenv()

app = Flask(__name__)
db_endpoint = os.environ.get("DB_ENDPOINT")
db_user = os.environ.get("DB_USERNAME")
db_password = os.environ.get("DB_PASSWORD")
db_port = os.environ.get("DB_PORT")
db_name = os.environ.get("DB_NAME")
# Database setup:
db_config = {
    'host': db_endpoint,
    'dbname': db_name,
    'user': db_user,
    'password': db_password,
    'port': db_port
}

db_manager = DatabaseManager()
db_manager.connect()


client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# Define the function to look up prices
def get_price(product_name, prices_table):
    # Check if product is in the table, return price
    return prices_table.get(product_name, "Price not found")

price_function = {
    "name": "get_price",
    "description": "Get the price of a product",
    "parameters": {
        "type": "object",
        "properties": {
            "product_name": {"type": "string", "description": "The name of the product"}
        },
        "required": ["product_name"]
    }
}


@app.route('/')
def home():
    return render_template('index.html', title="Home")

@app.route('/airpods')
def airpods():
    return render_template('index.html', title="AirPods")

@app.route('/macbook')
def macbook():
    return render_template('index.html', title="MacBook")

@app.route('/yamahayzf1000')
def yamahayzf1000():
    return render_template('index.html', title="Yamaha yzf1000")

@app.route('/nordica')
def nordica():
    return render_template('index.html', title="Nordica Bootfitter")

# API route that uses dynamic file content
@app.route('/api', methods=['POST'])
def api_call():
    user_input = request.json.get('text')
    # Determine which file content to use based on the referer URL
    route_name = request.referrer.split('/')[-1]  # Get last part of URL, e.g., "airpods"
    file_content = db_manager.fetch_data("SELECT context FROM CONTEXT WHERE product = %s", [route_name])
    print(file_content)

    # Use OpenAI API with the appropriate file content
    chat_completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": file_content },
            {"role": "user", "content": user_input + f"Regarding my {route_name}:"},
        ],
        functions=[price_function],
        function_call="auto"
    )
    response = chat_completion.choices[0].message.content
    print(response)


    log_query = "INSERT INTO questionlog (product, question, response) VALUES (%s, %s, %s)"
    params = (route_name, user_input, response)

    db_manager.write_data(query=log_query, params=params)
    return jsonify({"response": response})  # Wrap response in JSON

if __name__ == '__main__':
    app.run(debug=True)
