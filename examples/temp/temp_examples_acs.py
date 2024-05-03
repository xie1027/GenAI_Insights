# codes from: https://medium.com/@antonyseabra/unleashing-the-power-of-knowledge-connecting-chatgpt-to-databases-for-advanced-question-answering-8dfe5f140b1b
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from llama_index.core.utilities.sql_wrapper import SQLDatabase
from llama_index.core.indices.struct_store import (
    NLSQLTableQueryEngine,
    SQLTableRetrieverQueryEngine,
)
from openai import OpenAI
from sqlalchemy import create_engine, MetaData

from sqlalchemy import insert
# Create tables
from sqlalchemy import Table, Column, String, Numeric, Date, ForeignKey, insert
import pandas as pd
import os
import openai
import re
os.environ["DC_STATEHOOD"] = "1"
import us
#us.states.STATES.append(us.states.DC)
import sqlparse



engine = create_engine("postgresql://postgres:pwd@localhost:5432/postgres")
metadata_obj = MetaData()

# Load data
acs_path = "/Users/weichen/PycharmProjects/GenAi/langchain_app/Data/acs_dem.csv"
acs_df_dem = pd.read_csv(acs_path)
acs_path = "/Users/weichen/PycharmProjects/GenAi/langchain_app/Data/acs_econ.csv"
acs_df_econ = pd.read_csv(acs_path)
acs_path = "/Users/weichen/PycharmProjects/GenAi/langchain_app/Data/acs_housing.csv"
acs_df_housing = pd.read_csv(acs_path)

# Date base set up: create Tables
## Demography Table
table_name = "acs_dem"
# Start defining the table with the table name and metadata
acs_dem_table = Table(
    table_name,
    metadata_obj,
)
# Loop over your DataFrame's columns to add them as columns in the table
for i, column_name in enumerate(acs_df_dem.columns):
    if i == 0:  # First column is a String
        acs_dem_table.append_column(Column(column_name, String(20), primary_key=True))
    elif i == 1:  # Second column is also a String but marked as a primary key
        acs_dem_table.append_column(Column(column_name, Numeric, primary_key=True))
    else:  # The rest of the columns are Numeric and nullable
        acs_dem_table.append_column(Column(column_name, Numeric, nullable=True))

# Econ Table
table_name = "acs_econ"
# Start defining the table with the table name and metadata
acs_econ_table = Table(
    table_name,
    metadata_obj,
)
# Loop over your DataFrame's columns to add them as columns in the table
for i, column_name in enumerate(acs_df_econ.columns):
    if i == 0:  # First column is a String
        acs_econ_table.append_column(Column(column_name, String(20), primary_key=True))
    elif i == 1:  # Second column is also a String but marked as a primary key
        acs_econ_table.append_column(Column(column_name, Numeric, primary_key=True))
    else:  # The rest of the columns are Numeric and nullable
        acs_econ_table.append_column(Column(column_name, Numeric, nullable=True))

# Housing Table
table_name = "acs_housing"
# Start defining the table with the table name and metadata
acs_housing_table = Table(
    table_name,
    metadata_obj,
)
# Loop over your DataFrame's columns to add them as columns in the table
for i, column_name in enumerate(acs_df_housing.columns):
    if i == 0:  # First column is a String
        acs_housing_table.append_column(Column(column_name, String(20), primary_key=True))
    elif i == 1:  # Second column is also a String but marked as a primary key
        acs_housing_table.append_column(Column(column_name, Numeric, primary_key=True))
    else:  # The rest of the columns are Numeric and nullable
        acs_housing_table.append_column(Column(column_name, Numeric, nullable=True))

metadata_obj.create_all(engine)

# Insert rows
# Each dictionary represents a row in the DataFrame, with column names as keys
rows_to_insert = acs_df_dem.to_dict(orient='records')
# Connect to the database
for row in rows_to_insert:
    stmt = insert(acs_dem_table).values(**row)
    with engine.connect() as connection:
        cursor = connection.execute(stmt)
        connection.commit()

