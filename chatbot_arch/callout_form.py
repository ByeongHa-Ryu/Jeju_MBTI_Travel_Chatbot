import os
from contextlib import redirect_stdout
import io
from prompts import *
from blocks_and_functions import *


# def Callout(message,memory):
#     try:
#         # Query classification 
#         classification_response = llm.invoke(input=cls_llm_inst.format(input_query=message,memory = memory))

#         if "분석 관련" in classification_response:
#             print(message, ': cls 임시 print문 : 분석')
            
#             # process for sending Verbose of the agent to the post processor 
#             f = io.StringIO()
#             with redirect_stdout(f):
#                 analysis_result = agent.invoke(
#                     input=message)
                
#             verbose_output = f.getvalue()
#             #print(verbose_output)
            
#             # post processor 
#             final_response = llm.invoke(
#                 input=post_agent_inst.format(
#                     input_query = message,
#                     verbose_output = verbose_output,
#                     analysis_result = analysis_result
#                     )
#             )
        
#         elif "추천 관련" in classification_response: 
#             print('cls 임시 print문 : 추천')
#             # 맛집 추천
#             # mbti별 csv 불러옴
#             #final_respons = llm.invoke(input=rag_inst)
#             return None

        
#         else:
#             print('cls 임시 print문 : 일반 질문')

#             final_response = llm.invoke(
#                 input=main_persona.format(input_query=message,memory = memory)
#             )
            


#     except Exception as e:
#         final_response = f"에러가 발생했습니다: {e}"

#     return final_response

import streamlit as st
import folium
from streamlit_folium import folium_static
import google.generativeai as genai
import json
import re

# Gemini 모델 설정
def setup_gemini(api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    return model

def parse_restaurant_info(response):
    """
    Gemini 응답에서 맛집 정보를 파싱하는 함수
    JSON 형식이 아닐 경우를 대비한 예외처리 포함
    """
    try:
        # JSON 형식 문자열 찾기
        json_pattern = r'\{[\s\S]*\}'
        json_match = re.search(json_pattern, response)
        
        if json_match:
            json_str = json_match.group()
            data = json.loads(json_str)
            return data["restaurants"]
        return None
    except:
        return None

def create_restaurant_map(restaurants):
    """맛집 위치를 표시하는 지도 생성"""
    # 제주도 중심 좌표
    jeju_center = [33.399, 126.562]
    
    # 지도 생성
    m = folium.Map(location=jeju_center, zoom_start=11)
    
    # 각 맛집에 마커 추가
    for restaurant in restaurants:
        popup_html = f"""
        <div style='width: 200px'>
            <h4>{restaurant['name']}</h4>
            <p>{restaurant['description']}</p>
            <p><b>주소:</b> {restaurant['address']}</p>
        </div>
        """
        
        folium.Marker(
            location=restaurant['coords'],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=restaurant['name'],
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
    
    return m




def Callout(message, memory):
    """Gemini를 사용하여 챗봇 응답을 생성하고 지도를 표시하는 함수"""
    try:
        # Gemini API 키 설정 (실제 사용시에는 환경변수나 st.secrets에서 가져오기)
        GOOGLE_API_KEY = "AIzaSyA5NtPvAnpOcnAmlC1PeKNM6Z-Vx8IkLOw"
        model = setup_gemini(GOOGLE_API_KEY)
        
        # 프롬프트 설정
        prompt = f"""
        당신은 제주도 맛집 추천 전문가입니다. 맛집 추천 요청에 대해 다음 JSON 형식으로 응답해주세요:
        
        {{
            "restaurants": [
                {{
                    "name": "식당이름",
                    "address": "상세주소",
                    "coords": [위도, 경도],
                    "description": "맛집 설명"
                }}
            ]
        }}
        
        JSON 형식 응답 후에 일반적인 추천 설명도 추가해주세요.
        
        사용자 질문: {message}
        """
        
        # Gemini API 호출
        response = model.generate_content(prompt)
        response_text = response.text
        
        # 응답에서 맛집 정보 파싱
        restaurants = parse_restaurant_info(response_text)
        
        # 맛집 정보가 있으면 지도 생성
        if restaurants:
            # JSON 부분을 제외한 설명 텍스트 표시
            explanation_text = re.sub(r'\{[\s\S]*\}', '', response_text).strip()
            st.write(explanation_text)
            
            st.write("🗺️ 추천 맛집 위치:")
            m = create_restaurant_map(restaurants)
            folium_static(m)
            
        else:
            st.write(response_text)
            
        return response_text
        
    except Exception as e:
        error_message = f"에러가 발생했습니다: {str(e)}"
        st.error(error_message)
        return error_message

# 추가: 맛집 데이터베이스 (예시)
RESTAURANT_DATABASE = {
    "제주 흑돼지": {
        "coords": [33.499, 126.531],
        "address": "제주시 ***",
        "description": "제주 흑돼지 전문점"
    },
    "해물탕": {
        "coords": [33.243, 126.559],
        "address": "서귀포시 ***",
        "description": "신선한 해산물로 만드는 해물탕"
    }
    # 더 많은 맛집 정보 추가 가능
}