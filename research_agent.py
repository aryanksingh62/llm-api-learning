from openai import OpenAI
import json
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel
from bs4 import BeautifulSoup
import requests
import logging
import time

load_dotenv()
client = OpenAI()
INPUT_FILE= "history2.json"

logging.basicConfig(
    filename="error2.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def web_search(topic):
    logging.info(f"web_serach tool started")
    url= f"https://en.wikipedia.org/wiki/{topic}"

    for i in range(1,4):
        try:
            response= requests.get(url,headers={"User_Agent":"Mozilla/5.0"})
            response.raise_for_status()

            soup= BeautifulSoup(response.text,"html.parser")
            logging.info(f"web_search tool success in the  #{i} trail.")
            return soup
        
        except requests.RequestException as e:
            logging.error(f"web_search tool failed #{i} times and error:--{e}")
            if i==3:
                return f"web_search tool failed after all #{i} attempts and the reason is:--{e}"
            time.sleep(2)   
            

def notes_maker(notes):

    logging.info(f"notes_maker tool staretd")
    notes_file="notes.json"

    try:
        if not Path(notes_file).is_file():
            Path(notes_file).touch()
            with open(notes_file,"w") as f:
                json.dump([],f,indent=4)

        with open(notes_file,"r") as f:
            data= json.load(f)

        data.append(notes)

        with open(notes_file,"w") as f:
            json.dump(notes,f,indent=4)
            
            logging.info(f"notes_maker success")
            return
        
    except Exception as e:
        logging.error(f"tool: notes_maker--{e}\n")
        return f"notes_maker failed{e}"

def notes_recaller(file_name):
    logging.info(f"notes_recaller tool started")

    try:
        if not Path(file_name).is_file():
            return f"INVALID FILE: there is no file with name {file_name} exist."

        with open(file_name,"r",encoding="utf-8") as f:
            notes= json.load(f)
            logging.info(f"notes_recaller tool worked succesfully.")
            return notes
        
    except Exception as e:
        error= f"notes_recaller tool failed and the error:--{e}"
        logging.error(error)
        return error

web_search_tool= {
    "type":"function",
    "name":"web_search",
    "description":"search the web and the find the information about anything",
    "parameters":{
        "type":"object",
        "properties":{
            "topic":{
                "type":"string",
                "description":"the topic , that need to find the about information about it "
                },
            },
            "required":["topic"],
        },        
    }

notes_maker_tool={
    "type":"function",
    "name":"notes_maker",
    "description":"stores the information/notes in a file",
    "parameters":{
        "type":"object",
        "properties":{
            "notes":{
                "type":"string",
                "description":"the notes/information to be stored in that file "
                },
            },
            "required":["notes"],
        },        
    }

notes_recaller_tool={
    "type":"function",
    "name":"notes_recaller",
    "description":"read the information/notes from a file",
    "parameters":{
        "type":"object",
        "properties":{
            "notes":{
                "type":"string",
                "description":"the notes/information to be read from that file "
                },
            },
            "required":["notes"],
        },        
    }

tools=[web_search_tool,notes_maker_tool,notes_recaller_tool]

class Checker(BaseModel):
    memory: str

func_map={"web_search":web_search,
         "notes_maker":notes_maker,
          "notes_recaller":notes_recaller}

def call_function(name,args):
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
            return response
        
        except Exception as e:
            logging.error(f"api request failed:#{i} {e}")
            time.sleep(2)
    return None

def call_api_for_memory(messg):
    logging.info("api request failed for long_term memory summariztion")
    for i in range(1,4):
        try:
            response = client.responses.create(
                            model="gpt-5.4-mini",
                            input=messg,
                            text_format= Checker
                )
            return response
        
        except Exception as e:
            logging.error(f"api request for long_term memory failed:#{i} {e}")
            time.sleep(2)    
    return None
     
def load_memory(input_file):
    if not Path(input_file).is_file():
        Path(input_file).touch()
        
        with open(input_file,"w",encoding="utf-8") as f:
            json.dump([],f)
            return []
    with open(input_file,"r",encoding="utf-8") as f:
        data= json.load(f)
        return data
    
def save_memory(input_file,data):
    with open(input_file,"w",encoding="utf-8") as f:
        json.dump(data,f)

memory= load_memory(INPUT_FILE)
messages= [{"role":"system","content":f"important summary of entire converation is:{memory}"}]

logging.info("Agent started")
while True:
    user_input= input("lets talk: ").strip()
    if user_input=="exit":
        print("Exiting agent")
        break

    messages.append({"role":"user","content":user_input})

    max_iteration=50
    iteration=0
    while iteration<=max_iteration:
        if len(messages)>=50:
            logging.info("api calling for short term memory summarization")
            try:
                summary= client.responses.create(
                    model="gpt-5.4-mini",
                    input=[{"role":"user","content":f"give me the summary of this conversation:{messages}"}]
                )
                messages= [{"role":"system","content":f"converstaion summary:{summary.output_text}"}] + messages[-10:]
            except Exception as e:
                logging.error(e)

        response= call_api(messages)
        if response is None:
            print(f"api call failed after #3 attempts")
            break

        tool_found= False

        for tool_call in response.output:
            if tool_call.type != "function_call":
                continue

            tool_found= True

            name= tool_call.name
            args= json.loads(tool_call.arguments)
            result= call_function(name,args)

            messages.append(tool_call)
            messages.append({ "type": "function_call_output",
                            "call_id": tool_call.call_id,
                            "output": str(result)})
        
        if not tool_found:
            print(response.output_text)
            messages.append(response.output_text)

            messg=[{"role":"user","content":f"extract the important details from this:{response.output_text} and {messages}"}]
            imp_memory = call_api_for_memory(messg)

            if imp_memory is None:
                logging.error("memory is not saved")
                continue

            parsed_data= imp_memory.output_parsed.model_dump()
            memory.append(parsed_data)
            save_memory(INPUT_FILE,memory)
            break
        iteration+=1