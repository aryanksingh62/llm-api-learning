from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
import json

load_dotenv()
client= OpenAI()
INPUTFILE="test.txt"
OUTPUTFILE="result.json"

class Checker(BaseModel):
    summary: str
    key_points: list[str]
    action_items: str

def check_file(input_file):
    if not Path(input_file).is_file():
        print("Invalid file")
        return
    with open(input_file,"r",encoding="utf-8") as f:
        cont= f.read()
        if len(cont)==0:
            print("file is empty")
            return
        return cont
    
def gpt(content):
    response = client.responses.parse(
            model="gpt-5.4-mini",
            input= f"analyze this {content}",
            text_format= Checker
        )
    data= response.output_parsed
    final_data= data.model_dump()
    return final_data

def save_to_file(output_file,data):
    Path(output_file).touch(exist_ok=True)

    with open(output_file,"a") as f:
        json.dump(data,f,indent=2)
        print("saved succesfully✅")

if __name__=="__main__":
    content= check_file(INPUTFILE)
    print("file check succesfully")
    if content:
        data= gpt(content)
        save_to_file(OUTPUTFILE,data)