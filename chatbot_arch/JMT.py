from callout_form import * 

def run_agent_continuously():
    print("JMT에게 뭐든 물어보세요.")

    while True:
        input_query = input("질문: ")
        
        if input_query.lower() == "exit":
            print("대화를 종료합니다.")
            break
        
        try:
            response = Callout(message=input_query)
            print("AI:", response) 
        except Exception as e:
            print("에러가 발생했습니다:", e)

if __name__=="__main__":
    run_agent_continuously()