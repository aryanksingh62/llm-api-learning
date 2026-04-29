from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
client= OpenAI()

def read_file(input_file):
    if not Path(input_file).is_file():
        print("Invalid file")
        return
    with open(input_file,"r",encoding="utf-8") as f:
        data= f.read()
        if data:
            return data
        else:
            print("file is empty.")
            return

def summarize(data):
    response= client.responses.create(
        model="gpt-5.4-mini",
        input=f"summarize this- {data}"
    )
    return response.output_text

if __name__=="__main__":
    INPUT_FILE="sample.txt"
    data=read_file(INPUT_FILE)
    if data:
        summary=summarize(data)
        print(f"Here is the summmary of the file..\n{'*'*30}\n{summary}")

    