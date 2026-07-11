from langgraph.prebuilt import ToolNode , tools_condition
from langgraph.graph import MessagesState, StateGraph,START,END
from langchain.tools import tool
from langchain.messages import HumanMessage, SystemMessage
from  dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver
from datetime import datetime

load_dotenv()
memory= MemorySaver()
thread_config= {"configurable":{"thread_id":"1"}}

model= init_chat_model("openai:gpt-5.4-mini",
                       temperature=0.2,
                       timeout=10)

system_prompt= """you are a helpul study planner agent,
                tools you have:
                1.calender tool: to check the user weekly routine, which help to make plan.
                2.date tool; to check the current date for user then make the plan accrding to it.

                Always use the date tool first to know today's date.
                Then use the calendar tool to know the user's weekly routine.
                After collecting this information, create the study timetable."""

@tool
def calender_tool():
    """Returns the average weekly routine use it wehn you need the user routine"""

    routine={"Monday":
            ["9am–12pm College","2pm–4pm Lab","6pm–7pm Gym"],

            "Tuesday":
            ["10am–1pm College","2pm-4pm lab"],

            "Wednesday":
            ["Free"],

            "Thursday":
            ["9am–12pm College"],
            
            "friday":
            ["8am-2pm part time work"],

            "saturday and sunday":"free"}
    return routine


@tool
def date_tool():
    """it tells the the current date"""

    return f"today's date is {datetime.now().date()}"

tools=[calender_tool,date_tool]
model_with_tools= model.bind_tools(tools)
tool_node= ToolNode(tools)

def agent_node(state):
    response= model_with_tools.invoke([SystemMessage(content=system_prompt)] + state["messages"])
    return {"messages":[response]}
    
builder= StateGraph(MessagesState)
#add nodes
builder.add_node("tools",tool_node)
builder.add_node("agent",agent_node)
#add_edges
builder.add_edge(START,"agent")
builder.add_conditional_edges("agent",tools_condition)
builder.add_edge("tools","agent")

graph= builder.compile(checkpointer=memory)

result= graph.stream({"messages":[HumanMessage(content="I have DSA tomorrow, OS next week and DBMS in 5 days. Make a study plan.")]},
                     thread_config,stream_mode="messages",version="v2")
for event in result:
    message_chunk,metadata= event["data"]
    if message_chunk.content:
        print(message_chunk.content,end=" ",flush=True)
    
# print(result["messages"][-1].content)