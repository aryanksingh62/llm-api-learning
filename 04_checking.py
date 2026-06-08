from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()
client=  OpenAI()
user_input=input("enter the name of topic:").strip()

class Analyze(BaseModel):
    topic:str
    difficulty:str
    summary:str
    key_points: list[str]
 
response= client.responses.parse(
    model="gpt-5.4-mini",
    input= f"Analyze {user_input}",
    text_format= Analyze
)
data= response.output_parsed
print(data)
print(data.key_points)