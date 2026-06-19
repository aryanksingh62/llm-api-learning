from openai import OpenAI
import json
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel
import requests
import logging
import time
import os

load_dotenv()
client = OpenAI()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

INPUT_FILE= "history3.json"

logging.basicConfig(
    filename="error3.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def web_search(query):
    logging.info("web_search tool started")

    url = "https://api.tavily.com/search"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TAVILY_API_KEY}"
    }
    payload = {
        "query": query,
        "search_depth": "basic",
        "max_results": 5
    }

    for i in range(1, 4):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()

            results = []
            for r in data.get("results", []):
                results.append({
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "summary": r.get("content")
                })

            logging.info(f"web_search tool success on attempt #{i}")
            return results

        except requests.RequestException as e:
            logging.error(f"web_search tool failed #{i} times, error: {e}")
            if i == 3:
                return f"web_search tool failed after 3 attempts: {e}"
            time.sleep(2)

class Report(BaseModel):
    topic: str
    summary: str
    key_points: list[str]
    sources: list[str]

def make_report(topic,summary,key_points,sources):

    logging.info(f"report maker tool staretd")
    report="report.json"
    content={
    "topic": topic,
    "summary": summary,
    "key_points": key_points,
    "sources": sources
    }
    report_content=Report.model_validate(content)
    try:
        if not Path(report).is_file():
            Path(report).touch()
            with open(report,"w") as f:
                json.dump([],f)

        with open(report,"r") as f:
            data= json.load(f)

        data.append(report_content.model_dump())

        with open(report,"w") as f:
            json.dump(data,f,indent=4)
            
            logging.info(f"report maker success")
            return "Report saved successfully."
        
    except Exception as e:
        logging.error(f"tool: report_maker--{e}\n")
        return f"report_maker failed{e}"


web_search_tool = {
    "type": "function",
    "name": "web_search",
    "description": "Search the web for a topic or question. Returns up to 5 ranked results, each with title, URL, a short summary, and the full page text.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "the search query or question to look up on the web"
            },
        },
        "required": ["query"],
    },
}

report_maker_tool = {
    "type": "function",
    "name": "make_report",
    "description": "Stores the information in a structured way in a file.",
    "parameters": {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "The title/topic the information is about."
            },
            "summary": {
                "type": "string",
                "description": "A brief summary of the topic."
            },
            "key_points": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "Important points about the topic."
            },
            "sources": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "URLs or sources used to create the report."
            }
        },
        "required": ["topic", "summary", "key_points", "sources"]
    }
}


tools=[web_search_tool,report_maker_tool]

class Checker(BaseModel):
    memory: str

func_map={"web_search":web_search,
         "make_report":make_report}

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

def call_api_for_memory(messg):
    logging.info("api call for long_term memory summariztion started.")
    for i in range(1,4):
        try:
            response = client.responses.parse(
                            model="gpt-5.4-mini",
                            input=messg,
                            text_format= Checker
                )
            return response
        
        except Exception as e:
            logging.error(f"api request for long_term memory failed:#{i} {e}")
            time.sleep(20)    
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
messages= [{"role":"system","content":"""You are a research agent.
                    When the user gives a topic:

                    1. Call web_search.
                    2. Analyze results.
                    3. Select relevant information.
                    4. Call report_maker with:
                        topic
                        summary
                        key_points
                        sources
                    5. After report_maker succeeds, stop and tell the user that the report was saved.

                    Never call the same tool repeatedly."""},
           {"role":"system","content":f"important summary of entire converation is:{memory}"}]

logging.info("Agent started")
while True:
    user_input= input("lets talk: ").strip()
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
                messages= [{"role":"system","content":f"converstaion summary:{summary.output_text}"}]
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
                            "output": json.dumps(result)})
        
        if not tool_found:
            print(response.output_text)
            messages.append({"role":"assistant","content":response.output_text})

            messg=[{"role":"user","content":f"extract permanent facts:{response.output_text}"}]
            imp_memory = call_api_for_memory(messg)

            if imp_memory is None:
                logging.error("memory is not saved")
                continue

            parsed_data= imp_memory.output_parsed.model_dump()
            memory.append(parsed_data)
            save_memory(INPUT_FILE,memory)
            break
        iteration+=1