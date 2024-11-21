from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
from database_manager import DatabaseManager
from uuid import uuid4
from langdetect import detect
import os
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Adding Session Middleware for session storage
app.add_middleware(SessionMiddleware, secret_key=os.urandom(24))

# Serve static files like CSS, JS
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 Templates
templates = Jinja2Templates(directory="static")
try:
    # Database configuration
    db_endpoint = os.environ.get("DB_ENDPOINT")
    db_user = os.environ.get("DB_USERNAME")
    db_password = os.environ.get("DB_PASSWORD")
    db_port = os.environ.get("DB_PORT")
    db_name = os.environ.get("DB_NAME")
except:
    raise KeyError("Database credentials where not loaded")

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
    raise ConnectionError("Could not connect to the database")

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Price function definition for use with OpenAI
def get_price(product_name, prices_table):
    return prices_table.get(product_name, "Price not found")

# Define request model for feedback
class FeedbackRequest(BaseModel):
    helpful: bool
    response_id: str

# Define request model for API input
class APIRequest(BaseModel):
    text: str

# Routes for rendering templates
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    logger.info("Home page accessed")
    return templates.TemplateResponse('login.html', {"request": request, "title": "Home"})

@app.get("/airpods", response_class=HTMLResponse)
async def airpods(request: Request):
    return templates.TemplateResponse('index.html', {"request": request, "title": "AirPods"})

@app.get("/macbook", response_class=HTMLResponse)
async def macbook(request: Request):
    return templates.TemplateResponse('index.html', {"request": request, "title": "MacBook"})

@app.get("/yamahayzf1000", response_class=HTMLResponse)
async def yamahayzf1000(request: Request):
    return templates.TemplateResponse('index.html', {"request": request, "title": "Yamaha yzf1000"})

@app.get("/nordica", response_class=HTMLResponse)
async def nordica(request: Request):
    return templates.TemplateResponse('index.html', {"request": request, "title": "Nordica Bootfitter"})

@app.get("/yamahar1", response_class=HTMLResponse)
async def yamahar1(request: Request):
    return templates.TemplateResponse('index.html', {"request": request, "title": "yamahar1"})

@app.post("/clear_session")
async def clear_session(request: Request):
    if "messages" in request.session:
        request.session.pop("messages")
    return {"status": "session cleared"}

@app.post("/api")
async def api_call(request: Request, api_request: APIRequest):
    logger.info("An api call was made")
    try:
        user_input = api_request.text
        # Detect input language
        question_language = detect(user_input)
        route_name = "unknown"  # Placeholder until request headers can be accessed properly

        # Retrieve context from the database
        file_content = db_manager.fetch_context("SELECT context FROM CONTEXT WHERE product = %s", [route_name])

        # Initialize session message history if it doesn't exist
        if 'messages' not in request.session:
            request.session['messages'] = []

        # Assign or retrieve the chat_id for the session
        if 'chat_id' not in request.session:
            request.session['chat_id'] = str(uuid4())

        # Append user's message to the session history
        request.session['messages'].append({
            "role": "user",
            "content": user_input + f"Regarding my {route_name}:"
        })

        # Prepare messages for OpenAI API call, starting with system content
        messages = [{"role": "system", "content": file_content}]
        messages.extend(request.session['messages'])

        # Make the API call to OpenAI with the conversation history
        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )

        # Generate unique ID for assistant's response message
        assistant_message_id = str(uuid4())

        response = chat_completion.choices[0].message.content
        response_language = detect(response)

        # Append assistant's response to session history
        request.session['messages'].append({
            "role": "assistant",
            "content": response,
            "message_id": assistant_message_id
        })

        # Log the interaction in the database
        log_query = """
            INSERT INTO questionlog (product, question, response, chat_id, q_lang, r_lang, response_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            route_name, user_input, response, request.session['chat_id'], question_language, response_language,
            assistant_message_id
        )
        db_manager.write_data(query=log_query, params=params)

        # Return JSON response
        response = response.replace("\ue61f", "&trade;")
        return {"response": response, "response_id": assistant_message_id}

    except Exception as e:
        return {"error": str(e)}, 500

@app.post("/submit_feedback")
async def submit_feedback(feedback: FeedbackRequest):
    try:
        feedback_query = """
            UPDATE questionlog
            SET helpful = %s
            WHERE response_id = %s
        """
        db_manager.write_data(
            query=feedback_query,
            params=(feedback.helpful, feedback.response_id)
        )

        return {"status": "success", "message": "Feedback recorded"}

    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
