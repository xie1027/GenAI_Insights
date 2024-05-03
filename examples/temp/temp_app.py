import streamlit as st
# from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from streamlit_option_menu import option_menu
import pandas as pd
from dotenv import load_dotenv
# from langchain.chat_models import ChatOpenAI
from langchain import SQLDatabase, OpenAI
# from langchain_experimental.sql import SQLDatabaseChain
from sqlalchemy import create_engine, MetaData
from sqlalchemy import Table, Column, String, Numeric, Date, ForeignKey, insert
from llama_index.core.utilities.sql_wrapper import SQLDatabase
from llama_index.core.indices.struct_store import (
    NLSQLTableQueryEngine,
    SQLTableRetrieverQueryEngine,
)
import matplotlib.pyplot as plt
from sqlalchemy import Table, Column, String, Numeric, Date, ForeignKey

# Storing the response
if 'generated' not in st.session_state:
    st.session_state['generated'] = []


def generate_response(message, table_list, engine):

    # Connect to the database
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
    input_text = st.text_input("You: ", "", key="input")
    return input_text


def get_check_box():
    # Define a list of table names available for selection
    available_tables = ["acs_dem", "acs_econ", "acs_housing"]

    # Dictionary to store the selected status of each table
    selected_tables = {}

    # Create a container with a column for each checkbox
    cols = st.columns(len(available_tables))

    # Dictionary mapping internal table names to user-friendly names
    table_names = {"acs_dem": "ACS Demographics", "acs_econ": "ACS Economics",
                   "acs_housing": "ACS Housing"}

    # Create a checkbox in each column and store the selection status
    for col, table in zip(cols, available_tables):
        display_name = table_names.get(table, table)  # Fallback to the table name if not found in dictionary
        #selected_tables[table] = col.checkbox(f"Include {table}", value=True)
        selected_tables[table] = col.checkbox(f"Include {display_name}", value=True)

    return selected_tables

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
    # st.header('Ask a Question:')

    with st.sidebar:
        selected = option_menu(
            menu_title='InsightQuery',
            options=['Home', 'Data Dictionary', 'Upload Your Data File'],
            icons=['house', 'database', 'file-earmark-arrow-up'],
            default_index=0
        )

    engine = create_engine("sqlite:///acs.sqlite", future=True)
    print("just once")




    if selected == 'Home':
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
        table_list = get_check_box()

        if table_list:
            st.session_state["table"] = table_list

        if user_input:
            # Generate response for the user input
            table_list = st.session_state["table"]
            selected_tables = [key for key, value in table_list.items() if value]
            # check if new table exists
            if "acs_new" in SQLDatabase(engine).metadata_obj.tables:
                print("YES, NEW TABLE ADDED")
                selected_tables.append("acs_new")

            response = generate_response(user_input, selected_tables, engine)
            st.session_state["generated"] = response.ai_answer
            st.session_state["sql_query"] = response.sql_query
            st.session_state["sql_answer"] = response.sql_answer

        if st.session_state['generated']:
            # Display the generated response
            # st.write(st.session_state['generated'])
            st.markdown(":speech_balloon: **Answer:**")
            st.markdown(st.session_state['generated'])

            ############
            # if there is state, plot
            chart_data = st.session_state["sql_answer"]
            if chart_data is not None:
                if "state" in chart_data.columns and len(chart_data) > 2:
                    if "year" in chart_data.columns:
                        chart_data = chart_data[chart_data['year'] == 2021].drop('year', axis=1)
                    chart_data = pd.DataFrame(chart_data)
                    chart_data.set_index('state', inplace=True)
                    st.bar_chart(chart_data)

            st.markdown(":speech_balloon: **SQL Query:**")
            st.text(st.session_state['sql_query'])
            st.markdown(":speech_balloon: **SQL Result:**")

            if 'sql_answer' in st.session_state and st.session_state['sql_answer'] is not None:
                format_dict = {col: "{:,.1f}" for col in
                               st.session_state['sql_answer'].select_dtypes(include=['float']).columns}
                st.dataframe(st.session_state['sql_answer'].style.format(format_dict))



    if selected == 'Data Dictionary':

        housing, econ, dem = st.tabs(['ACS Housing Table', 'ACS Demographics Table', 'ACS Economics Table'])
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

    if selected == 'Upload Your Data File':

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
            st.write(new_df)








if __name__ == '__main__':
    main()