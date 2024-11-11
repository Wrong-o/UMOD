from dotenv import load_dotenv
import os
load_dotenv()


secret_key = os.getenv("API_KEY")
print(secret_key)
