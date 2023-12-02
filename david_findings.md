# David Findings

[GitHub CoPilot](https://github.com/features/copilot) is the best of the lot.  Almost everytime it provided the correct code for the provided prompt (code comment or docstring). When the code was not correct it needed mininal revision to get it working.

[Sketch](https://pypi.org/project/sketch/) very basic and not too useful.  You ask a question and it tells you what or how to do it but it does not do it.

[pandas-LLM](https://pypi.org/project/pandas-llm/) provides answers to basic questions, could not do a simple plot.

[PandasAI](https://pypi.org/project/pandasai/#description) answers to questions were wrong more than right. I needed to take a few attempts at the prompt to get the correct answer.  It can plot, but you need to work on getting the correct prompt.

[LangChain](https://pypi.org/project/langchain/) can connect to database and answer questions about it.  But the issue is the size of the database meta data provide along with the prompt. The size of the database meta data is related to the number of table and columns in the database.  The meta data size has nothing to do with the volume of data in the database.  So if there are a few tables in the database you can ask a question and get a response within the roundtrip token limit.  But if the database contains a lot of tables with a lot of columns then the token size of the prompt will be too large to make the round trip.  This can be addressed by streamlining the meta data provided to the prompt. For each table in the database the meta data consists of the create table statement and a dump of the first five rows of the table.
