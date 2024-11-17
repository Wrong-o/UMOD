from dotenv import load_dotenv
from openai import OpenAI
import os
from flask import Flask, render_template, request, jsonify, session
from datetime import datetime
from database_manager import DatabaseManager
from flask_session import Session 
import uuid
from langdetect import detect

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Set a secret key for session encryption

# Configure Flask-Session for server-side session storage
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Database configuration
db_endpoint = os.environ.get("DB_ENDPOINT")
db_user = os.environ.get("DB_USERNAME")
db_password = os.environ.get("DB_PASSWORD")
db_port = os.environ.get("DB_PORT")
db_name = os.environ.get("DB_NAME")

# Initialize database configuration
db_config = {
    'host': db_endpoint,
    'dbname': db_name,
    'user': db_user,
    'password': db_password,
    'port': db_port
}

# Database and OpenAI initialization
try:
    db_manager = DatabaseManager()
except ValueError:
    raise ValueError("Construction of the db_manager failed.")

try:
    db_manager.connect()
except ConnectionError:
    raise ConnectionError("")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Price function definition for use with OpenAI
def get_price(product_name, prices_table):
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

# Routes for rendering templates
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


@app.route('/api', methods=['POST'])
def api_call():
    user_input = request.json.get('text')
    question_language = detect(user_input)
    route_name = request.referrer.split('/')[-1]  # Get last part of URL, e.g., "airpods"
    
    # Retrieve context from the database
    file_content = db_manager.fetch_context("SELECT context FROM CONTEXT WHERE product = %s", [route_name])

    # Initialize session message history if it doesn't exist
    if 'messages' not in session:
        session['messages'] = []
    
    # Assign or retrieve the chat_id for the session
    if 'chat_id' not in session:
        session['chat_id'] = str(uuid.uuid4())  # Generate a unique chat_id

    # Append the user's message to the session history
    session['messages'].append({"role": "user", "content": user_input + f"Regarding my {route_name}:"})

    # Prepare messages for OpenAI API call, starting with the system content
    messages = [{"role": "system", "content": file_content}]
    messages.extend(session['messages'])  # Add conversation history

    # Make the API call to OpenAI with the conversation history
    chat_completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        functions=[price_function],
        function_call="auto"
    )

    response = chat_completion.choices[0].message.content
    response_language = detect(response)
    print("reponse language", response_language)
    print("question language", question_language)
    session['messages'].append({"role": "assistant", "content": response})  # Add assistant response to history

    # Log the interaction in the database with chat_id
    log_query = "INSERT INTO questionlog (product, question, response, chat_id, q_lang, r_lang) VALUES (%s, %s, %s, %s, %s, %s)"
    params = (route_name, user_input, response, session['chat_id'], question_language, response_language)
    db_manager.write_data(query=log_query, params=params)

    # Replace special characters and return JSON response
    response = response.replace("\ue61f", "&trade;")
    return jsonify({"response": response})

# Endpoint to clear the session history (useful for debugging or starting new conversations)
@app.route('/clear_session', methods=['POST'])
def clear_session():
    session.pop('messages', None)
    return jsonify({"status": "session cleared"})

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/api', methods=['POST'])
def api_call():
    user_input = request.json.get('text')
    question_language = detect(user_input)
    route_name = request.referrer.split('/')[-1]  # Get last part of URL, e.g., "airpods"
    
    # Retrieve context from the database
    file_content = db_manager.fetch_context("SELECT context FROM CONTEXT WHERE product = %s", [route_name])

    # Initialize session message history if it doesn't exist
    if 'messages' not in session:
        session['messages'] = []
    
    # Assign or retrieve the chat_id for the session
    if 'chat_id' not in session:
        session['chat_id'] = str(uuid.uuid4())  # Generate a unique chat_id

    # Append the user's message to the session history
    session['messages'].append({"role": "user", "content": user_input + f"Regarding my {route_name}:"})

    # Prepare messages for OpenAI API call, starting with the system content
    messages = [{"role": "system", "content": file_content}]
    messages.extend(session['messages'])  # Add conversation history

    # Make the API call to OpenAI with the conversation history
    chat_completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        functions=[price_function],
        function_call="auto"
    )

    response = chat_completion.choices[0].message.content
    response_language = detect(response)
    print("reponse language", response_language)
    print("question language", question_language)
    session['messages'].append({"role": "assistant", "content": response})  # Add assistant response to history

    # Log the interaction in the database with chat_id
    log_query = "INSERT INTO questionlog (product, question, response, chat_id, q_lang, r_lang) VALUES (%s, %s, %s, %s, %s, %s)"
    params = (route_name, user_input, response, session['chat_id'], question_language, response_language)
    db_manager.write_data(query=log_query, params=params)

    # Replace special characters and return JSON response
    response = response.replace("\ue61f", "&trade;")
    return jsonify({"response": response})

@app.route('/submit_feedback', methods=['POST'])  # Changed from GET to POST
def submit_feedback():
    try:
        data = request.json  # Changed from args to json
        helpful = data.get('helpful')
        message = data.get('message', '')
        
        # Get route name from referer header
        referer = request.headers.get('Referer', '')
        route_name = referer.split('/')[-1] if referer else 'unknown'
        
        # Sanitize the route name
        route_name = route_name.split('?')[0]  # Remove query parameters if any
        if not route_name:
            route_name = 'unknown'
            
        feedback_query = """
            INSERT INTO feedback_log 
            (product, message, is_helpful, chat_id) 
            VALUES (%s, %s, %s, %s)
        """
        
        chat_id = session.get('chat_id', str(uuid.uuid4()))
        
        db_manager.write_data(
            query=feedback_query,
            params=(route_name, message, helpful, chat_id)
        )

        return jsonify({
            "status": "success", 
            "message": "Feedback recorded"
        }), 200

    except Exception as e:
        print(f"Error recording feedback: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

@app.route('/clear_session', methods=['POST'])
def clear_session():
    pass
    

if __name__ == '__main__':
    app.run(debug=True)
