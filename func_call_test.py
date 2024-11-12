from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# Define the function to look up prices
def get_link(product_name, prices_table):
    # Check if product is in the table, return price
    return prices_table.get(product_name.lower(), "Link not found")

# Mock price table as a dictionary
prices_table = {
    "apple": "http://lidl.se/apples",
    "motor olja": "Motore.se/lmao",
    "chocolate": 2.5,
    # Add other products as needed
}

# Register the function with OpenAI
function = {
    "name": "get_link",
    "description": "Get the link to a product",
    "parameters": {
        "type": "object",
        "properties": {
            "product_name": {"type": "string", "description": "The name of the product"}
        },
        "required": ["product_name"]
    }
}

# Call the API
response = client.chat.completions.create(
    messages=[
        {"role": "user", "content": "What are"},
    ],
    model="gpt-3.5-turbo",
    functions=[function],
    function_call="auto"
)

# Check if response includes a function call
try:
    function_call = response.choices[0].message.function_call
    if function_call:
        # Parse arguments as a dictionary
        arguments = json.loads(function_call.arguments)
        product_name = arguments["product_name"]
        # Look up the price
        price = get_link(product_name, prices_table)
        print(f"The price of {product_name} is {price}")
except AttributeError as e:
    print("Error accessing function call:", e)
except json.JSONDecodeError as e:
    print("Error parsing function call arguments:", e)



