from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

response = client.responses.create(
    model="gpt-5.4-mini",
    input="who is salman khan in bollywood industry."
)
print("-"*15)
print(response.output_text)