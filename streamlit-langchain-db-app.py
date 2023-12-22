"""
Streamlit Langchain DB App

https://dev.to/ssk14/query-database-using-langchain-275g

How many rows are in the acs table?
    There are 520 rows in the acs table.

How many geographic areas are in the acs table?
    There are 52 geographic areas in the acs table.

What are the distinct years in the acs table?
    2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021

How many five to nine year olds are in Alabama in 2021?
    301,814

Usage Examples:

# Instantiate the DataAIQuestioner class
questioner = DataAIQuestioner(
    question="How many nine year olds were in Kentucky in 2020?",
    db_path=Parameters.db_path,
    openai_api_key=Parameters.openai_api_key,
)
# Execute the data analysis
questioner.execute_data_analysis()

# Instantiate the DataAIQuestioner class
questioner = DataAIQuestioner(
    question="How many nine year olds were in Kentucky by year?",
    db_path=Parameters.db_path,
    openai_api_key=Parameters.openai_api_key,
)
# Execute the data analysis
questioner.execute_data_analysis()

streamlit run streamlit-langchain-db-app.py
"""
import streamlit as st
from ai_db_tools import Parameters, DataAIQuestioner

# Storing the response
if 'generated' not in st.session_state:
    st.session_state['generated'] = []

def get_text():
    # Get user input from text input field
    input_text = st.text_input("You: ", "", key="input")
    return input_text  

def main():
    # Display header
    st.header('Query Database Like you Chat')

    # Get user input
    user_input = get_text()

    # Generate response for the user input
    if user_input:
        questioner = DataAIQuestioner(
            question=user_input,
            db_path=Parameters.db_path,
            openai_api_key=Parameters.openai_api_key,
        )

        # Execute the data analysis
        questioner.execute_data_analysis()

        st.divider()
        st.subheader("Question:")
        st.text(questioner.question)
        st.divider()
        st.subheader("SQL Prompt:")
        st.text(questioner.Answer.sql_prompt)
        st.divider()
        st.subheader("SQL:")
        st.text(questioner.Answer.sql)
        st.divider()
        st.subheader("Result:")
        st.text(questioner.Answer.table_text)
        st.divider()
        st.subheader("Readable Format Prompt:")
        st.text(questioner.Answer.put_in_readable_format_prompt)
        st.divider()
        st.subheader("Readable Format:")
        st.text(questioner.Answer.cleaned_result)
        st.divider()
        st.subheader("Plot Prompt:")
        st.text(questioner.DFPlot.prompt)
        st.divider()
        st.subheader("Python Code for Plot:")
        st.text(questioner.DFPlot.python_code)
        st.divider()
        st.header("More than one data point:")
        st.text(questioner.DFPlot.more_than_one_data_point)
        st.divider()
        st.subheader("Plot Code Error:")
        st.text(questioner.DFPlot.plot_code_error)
        st.divider()
        st.subheader("Plot:")
        st.image("_plot.png", caption=questioner.question)
        st.divider()


if __name__ == '__main__':
    main()
