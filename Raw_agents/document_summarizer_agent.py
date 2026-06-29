from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import fitz
import logging
from pydantic import BaseModel
import json
import time

load_dotenv()
client= OpenAI()

INPUT_FILE="history.json"

logging.basicConfig(
    filename="error.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

system_prompt={"role":"system","content":"""you are a document summarizer.
               whenever user asked to summarie for any document/file then,

               1. Call file_reader.
               2. summarize the result.
               3. Call report_writer, with
                    filename,summary,key_points,action_items.
               4. after report maker succed,stop and tell the user that the report was saved.
                   Never call the same tool repeatedly."""}

def file_reader(file_read):
    
    logging.info("file Reading tool started.")
    try:
        suf= Path(file_read).suffix.lower()

        if suf==".txt":
            with open(file_read,"r",encoding="utf-8") as f:
                data= f.read()
                logging.info("file reader tool succed")
                return f"here is the data of the text file,{file_read} is-:{data}"

        elif suf==".pdf":
            doc = fitz.open(file_read)
            text = ""

            for page in doc:
                text += page.get_text()
                if len(text) > 30000:
                    break

            doc.close()
            logging.info("file reader tool succed")
            return f"here is the data of the pdf,{file_read} is-:{text}"
        
        else:
            logging.info("tool succed but invalid file")
            return f"INVALID FILE: we can't access these types of documents"
            
    except Exception as e:
        logging.error(f"the file_reader tool failed:--{e}")
        return f"file reader tool has failed and the error is:--{e}"

class Format(BaseModel):
    filename: str
    summary: str
    key_points: list[str]
    action_items: list[str]

def report_writer(filename,summary,key_points,action_items):

    logging.info("report writer tool started")
    try:
        report_file="report.json"
        content={"filename":filename,"summary":summary,"key_points":key_points,"action_items":action_items}
        validate_report_content= Format.model_validate(content)
        report_content= validate_report_content.model_dump()

        if not Path(report_file).is_file():
            with open(report_file,"w") as f:
                json.dump([],f)
        
        with open(report_file,"r") as f:
            data=json.load(f)

        data.append(report_content)
        with open(report_file,"w") as f:
            json.dump(data,f,indent=4)
            logging.info("writer tool succeed")

        memory.append({"document":filename, "summary": summary})
        save_memory(INPUT_FILE,memory)
        return "summarize Report saved succesfully"

    except Exception as e:
        error=f"report writer tool failed and the error is:--{e}"
        logging.error(error)
        return error
 

file_reader_tool={
    "type":"function",
    "name":"file_reader",
    "description":"it reads the data of the document/file",
    "parameters":{
        "type":"object",
        "properties":{
            "file_read":{
                "type":"string",
                "description":"that document/file that are going to read"
                },
            },
            "required":["file_read"],
        },        
    }

report_writer_tool={
    "type":"function",
    "name":"report_writer",
    "description":"it write the summary of document in a structed way into a file",
    "parameters":{
        "type":"object",
        "properties":{
            "filename":{"type":"string",
                        "description":"name of the document"
                    },
            "summary":{"type":"string",
                      "description":"A breif summary of the data that document/file"
                    },
            "key_points":{"type":"array",
                          "items":{"type":"string"},
                          "description":"important points of the data in document/file"
                    },
            "action_items":{"type":"array",
                            "items":{"type":"string"},
                            "description":"specific task that the data from documment/file pointing towards"
                    }
            },
            "required":["filename","summary","key_points","action_items"],
        },        
    }
tools=[file_reader_tool,report_writer_tool]

func_map={"file_reader":file_reader,
         "report_writer":report_writer}

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
            logging.info("api call successfully done")
            return response
        
        except Exception as e:
            logging.error(f"api request failed:#{i} and the error is:--{e}")
            time.sleep(20)
    return None

def load_memory(input_file):
    if not Path(input_file).is_file():
        with open(input_file,"w",encoding="utf-8") as f:
            json.dump([],f)
            return []
        
    with open(input_file,"r",encoding="utf-8") as f:
        data= json.load(f)
        return data
    
def save_memory(input_file,data):
    with open(input_file,"w",encoding="utf-8") as f:
        json.dump(data,f)
        logging.info("memory saved succesfully")

memory= load_memory(INPUT_FILE)
messages= [system_prompt,{"role":"system","content":f"history of chats:{memory[-10:]}"}]

logging.info("Agent started")
while True:
    user_input=input("tell me what's the matter: ").strip()
    if user_input=="exit":
        print("Exiting agent")
        break

    messages.append({"role":"user","content":user_input})

    max_iteration=5
    iteration=0
    while iteration<=max_iteration:
        if len(messages)>=20:
            logging.info("api calling for short term memory summarization")
            try:
                summary= client.responses.create(
                    model="gpt-5.4-mini",
                    input=[{"role":"user","content":f"give me the summary of this conversation:{messages[-20:]}"}]
                )
                messages = [system_prompt,
                            {"role": "system", "content": f"conversation summary: {summary.output_text}"}]
                
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
            try:
                logging.info(" tool call happen")
                result = call_function(name, args)
            except Exception as e:
                result = f"tool '{name}' failed: {e}"
                logging.error(e)

            messages.append(tool_call)
            messages.append({ "type": "function_call_output",
                            "call_id": tool_call.call_id,
                            "output": json.dumps(result)})
        
        if not tool_found:
            print(response.output_text)
            messages.append({"role":"assistant","content":response.output_text})
            
            break
        iteration+=1
