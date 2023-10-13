# GenAI_Insights
This repository serves as a centralized location for sharing documents related to the AI Seeding Effort -- Analytic Insights and Ad-hoc Analyses.

## Documents 
1. [Tools & Questions](https://docs.google.com/document/d/1lX_OhzyxmRfg6PNLbMXUOBh2S1BGB4E77usqPBLc2-Y/edit?usp=sharing)   

## development-david
This was run using Python 3.10.12 in a virtual environment (venv). 

The requirements file installs:  
- pandas,
- black, and
- The necessary packages to run *LangChain*, *sketch*, and *pandas-LLM*.  

> Note: LangChain and pandas-LLM need an OpenAI API Key.  

### .env
The environment file contains:  

```OPENAI_API_KEY=<your key without quotes>```  

I will provide everyone with the API Key.  

> Note: The **gitignore** needs to be used so that the **.env** is not loaded to the repository, exposing the API Key.  
