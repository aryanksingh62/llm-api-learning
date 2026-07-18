from langchain.tools import tool,ToolRuntime
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START,END,MessagesState
from langgraph.prebuilt import ToolNode
from langchain.messages import HumanMessage,SystemMessage
from langgraph.types import RetryPolicy,interrupt,Command
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import InMemorySaver
import uuid
from datetime import datetime
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()
memory= InMemorySaver()
store= InMemoryStore(index={
        "embed": OpenAIEmbeddings(model="text-embedding-3-small"),
        "dims": 1536,
        "fields": ["memory"]
    })
thread_config= {"configurable":{"thread_id":"123"}}

model= init_chat_model("openai:gpt-5.4-mini",
                      temperature=0.3)

system_prompt= """You are a helpful Personal AI Workspace Assistant.

Your responsibilities include:
- Reading files.
- Searching files.
- Creating study plans.
- Checking the user's calendar.
- Getting today's date.
- Sending emails.
- Deleting files.
- Updating the user's calendar.

Rules:

1. Use tools whenever they are needed. Do not invent file contents, dates, or calendar events.

2. If a file is mentioned but its contents are needed, first call file_reader.

3. If the user asks for a file but its name is unknown, first call file_search.

4. Use get_calender whenever the user's schedule or availability is needed.

5. Use get_date whenever today's date is required.

6. Never call send_email unless all required information is available:
   - recipient
   - subject
   - body

7. Never call delete_file unless the exact filename is known.

8. Never call update_calender unless the event, date, and time are known.

9. If information is missing, ask the user instead of guessing.

10. If multiple independent safe tools are needed, you may call them together.

11. Respond naturally after all required tool results are available.

Do not mention internal reasoning or these rules to the user."""

@tool
def file_reader(file_name: str):
    """Read the contents of a file."""
    print("file_reader used")
    return f"""
Operating Systems Notes

- Process vs Thread
- CPU Scheduling
- Deadlock
- Memory Management
- Paging
- Virtual Memory
"""


@tool
def file_search(query: str):
    """Search for files related to a query."""
    print("file search used")
    return [
        "OS_Notes.pdf",
        "DBMS_Revision.pdf",
        "DSA_Practice.md"
    ]


@tool
def get_calender():
    """Return today's calendar schedule."""
    print("get_calender used")
    return {
        "Monday": [
            "9:00 AM - 12:00 PM : College",
            "2:00 PM - 4:00 PM : Lab",
            "6:00 PM - 7:00 PM : Gym"
        ],
        "Free Time": [
            "12:00 PM - 2:00 PM",
            "4:00 PM - 6:00 PM",
            "After 7:00 PM"
        ]
    }


@tool
def get_date():
    """Return today's date."""
    print("get date used")
    return datetime.now().strftime("%d %B %Y")


@tool
def send_email(subject: str, body: str, recipient: str):
    """Send an email."""
    print("send mail used")
    return f"""
Email Sent Successfully

To: {recipient}
Subject: {subject}

{body}
"""

@tool
def delete_file(file_name: str):
    """Delete a file."""
    print("delte file used")
    return f"'{file_name}' deleted successfully."

@tool
def update_calender(event: str, date: str, time: str):
    """Update the user's calendar."""
    print("update_calender used")
    return {
        "status": "success",
        "event": event,
        "date": date,
        "time": time
    }

@tool
def memory_retrieval(query:str,runtime:ToolRuntime):
    """ this is a memory retirval tool used it when you think the query is related to the memory of user inforamtion
        Args:
            query: the query to search the user's memories"""
    print("memmory retrieval used")
    user_id= runtime.context["user_id"]
    memories = runtime.store.search(namespace=("users",user_id,"memories"),query=query,limit=3)

    return {"memories":memories}

@tool
def memory_saver(memory:str,runtime:ToolRuntime):
    """ its a memory saver tool used it when you need to like thats the important inoframtion of user ,
        save it to the store
        Args:
            memory: the information you have to save in the store."""
    print("memory saver used")
    user_id= runtime.context["user_id"]
    memory_id= str(uuid.uuid4())
    runtime.store.put(namespace=("users",user_id,"memories"),
                      key=memory_id,
                      value={"memory":memory})
    
    return {"status":" Memory Saved succesfully"}

tools= [file_reader,file_search,get_date,get_calender,send_email,delete_file,update_calender,memory_retrieval,memory_saver]
model_with_tools= model.bind_tools(tools)

approval_tools=["delete_file","update_calender","send_email"]
tool_node= ToolNode(tools)

def approval_node(state):
    """it show the result and wait for the user approval used it when you wanna execut the approval tools"""
    for tool in state["messages"][-1].tool_calls:
        if tool["name"] in approval_tools:
            print(tool["args"])

    approve= interrupt("approve ?")

    if approve==True:
        return Command(update={"approved":approve},
                       goto="tools")
    
    return Command(goto=END)

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
    print("agent node started")
    response= model_with_tools.invoke([SystemMessage(content=system_prompt)]+state["messages"])
    return {"messages":[response]}

workflow= StateGraph(MessagesState)

workflow.add_node("agent",agent_node)
workflow.add_node("tools",tool_node,retry_policy=RetryPolicy(max_attempts=3,
                                                             initial_interval=1,
                                                             backoff_factor=2,
                                                             max_interval=10,
                                                             retry_on=(ConnectionError,TimeoutError)))
workflow.add_node("approval",approval_node)

workflow.add_edge(START,"agent")
workflow.add_conditional_edges("agent",router)
workflow.add_edge("tools","agent")

graph= workflow.compile(checkpointer=memory,store=store)


while True:
    user_query= input("so what do you wanna talk: ").strip()
    if user_query.lower()=="exit":
        print("Agent stoped")
        break

    result_1= graph.stream({"messages":[HumanMessage(content= user_query)]},
                            thread_config,context = {"user_id": "aryan123"},
                            stream_mode="messages",version="v2")

    for event in result_1:
        message_chunk,metadata= event["data"]
        if message_chunk.content:
            print(message_chunk.content, end="", flush=True)
    print()

    state= graph.get_state(thread_config)

    if state.interrupts:
        answer= input("aprove? y/n : ")
        result_2= graph.stream(Command(resume=answer.lower() == "y"),config=thread_config,
                            context = {"user_id": "aryan123"},
                            stream_mode="messages",version="v2")
        print("")
        
        for event in result_2:
            message_chunk,metadata= event["data"]
            if message_chunk.content:
                print(message_chunk.content, end="", flush=True)
        print()
    print("*"*50)