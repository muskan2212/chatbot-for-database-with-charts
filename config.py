import os
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase

load_dotenv()
OPENAI_API_KEY= os.getenv("OPENAI_API_KEY")

def db_conn():
    try:
        db = SQLDatabase.from_uri("sqlite:///Chinook.db")
        return db
    except Exception as e:
        return f"Error: {str(e)}"