rows_to_insert = acs_df_econ.to_dict(orient='records')
# Connect to the database
for row in rows_to_insert:
    stmt = insert(acs_econ_table).values(**row)
    with engine.connect() as connection:
        cursor = connection.execute(stmt)
        connection.commit()

rows_to_insert = acs_df_housing.to_dict(orient='records')
# Connect to the database
for row in rows_to_insert:
    stmt = insert(acs_housing_table).values(**row)
    with engine.connect() as connection:
        cursor = connection.execute(stmt)
        connection.commit()

'''
# Use engine to execute a SELECT command
with engine.connect() as connection:
    cursor = connection.exec_driver_sql("SELECT * FROM acs_dem limit 10")
    print(cursor.fetchall())
# acs_dem_table.drop(engine)
'''

# Configure OPENAI_API_KEY environment variable and api_key for openai library

os.environ['OPENAI_API_KEY'] = ''
openai.api_key = ""

# engine = create_engine("postgresql://postgres:pwd@localhost:5432/postgres")
# Connect llamindex to the PostgreSQL engine, naming the table we will use
sql_database = SQLDatabase(engine, include_tables=["acs_dem", "acs_econ", "acs_housing"])
# Create a structured store to offer a context to GPT
query_engine = NLSQLTableQueryEngine(sql_database)
#"gpt-4-turbo"
query_engine.engine = "gpt-4"

# Questions: Invoke query_engine to ask a question and get answer

## Question 1: simply direct question from one table
response = query_engine.query("What is the total population of New York in 2021?")
str(response)  #  'The total population of New York in 2021 is approximately 20,114,745.'  <- correct
# Get answer metadata: PostgreSQL query <- we can output SQL codes here
response.metadata
print(response.metadata.get("sql_query"))

response.metadata.get("result") == None

'''
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import NLSQLRetriever

# default retrieval (return_raw=True)
nl_sql_retriever = NLSQLRetriever(
    sql_database, tables=["acs_dem", "acs_econ", "acs_housing"], return_raw=True
)
query_engine2 = RetrieverQueryEngine.from_args(nl_sql_retriever)
response = query_engine2.query(
    "Return the top 5 states (along with their populations) with the highest population."
)
'''
"Return the top 5 states (along with their populations) with the highest population"

response = query_engine.query("Write a SQL query which finds the total population of New York in 2021.")
str(response)  #  'The total population of New York in 2021 is approximately 20,114,745.'
# Get answer metadata: PostgreSQL query <- we can output SQL codes here
response.metadata

# info not ava in data
response = query_engine.query("What was the average educational attainment in New York in 2021?")
str(response) # 'The query provided is invalid SQL syntax. Please review and correct the query to retrieve the average educational attainment in New York in 2021.'

#How many nine year olds were in Kentucky in 2020? #275,013

# complex function
# group by
response = query_engine.query("What was the average population of each state?")
str(response)  # 'The average population of each state varies significantly, with California having the highest average population of approximately 38,634,332. Texas follows closely behind with an average population of around 27,149,04, and Florida with approximately 20,125,323. The total tokens used in this query were 52.'
response.metadata

# window function
response = query_engine.query("List the top 3 states with fewer population than the previous year.")
str(response)  # 'The top 3 states with fewer population than the previous year are California, with a population of 39,455,353 in 2021, 39,346,023 in 2020, and 39,283,497 in 2019.'
print(response.metadata.get("sql_query"))

response = query_engine.query("what were the average total population for all state.")
str(response)
print(response.metadata.get("sql_query"))

# format
# You would need to install sqlparse via pip first:
# pip install sqlparse


# What if "Year" variable is missing?
response = query_engine.query("What was the total population of New York?")
str(response)  # 'The total population of New York varies slightly each year, but based on the data provided, it ranges from approximately 19,148,453 to 20,114,745.'

# The answer is considered correct, but we could design it to ask for state or year if either one is missing (primary keys)

