from dotenv import load_dotenv
from openai import OpenAI
import os
from flask import Flask, render_template, request, jsonify
from datetime import datetime

load_dotenv()

app = Flask(__name__)

# Define file paths for each route
file_paths = {
    "airpods": "airpods.txt",
    "macbook": "macbook.txt",
    "yamahayzf1000": "yamaha_yzf1000.txt",
    "nordica" : "nordica.txt"
}

link_tables = {
    "airpods": "airpods.txt",
    "macbook": "macbook.txt",
    "yamahayzf1000": "yamaha_yzf1000.txt",
    "nordica" : "nordica.txt"
}

log_file = "interaction_log.txt"  

# Mock price table as a dictionary
prices_table = nordica_table


client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def get_file_content(product):
    """Read file content based on the product name."""
    path = file_paths.get(product.lower())
    if path:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    return "File not found."

def log_interaction(user_input, response):
    """Log user input and response to a text file."""
    with open(log_file, "a", encoding="utf-8") as file:
        file.write(f"Timestamp: {datetime.now()}\n")
        file.write(f"User Input: {user_input}\n")
        file.write(f"Response: {response}\n")
        file.write("="*50 + "\n")  # Separator for readability

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
    route_name = route_name if route_name in file_paths else "airpods"  # Default to "airpods"
    file_content = get_file_content(route_name)

    # Use OpenAI API with the appropriate file content
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": file_content },
            {"role": "user", "content": user_input + "If question is not relevant to input, ask for clarification."},
        ],
        model="gpt-3.5-turbo-0613",
        functions=[price_function],
        function_call="auto"
    )
    response = chat_completion.choices[0].message.content
    print(response)
    log_interaction(user_input, response)  # Log input and output
    return jsonify({"response": response})  # Wrap response in JSON

if __name__ == '__main__':
    app.run(debug=True)
