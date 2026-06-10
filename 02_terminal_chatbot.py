from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client=OpenAI()

messages=[{"role": "system", "content": "You are a helpful assistant."}]

while True:
    user_input=input("what you wanna talk (type 'exit' to quit): ").strip()

    if user_input.lower()=="exit":
        print("Exiting chatbot...")
        break

    messages.append({"role":"user","content":user_input})

    with client.responses.stream(
        model="gpt-5.4-mini",
        input= messages,
    ) as response:

        full_response=""
        print("*"*30)
        print("Assistant: ", end="", flush=True)

        for event in response:
            if event.type == "response.output_text.delta":
                print(event.delta,end="",flush=True)
                full_response+=event.delta
        print()
        final_response= response.get_final_response()

        messages.append({"role": "assistant", "content": full_response})
        print(f"total token usage: {final_response.usage.total_tokens}")