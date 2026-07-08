from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain.messages import HumanMessage , SystemMessage
from langgraph.prebuilt import ToolNode,tools_condition
from langgraph.graph import MessagesState,StateGraph, START, END
from dotenv import load_dotenv

load_dotenv()
model= init_chat_model("openai:gpt-5.4-mini",
                       temperature=0.2,
                       timeout=10)

@tool
def add(a:int,b:int) -> int:
    """it can add any two integers
    Args:
        a: first int
        b: second int"""
    
    return a+b

@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a * b

tools=[add,multiply]
model_with_tools= model.bind_tools(tools)

def agent_node(state):

    response= model_with_tools.invoke([SystemMessage(content=SystemMessage(
    content="""
                You are a calculator assistant.

                You MUST use the provided tools for every arithmetic operation.

                Do not perform any calculation yourself.

                For every addition, subtraction, multiplication, or division,
                always call the appropriate tool.

                Even if the answer is obvious, never calculate mentally.

                Only answer after receiving the tool results.
                """
                ))] + state["messages"])

    return {"messages":[response]}

tool_node= ToolNode(tools)

builder= StateGraph(MessagesState)
#add nodes
builder.add_node("agent",agent_node)
builder.add_node("tools",tool_node)
#add edges
builder.add_edge(START,"agent")
builder.add_conditional_edges("agent",tools_condition)
builder.add_edge("tools","agent")

graph= builder.compile()
result =graph.invoke({"messages":[HumanMessage(content= "What is (5 + 3) * 10?")]})
print(result["messages"][-1].content)