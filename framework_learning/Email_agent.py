from langgraph.prebuilt import ToolNode , tools_condition
from langgraph.graph import MessagesState, StateGraph,START,END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from langchain.tools import tool
from langchain.messages import HumanMessage, SystemMessage
from langchain.chat_models import init_chat_model
from  dotenv import load_dotenv

load_dotenv()
memory= MemorySaver()
config={"configurable":{"thread_id":"1j"}}

model= init_chat_model("openai:gpt-5.4-mini",
                       temperature=0.3)
system_prompt= """you are helpful agent, whose job is to send emails 
                  by searching contacts details of the persons users want to send email.
                  you ahve two tools:
                  1.search_contacts: used to find the contact details like phon eno. and email adress.
                  2. send_email use it when you want to send the email the respective email addrres. 
                  """

@tool
def search_contact(name:str):
    ###dummy data work learnig might replace later with real ones
    """it search user contacts and find contact details by there name.
    Args:
        name: name of the person the contect details user wants """
    print("search_data")
    details={"name":"professor rahul",
             "email":"xxxsome@gmial.com",
             "phone":"+91-9922132105"}
    return details["email"]

@tool
def send_email(subject:str,body:str,recipient:str):
    """this tool used it when user want to send an email 
    Args:
    subject: the email is about or the pupose of the email 
    body:the full context of the email
    reccipent: the email address of the person we are sending the email"""

    print("email sent succcesfully")
    return "email sent succesfully"

tools=[search_contact,send_email]
model_with_tools=model.bind_tools(tools)
tool_node=ToolNode(tools)

def approval_node(state):
    """it show the result and wait for the user approval"""
    for tool_call in state["messages"][-1].tool_calls:
        if tool_call["name"]=="send_email":
            print(state["messages"][-1].tool_calls[0]["args"]["subject"])
            print(state["messages"][-1].tool_calls[0]["args"]["body"])
            print(state["messages"][-1].tool_calls[0]["args"]["recipient"])
    approve=interrupt("need approval..??")

    if approve==True:
        return Command(goto="tools")
    return Command(goto=END)

def router(state):
    """it checks before running any tools that it needs human approval or not."""
    print("router")
    safe_tools=["search_contact"]
    approval_tool=["send_email"]

    for tool_call in state["messages"][-1].tool_calls:
        tool= tool_call["name"]

        if tool in safe_tools:
            return "tools"
        if tool in approval_tool:
            return "approval"
    return END

def agent_node(state):
    print("agent node started")
    response= model_with_tools.invoke([SystemMessage(content=system_prompt)] + state["messages"])
    return {"messages":[response]}


builder= StateGraph(MessagesState)
builder.add_node("agent",agent_node)
builder.add_node("approval",approval_node)
builder.add_node("tools",tool_node)

builder.add_edge(START,"agent")
builder.add_conditional_edges("agent",router)
builder.add_edge("tools","agent")

graph= builder.compile(checkpointer=memory)

result= graph.invoke({"messages":[HumanMessage(content="write and send an Email my professor rahul,saying I'm sick")]},config)

state = graph.get_state(config)

if state.interrupts:
    answer = input("Approve? (y/n): ")

    result=graph.invoke(Command(resume=answer.lower() == "y"),config=config)
    print(result["messages"][-1].content)