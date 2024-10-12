from langchain_google_genai import GoogleGenerativeAI #type:ignore
from dotenv import load_dotenv
import os
from contextlib import redirect_stdout
import io
from prompts import *
from langchain.prompts import PromptTemplate
from blocks import *


def Callout(message):
    try:
        # Query classification 
        classification_response = llm.invoke(input=cls_llm_inst.format(input_query=message))

        if "분석 관련" in classification_response:
            print('cls 임시 print문 : 분석')
            
            # process for sending Verbose of the agent to the post processor 
            f = io.StringIO()
            with redirect_stdout(f):
                analysis_result = agent.invoke(
                    input=message)
                
            verbose_output = f.getvalue()
            
            # post processor 
            final_response = llm.invoke(
                input=post_agent_inst.format(
                    input_query = message,
                    verbose_output = verbose_output,
                    analysis_result = analysis_result
                    )
            )
            

        
        elif "추천 관련" in classification_response: 
            return None #RAG
        
        else:
            print('cls 임시 print문 : 일반 질문')

            final_response = llm.invoke(
                input=main_persona.format(input_query=message)
            )
            


    except Exception as e:
        final_response = f"에러가 발생했습니다: {e}"

    return final_response

