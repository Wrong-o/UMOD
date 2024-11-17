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

@app.route('/yamahar1')
def yamahar1():
    return render_template('index.html', title="yamahar1")


@app.route('/clear_session', methods=['POST'])
def clear_session():
    session.pop('messages', None)
    return jsonify({"status": "session cleared"})

@app.route('/api', methods=['POST'])
def api_call():
    try:  
        user_input = request.json.get('text')
        question_language = detect(user_input)
        route_name = request.referrer.split('/')[-1] 
        
        # Retrieve context from the database
        file_content = db_manager.fetch_context("SELECT context FROM CONTEXT WHERE product = %s", [route_name])

        # Initialize session message history if it doesn't exist
        if 'messages' not in session:
            session['messages'] = []
        
        # Assign or retrieve the chat_id for the session
        if 'chat_id' not in session:
            session['chat_id'] = str(uuid.uuid4())  # Generate a unique chat_id

        # Append the user's message to the session history with a unique identifier
        session['messages'].append({
            "role": "user",
            "content": user_input + f"Regarding my {route_name}:"
        })

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

        # Generate unique ID for assistant's response message
        assistant_message_id = str(uuid.uuid4())

        response = chat_completion.choices[0].message.content
        response_language = detect(response)


        # Append assistant's response to the session history with a unique identifier
        session['messages'].append({
            "role": "assistant",
            "content": response,
            "message_id": assistant_message_id
        })

        # Log the interaction in the database with chat_id and message IDs
        log_query = """
            INSERT INTO questionlog (product, question, response, chat_id, q_lang, r_lang, response_id) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            route_name, user_input, response, session['chat_id'], question_language, response_language,
            assistant_message_id
        )
        db_manager.write_data(query=log_query, params=params)

        # Replace special characters and return JSON response
        response = response.replace("\ue61f", "&trade;")
        return jsonify({"response": response, "response_id": assistant_message_id})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/submit_feedback', methods=['POST'])  # Changed from GET to POST
def submit_feedback():
    try:
        data = request.json  # Changed from args to json
        helpful = data.get('helpful')
        response_id = data.get('response_id')
        # Get route name from referer header
        referer = request.headers.get('Referer', '')
        route_name = referer.split('/')[-1] if referer else 'unknown'
        
        # Sanitize the route name
        route_name = route_name.split('?')[0]  # Remove query parameters if any
        if not route_name:
            route_name = 'unknown'
        
        feedback_query = """
            UPDATE questionlog 
            SET helpful = %s
            WHERE response_id = %s
        """

        # Make sure to correctly pass the parameters in the right order
        db_manager.write_data(
            query=feedback_query,
            params=(helpful, response_id)  # Corrected the parameter order
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
    
if __name__ == '__main__':
    app.run(debug=True)
