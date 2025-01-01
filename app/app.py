from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
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
from typing import Any, Optional
import json
from app.exceptions import UserNotFoundError
from app.schemas import QuestionLogSchema


current_directory = os.path.dirname(os.path.abspath(__file__))
templates_directory = os.path.join(current_directory, "templates")
static_directory = os.path.join(current_directory, "static")

app = FastAPI(openapi_url="/openapi.json")

app.mount("/templates", StaticFiles(directory=templates_directory), name="templates")
app.mount("/static", StaticFiles(directory=static_directory), name="static")

#####


# Load environment variables
load_dotenv()

# Configure logging: Read through docker logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

#Initialize the application
app = FastAPI()


def log_all_files(directory, dir_name):
    for root, _, files in os.walk(directory):
        for file in files:
            logger.info(f"File in {dir_name}: {os.path.join(root, file)}")

"""
uncomment this to get the files in docker logs
log_all_files(templates_directory, "templates") Example usage
log_all_files(static_directory, "static")


"""
# Adding Session Middleware for session storage
app.add_middleware(SessionMiddleware, secret_key=os.urandom(24))



# Set up Jinja2 Templates
templates = Jinja2Templates(directory=templates_directory)

db_endpoint = os.environ.get("DB_ENDPOINT")
db_user = os.environ.get("DB_USERNAME")
db_password = os.environ.get("DB_PASSWORD")
db_port = os.environ.get("DB_PORT")
db_name = os.environ.get("DB_NAME")

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
# Validate environment variables
if not all([db_endpoint, db_user, db_password, db_port, db_name, client]):
    raise ImportError("Database credentials were not loaded. Missing or broken .env file.")


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

