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
import folium
from folium import plugins
import streamlit as st
from streamlit_folium import st_folium
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

## RAG 
#device settings 
# device = "cuda" if torch.cuda.is_available() else "cpu"
model_name = "jhgan/ko-sroberta-multitask"
tokenizer = AutoTokenizer.from_pretrained(model_name)
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

import folium
from folium import plugins
import streamlit as st
from streamlit_folium import st_folium
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

### 여기 변경
### 임베딩, retriever, metadata 등 추가해야함

def load_faiss_and_search(query, k=3):
    """FAISS DB에서 쿼리와 관련된 맛집 검색"""
    try:
        # 임베딩 모델 초기화
        embeddings = HuggingFaceEmbeddings(
            model_name="jhgan/ko-sroberta-multitask",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # FAISS 로드
        db = FAISS.load_local(
            "faiss_db", 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        
        # 검색 쿼리 생성
        search_query = f"{query} {st.session_state.get('mbti', '')}"
        
        # 유사도 검색 수행
        docs = db.similarity_search_with_score(search_query, k=k)
        
        # 검색 결과를 데이터프레임으로 변환
        restaurants_data = []
        for doc, score in docs:
            metadata = doc.metadata
            restaurants_data.append({
                '음식점명': metadata['음식점명'],
                '주소': metadata['주소'],
                '위도': float(metadata['위도']),
                '경도': float(metadata['경도']),
                'similarity_score': score
            })
        
        return pd.DataFrame(restaurants_data)
    
    except Exception as e:
        st.error(f"FAISS 검색 중 오류 발생: {str(e)}")
        return None

def create_map_with_restaurants(restaurants_df):
    """맛집 정보로 지도 생성"""
    try:
        if restaurants_df is None or restaurants_df.empty:
            st.warning("맛집 데이터가 없습니다.")
            return None
            
        # 첫 번째 맛집 위치로 중심 좌표 설정
        center_lat = restaurants_df.iloc[0]['위도']
        center_lng = restaurants_df.iloc[0]['경도']
        
        # 지도 생성
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=14,  # 줌 레벨 조정
            tiles='CartoDB positron',
            width=800,  # 지도 크기 명시
            height=600
        )
        
        # 맛집 마커 추가
        for idx, row in restaurants_df.iterrows():
            popup_content = f"""
                <div style='width: 200px'>
                    <h4 style='margin: 0; padding: 5px 0;'>{row['음식점명']}</h4>
                    <p style='margin: 5px 0;'>주소: {row['주소']}</p>
                </div>
            """
            
            folium.Marker(
                location=[row['위도'], row['경도']],
                popup=folium.Popup(popup_content, max_width=300),
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
        
        return m
    except Exception as e:
        st.error(f"지도 생성 중 오류 발생: {str(e)}")
        return None

def display_map(restaurants_df):
    """지도 표시 함수"""
    try:
        # 상태 초기화
        if 'map_data' not in st.session_state:
            st.session_state.map_data = None
        
        if 'current_restaurants' not in st.session_state:
            st.session_state.current_restaurants = None
            
        # 새로운 데이터가 들어왔을 때만 지도 업데이트
        if (st.session_state.current_restaurants is None or 
            not restaurants_df.equals(st.session_state.current_restaurants)):
            
            st.session_state.current_restaurants = restaurants_df.copy()
            
            # 첫 번째 맛집 위치로 중심 좌표 설정
            center_lat = restaurants_df.iloc[0]['위도']
            center_lng = restaurants_df.iloc[0]['경도']
            
            # 지도 생성
            m = folium.Map(
                location=[center_lat, center_lng],
                zoom_start=14,
                tiles='CartoDB positron',
            )
            
            # 맛집 마커 추가
            for idx, row in restaurants_df.iterrows():
                popup_content = f"""
                    <div style='width: 200px'>
                        <h4 style='margin: 0; padding: 5px 0;'>{row['음식점명']}</h4>
                        <p style='margin: 5px 0;'>주소: {row['주소']}</p>
                    </div>
                """
                
                folium.Marker(
                    location=[row['위도'], row['경도']],
                    popup=folium.Popup(popup_content, max_width=300),
                    icon=folium.Icon(color='red', icon='info-sign')
                ).add_to(m)
            
            # 지도를 고정된 컨테이너에 표시
            map_container = st.empty()
            with map_container:
                st.session_state.map_data = st_folium(
                    m,
                    width=700,
                    height=500,
                    returned_objects=["last_clicked"],
                    key="stable_map"
                )
        
        return st.session_state.map_data
        
    except Exception as e:
        st.error(f"지도 표시 중 오류 발생: {str(e)}")
        return None

def format_restaurant_response(restaurants_df):
    """맛집 정보를 LLM에 전달하기 위한 포맷팅"""
    try:
        if restaurants_df is None or restaurants_df.empty:
            return "죄송합니다. 맛집을 찾을 수 없습니다."
            
        # LLM에 전달할 맛집 정보 구성
        restaurants_info = []
        for idx, row in restaurants_df.iterrows():
            restaurant_info = {
                "이름": row['음식점명'],
                "주소": row['주소'],
                "유사도_점수": float(row['similarity_score'])  # 유사도 점수 추가
            }
            restaurants_info.append(restaurant_info)
            
        return restaurants_info
        
    except Exception as e:
        return f"맛집 정보 포매팅 중 오류 발생: {str(e)}"

def generate_llm_response(query, restaurants_info, user_mbti=None):
    """LLM을 사용하여 맛집 추천 응답 생성"""
    try:
        # LLM 프롬프트 구성
        prompt = f"""사용자 질문: {query}

    아래는 검색된 맛집 정보입니다:
        {restaurants_info}

        {f'사용자의 MBTI는 {user_mbti}입니다.' if user_mbti else ''}

        위 정보를 바탕으로 다음 가이드라인에 따라 자연스러운 맛집 추천 답변을 작성해주세요:

        1. 친근하고 자연스러운 톤으로 답변을 작성해주세요.
        2. 각 맛집의 장점과 특징을 자연스럽게 설명해주세요.
        3. 맛집들의 위치적 특성이나 접근성에 대해 언급해주세요.
        4. 사용자의 MBTI가 있다면, 그에 맞춘 맛집 설명을 추가해주세요.
        5. 마지막에는 즐거운 식사가 되길 바라는 멘트로 마무리해주세요.

        답변에서는 위도/경도 정보나 유사도 점수는 언급하지 말아주세요."""

        # LLM으로 응답 생성
        response = llm.invoke(input=prompt)
        return response
        
    except Exception as e:
        return f"LLM 응답 생성 중 오류 발생: {str(e)}"


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
