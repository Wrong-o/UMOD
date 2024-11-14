import streamlit as st
from wordcloud import WordCloud
from collections import Counter
import matplotlib.pyplot as plt
import nltk
from nltk.tokenize import word_tokenize
import streamlit as st
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from database_manager import DatabaseManager

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
language_list = db_manager.fetch_languageslist(table="questionlog")
languages = [item['q_lang'] for item in language_list]
st.title("NLP of the question asked")

selected_product = st.selectbox("Choose a product:", products)
selected_language = st.selectbox("Choose a language:", languages)
if st.button("Press to fetch data"):
    word_data = db_manager.fetch_questions_by_language(selected_product, selected_language)
    tokens = []
    if word_data:
        for entry in word_data:
            question_text = entry['question']
            tokens.extend([word.lower() for word in word_tokenize(question_text)])
    else:
        question_text = "Missing data Missing data"
        tokens.extend([word.lower() for word in word_tokenize(question_text)])
    text = ' '.join(tokens)
    if text:
        wordcloud = WordCloud(width=800, height=400, background_color='black').generate(text)
    else:
        text = ""
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    st.pyplot(plt)

