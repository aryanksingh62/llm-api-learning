from openai import OpenAI
from pydantic import BaseModel
import logging
from dotenv import load_dotenv
import time
import json
from pathlib import Path

load_dotenv()
client= OpenAI()
memory_file="history.json"

logging.basicConfig(
    filename="error.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
system_prompt={"role":"system","content":""" when user gave input and normal queries..then
               1. call save_memory and saved the sumarize information.
                but whenevr user ask something like that been talked between you and user then
               2. call search_memory and find relevant answer .. """}


def search_memory(query):
    
    logging.info("search memory tool started")
    if not Path(memory_file).is_file():
        return f"we dont have any past conversation memory file is empty"
    
    with open(memory_file,"r") as f:
        memories =json.load(f)
        prompt = f"""User query:
                    {query}

                    Memories:
                    {memories}

                    Return only the relevant memories.
                    """
    response = client.responses.create(
        model="gpt-5.4-mini",
        input=prompt
    )
    logging.info("search tool succed")
    return response.output_text

class Format(BaseModel):
    memory: str

def save_memory(memory):
    logging.info("save_memory_tool started")
                 
    content={"memory":memory}
    data= Format.model_validate(content).model_dump()

    if not Path(memory_file).is_file():
        with open(memory_file,"w") as f:
            json.dump([],f)
    
    with open(memory_file,"r") as f:
        save_data=json.load(f)
    
    save_data.append(data)
    with open(memory_file,"w") as f:
        json.dump(save_data,f,indent=4)
        logging.info(f"memory saved succesfully")
    return f"memory saved suucesfully"

search_memory_tool={
    "type": "function",
    "name": "search_memory",
    "description": "it searches the memory_file and find the relvant information user asked",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "user aksed for the the information by sarhcing memory_file"
            },
        },
        "required": ["query"],
    },
}

save_meomry_tool= {
    "type": "function",
    "name": "save_memory",
    "description": "it saved the summary of the summary of the assiatant output of user query.",
    "parameters": {
        "type": "object",
        "properties": {
            "memory":{"type":"string",
                       "desscription":"A breif summary of the user_input." 
            },
        },
        "required": ["memory"],
    },
}

tools= [search_memory_tool,save_meomry_tool]

func_map={"save_memory":save_memory,
           "search_memory":search_memory}

def call_tool(name,args):
    return func_map[name](**args)

def call_api(messages):

    logging.info("api call started")
    for i in range(1,4):
        try:
            response= client.responses.create(
                model="gpt-5.4-mini",
                input= messages,
                tools=tools
            )
            logging.info("api call successfully done")
            return response
        
        except Exception as e:
            logging.error(f"api request failed:#{i} and the error is:--{e}")
            time.sleep(10)
    return None

logging.info("Agent started")

messages=[system_prompt]
while True:
    user_input=input("lets talk: ").strip()
    if user_input=="exit":
        print("Exiting agent")
        logging.info("Agent stoped")
        break
    messages.append({"role":"user","content":user_input})

    iteration=0
    max_iteration=5
    while iteration<max_iteration:
        response=call_api(messages)
        if response is None:
            print("api call failed after #all three attempts.")
            break

        tool_found= False
        for tool_call in response.output:
            if tool_call.type != "function_call":
                continue

            tool_found= True

            name= tool_call.name
            args= json.loads(tool_call.arguments)
            try:
                result= call_tool(name,args)
                logging.info("tool calling succeed.")

            except Exception as e:
                result= f"tool call failed :--{e}"
                logging.error(result)
            
            messages.append(tool_call)
            messages.append({"type":"function_call_output",
                                "call_id":tool_call.call_id,
                                "output":json.dumps(result)})
        
        if not tool_found:
            print(response.output_text)
            messages.append({"role":"assitant","content":response.output_text})
            break
        iteration+=1