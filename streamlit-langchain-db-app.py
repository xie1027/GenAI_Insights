"""
Streamlit Langchain DB App

https://dev.to/ssk14/query-database-using-langchain-275g

How many rows are in the acs table?
    There are 520 rows in the acs table.

How many geographic areas are in the acs table?
    There are 52 geographic areas in the acs table.

What are the distinct years in the acs table?
    2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021

How many five to nine year olds are in Alabama in 2021?
    301,814

streamlit run streamlit-langchain-db-app.py
"""
import streamlit as st
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain

# Storing the response
if 'generated' not in st.session_state:
    st.session_state['generated'] = []

def generate_response(message):
    # Connect to the database
    # dburi = "sqlite:///Data/data.sqlite3"
    dburi = "sqlite:///Data/acs.sqlite3"
    db = SQLDatabase.from_uri(dburi)

    # Create an instance of LLM
    llm = ChatOpenAI()

    # Create an SQLDatabaseChain using the ChatOpenAI model and the database
    db_chain = SQLDatabaseChain.from_llm(llm=llm, db=db)
    ai_response = db_chain.run(message)

    return ai_response

def get_text():
    # Get user input from text input field
    input_text = st.text_input("You: ", "", key="input")
    return input_text  

def main():
    # Load environment variables
    load_dotenv()

    # Display header
    st.header('Query Database Like you Chat')

    # Get user input
    user_input = get_text()

    if user_input:
        # Generate response for the user input
        st.session_state["generated"] = generate_response(user_input)

    if st.session_state['generated']:
        # Display the generated response
        st.write(st.session_state['generated'])

if __name__ == '__main__':
    main()
