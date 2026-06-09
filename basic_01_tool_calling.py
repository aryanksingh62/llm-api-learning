from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()
client=OpenAI()

def calculator(expression):
    print("calcutor used")
    return str(eval(expression))

tools= [
    {"type":"function",
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
]

messages = [{"role":"user","content":f"what is 25*7? Use the calculator tool and explain the result"}]

response= client.responses.create(
    model= "gpt-5.4-mini",
    input= messages,
    tools= tools
)

tool_call= response.output[0]
print(tool_call.name)
args= json.loads(tool_call.arguments)
result= calculator(args["expression"])

messages.append(tool_call)

messages.append({"type":"function_call_output","call_id":tool_call.call_id,"output":result})

final_response= client.responses.create(
    model= "gpt-5.4-mini",
    input= messages,
    tools=tools
)
print(final_response.output_text)