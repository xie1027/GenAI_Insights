import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import re
import os
os.environ["DC_STATEHOOD"] = "1"
import us
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

def generate_response(message, table_list):
    # Connect to the database
    # dburi = "sqlite:///acs.db"
    # db = SQLDatabase.from_uri(dburi)

    # Connect llamindex to the PostgreSQL engine, naming the table we will use
    engine = create_engine("sqlite:///acs.sqlite")
    sql_database = SQLDatabase(engine, include_tables=table_list)
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
    if response.metadata.get("result") == None:
        sql_answer = None
    else:
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
    input_text = st.text_input(r"$\textsf{\large Please enter a question into the following box and the bot will return an answer:}$", "", key="input")
    return input_text

def get_check_box():
    # Define a list of table names available for selection
    available_tables = ["acs_dem", "acs_econ", "acs_housing"]

    # Dictionary to store the selected status of each table
    selected_tables = {}

    # Create a container with a column for each checkbox
    cols = st.columns(len(available_tables))

    # Dicionary mapping internal table names to user-friendly names
    # 'ACS Housing Table', 'ACS Demographics Table', 'ACS Economics Table'
    table_names = {"acs_dem": "ACS Demographics", "acs_econ": "ACS Economics", "acs_housing": "ACS Housing"}

    # Create a checkbox in each column and store the selection status
    for col, table in zip(cols, available_tables):
        display_name = table_names.get(table, table) # fallback to the table name if not found in dic
        selected_tables[table] = col.checkbox(f"Include {display_name}", value=True)

    return selected_tables
    
def replace_abbreviations_with_names(prompt):
    # Regular expression pattern to match standalone state abbreviations
    # Word boundaries (\b) ensure abbreviations are standalone words

    pattern = r'\b(' + '|'.join(re.escape(state.abbr) for state in us.states.STATES) + r')\b'

    def replace_match(match):
        print(match)
        # Use the matched abbreviation to look up the state
        state = us.states.lookup(match.group())
        return state.name if state else match.group()

    # Replace all found abbreviations in the sentence using the pattern and replacement function
    updated_prompt = re.sub(pattern, replace_match, prompt)
    #updated_sentence = re.sub(pattern, replace_match, sentence, flags=re.IGNORECASE)
    return updated_prompt
    
def main():
    # Load environment variables
    load_dotenv()

    # Display header
    #st.header('Ask a Question:')

    with st.sidebar:
        selected=option_menu(
            menu_title='InsightQuery',
            options=['Home', 'Data Dictionary', 'Meet the Bot'],
            icons =['house', 'database'],
            default_index=0
        )

    if selected=='Home':
        # Create columns for layout
        col1, col2, col3 = st.columns(3)  # Adjust the ratio based on your needs
    
        # Display robot head image in the first column
        with col1:
            st.image("fannie_mae_logo.jpg", width=50)

        with col2:
            st.image("3662817.png")  # Adjust width as needed
    
        # Get user input
        user_input = replace_abbreviations_with_names(get_text())
        
        # test: get user selection
        table_list = get_check_box()

        if table_list:
            st.session_state["table"] = table_list


        if user_input:
            # Generate response for the user input
            table_list = st.session_state["table"]
            user_check_box = [key for key, value in table_list.items() if value]
            response = generate_response(user_input, user_check_box)
            st.session_state["generated"] = response.ai_answer
            st.session_state["sql_query"] = response.sql_query
            st.session_state["sql_answer"] = response.sql_answer
    
        if st.session_state['generated']:
            # Display the generated response
            #st.write(st.session_state['generated'])
            st.markdown("**Answer:**")
            st.markdown(st.session_state['generated'])

            # plot it only if including "state". if including "year", only plot 2021
            chart_data = st.session_state["sql_answer"]
            if chart_data is not None:
                if "state" in chart_data.columns and len(chart_data) > 2:
                    if "year" in chart_data.columns:
                        chart_data = chart_data[chart_data.year == 2021].drop("year", axis = 1)
                        st.markdown("**Data in 2021**")
                    chart_data = pd.DataFrame(chart_data)
                    chart_data.set_index("state", inplace = True)
                    st.bar_chart(chart_data)

            st.markdown("**SQL Query:**")
            st.text(st.session_state['sql_query'])
            st.markdown("**SQL Result:**")
            if st.session_state['sql_answer'] is not None:
                format_dict = {col: "{:,.1f}" for col in
                               st.session_state['sql_answer'].select_dtypes(include=['float']).columns}
                st.dataframe(st.session_state['sql_answer'].style.format(format_dict))

    if selected=='Data Dictionary':

        housing, dem, econ = st.tabs(['ACS Housing Table', 'ACS Demographics Table', 'ACS Economics Table'])
        engine = create_engine("sqlite:///acs.sqlite", future=True)
        conn = engine.connect()

        housing.markdown('The American Community Survey (ACS) Housing Table from 2012 to 2021 provides an in-depth view of the U.S. housing landscape, including housing occupancy, types, owner versus renter statistics, among others.')
        with engine.connect() as connection:
            cursor = connection.exec_driver_sql("SELECT * FROM acs_housing limit 10")
            housing.dataframe(pd.DataFrame(cursor.fetchall()))

        dem.markdown("The American Community Survey (ACS) Demographics Table from 2012 to 2021 provides a detailed look at the evolving characteristics of the U.S. population, including age, race, household structure, among others.")
        with engine.connect() as connection:
            cursor = connection.exec_driver_sql("SELECT * FROM acs_dem limit 10")
            dem.dataframe(pd.DataFrame(cursor.fetchall()))

        econ.markdown('The American Community Survey (ACS) Economics Table from 2012 to 2021 provides a comprehensive overview of the economic conditions affecting the U.S. population, including employment status, income levels, industry participation, among others.')
        with engine.connect() as connection:
            cursor = connection.exec_driver_sql("SELECT * FROM acs_econ limit 10")
            econ.dataframe(pd.DataFrame(cursor.fetchall()))



if __name__ == '__main__':
    main()