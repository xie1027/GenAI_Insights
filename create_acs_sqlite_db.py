"""
Create an ACS SQLite database

python create_acs_sqlite_db.py
"""
import sqlite3
import pathlib
import logging
import datetime
from pandas import DataFrame, read_csv

# Start time
start_time: datetime.datetime = datetime.datetime.now()

# Get the script name
script_name: str = pathlib.Path(__file__).name.replace(".py", ".log")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(script_name, mode="w"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
logger.info(f"{script_name=}")

# Data location
data_dir: pathlib.PosixPath = pathlib.Path.cwd() / "Data"

# Create permanent SQLite database in Data directory
db = sqlite3.connect(data_dir / "acs.sqlite3")  # ":memory:"

# Load ACS data into SQLite database
acs_df: DataFrame = read_csv(data_dir / "ACS_2012_21.csv")
acs_df.to_sql(name="acs", con=db, if_exists="replace", index=False)
logger.info(f"acs loaded into database")

# List all tables in SQLite database
cursor = db.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables: list[tuple] = cursor.fetchall()
logger.info(tables)

# List all columns and types in SQLite database
for table_name in tables:
    logger.info(f"Table Name: {table_name[0]}")
    cursor.execute(f"PRAGMA table_info({table_name[0]})")
    columns = cursor.fetchall()
    for column in columns:
        logger.info(f"Column Name: {column[1]}")
        logger.info(f"Column Type: {column[2]}")
    logger.info("\n")

# Close the cursor and connection
cursor.close()
db.close()

# End time
end_time: datetime.datetime = datetime.datetime.now()

# Elapsed time formatted
elapsed_time: datetime.timedelta = str(end_time - start_time)

logger.info(f"{script_name=} completed in {elapsed_time=}")
