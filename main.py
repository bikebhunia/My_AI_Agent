from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from tools import search_tool, wiki_tool, save_tool

load_dotenv()

class ResearchResponse(BaseModel):
    topic: str
    summary: str
    sources: list[str]
    tools_used: list[str]

llm = ChatAnthropic(model="claude-haiku-4-5-20251001")

parser = PydanticOutputParser(pydantic_object=ResearchResponse)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are a research assistant that will help generate a research paper.
            Answer the user query and use necessary tools.
            If a tool fails, continue using other available tools to complete the task.
            Wrap the output in this format and provide no other text\n{format_instructions}
            """,
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{query}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
).partial(format_instructions=parser.get_format_instructions())

tools = [search_tool, wiki_tool, save_tool]

agent = create_tool_calling_agent(
    llm=llm,
    prompt=prompt,
    tools=tools
)

# handle_tool_error=True prevents a single tool crash from killing the agent
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_tool_error=True,       # gracefully recover from tool errors
    handle_parsing_errors=True,   # gracefully recover from output parse errors
)

query = input("Hey Jyoti , what can I help you research? ")
raw_response = agent_executor.invoke({"query": query})

try:
    output = raw_response.get("output")
    text = output[0]["text"] if isinstance(output, list) else output
    structured_response = parser.parse(text)
    print(structured_response)
except Exception as e:
    print("Error parsing response:", e, "\nRaw Response:", raw_response)

