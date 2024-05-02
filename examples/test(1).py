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
 
def main():

    with st.sidebar:
        selected=option_menu(
            menu_title='InsightQuery',
            options=['Home', 'Data Dictionary'],
            icons =['house', 'database'],
            default_index=0
        )

    if selected=='Home':
        st.write('Hello, *World!* :sunglasses:')

    if selected=='Data Dictionary':

        housing, econ, dem = st.tabs(['ACS Housing Table', 'ACS Demographics Table', 'ACS Economics Table'])
        engine = create_engine("sqlite:///acs.sqlite", future=True)
        conn = engine.connect()

        housing.text('some description')
        with engine.connect() as connection:
            cursor = connection.exec_driver_sql("SELECT * FROM acs_housing limit 10")
            housing.print(pd.DataFrame(cursor.fetchall()).keys())

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