response = query_engine.query("What is the total population in 2021?")
str(response)  # 'The total population in 2021 varies across different regions, with values ranging from approximately 500,000 to over 29 million.' should be 576,641 - 39,455,353

response = query_engine.query("What is the sum of total population of all states in 2021?")
str(response)  # 'The sum of the total population of all states in 2021 is 333,036,755.' <-- this is correct

response = query_engine.query("What is the total population of NY in 2021?")
str(response)  #  'The query did not return any results for the total population of New York in 2021. It is possible that the data for this specific query is not available or there was an error in the query execution.'


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
# Example uses
print(replace_abbreviations_with_names("What was the total population of NY in 2021?"))

def check_prompt_for_state_and_year(prompt):
    # Generate a list of all state names and abbreviations
    states = [state.name for state in us.states.STATES]

    # Convert the state names and abbreviations to lowercase for case-insensitive matching
    states_lower = [state.lower() for state in states]

    # Checking for a year in the prompt, specifically between 2012 and 2021
    year_match = re.search(r'\b(201[2-9]|202[01])\b', prompt)

    # Checking for a state in the prompt
    state_found = any(state.lower() in prompt.lower() for state in states)
    if not year_match:
        if re.search(r'\b(19|20)\d{2}\b', prompt):  # Checks for any 4-digit year
            return "We don't have data for this year."
        return "Please specify a year between 2012 and 2021."
    elif not state_found:
        return "Please specify a state or indicate that you want the sum for all states."
    else:
        return "Your prompt contains both a state and an acceptable year."

# Example uses
user_prompt0 = "What is the total population in 2021?"
user_prompt1 = "What is the total population of Alaska?"
user_prompt2 = "What is the total population of Alaska in 2023?"
user_prompt3 = "What is the total population of Alaska in 2018?"
print(check_prompt_for_state_and_year(user_prompt0))
print(check_prompt_for_state_and_year(user_prompt1))
print(check_prompt_for_state_and_year(user_prompt2))
print(check_prompt_for_state_and_year(user_prompt3))

response = query_engine.query(replace_abbreviations_with_names("What is the total population of NY in 2021?"))
str(response) # 'The total population of New York in 2021 is approximately 20,114,745.'

### Abbreviations need manual translation."


# The next inquiry we pose exclusively requires information from the acs_econ table
response = query_engine.query("How many people were unemployed in New York in 2021?")
str(response) # In 2021, there were approximately 642,913 people unemployed in New York.

# The next inquiry we pose exclusively requires information from the acs_housing table
response = query_engine.query("What was the homeowner vacancy rate in New York in 2021?")
str(response) # 'The homeowner vacancy rate in New York in 2021 was 1.3%.' even when the var name is abb

#What was the homeowner vacancy rate in each state in 2015?
# list the change in females from the prior year grouped by state and year

# The next inquiry we pose particular query necessitates a join operation between the two tables acs_dem & acs_econ
response = query_engine.query("What was the ratio of people in the labor force to the total population of New York in 2021?")
str(response) # 'The ratio of people in the labor force to the total population of New York in 2021 was approximately 51.3%.' correct:10331727/20114745
response.metadata


# This question necessitates the integration of three tables — acs_dem & acs_econ & acs_housing — in a join operation
response = query_engine.query("In 2021, for the state with the highest female population, list the number of unemployed individuals and the number of housing units with a mortgage.")
str(response) # 'In 2021, California had the highest female population. There were 1,303,741 unemployed individuals and 5,075,316 housing units with a mortgage in the state.'


# tokens
import tiktoken
encoding = tiktoken.get_encoding("cl100k_base")
encoding = tiktoken.encoding_for_model("gpt-4")

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

num_tokens_from_string("What is the total population of New York in 2021?", "cl100k_base")
# token
response = query_engine.query("What is the total population of New York in 2021? Can you return the number of tokens used?")
str(response)


# chat

