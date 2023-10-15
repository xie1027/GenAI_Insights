"""
Read in CSV files and create a SQLite database
"""
import sqlite3
import pathlib
import logging
import datetime
import bs4
import xml.etree.ElementTree as ET
from pandas import DataFrame, read_csv
from typing import Generator

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

# BEA data location
bea_dir: pathlib.PosixPath = data_dir / "bea_data"

# Get the CSV files, which contain all states
csv_files: Generator = bea_dir.glob("**/*ALL*.csv")

# Get the XML definition files
xml_files: Generator = bea_dir.glob("**/*definition*.xml")

# Get the HTML footnotes files
html_files: Generator = bea_dir.glob("**/*Footnotes*.html")

# Read CSV files into a dictionary of DataFrames
dfs: dict[str, DataFrame] = {
    f.stem[: f.stem.index("__")].lower(): read_csv(f) for f in csv_files
}
# Check that all CSV files were read into DataFrames
logger.info(
    f"All CSV files were read into DataFrames: {len(dfs.keys())==len([f for f in bea_dir.glob('**/*ALL*.csv')])}"
)

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

# Create permanent SQLite database in Data directory
db = sqlite3.connect(data_dir / "data.sqlite3")  # ":memory:"

# Load all DataFrames into SQLite database
for k, v in dfs.items():
    v.to_sql(name=k, con=db, if_exists="replace", index=False)
    logger.info(f"{k} loaded into database")

# Load ACS data into SQLite database
acs_df: DataFrame = read_csv(data_dir / "ACS_2012_21.csv")
acs_df.to_sql(name="acs", con=db, if_exists="replace", index=False)
logger.info(f"acs loaded into database")

# Load XML definition data into SQLite database
for f in xml_files:
    # Parse the XML file
    tree = ET.parse(f)
    root = tree.getroot()

    # Extract the data from the XML file
    data = []
    for child in root:
        row = {}
        for subchild in child:
            row[subchild.tag] = subchild.text
        data.append(row)

    # Create a pandas dataframe from the extracted data
    df = DataFrame(data)

    # XML meta data file name
    file_name: str = f"{f.stem[: f.stem.index('__')].lower()}_definitions"

    # Load XML meta data into SQLite database
    df.to_sql(name=file_name, con=db, if_exists="replace", index=False)
    logger.info(f"{file_name} loaded into database")

# Load HTML footnote data into SQLite database
for f in html_files:
    # read the HTML file
    with open(f, "r") as raw_html:
        html: str = raw_html.read()

    # parse the HTML using BeautifulSoup
    soup: bs4.BeautifulSoup = bs4.BeautifulSoup(html, "html.parser")

    # find the list element
    list_element: bs4.element.Tag = soup.find("ul")

    # extract the list items
    list_items: bs4.element.ResultSet = list_element.find_all("li")

    # save the list items in a Python list
    result: list = []
    for item in list_items:
        result.append(item.text.strip())

    # Create a DataFrame
    df: DataFrame = DataFrame(result, columns=["Footnotes"])

    # HTML footnote file name
    file_name: str = f"{f.stem[: f.stem.index('__')].lower()}_footnotes"

    # Load HTML footnote data into SQLite database
    df.to_sql(name=file_name, con=db, if_exists="replace", index=False)
    logger.info(f"{file_name} loaded into database")

# List all tables in SQLite database
cursor = db.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
logger.info(cursor.fetchall())

# Close database connection
db.close()

# End time
end_time: datetime.datetime = datetime.datetime.now()

# Elapsed time formatted
elapsed_time: datetime.timedelta = str(end_time - start_time)

logger.info(f"{script_name=} completed in {elapsed_time=}")
