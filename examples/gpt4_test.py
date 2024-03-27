from llama_index.core.utilities.sql_wrapper import SQLDatabase
from llama_index.core.indices.struct_store import (
    NLSQLTableQueryEngine,
    SQLTableRetrieverQueryEngine,
)
from sqlalchemy import create_engine, MetaData
from sqlalchemy import Table, Column, String, Numeric, Date, ForeignKey
from sqlalchemy import insert
# Create tables
from sqlalchemy import Table, Column, String, Numeric, Date, ForeignKey

engine = create_engine("postgresql://postgres:pwd@localhost:5432/postgres")
metadata_obj = MetaData()

table_name = "car_brands"
car_brands_table = Table(
    table_name,
    metadata_obj,
    Column("brand", String(30), primary_key=True),
    Column("country", String(50), nullable=False)
)
table_name = "car_models"
car_models_table = Table(
    table_name,
    metadata_obj,
    Column("model", String(50), primary_key=True),
    Column("brand", String(30), ForeignKey("car_brands.brand"), nullable=False)
)
table_name = "customers"
customers_table = Table(
    table_name,
    metadata_obj,
    Column("name", String(50), primary_key=True),
    Column("country", String(50), nullable=False)
)
table_name = "sales"
sales_table = Table(
    table_name,
    metadata_obj,
    Column("customer", String(50), ForeignKey("customers.name"), nullable=False),
    Column("car_model", String(50), ForeignKey("car_models.model"), nullable=False),
    Column("sale_date", Date, nullable=False),
    Column("price", Numeric(10,2), nullable=False),
)

metadata_obj.create_all(engine)

# Use engine to execute a SELECT command
with engine.connect() as connection:
    cursor = connection.exec_driver_sql("SELECT * FROM car_brands")
    print(cursor.fetchall())

# Configure OPENAI_API_KEY environment variable and api_key for openai library
import os
os.environ['OPENAI_API_KEY'] = ''

import openai
openai.api_key = ""




# Connect llamindex to the PostgreSQL engine, naming the table we will use
sql_database = SQLDatabase(engine, include_tables=["car_brands"])
# Create a structured store to offer a context to GPT
query_engine = NLSQLTableQueryEngine(sql_database)
query_engine.engine = "gpt-4"

# Invoke query_engine to ask a question and get answer
response = query_engine.query("Which car brands are from France?")
str(response)

# Get answer metadata: PostgreSQL query <- we can output SQL codes here
response.metadata



# Insert data in the car_models table
rows = [
    {"model": "C3", "brand": "Citroen"},
    {"model": "C4", "brand": "Citroen"},
    {"model": "Creta", "brand": "Hyundai"},
    {"model": "HB20", "brand": "Hyundai"},
    {"model": "Santa Fé", "brand": "Hyundai"},
    {"model": "Tucson", "brand": "Hyundai"},
    {"model": "Compass", "brand": "Jeep"},
    {"model": "Renegade", "brand": "Jeep"},
    {"model": "Captur", "brand": "Renault"},
    {"model": "Duster", "brand": "Renault"},
    {"model": "Sandero", "brand": "Renault"},
    {"model": "V60", "brand": "Volvo"}
]
for row in rows:
    stmt = insert(car_models_table).values(**row)
    with engine.connect() as connection:
        cursor = connection.execute(stmt)
        connection.commit()

# Use engine to execute a SELECT command
with engine.connect() as connection:
    cursor = connection.exec_driver_sql("SELECT * FROM car_models")
    print(cursor.fetchall())

# Connect llamindex to the PostgreSQL engine, naming the table we will use
sql_database = SQLDatabase(engine, include_tables=["car_brands", "car_models"])
# Create a structured store to offer a context to GPT
query_engine = NLSQLTableQueryEngine(sql_database)


# Invoke query_engine to ask a question and get answer
# The next inquiry we pose exclusively requires information from the car_models table
response = query_engine.query("Which car models are from Hyundai?")
response


# Invoke query_engine to ask a question and get answer
# The next inquiry we pose particular query necessitates a join operation between the two tables,
response = query_engine.query("Which car models are produced in France?")
response


# Insert data in the customers table
rows = [
    {"name": "Antony", "country": "Brazil"},
    {"name": "Darcy", "country": "France"},
    {"name": "Karl", "country": "German"},
    {"name": "Kim", "country": "South Korea"},
    {"name": "Lee", "country": "South Korea"},
    {"name": "Manon", "country": "France"},
    {"name": "Mark", "country": "USA"}
]
for row in rows:
    stmt = insert(customers_table).values(**row)
    with engine.connect() as connection:
        cursor = connection.execute(stmt)
        connection.commit()

# Insert data in the sales table
rows = [
    {"customer": "Antony", "car_model": "Renegade", "sale_date": "2023-07-01", "price": 1000.00},
    {"customer": "Darcy", "car_model": "Sandero", "sale_date": "2023-08-01", "price": 1500.00},
    {"customer": "Karl", "car_model": "C3", "sale_date": "2023-07-13", "price": 2000.00},
    {"customer": "Kim", "car_model": "Santa Fé", "sale_date": "2023-08-04", "price": 2500.00},
    {"customer": "Lee", "car_model": "Tucson", "sale_date": "2023-07-25", "price": 1000.00},
    {"customer": "Manon", "car_model": "Compass", "sale_date": "2023-08-01", "price": 1200.00},
    {"customer": "Mark", "car_model": "HB20", "sale_date": "2023-08-09", "price": 3000.00}
]
for row in rows:
    stmt = insert(sales_table).values(**row)
    with engine.connect() as connection:
        cursor = connection.execute(stmt)
        connection.commit()



# Connect llamindex to the PostgreSQL engine, naming the table we will use
sql_database = SQLDatabase(engine, include_tables=["car_brands", "car_models", "customers", "sales"])
# Create a structured store to offer a context to GPT
query_engine = NLSQLTableQueryEngine(sql_database)


# Invoke query_engine to ask a question and get answer
# This question is a straightforward query targeting the customers table
response = query_engine.query("Who are the customers from South Korea?")
response

# Invoke query_engine to ask a question and get answer
# This question necessitates the integration of three tables — car_brands, car_models, and sales — in a join operation
response = query_engine.query("What are the sales total of cars from Hyundai?")
response

# Invoke query_engine to ask a question and get answer
# This question requires to perform a full join across all four tables
response = query_engine.query("Who bought cars from Hyundai?")
response

# Invoke query_engine to ask a question and get answer
response = query_engine.query("What were the car models sold after 07/31/2023?")
response

# Invoke query_engine to ask a question and get answer
response = query_engine.query("Who bought cars made in the country where they were born?")
response



