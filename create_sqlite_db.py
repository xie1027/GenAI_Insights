"""
Read in CSV files and create a SQLite database
"""
import sqlite3
import pathlib
import logging
from pandas import DataFrame, read_csv
from typing import Generator

# Get the script name
script_name: str = pathlib.Path(__file__).name.replace(".py", ".log")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(script_name), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
logger.info(f"{script_name=}")

# Data location
data_dir: pathlib.PosixPath = pathlib.Path.cwd() / "Data"

# BEA data location
bea_dir: pathlib.PosixPath = pathlib.Path.cwd() / "Data/bea_data"

# Get the CSV files, which contain all states
csv_files: Generator = bea_dir.glob("**/*ALL*.csv")

# Read CSV files into a dictionary of DataFrames
dfs: dict[str, DataFrame] = {
    f.stem[: f.stem.index("__")].lower(): read_csv(f) for f in csv_files
}
# Check that all CSV files were read
# logger.info(dfs.keys())
# logger.info(len(dfs.keys()))
# logger.info(len([f for f in bea_dir.glob("**/*ALL*.csv")]))

# logger.info(dfs["sainc70"].info())
# logger.info(dfs["sainc70"].head())
# logger.info(dfs["sainc70"].tail())

# Remove rows with missing values from all DataFrames
dfs = {k: v.dropna(axis=0, how="any") for k, v in dfs.items()}

# Replace double quotes in all DataFrame values
dfs = {k: v.replace('"', "", regex=True) for k, v in dfs.items()}

# Convert year column to a single column in all DataFrames
dfs = {
    k: v.melt(
        id_vars=[
            "GeoFIPS",
            "GeoName",
            "Region",
            "TableName",
            "LineCode",
            "IndustryClassification",
            "Description",
            "Unit",
        ],
        var_name="Year",
        value_name="Value",
    )
    for k, v in dfs.items()
}

# logger.info(dfs["sainc70"].info())
# logger.info(dfs["sainc70"].head())
# logger.info(dfs["sainc70"].tail())

# Create permanent SQLite database in Data directory
db = sqlite3.connect(data_dir / "data.sqlite3")  # ":memory:"

# Load all DataFrames into SQLite database
for k, v in dfs.items():
    v.to_sql(name=k, con=db, if_exists="replace", index=False)
    logger.info(f"{k} loaded into database")

# List all tables in SQLite database
cursor = db.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
logger.info(cursor.fetchall())

# Close database connection
db.close()

# Unique values in IndustryClassification column for all DataFrames
# industries: dict[str, set[str]] = {
#     k: set(v["IndustryClassification"].unique()) for k, v in dfs.items()
# }
# for k, v in industries.items():
#     logger.info(f"{k=}")
#     logger.info(f"{len(v)=}")
#     logger.info(f"{v=}")
#     logger.info()
