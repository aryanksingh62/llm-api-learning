from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from pydantic import BaseModel
from langgraph.checkpoint.memory import InMemorySaver
import requests
from dotenv import load_dotenv

load_dotenv()

@tool
def get_weather(city:str, days:int) -> str:
    """get the weather for the trip you planning for.
       according to that you can decide what important 
       things to pack for the trip 
       
       Args:
            city: get the weather for this place/location
            days: no. of days we have to get the weather"""
    print("weather tool used")
    geo_url="https://geocoding-api.open-meteo.com/v1/search"

    params={"name":city,
            "count":1,
            "language": "en",
            "format": "json"}
    try:
        response= requests.get(geo_url,params=params).json()
        
        latitude= response["results"][0]["latitude"]
        longitude= response["results"][0]["longitude"]

    except Exception as e:
        return f"get_weather tool failed beacuse of the error:- {e}" 
    
    wearther_url= "https://api.open-meteo.com/v1/forecast"

    params={"latitude":latitude,
            "longitude":longitude,
            "daily": "weather_code,temperature_2m_max,temperature_2m_min",
            "forecast_days": days}
    
    weather= requests.get(wearther_url,params).json()

    result=""
    for i in range(days):
        result+=f"Day{i+1}:Max {weather["daily"]["temperature_2m_max"][i]},Min{weather["daily"]["temperature_2m_min"]}\n"

    if result:
        return f"here is the {days} days weather details of {city}:\n{result}"

@tool
def get_packing_tips(trip_type:str) -> str:

    """ it helps in packing based on the trip type like sunny and clear , or hiking or
         what kind of trip it is.
        
        Args:
            trip_type:  the type of trip should be  like any of it 
                        (beach, hiking, business)dependa on what that city is famous for and (winter,rainy)
                        depends on weather report in that city"""
    print("packing tool used")
    type= {"activity_based":{"beach":["suscreen","flip flos","waterproof bag"],
                            "hiking":["first aid kit","treking shoes","energy bars"],
                            "business":["formal wear","laptop","charger"]},
          "weather_based":{"winter":["warm jackets","gloves","any fire item"],
                            "rainy":["rain coat","waterproof bag"]}}
    
    if trip_type.lower() in type["activity_based"]:
        result= ", ".join(type["activity_based"][trip_type.lower()])
        return f"the things you need for you packing so must pack these:{result}"
    
    if trip_type.lower() in type["weather_based"]:
        result= ", ".join(type["weather_based"][trip_type.lower()])
        return f"the things you need for you packing so must pack these:{result}"

class Answer(BaseModel):
    destination: str
    weather_summary: str
    packing_list: list[str]
    reasoning: str

model= init_chat_model("openai:gpt-5.4-mini",
                       temperature=0.5,
                       timeout=15)

user_input=input("what yout wanna ask: ").strip()


agent= create_agent(model=model,
                    tools= [get_weather,get_packing_tips],
                    system_prompt="you are a helpful assiatnt which help the users in trip plaaning.",
                    response_format= Answer,
                    checkpointer= InMemorySaver())

thread_config = {"configurable":{"thread_id":"1"}}

result= agent.invoke({"messages":[{"role":"user","content":user_input}]},
                     thread_config)

print(result["structured_response"])