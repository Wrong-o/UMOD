import streamlit as st
from wordcloud import WordCloud
from langdetect import detect
from collections import Counter
import matplotlib.pyplot as plt

import streamlit as st
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database_manager import DatabaseManager

def detect_language(question):
    try:
        return detect(question)
    except:
        return "unknown"

def fetch_questions_by_language(db_manager, product):
    questions = db_manager.fetch_questions(product)
    language_data = {}
    
    for entry in questions:
        question = entry['question']
        lang = detect_language(question)
        if lang not in language_data:
            language_data[lang] = []
        language_data[lang].append(question)
        
    return language_data


try:
    db_manager = DatabaseManager()
except ValueError:
    raise ValueError("Construction of the db_manager failed.")

try:
    db_manager.connect()
except ConnectionError:
    raise ConnectionError("Cannot connect to the database")

product_list = db_manager.fetch_productlist(table="questionlog")

products = [item['product'] for item in product_list]
st.title("NLP of the question asked")

selected_option = st.selectbox("Choose an option:", products)
word_data = db_manager.fetch_questions(selected_option)
print(word_data)

db_manager.close()