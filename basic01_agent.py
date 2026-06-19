from openai import OpenAI
from dotenv import load_dotenv
import json
from pathlib import Path
from pydantic import BaseModel

load_dotenv()
client= OpenAI()
INPUT_FILE= "history.json"

def get_weather(city):
    return f"{city} is 35°C"

def get_time(city):
    return f"{city} is 2:30 pm"

def calculator(expression):
    print("calcutor used")
    return str(eval(expression))

calculator_tool={
    "type":"function",
     "name":"calculator",
     "description":"Evaluate a mathematical espression",
     "parameters":{
         "type": "object",
         "properties":{
             "expression":{
                "type":"string",
                "description": "it's an math expression to evaluate "
                },
            },
            "required":["expression"]
        },
    }


time_tool={
    "type":"function",
    "name":"get_time",
    "description":"find the time of the city",
    "parameters":{
        "type":"object",
        "properties":{
            "city":{
                "type":"string",
                "description":"the city to get the time for "
                },
            },
            "required":["city"],
        },        
    }

weather_tool={
    "type":"function",
    "name":"get_weather",
    "description":"find the weather of the city",
    "parameters":{
        "type":"object",
        "properties":{
            "city":{
                "type":"string",
                "description":"the city to get the weather information for "
                },
            },
            "required":["city"],
        },        
    }

tools=[calculator_tool,weather_tool,time_tool]

func_map= {"get_weather":get_weather,
       "get_time":get_time,
        "calculator":calculator}

class Checker(BaseModel):
    memory: str

#calling api fucntion
def call_function(name,args):
    return func_map[name](**args)

#loading memory function
def load_memory(input_file):

    if not Path(input_file).is_file():
        Path(input_file).touch()
        with open(input_file,"w") as f:
            json.dump([], f)
        return []
    
    with open(input_file,"r",encoding="utf-8") as f:
        data= json.load(f)
        return data
    
#saving memory function
def save_memory(input_file,data):
    with open(input_file,"w",encoding="utf-8") as f:
        json.dump(data,f,indent=2)

#load memory
long_memory= load_memory(INPUT_FILE)
messages=[{"role":"system","content":f"complete summarize conversation:{long_memory}"}]

while True:
    user_input=input("ask something: ")
    if user_input=="exit":
        break
    messages.append({
        "role": "user",
        "content": user_input
    })

    max_limit=10
    iteration=0

    while iteration< max_limit:

        if len(messages) >=10:
            summary= client.responses.create(
            model= "gpt-5.4-mini",
            input=[{"role":"user","content":f"give me the summary of this conversation: {messages}"}]
            )
            messages= [{"role":"system","content":f"converstaion summary:{summary.output_text}"}] + messages[-10:]


        response= client.responses.create(
            model="gpt-5.4-mini",
            input= messages,
            tools= tools
        )

        tool_found= False
        for tool_call in response.output:
            if tool_call.type != "function_call":
                continue

            tool_found= True

            name= tool_call.name
            args= json.loads(tool_call.arguments)
            result= call_function(name,args)

            messages.append(tool_call)
            messages.append({
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": str(result)
            })

        if not tool_found:
            print(response.output_text)
            messages.append({"role":"system",
                         "content":response.output_text})

            imp_memory= client.responses.parse(
                model="gpt-5.4-mini",
                input=[{"role":"user","content":f" give the important details from these:-{response.output_text} and {messages}"}],
                text_format=Checker
            )

            parsed_data = imp_memory.output_parsed.model_dump()
            long_memory.append(parsed_data)
            save_memory(INPUT_FILE,long_memory)

            break
        iteration+=1