from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from pydantic import BaseModel
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

def get_weather(city:str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

class StudyNotes(BaseModel):
    summary: str
    key_points: list[str]

system_prompt="you are helpgul study assistant"

model= init_chat_model(
    "openai:gpt-5.4-mini",
    temperature=0.5,
    timeout=10
)

agent= create_agent(
    model=model,
    tools=[get_weather],
    system_prompt=system_prompt,
    # response_format=StudyNotes,
    checkpointer= InMemorySaver())

thread_config = {"configurable":{"thread_id":"1"}}

while True:
    query=input("what can i help?: ").strip()
    if query.lower()=="exit":
        print("exiting agent")
        break
    stream= agent.stream({"messages":[{"role":"user","content":query}]},thread_config,stream_mode="messages")
    
    for message, metadata in stream:
        if message.content:
            print(message.content, end="", flush=True)

    print()
    