#get login: loggs that login was accessed, render login.html
@app.get("/login", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def login_get(request: Request):
    """
    Logs the page access and return the login templates
    """
    logger.info("Login page accessed")
    return templates.TemplateResponse('login.html', {"request": request, "title": "Login"})

@app.post("/login", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    """
    Gets username and password from the frontend.
    Initialises UserManager with the db_config.
    Attempts a login
    If successfull, redirects to /home
    """
    user_manager = UserManager(db_config)

    try:
        login_result = user_manager.login(username, password)
        if login_result == "Login successful":
        #Store user info in session or redirect to a new page
            request.session["username"] = username
            logger.info(f"User '{username}' logged in successfully.")
            return RedirectResponse(url="/home", status_code=302)
        #Render login page with error message
    except UserNotFoundError:
        raise HTTPException(detail="User was not found", status_code= 404)
    """
         return templates.TemplateResponse('login.html', {
            "request": request, 
            "title": "Login", 
            "error": "Invalid credentials"
        })
    """
   

@app.get("/home", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def landing_page(request: Request):
    """
    Gets the product list and displays the avalible UMOD variants
    """
    try:
        active_products = db_manager.fetch_productlist()
        logger.info("Someone is on landing page. This is the products that we will try to display:")
        logger.info(active_products)
    #
    # Prepare products with display names and normalized URLs
        product_list = [
            {"display": row['product_name'], "url": row['product_name'].replace(" ", "").lower()}
            for row in active_products
        ]
    except Exception as e:
        logger.error("When accessing the homepage, the following error occured: ")
        logger.error(e)
        raise HTTPException(detail=f"Error: {e} when getting product list", status_code=  204)
    return templates.TemplateResponse('landing.html', {"request": request, "products": product_list})



@app.get("/{product_name}", response_class=HTMLResponse)
async def product_page(request: Request, product_name: str):
    """
    When user tries to access a specific product:
    1. Normalize the input by removing spaces and uppercase
    2. Attmempt to fetch the correct UMOD variant
    3. Return error page if not avalible
    4. Render the correct page if product is avalible
    """
    
    route_name = product_name.lower().replace(" ","")

    try:
        db_manager.check_product_in_productlist(route_name)
        """
        return templates.TemplateResponse('error.html', {
            "request": request,
            "title": "Error",
            "message": "Product not found"
        })
        
        """
    
        db_result = db_manager.fetch_manual(route_name)
        logger.info(db_result)
        if not db_result:
            raise HTTPException(status_code=404, detail="Product not found")
        manual = db_result[0]["manual"]
    except ConnectionError as e:
            logger.error(f"Error fetching context: {e}")
    return templates.TemplateResponse('index.html', {
        "request": request,
        "title": product_name.capitalize(),
        "context": manual
    })

@app.get("/upload", response_class=HTMLResponse)
async def upload(request: Request):
    """
    Go to custom upload page
    """
    logger.info("Upload page accessed")

    return templates.TemplateResponse('upload.html', {"request": request, "title": "Upload"})

@app.get("/", response_class=HTMLResponse)
async def home():
    """
    This function is called when root url is accessed
    """
    return RedirectResponse(url="/login")


@app.post("/clear_session")
async def clear_session(request: Request):
    """
    Clears the sessions, removes the previous messages from context
    **NOT IMPLEMENTED YET**
    """
    if "messages" in request.session:
        request.session.pop("messages")
    return {"status": "session cleared"}
"""
async def fetch_purchase_link(product: str):
    query = "SELECT link FROM product_links WHERE product_name = %s"
    result = db_manager.fetch_data(query, (product,))
    if not result:
        return "Can't find link"
    return result[0]['link']
"""
@app.post("/api")
async def api_call(request: Request, api_request: APIRequest):
    """
    Returns information in JSON format
    This user sends all messages from the session to the API and returns the api response.
    It logs all responses using db_manager.
    Logs along the way to help debugging 
    """
    logger.info("An api call initiated")
    try:
        user_input = api_request.text
        question_language = detect(user_input)
        route_name = request.headers.get("referer", "").split('/')[-1]

        try:
            db_result = db_manager.fetch_manual(route_name)
            manual = db_result[0]["manual"]
        except ConnectionError as e:
            logger.error(f"Error fetching context: {e}")

        #avalible_images = db_manager.get_images(route_name)


        if 'chat_id' not in request.session:
            request.session['chat_id'] = str(uuid4())
        logger.info(f"The chat_id was added : {request.session['chat_id']}")
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

        #API call, starting with manual content
        messages = [{"role": "system", "content": manual + "Short and to the point"}]
        messages.extend(request.session['messages'])
        logger.info("messages are working")
        # call to OpenAI with the conversation history
        try: 
            logger.info("Making the call")
            chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
            logger.info("call succesfull")
        except Exception as e:
            logger.error(f"api called failed: {e}")

        #Generate unique ID 
        assistant_message_id = str(uuid4())

        response = chat_completion.choices[0].message.content
        logger.info(chat_completion)
        logger.info(f"The following reponse was gotten from the api: {response}")
        response_language = detect(response)

        #Append response to history
        request.session['messages'].append({
            "role": "assistant",
            "content": response,
            "message_id": assistant_message_id
        })

        #Log the interaction in the database
        try:
            """
            log_query = """
                #INSERT INTO questionlog (product, question, response, chat_id, q_lang, r_lang, response_id)
                #VALUES (%s, %s, %s, %s, %s, %s, %s);
            """
            
            params = (
                route_name, user_input, response, request.session['chat_id'], question_language, response_language,
                assistant_message_id
            )
            logger.info(route_name, user_input, response, request.session['chat_id'], question_language, response_language, assistant_message_id)
            db_manager.write_data(query=log_query, params=params)
            """

            log_query = QuestionLogSchema(
                product=route_name,
                question=user_input,
                response=response,
                chat_id=request.session['chat_id'],
                question_language=question_language,
                response_language=response_language,
                response_id=assistant_message_id

            )
            db_manager.log_question(log_query) 
            logger.info("The question was sent to the log")
            logger.info(f"{response} is respones")
            response = response.replace("\ue61f", "&trade;")
            logger.info(f"Formatted API response: \n {response}")
        except Exception as e:
            raise Exception(f"{e}")
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
    """
    Submits binary feedback from the user and appends its to the database with responses.

    """
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


# FrontendErrorLog is a temporary, made for troubleshooting displaying issues due to formatting.
class FrontendErrorLog(BaseModel):
    message: str
    url: Optional[str] = None
    type: Optional[str] = None
    timestamp: str
    stack: Optional[str] = None
    response_id: str


@app.post("/log_frontend_error")
async def log_frontend_error(error_log: FrontendErrorLog):
    """
    Front end sends frontend errormessages
    Error is logged and can be viewed in docker logs
    """
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
        
        if error_log.stack:
            logger.error(f"Stack Trace: {error_log.stack}")
        
        return {"status": "error logged"}
    
    except Exception as e:
        logger.error(f"Failed to process frontend error log: {str(e)}")
        return {"status": "error logging failed"}, 500




@app.post("/self_upload_api")
async def self_upload_api_call(request: Request, api_request: APIRequest, user_uploaded_manual: str):
    """
    WIP
    Returns information in JSON format
    This user sends all messages from the session to the API and returns the api response.
    It logs all responses using db_manager.
    Logs along the way to help debugging 
    """
    logger.info("An api call initiated")
    try:
        user_input = api_request.text
        try:
            manual = user_uploaded_manual
            
        except ConnectionError as e:
            logger.error(f"Error fetching context: {e}")

        

        if 'chat_id' not in request.session:
            request.session['chat_id'] = str(uuid4())
        logger.info(f"The chat_id was added : {request.session['chat_id']}")
        try:
            if "messages" not in request.session:
                request.session["messages"] = [
                    {
                        "role": "user",
                        "content": user_input
                    }
                ]
            else:
                request.session['messages'].append({
                    "role": "user",
                    "content": user_input
                })
        except Exception as e:
            logger.error(f"Error when adding messages to session history: {e}")

        #API call, starting with manual content
        messages = [{"role": "system", "content": manual + "Short and to the point"}]
        messages.extend(request.session['messages'])
        logger.info("messages are working")
        # call to OpenAI with the conversation history
        try: 
            logger.info("Making the call")
            chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
            logger.info("call succesfull")
        except Exception as e:
            logger.error(f"api called failed: {e}")

        #Generate unique ID 
        assistant_message_id = str(uuid4())

        response = chat_completion.choices[0].message.content
        logger.info(chat_completion)
        logger.info(f"The following reponse was gotten from the api: {response}")

        #Append response to history
        request.session['messages'].append({
            "role": "assistant",
            "content": response,
            "message_id": assistant_message_id
        })
        return JSONResponse(content={
            "response": response, 
            "response_id": assistant_message_id
            })
    
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )
    


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
