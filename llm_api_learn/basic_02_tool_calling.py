from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()
client= OpenAI()

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

def call_function(name,args):
    if name=="get_weather":
        return get_weather(**args)
    if name=="get_time":
        return get_time(**args)
    if name=="calculator":
        return calculator(**args)
    

tools=[calculator_tool,weather_tool,time_tool]
messages=[{"role":"user","content":"what is the time in london"}]

response= client.responses.create(
    model="gpt-5.4-mini",
    input= messages,
    tools= tools
)

for tool_call in response.output:
    if tool_call.type != "function_call":
        continue

    name= tool_call.name
    args= json.loads(tool_call.arguments)
    result= call_function(name,args)

    messages.append(tool_call)
    messages.append({
        "type": "function_call_output",
        "call_id": tool_call.call_id,
        "output": str(result)
    })

final_response= client.responses.create(
    model= "gpt-5.4-mini",
    input= messages,
    tools= tools
)

print(final_response.output_text)