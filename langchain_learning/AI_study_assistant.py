from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
query=input("what can i help?: ").strip()

prompt= ChatPromptTemplate.from_template(""" 
    you are a helpful study assistant.
    query:{query}
    
    Explain the topic clearly.""")

model= init_chat_model(
    "openai:gpt-5.4-mini",
)

class StudyNotes(BaseModel):
    summary: str
    key_points: list[str]

structured_model= model.with_structured_output(StudyNotes)

chain= prompt | structured_model
result= chain.invoke({"query":query})
print(result.summary)