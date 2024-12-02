from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
from app.database_manager import DatabaseManager
from app.user_manager import UserManager
from uuid import uuid4
from langdetect import detect
import os
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import json
import html

current_directory = os.path.dirname(os.path.abspath(__file__))
templates_directory = os.path.join(current_directory, "templates")
static_directory = os.path.join(current_directory, "static")

app = FastAPI(openapi_url="/openapi.json")

app.mount("/templates", StaticFiles(directory=templates_directory), name="templates")
app.mount("/static", StaticFiles(directory=static_directory), name="static")

#####


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
app = FastAPI()


def log_all_files(directory, dir_name):
    for root, _, files in os.walk(directory):
        for file in files:
            logger.info(f"File in {dir_name}: {os.path.join(root, file)}")

log_all_files(templates_directory, "templates")
log_all_files(static_directory, "static")

# Adding Session Middleware for session storage
app.add_middleware(SessionMiddleware, secret_key=os.urandom(24))

# Serve static files like CSS, JS

# Set up Jinja2 Templates
templates = Jinja2Templates(directory=templates_directory)

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


@app.middleware("http")
async def log_requests(request, call_next):
    response = await call_next(request)
    logger.info(f"Request path: {request.url.path}, Status code: {response.status_code}")
    return response

# Add this middleware to the FastAPI app
app.add_middleware(BaseHTTPMiddleware, dispatch=log_requests)


@app.get("/", response_class=HTMLResponse)
async def home():
    # Redirect to the login page by default
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    logger.info("Login page accessed")
    return templates.TemplateResponse('login.html', {"request": request, "title": "Login"})

@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    # Initialize UserManager with db configuration
    user_manager = UserManager(db_config)

    # Attempt to login with provided credentials
    login_result = user_manager.login(username, password)

    if login_result == "Login successful":
        # Store user info in session or redirect to a new page
        request.session["username"] = username
        logger.info(f"User '{username}' logged in successfully.")
        return RedirectResponse(url="/yamahayzf1000r1", status_code=302)
    else:
        # Render login page with error message
        return templates.TemplateResponse('login.html', {
            "request": request, 
            "title": "Login", 
            "error": "Invalid username or password"
        })



@app.get("/airpods", response_class=HTMLResponse)
async def airpods(request: Request):
    return templates.TemplateResponse('index.html', {"request": request, "title": "AirPods"})

@app.get("/umod", response_class=HTMLResponse)
async def umod(request: Request):
    return templates.TemplateResponse('index.html', {"request": request, "title": "umod"})

@app.get("/macbook", response_class=HTMLResponse)
async def macbook(request: Request):
    return templates.TemplateResponse('index.html', {"request": request, "title": "MacBook"})

@app.get("/yamahayzf1000r1", response_class=HTMLResponse)
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
        route_name = request.headers.get("referer", "").split('/')[-1]

        # Retrieve context from the database
        try:
            file_content = db_manager.fetch_context("SELECT context FROM context WHERE product = %s", [route_name])
            #logger.info(f"The following content was fetched {file_content}")
        except ConnectionError as e:
            logger.error(f"Error fetching context: {e}")

        # Assign or retrieve the chat_id for the session
        if 'chat_id' not in request.session:
            request.session['chat_id'] = str(uuid4())
        logger.info(f"The chat_id was added : {request.session['chat_id']}")
        # Append user's message to the session history
        try:
            if "messages" not in request.session:
                request.session["messages"] = [
                    {
                        "role": "user",
                        "content": user_input + f"Regarding my {route_name}:"
                    }
                ]
            else:
                request.session['messages'].append({
                    "role": "user",
                    "content": user_input + f"Regarding my {route_name}"
                })
        except Exception as e:
            logger.error(f"Error when adding messages to session history: {e}")

        # Prepare messages for OpenAI API call, starting with system content
        messages = [{"role": "system", "content": file_content + "Short and to the point"}]
        messages.extend(request.session['messages'])
        logger.info("messages are working")
        # Make the API call to OpenAI with the conversation history
        try: 
            logger.info("Making the call")
            chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
            logger.info("call succesfull")
        except Exception as e:
            logger.error(f"api called failed: {e}")

        # Generate unique ID for assistant's response message
        assistant_message_id = str(uuid4())

        response = chat_completion.choices[0].message.content
        logger.info(chat_completion)
        logger.info(f"The following reponse was gotten from the api: {response}")
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
        logger.info("The question was sent to the log")
        params = (
            route_name, user_input, response, request.session['chat_id'], question_language, response_language,
            assistant_message_id
        )
        db_manager.write_data(query=log_query, params=params)
        response = html.escape(response)  # Escape HTML-like content
        response = response.replace("\ue61f", "&trade;")
        logger.info(f"Formatted API response: \n {response}")

        try:
            logger.info(json.dumps({"response": response, "response_id": assistant_message_id}))
            return JSONResponse(content={
                "response": response, 
                "response_id": assistant_message_id
            })
        except Exception as e:
            logger.error(f"Error in formatting JSON response: {str(e)}")
            return JSONResponse(
                content={"error": "Response formatting failed", "details": str(e)},
                status_code=500
            )
    except Exception as e:
        logger.error(f"Error: {e}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

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

class FrontendErrorLog(BaseModel):
    message: str
    url: Optional[str] = None
    type: Optional[str] = None
    timestamp: str
    stack: Optional[str] = None
    response_id: str


@app.post("/log_frontend_error")
async def log_frontend_error(error_log: FrontendErrorLog):
    try:
        # Use the existing logger to log frontend errors
        logger.error(
            "Frontend Error Logged: "
            f"Message: {error_log.message}, "
            f"URL: {error_log.url}, "
            f"Type: {error_log.type}, "
            f"Timestamp: {error_log.timestamp},"
            f"response_id: {error_log.response_id}"
        )
        
        # If you want to include stack trace (optional)
        if error_log.stack:
            logger.error(f"Stack Trace: {error_log.stack}")
        
        return {"status": "error logged"}
    
    except Exception as e:
        logger.error(f"Failed to process frontend error log: {str(e)}")
        return {"status": "error logging failed"}, 500




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
