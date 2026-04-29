from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client=OpenAI()
while True:
    user_input=input("what you wanna talk (type exit to quit): ").strip()

    if user_input.lower()=="exit":
        print("Exiting chatbot...")
        break
    if not user_input:
        continue

    response= client.responses.create(
        model="gpt-5.4-mini",
        input= user_input
    )

    print("*"*30)
    print(response.output_text)
    print()