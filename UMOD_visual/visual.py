import streamlit as st
from wordcloud import WordCloud
from collections import Counter
import matplotlib.pyplot as plt
import nltk
from nltk.tokenize import word_tokenize
import streamlit as st
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database_manager import DatabaseManager
nltk.download('punkt')

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

selected_product = st.selectbox("Choose an product:", products)
selected_language = st.selectbox("Choose an language:", languages)
word_data = db_manager.fetch_questions_by_language(selected_product, selected_language)

tokens = []
print(word_data)
if word_data:
    print("hit")
    for entry in word_data:
        question_text = entry['question']
        tokens.extend([word.lower() for word in word_tokenize(question_text)])
    text = ' '.join(tokens)
    wordcloud = WordCloud(width=800, height=400, background_color='black').generate(text)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    st.pyplot(plt)
else:
    st.write(f"No question found for {selected_product} in {selected_language}")  

db_manager.close()