from langgraph.prebuilt import ToolNode , tools_condition
from langgraph.graph import MessagesState, StateGraph,START,END
from langgraph.checkpoint.memory import MemorySaver
from langchain.tools import tool
from langchain.messages import HumanMessage, SystemMessage
from langchain.chat_models import init_chat_model
from  dotenv import load_dotenv

load_dotenv()
memory= MemorySaver()
thread_config={"configurable":{"thread_id":"1j"}}

model= init_chat_model("openai:gpt-5.4-mini",
                       temperature=0.3)

system_prompt=""""
    You are an AI Travel Planner.

    Your job is to plan trips.
    always run
    Use tools whenever you need current information
    1. get_weather tool for find the weather in the destionatio for certain days
    2. get_hotel tool for find the affordable hotels option to stay.
    3. get_flight tool for find the affordable flight for reaching the destination.
    4.extract info tool for exrtacting destination and budget then udating the travelstate

    Always consider the user's budget and preferences.
    """

@tool
def get_flight(destination:str) ->list:
    """searches the flight and get the prices for the destination user want to know"""

    flights=[{
        "airline": "Japan Airlines",
        "price": 52000,
        "stops": 1},
    {
        "airline": "Air India",
        "price": 48000,
        "stops": 0
    }]
    return {"flights":flights}

@tool
def get_weather(detination:str,days:int) -> str:
    """find the weather for user destination for particular no of. days
    Args:
        destination: find the weather for that location
        days: to find the weather for these many days"""

    return {"weather":f"partly cloudy, 26 degree for next {days} days"}

@tool
def get_hotel(destination:str):
    """ it searche the for the cheap hotels for user in destination place """
    hotels=[{
        "name": "Shinjuku Grand Hotel",
        "city": "Tokyo",
        "country": "Japan",
        "stars": 4,
        "price_per_night": 145
    },
    {
        "name": "Tokyo Sakura Inn",
        "city": "Tokyo",
        "country": "Japan",
        "stars": 3,
        "price_per_night": 82
    },
    {
        "name": "Imperial Tokyo Suites",
        "city": "Tokyo",
        "country": "Japan",
        "stars": 5,
        "price_per_night": 310
    }]
    return {"hotels":hotels} 

@tool
def extract_info(destination:str,budget:int):
    """it extract  the important details like destination and budget from the user query
    Args:
        destination: where do user plan want to travel/go 
        budget: what the budget user have for this trip. its integer"""
    
    return {"destination":destination,"budget":budget}

tools=[get_flight,get_hotel,get_weather]
model_with_tools=model.bind_tools(tools)
tool_node= ToolNode(tools)

def extract_node(state):
    return 

def agent_node(state):
    travel_info = f"""
                    Destination: {state["destination"]}
                    Budget: {state["budget"]}
                    Weather: {state["weather"]}
                    flights: {state["flights"]}
                    Hotels: {state["hotels"]}"""
    
    response= model_with_tools([SystemMessage(content=travel_info),
                                SystemMessage(content=system_prompt) ,state["messages"]])
    return response

class Travelstate(MessagesState):
    destination: str| None
    budget: int |None
    hotels: list[dict] |None
    flights: list[dict] |None
    weather: str |None

builder =StateGraph(Travelstate)

builder.add_node("agent",agent_node)
builder.add_node("tools",tool_node)
builder.add_node("extract",extract_node)

builder.add_edge(START,"extract")
builder.add_edge("extract","agent")
builder.add_conditional_edges("agent",tools_condition)
builder.add_edge("tools","agent")

graph=builder.compile(checkpointer=memory)

result= graph.stream({"messages":[HumanMessage(content="Plan a 7-day Japan trip under ₹1.5 lakh.")]},
                     thread_config,stream_mode="messages",version="v2")
for event in result:
    message_chunk,metadata= event["data"]
    if message_chunk.content:
        print(message_chunk.content,end=" ",flush=True)