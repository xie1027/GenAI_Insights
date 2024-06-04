# The codes are inspired from these two posts: 
# https://dev.to/ssk14/query-database-using-langchain-275g
# https://medium.com/@antonyseabra/unleashing-the-power-of-knowledge-connecting-chatgpt-to-databases-for-advanced-question-answering-8dfe5f140b1b
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
from sqlalchemy import Table, Column, String, Numeric, Date, ForeignKey, insert
from llama_index.core.utilities.sql_wrapper import SQLDatabase
from llama_index.core.indices.struct_store import (
    NLSQLTableQueryEngine,
    SQLTableRetrieverQueryEngine,
)

# Storing the response
if 'generated' not in st.session_state:
    st.session_state['generated'] = []

def generate_response(message, table_list, engine):
    # Connect to the database
    # dburi = "sqlite:///acs.db"
    # db = SQLDatabase.from_uri(dburi)

    # Connect llamindex to the PostgreSQL engine, naming the table we will use
    # engine = create_engine("sqlite:///acs.sqlite")
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
    input_text = st.text_input(r"$\textsf{\large Please enter a question into the following box and the bot will return an answer:}$", "", key="input", placeholder = "Example: What was the total population of New York in 2021?")
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

def add_new_table(engine, new_df):
    # add this table as a temp table in the database
    sql_database = SQLDatabase(engine)
    metadata_obj = sql_database.metadata_obj

    # Start defining the table with the table name and metadata
    table_name = "acs_new"

    # , prefixes=['TEMPORARY']
    new_table = Table(table_name, metadata_obj)
    # Loop over your DataFrame's columns to add them as columns in the table
    for i, column_name in enumerate(new_df.columns):
        if i == 0:  # First column is a String
            new_table.append_column(Column(column_name, String(20), primary_key=True))
        elif i == 1:  # Second column is also a String but marked as a primary key
            new_table.append_column(Column(column_name, Numeric, primary_key=True))
        else:  # The rest of the columns are Numeric and nullable
            new_table.append_column(Column(column_name, Numeric, nullable=True))

    metadata_obj.create_all(engine)

    # Insert rows
    rows_to_insert = new_df.to_dict(orient='records')
    # Connect to the database
    for row in rows_to_insert:
        stmt = insert(new_table).values(**row)
        with engine.connect() as connection:
            cursor = connection.execute(stmt)
            connection.commit()

    st.markdown(":smiley: **Table Added!**")


