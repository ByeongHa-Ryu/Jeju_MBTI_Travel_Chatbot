import os
from contextlib import redirect_stdout
import io
from prompts import *
from blocks_and_functions import *


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
        
        elif "추천 관련" in classification_response: 
            print('cls 임시 print문 : 추천')
            #final_respons = llm.invoke(input=rag_inst)
            return None

        
        else:
            print('cls 임시 print문 : 일반 질문')

            final_response = llm.invoke(
                input=main_persona.format(input_query=message,memory = memory)
            )
            


    except Exception as e:
        final_response = f"에러가 발생했습니다: {e}"

    return final_response

