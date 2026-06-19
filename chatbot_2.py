from openai import OpenAI
from dotenv import load_dotenv
import logging
import time

load_dotenv()
client=OpenAI()
logging.basicConfig(
    filename="error.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.info(" chatbot code started")

def call_api(messages):

    for i in range(3,0,-1):
        try:
            response= client.responses.create(
                model="gpt-5.4-mini",
                input= messages,
            )
            return response
        
        except Exception as e:
            print(f"api reuest failed, {i-1} more chances left\n")
            logging.error(f"api request failed: {e}")
            time.sleep(2)
    return None

messages=[{"role": "system", "content": "You are a helpful assistant."}]

while True:
    user_input=input("what you wanna talk (type 'exit' to quit): ").strip()

    if user_input.lower()=="exit":
        print("Exiting chatbot...")
        break

    messages.append({"role":"user","content":user_input})

    response= call_api(messages)
    if response is None:
        print("something went wrong")
        continue

    print(response.output_text)
    print(response[0].type)
    messages.append({"role": "assistant", "content": response.output_text})
    print(f"total token usage: {response.usage.total_tokens}")