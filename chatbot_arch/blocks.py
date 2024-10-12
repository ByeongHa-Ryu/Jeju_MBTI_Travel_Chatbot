from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents.agent_types import AgentType
from langchain_core.output_parsers import StrOutputParser,JsonOutputParser
from langchain_google_genai import GoogleGenerativeAI # type: ignore
from dotenv import load_dotenv
import os
from prompts import cls_llm_inst
import pandas as pd

load_dotenv()
my_api_key = os.getenv("GOOGLE_API_KEY")


## LLM call 
llm = GoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=my_api_key)


## dataframe agent 
data_dir = '/Users/ryubyeongha/Desktop/KMU/2024_KMU/4-2/빅콘테스트/JMT/JEJU_MCT_DATA.csv'
df = pd.read_csv(data_dir,encoding='cp949')

agent = create_pandas_dataframe_agent(
    llm=llm,                           
    df=df,                             
    verbose=False,                      
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    output_parser = JsonOutputParser(),
    allow_dangerous_code=True 
)

## RAG 
