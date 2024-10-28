from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents.agent_types import AgentType
from langchain_core.output_parsers import StrOutputParser,JsonOutputParser
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import GoogleGenerativeAI # type: ignore
from langchain.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import ConfigurableField

from dotenv import load_dotenv
import os
from prompts import cls_llm_inst
import pandas as pd
from prompts import * 
import streamlit as st
from transformers import AutoTokenizer, AutoModel
import numpy as np 

"""LLM Blocks"""

load_dotenv()
my_api_key = os.getenv("GOOGLE_API_KEY")


## LLM call 
llm = GoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=my_api_key)

## dataframe agent 
data_dir = 'data/JEJU_MCT_DATA_final.csv'
df = pd.read_csv(data_dir)


## Data Frame agent on Gemini Engine 
agent = create_pandas_dataframe_agent(
    llm=llm,                           
    df=df,                             
    verbose=True,                      
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
    output_parser = StrOutputParser(),
    prompt = agent_inst,
    allow_dangerous_code=True 
)

# ## RAG
mbti = "ENFP"
month="3"

model_name = "upskyy/bge-m3-Korean"
model_kwargs = {'device': 'cpu'} 
embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs
        # encode_kwargs=encode_kwargs
)


# 저장된 데이터를 로드
loaded_db = FAISS.load_local(
    folder_path=f"./database/mct_db/{mbti}/{month}",
    index_name=f"mct_{mbti}_{month}",
    embeddings=embeddings,
    allow_dangerous_deserialization=True,
)
# k 설정
retriever = loaded_db.as_retriever(search_kwargs={"k": 1}).configurable_fields(
    search_type=ConfigurableField(
        id="search_type",
        name="Search Type",
        description="The search type to use",
    ),
    search_kwargs=ConfigurableField(
        # 검색 매개변수의 고유 식별자를 설정
        id="search_kwargs",
        # 검색 매개변수의 이름을 설정
        name="Search Kwargs",
        # 검색 매개변수에 대한 설명을 작성
        description="The search kwargs to use",
    ),
)

config = {
    "configurable": {
        "search_type": "mmr",
        "search_kwargs": {"k": 5, "fetch_k": 20, "lambda_mult": 0.8},
    }
}



"""Fuctions for JMT app"""

## MBTI validate
def validate_mbti(mbti):
    # input length 
    if len(mbti) != 4:
        return False
    
    # input value
    if mbti[0] not in {"E", "I"}: 
        return False
    if mbti[1] not in {"N", "S"}: 
        return False
    if mbti[2] not in {"F", "T"}:
        return False
    if mbti[3] not in {"P", "J"}: 
        return False

    return True  

def clear_chat_history():
    st.session_state.memory = ConversationBufferMemory()
    st.session_state.messages = [{"role": "assistant", "content": "제주도를 여행하기 딱 좋은 날씨네요 😎"}]
