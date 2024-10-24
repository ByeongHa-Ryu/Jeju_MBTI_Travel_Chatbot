import os
from contextlib import redirect_stdout
import io
from prompts import *
from blocks_and_functions import *
import streamlit as st
import folium
from streamlit_folium import folium_static
import google.generativeai as genai
import json
import re
from langchain.vectorstores import FAISS
from streamlit_folium import st_folium
import random
from langchain_community.embeddings import HuggingFaceEmbeddings


embeddings = HuggingFaceEmbeddings(
    model_name="jhgan/ko-sroberta-multitask",  # 한국어 임베딩 모델
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

def Callout(message,memory):
    try:
        # Query classification 
        classification_response = llm.invoke(input=cls_llm_inst.format(input_query=message,memory = memory))

        if "분석 관련" in classification_response:
            print(message, ': cls 임시 print문 : 분석')
            
            # process for sending Verbose of the agent to the post processor 
            f = io.StringIO()
            with redirect_stdout(f):
                analysis_result = agent.invoke(
                    input=message)
                
            verbose_output = f.getvalue()
            #print(verbose_output)
            
            # post processor 
            final_response = llm.invoke(
                input=post_agent_inst.format(
                    input_query = message,
                    verbose_output = verbose_output,
                    analysis_result = analysis_result
                    )
            )
        
        ### 여기 변경
        elif "추천 관련" in classification_response:
            print('cls 임시 print문 : 추천')
            
            try:
                # FAISS로 맛집 검색
                restaurants_df = load_faiss_and_search(message, k=3)
                
                if restaurants_df is not None and not restaurants_df.empty:
                    # 맛집 정보 구성
                    restaurants_info = format_restaurant_response(restaurants_df)
                    
                    # LLM 응답 생성
                    user_mbti = st.session_state.get('mbti', None)
                    final_response = generate_llm_response(message, restaurants_info, user_mbti)
                    
                    # 지도 표시
                    title_container = st.empty()
                    title_container.subheader("🗺️ 추천 맛집 위치")
                    display_map(restaurants_df)
                    
                else:
                    final_response = "죄송합니다. 해당하는 맛집을 찾을 수 없습니다."
                
            except Exception as e:
                final_response = f"맛집 추천 처리 중 에러가 발생했습니다: {e}"
                print(f"Error in recommendation: {e}")
        

        
        
        else:
            print('cls 임시 print문 : 일반 질문')
            final_response = llm.invoke(
                input=main_persona.format(input_query=message,memory = memory)
            )

    except Exception as e:
        final_response = f"에러가 발생했습니다: {e}"

    return final_response

