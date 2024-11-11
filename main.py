from dotenv import load_dotenv
from openai import OpenAI
import os
load_dotenv()

file_path = "airpods.txt"

with open(file_path, "r", encoding="utf-8") as file:
    airpods_content = file.read()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)



question = input("What do you need to know?: ")
chat_completion = client.chat.completions.create(
    messages=[
        {"role": "system", "content": airpods_content},
        {"role": "user", "content": question},
    ],
    model="gpt-3.5-turbo",
)
print(chat_completion.choices[0].message.content)