def main():
    # Load environment variables
    load_dotenv()

    # Display header
    #st.header('Ask a Question:')

    with st.sidebar:
        selected=option_menu(
            menu_title='InsightQuery',
            options=['Meet the Bot', 'Home', 'Data Dictionary', 'Upload Your Data File'],
            icons =['robot', 'house', 'database', 'file-earmark-arrow-up'],
            default_index=0
        )

    engine = create_engine("sqlite:///acs.sqlite", future=True)
    
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
            selected_tables = [key for key, value in table_list.items() if value]

            # check if new table exists
            if "acs_new" in SQLDatabase(engine).metadata_obj.tables:
                selected_tables.append("acs_new")
                
            response = generate_response(user_input, selected_tables, engine)
            st.session_state["generated"] = response.ai_answer
            st.session_state["sql_query"] = response.sql_query
            st.session_state["sql_answer"] = response.sql_answer
    
        if st.session_state['generated']:
            # Display the generated response
            #st.write(st.session_state['generated'])
            st.markdown(":speech_balloon: **Answer:**")
            st.markdown(st.session_state['generated'])

            # plot it only if including "state". if including "year", only plot 2021
            chart_data = st.session_state["sql_answer"]
            if chart_data is not None:
                chart_data = pd.DataFrame(chart_data)
                # Check for required columns and adequate data length
                if len(chart_data) > 2 and ("state" in chart_data.columns or "year" in chart_data.columns):
                    # Specific handling when both 'state' and 'year' columns are present
                    if "state" in chart_data.columns and "year" in chart_data.columns:
                        chart_data = chart_data[chart_data['year'] == 2021].drop('year', axis=1)
                        chart_data.set_index('state', inplace=True)
                        st.markdown("**Data in 2021**")
                        st.bar_chart(chart_data)
                    # Handling when only 'year' is present
                    elif "year" in chart_data.columns:
                        chart_data.set_index('year', inplace=True)
                        st.line_chart(chart_data)
                    # Handling when only 'state' is present
                    else:
                        chart_data.set_index('state', inplace=True)
                        st.bar_chart(chart_data)
            #if chart_data is not None:
            #    if "state" in chart_data.columns and len(chart_data) > 2:
            #        if "year" in chart_data.columns:
            #            chart_data = chart_data[chart_data.year == 2021].drop("year", axis = 1)
            #            st.markdown("**Data in 2021**")
            #        chart_data = pd.DataFrame(chart_data)
            #        chart_data.set_index("state", inplace = True)
            #        st.bar_chart(chart_data)

            st.markdown(":speech_balloon: **SQL Query:**")
            st.text(st.session_state['sql_query'])
            st.markdown(":speech_balloon: **SQL Result:**")
            if st.session_state['sql_answer'] is not None:
                format_dict = {col: "{:,.1f}" for col in
                               st.session_state['sql_answer'].select_dtypes(include=['float']).columns}
                st.table(st.session_state['sql_answer'].style.format(format_dict))

    if selected=='Data Dictionary':

        housing, dem, econ = st.tabs(['ACS Housing Table', 'ACS Demographics Table', 'ACS Economics Table'])
        #engine = create_engine("sqlite:///acs.sqlite", future=True)
        conn = engine.connect()

        housing.markdown('The American Community Survey (ACS) Housing Table from 2012 to 2021 provides an in-depth view of the U.S. housing landscape, including housing occupancy, types, owner versus renter statistics, among others.')
        with engine.connect() as connection:
            cursor = connection.exec_driver_sql("SELECT * FROM acs_housing limit 10")
            housing.table(pd.DataFrame(cursor.fetchall()))

            


        dem.markdown("The American Community Survey (ACS) Demographics Table from 2012 to 2021 provides a detailed look at the evolving characteristics of the U.S. population, including age, race, household structure, among others.")
        with engine.connect() as connection:
            cursor = connection.exec_driver_sql("SELECT * FROM acs_dem limit 10")
            dem.table(pd.DataFrame(cursor.fetchall()))

        econ.markdown('The American Community Survey (ACS) Economics Table from 2012 to 2021 provides a comprehensive overview of the economic conditions affecting the U.S. population, including employment status, income levels, industry participation, among others.')
        with engine.connect() as connection:
            cursor = connection.exec_driver_sql("SELECT * FROM acs_econ limit 10")
            econ.table(pd.DataFrame(cursor.fetchall()))

    

    if selected=='Meet the Bot':

        col1, col2 = st.columns(2)  
    
        with col1:
            st.image("3662817.png")
            
        with col2:
            st.markdown("**Hi! My name is Ivan :smiley: - I'm the InsightQuery bot.**")
            st.write("I'm a whiz with tables!")
            st.write("Just hand over any table, and I'll reveal all its secrets and insights.")
    
    if selected=='Upload Your Data File':
        uploaded_file = st.file_uploader("Choose a file")
        if uploaded_file is not None:
            new_df = pd.read_csv(uploaded_file)
            # drop acs_new
            metadata_obj = SQLDatabase(engine).metadata_obj
            if "acs_new" in metadata_obj.tables:
                # Get the table from metadata
                table_to_drop = metadata_obj.tables["acs_new"]
                table_to_drop.drop(engine)  # Drop the table

            add_new_table(engine, new_df)
            with engine.connect() as connection:
                cursor = connection.exec_driver_sql("SELECT * FROM acs_new limit 10")
                st.table(pd.DataFrame(cursor.fetchall()))



if __name__ == '__main__':
    main()