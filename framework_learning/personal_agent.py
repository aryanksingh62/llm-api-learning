from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START,END,MessagesState
from langgraph.prebuilt import ToolNode
from langchain.messages import HumanMessage,SystemMessage
from langgraph.types import RetryPolicy,interrupt,Command
from langgraph.store.memory import InMemoryStore
from langgraph.runtime import Runtime ,Context
from langgraph.checkpoint.sqlite import SqliteSaver
import uuid
from dotenv import load_dotenv

load_dotenv()
memory= SqliteSaver.from_conn_string("checkpoints.db")
store= InMemoryStore(index={
        "embed": ...,
        "dims": 1536,
        "fields": ["memory","$"]
    })
thread_config= {"congigurable":{"thread_id":"123"}}

model= init_chat_model("openi:gpt-5.4-mini",
                      temperature=0.3)

system_prompt=""

@tool
def file_reader():
    return

@tool
def file_search():
    return

@tool
def get_calender():
    return

@tool
def get_date():

    return

@tool
def send_emai():
    """ """
    return

@tool
def delete_file():
    """  """
    return

@tool
def update_calender():
    """  """
    return

tools= [file_reader,file_search,get_date,get_calender,send_emai,delete_file,update_calender]
model_with_tools= model.bind_tools(tools)
approval_tools=[delete_file,update_calender,send_emai]
tool_node= ToolNode(tools)

def approval_node(state):
    """it show the result and wait for the user approval"""
    for tool in state["messages"][-1].tool_calls:
        if tool["name"] in approval_tools:
            print()

    approve= interrupt("approve ?")

    if approve==True:
        return Command(update={"approved":approve},
                       goto="tools")
    
    return Command(goto="tools")

def router(state):
    """it checks before running any tools that it needs human approval or not."""
    safe_call=[]
    approve_call=[]

    for tool in state["messages"][-1].tool_calls:
        if tool["name"] in approval_tools:
            approve_call.append(tool["name"])
        else:
            safe_call.append(tool["name"])
    
    if len(approve_call)!=0:
        return "approval"
    if len(safe_call)!=0:
        return "tools"
    
    return END

def agent_node(state):

    response= model_with_tools.invoke(SystemMessage(content=system_prompt)+state["messages"])
    return {"messages":response}

workflow= StateGraph(MessagesState)

workflow.add_node("agent",agent_node)
workflow.add_node("tools",tool_node)
workflow.add_node("approval",approval_node)

workflow.add_edge(START,"agent")
workflow.add_edge("agent",router)
workflow.add_edge("tools","agent")

graph= workflow.compile(checkpointer=memory,store=store)

result_1= graph.stream({"messages":[HumanMessage(content="")]},
                        thread_config,context=Context(user_id="aryan123"),
                        stream_mode="messages",version="v2")

state= graph.get_state(thread_config)

if state.interrupts:
    answer= input("aprove? y/n : ")
    result_2= graph.stream(Command(resume=answer.lower() == "y"),config=thread_config,
                           context=Context(user_id="aryan123"),
                           stream_mode="messages",version="v2")
    for message, metadata in result_2:
        if message.content:
            print(message.content, end="", flush=True)