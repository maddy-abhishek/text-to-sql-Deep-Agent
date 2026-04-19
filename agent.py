import os

from deepagents import create_deep_agent
from deepagents.backends import StateBackend
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.tools import tool

# Load environment variables
load_dotenv()

@tool
def commentary(query: str) -> str:
    """Use this tool to narrate your reasoning steps and thought process."""
    return f"Noted: {query}"

def create_sql_deep_agent():
    """Create and return a text-to-SQL Deep Agent"""

    # Get base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Connect to MySQL database
    # mysql_uri = (
    #     f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
    #     f"@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT', 3306)}"
    #     f"/{os.getenv('MYSQL_DATABASE')}"
    # )
    # db = SQLDatabase.from_uri(mysql_uri, sample_rows_in_table_info=3)

    # Connect to Chinook database
    db_path = os.path.join(base_dir, "chinook.db")
    db = SQLDatabase.from_uri(f"sqlite:///{db_path}", sample_rows_in_table_info=3)

    # Initialize Claude Sonnet 4.5 for toolkit initialization
    model = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

    # Create SQL toolkit and get tools
    toolkit = SQLDatabaseToolkit(db=db, llm=model)
    sql_tools = toolkit.get_tools()

    # Add commentary tool alongside SQL tools
    all_tools = sql_tools + [commentary]

    # Create the Deep Agent with all parameters
    agent = create_deep_agent(
        model=model,  # Claude Sonnet 4.5 with temperature=0
        memory=["./AGENTS.md"],  # Agent identity and general instructions
        skills=[
            "./skills/"
        ],  # Specialized workflows (query-writing, schema-exploration)
        tools=all_tools,  # SQL database tools
        subagents=[],  # No subagents needed
        backend=StateBackend,  # Persistent file storage
        # Limit recursion to speed things up
        checkpointer=None,
    )

    return agent