from llama_index import ServiceContext, SimpleDirectoryReader, VectorStoreIndex
response = query_engine.query("What was the average population of each state?")
def answer_q(my_data, task_meg):
  # Initializing the agent
  agent = create_pandas_dataframe_agent(
      OpenAI(temperature=0),
      my_data,
      verbose=True)
  agent.run(task_meg)

# distribution: df_graph

task_meg = "Plot the average population of each state?"
#answer_q(df_graph, task_meg)

# if there are state/year
chart_data = pd.DataFrame({
    "state": ["ac", "ak", "dl"],
    "avg_pop": [1.3, 1.2, 4.3]
})

# st.bar_chart(chart_data)


###### add a table

# read database
engine = create_engine("sqlite:///acs.sqlite", future=True)
#table_list = ["acs_dem", "acs_econ", "acs_housing"]
# include_tables=table_list
sql_database = SQLDatabase(engine)
metadata_obj = sql_database.metadata_obj
#sql_database.metadata_obj.tables.keys()

# read csv and convert it into table
acs_path = "/Users/weichen/PycharmProjects/GenAi/sql_app/acs_education.csv"
new_df = pd.read_csv(acs_path)

# Start defining the table with the table name and metadata
table_name = "acs_new"

new_table = Table(table_name, metadata_obj, prefixes=['TEMPORARY'])
# Loop over your DataFrame's columns to add them as columns in the table
for i, column_name in enumerate(new_df.columns):
    if i == 0:  # First column is a String
        new_table.append_column(Column(column_name, String(20), primary_key=True))
    elif i == 1:  # Second column is also a String but marked as a primary key
        new_table.append_column(Column(column_name, Numeric, primary_key=True))
    else:  # The rest of the columns are Numeric and nullable
        new_table.append_column(Column(column_name, Numeric, nullable=True))

metadata_obj.create_all(engine)
# sql_database.metadata_obj.tables.keys()

# Insert rows
rows_to_insert = new_df.to_dict(orient='records')
# Connect to the database
for row in rows_to_insert:
    stmt = insert(new_table).values(**row)
    with engine.connect() as connection:
        cursor = connection.execute(stmt)
        connection.commit()

# add table into database
#table_list = table_list.append('acs_new')
#sql_database = SQLDatabase(engine, include_tables=table_list)

"acs_new" in sql_database.metadata_obj.tables



'''
# test
with engine.connect() as connection:
    cursor = connection.exec_driver_sql("SELECT * FROM acs_new limit 10")
    print(cursor.fetchall())
    
import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('acs.sqlite')

# Create a cursor object using the cursor() method
cursor = conn.cursor()

# Retrieve all table names using the SELECT statement from sqlite_master
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

# Fetch all results from the cursor into a list
tables = cursor.fetchall()

# Print the names of the tables
print("Tables in the database:")
for table in tables:
    print(table[0])

# Close the connection
conn.close()


def drop_table(table_name):
    # Reflect the current database schema into MetaData
    metadata.reflect(bind=engine)
    if table_name in metadata.tables:
        # Get the table from metadata
        table_to_drop = metadata.tables[table_name]
        table_to_drop.drop(engine)  # Drop the table
        print(f"Table {table_name} dropped")
    else:
        print(f"Table {table_name} does not exist")
'''

if "acs_new" in metadata_obj.tables:
    # Get the table from metadata
    table_to_drop = metadata_obj.tables["acs_new"]
    table_to_drop.drop(engine)  # Drop the table


engine = create_engine("sqlite:///acs.sqlite", future=True)
#table_list = ["acs_dem", "acs_econ", "acs_housing"]
#sql_database = SQLDatabase(engine, include_tables=table_list)
#metadata_obj = sql_database.metadata_obj

"acs_new" in SQLDatabase(engine).metadata_obj.tables

query_engine = NLSQLTableQueryEngine(sql_database)
#"gpt-4-turbo"
query_engine.engine = "gpt-4"

response = query_engine.query("What was the ratio of individuals with bachelor's degrees to the total population in New York in 2021?")
str(response)
print(response.metadata.get("sql_query"))

# What percentage of New York's total population had graduate degrees in 2021?
#