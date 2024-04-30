import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from sqlalchemy import create_engine, MetaData
from llama_index.core.utilities.sql_wrapper import SQLDatabase
from llama_index.core.indices.struct_store import (
    NLSQLTableQueryEngine,
    SQLTableRetrieverQueryEngine,
)

# Storing the response
if 'generated' not in st.session_state:
    st.session_state['generated'] = []

def generate_response(message):
    # Connect to the database
    # dburi = "sqlite:///acs.db"
    # db = SQLDatabase.from_uri(dburi)

    # Connect llamindex to the PostgreSQL engine, naming the table we will use
    engine = create_engine("sqlite:///acs.sqlite")
    sql_database = SQLDatabase(engine, include_tables=["acs_dem", "acs_econ", "acs_housing"])
    # Create a structured store to offer a context to GPT
    query_engine = NLSQLTableQueryEngine(sql_database)
    # "gpt-4-turbo"
    query_engine.engine = "gpt-4"
    response = query_engine.query(message)

    # Simulated response from a query engine
    class Response:
        def __init__(self, answer, sql_query, sql_answer):
            self.ai_answer = answer
            self.sql_query = sql_query
            self.sql_answer = sql_answer

    sql_query = response.metadata.get("sql_query")
    with engine.connect() as connection:
        cursor = connection.exec_driver_sql(sql_query)
        sql_answer = pd.DataFrame(cursor.fetchall()).dropna()

    for col in sql_answer.columns:
            # Temporarily attempt to convert column to numeric with coercion
            temp_series = pd.to_numeric(sql_answer[col], errors='coerce')

            # Check if the column can be converted fully to numeric (no NaNs resulted from actual strings)
            if not temp_series.isnull().any():
                # Since no NaNs were introduced, it's safe to convert this column to numeric
                sql_answer[col] = pd.to_numeric(sql_answer[col]).round(1)

    # Create an instance of Response class
    final_response = Response(response, sql_query, sql_answer)

    return final_response

def get_text():
    # Get user input from text input field
    input_text = st.text_input("You: ", "", key="input")
    return input_text

def main():
    # Load environment variables
    load_dotenv()

    # Display header
    #st.header('Ask a Question:')

    with st.sidebar:
        selected=option_menu(
            menu_title='InsightQuery',
            options=['Home', 'Data Dictionary'],
            icons =['house', 'database'],
            default_index=0
        )

    if selected=='Home':
        # Create columns for layout
        col1, col2 = st.columns([1, 4])  # Adjust the ratio based on your needs
    
        # Display robot head image in the first column
        with col1:
            st.image("3662817.png", width=100)  # Adjust width as needed
    
        # Display header in the second column
        with col2:
            st.header('Enter Your Question:')
    
        # Get user input
        user_input = get_text()

        if user_input:
            # Generate response for the user input
            response = generate_response(user_input)
            st.session_state["generated"] = response.ai_answer
            st.session_state["sql_query"] = response.sql_query
            st.session_state["sql_answer"] = response.sql_answer
    
        if st.session_state['generated']:
            # Display the generated response
            #st.write(st.session_state['generated'])
            st.text("Answer:")
            st.text(st.session_state['generated'])
            st.text("SQL Query:")
            st.text(st.session_state['sql_query'])
            st.text("SQL Result:")
            format_dict = {col: "{:,.1f}" for col in
                           st.session_state['sql_answer'].select_dtypes(include=['float']).columns}
            st.dataframe(st.session_state['sql_answer'].style.format(format_dict))

    if selected=='Data Dictionary':

        housing, econ, dem = st.tabs(['ACS Housing Table', 'ACS Demographics Table', 'ACS Economics Table'])
        engine = create_engine("sqlite:///acs.sqlite", future=True)
        conn = engine.connect()

        housing.text('some description')
        with engine.connect() as connection:
            cursor = connection.exec_driver_sql("SELECT * FROM acs_housing limit 10")
            housing.dataframe(pd.DataFrame(cursor.fetchall()))

        dem.text('some description')
        with engine.connect() as connection:
            cursor = connection.exec_driver_sql("SELECT * FROM acs_dem limit 10")
            dem.dataframe(pd.DataFrame(cursor.fetchall()))

        econ.text('some description')
        with engine.connect() as connection:
            cursor = connection.exec_driver_sql("SELECT * FROM acs_econ limit 10")
            econ.dataframe(pd.DataFrame(cursor.fetchall()))



if __name__ == '__main__':
    main()