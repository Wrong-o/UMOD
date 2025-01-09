from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select
from app.models import QuestionLog, Product
from datetime import datetime
from openai import OpenAI
import os
import logging
from typing import Any, Optional
from langdetect import detect
from uuid import uuid4
from sqlalchemy import inspect
from sqlalchemy.orm import Session
from app.database import get_db  # Make sure to import get_db correctly
from app.models import Product, Role, User, QuestionLog
from passlib.context import CryptContext
from passlib.hash import bcrypt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize the application
app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "supersecretkey"))

# Set up Jinja2 Templates
templates_directory = "/app/app/templates"
static_directory = "/app/app/static"
app.mount("/templates", StaticFiles(directory=templates_directory), name="templates")
app.mount("/static", StaticFiles(directory=static_directory), name="static")
templates = Jinja2Templates(directory=templates_directory)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
# Validate environment variables


# Define request models
class FeedbackRequest(BaseModel):
    helpful: bool
    response_id: str

class APIRequest(BaseModel):
    text: str

class FrontendErrorLog(BaseModel):
    message: str
    url: Optional[str] = None
    type: Optional[str] = None
    timestamp: str
    stack: Optional[str] = None
    response_id: str



def create_user(email: str, password: str, db: Session):
    user = User(email=email)
    user.set_password(password)
    db.add(user)
    db.commit()
    print(f"User {email} created")


def verify_user_login(email: str, password: str, db: Session) -> bool:
    user = db.query(User).filter_by(email=email).first()
    if user and user.check_password(password):
        return True
    return False


# Middleware for logging requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    logger.info(f"Request path: {request.url.path}, Status code: {response.status_code}")
    return response

# Routes
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = os.path.join(static_directory, "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return FileResponse("./static/favicon.ico")

@app.get("/test_user_table")
def test_user_table(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    logger.info("Login page accessed")
    return templates.TemplateResponse("login.html", {"request": request, "title": "Login"})

@app.post("/login")
def login(
    request: Request,
    email: str = Form(...),  # Accept `email` as form data
    password: str = Form(...),  # Accept `password` as form data
    db: Session = Depends(get_db),
):
    logger.info(email, password)
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.check_password(password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return RedirectResponse(url="/home", status_code=302)
    
# @app.get("/tables")
# async def get_tables(db: Session = Depends(get_db)):
#     tables = list_all_tables(db)
#     return {"available_tables": tables}

@app.get("/home", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    # Query all products from the product_table
    products = db.query(Product).all()

    # Prepare product list for display
    product_list = [
        {
            "display": product.product_name,  # Use `product_name` as the display name
            "url": product.product_name.replace(" ", "").lower()  # Create a URL-friendly version
        }
        for product in products
    ]

    # Render the template with the product list
    return templates.TemplateResponse("landing.html", {"request": request, "products": product_list})

@app.get("/upload", response_class=HTMLResponse)
async def upload(request: Request):
    logger.info("Upload page accessed")
    return templates.TemplateResponse("upload.html", {"request": request, "title": "Upload"})

@app.get("/{product_name}", response_class=HTMLResponse)
async def product_page(request: Request, product_name: str, db: Session = Depends(get_db)):
    # Query the product by name
    product = db.query(Product).filter(Product.product_name == product_name).first()
    
    # Handle case where product is not found
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Access the manual field
    manual_content = product.manual
    
    # Render the template with the manual content
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "title": product_name.capitalize(), "context": manual_content}
    )

@app.get("/register")
async def register_get(request: Request):
    return templates.TemplateResponse("regpage.html", {"request": request, "title": "Register"})
@app.post("/api")
async def api_call(request: Request, api_request: APIRequest, db: Session = Depends(get_db)):
    try:
        user_input = api_request.text
        product_name = request.headers.get("referer", "").split('/')[-1]

        # Language detection with error handling
        try:
            question_language = detect(user_input)
        except Exception:
            question_language = "unknown"
        manual_row = db.query(Product.manual).filter(Product.product_name == product_name).first()
        manual_content = manual_row.manual if manual_row else ""

        # Ensure SessionMiddleware is installed
        if not hasattr(request, "session"):
            raise RuntimeError("SessionMiddleware is not properly configured.")
        
        if 'chat_id' not in request.session:
            request.session['chat_id'] = str(uuid4())
        try:
            if "messages" not in request.session:
                request.session["messages"] = [
                    {
                        "role": "user",
                        "content": user_input + f"Regarding my {product_name}:"
                    }
                ]
            else:
                request.session['messages'].append({
                    "role": "user",
                    "content": user_input + f"Regarding my {product_name}"
                })
        except Exception as e:
            logger.error(f"Error when adding messages to session history: {e}")

        # API call, starting with manual content
        messages = [{"role": "system", "content": manual_content + " Short and to the point"}]
        messages.extend(request.session['messages'])
        # call to OpenAI with the conversation history
        try: 
            logger.info("Making the call")
            chat_completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            logger.info("call successful")
        except Exception as e:
            logger.error(f"api called failed: {e}")

        # Append response to history

        response_id = str(uuid4())

        messages = [{"role": "user", "content": user_input}]
        chat_id = request.session.get("chat_id", str(uuid4()))
        request.session["chat_id"] = chat_id


        response_content = chat_completion.choices[0].message.content
        response_language = detect(response_content)
        
        request.session['messages'].append({
            "role": "assistant",
            "content": response_content,
            "message_id": response_id
        })
        # Simulate OpenAI API call

        # Log entry in the database
        log_entry = QuestionLog(
            product="Test Product",
            question=user_input,
            response=response_content,
            chat_id=chat_id,
            q_lang=question_language,
            r_lang=response_language,
            response_id=response_id
        )
        db.add(log_entry)
        db.commit()

        return JSONResponse(content={"response": response_content, "response_id": response_id})

    except Exception as e:
        logger.error(f"Error in /api endpoint: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/submit_feedback")
async def submit_feedback(feedback: FeedbackRequest, db: Session = Depends(get_db)):
    db.query(QuestionLog).filter(QuestionLog.response_id == feedback.response_id).update({"helpful": feedback.helpful})
    db.commit()
    return {"status": "success", "message": "Feedback recorded"}


@app.post("/frontend-log")
async def frontend_log(request: Request):
    """
    Endpoint to receive logs from the frontend and write them to the backend log.
    """
    data = await request.json()
    
    # Map string levels to logging module levels
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }
    
    # Default to INFO level if level is not found or invalid
    log_level = level_map.get(data.get("type", "").lower(), logging.INFO)
    message = data.get("message", "No message provided")
    url = data.get("url", "No URL provided")
    stack = data.get("stack", "No stack trace provided")

    # Log the message at the determined level
    logger.log(
        log_level,
        f"Frontend Error Logged: {message} | URL: {url} | Stack: {stack}"
    )
    
    return {"status": "log received"}

@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/login")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
