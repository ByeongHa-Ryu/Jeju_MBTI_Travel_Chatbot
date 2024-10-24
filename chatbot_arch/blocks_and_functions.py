from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents.agent_types import AgentType
from langchain_core.output_parsers import StrOutputParser,JsonOutputParser
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import GoogleGenerativeAI # type: ignore
from dotenv import load_dotenv
import os
from prompts import cls_llm_inst
import pandas as pd
from prompts import * 
import streamlit as st
from transformers import AutoTokenizer, AutoModel
import numpy as np 
# import FAISS
# import torch

"""LLM Blocks"""

load_dotenv()
my_api_key = os.getenv("GOOGLE_API_KEY")


## LLM call 
llm = GoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=my_api_key)

## dataframe agent 
data_dir = 'data/JEJU_MCT_DATA_v2.csv'
df = pd.read_csv(data_dir,encoding='cp949')


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
# #device settings 
# device = "cuda" if torch.cuda.is_available() else "cpu"
# model_name = "jhgan/ko-sroberta-multitask"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# embedding_model = AutoModel.from_pretrained(model_name).to(device)

# # embedding func
# def embed_text(text):
#     # 토크나이저의 출력도 GPU로 이동
#     inputs = tokenizer(text, return_tensors='pt', padding=True, truncation=True).to(device)
#     with torch.no_grad():
#         # 모델의 출력을 GPU에서 연산하고, 필요한 부분을 가져옴
#         embeddings = embedding_model(**inputs).last_hidden_state.mean(dim=1)
#     return embeddings.squeeze().cpu().numpy()  # 결과를 CPU로 이동하고 numpy 배열로 변환

# def generate_response_with_faiss(
#     question, df, embeddings, model, embed_text, 
#     time, local_choice, index_path=os.path.join(module_path, 'faiss_index.index'), 
#     max_count=10, k=3, print_prompt=True):
#     return None



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
