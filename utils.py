from config import db_conn
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing_extensions import TypedDict
from ast import literal_eval

db = db_conn()

class chart_data(TypedDict):
    chart: str | None
    x: str | None
    y: str | None

class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
agent_executor = create_sql_agent(llm, db=db_conn(), agent_type="openai-tools", verbose=True)

from langchain_core.prompts import ChatPromptTemplate

system_message = """
Given an input question, create a syntactically correct {dialect} query to
run to help find the answer. Unless the user specifies in his question a
specific number of examples they wish to obtain, always limit your query to
at most {top_k} results. You can order the results by a relevant column to
return the most interesting examples in the database.

Never query for all the columns from a specific table, only ask for a the
few relevant columns given the question.

Pay attention to use only the column names that you can see in the schema
description. Be careful to not query for columns that do not exist. Also,
pay attention to which column is in which table.

Only use the following tables:
{table_info}
"""

user_prompt = "Question: {input}"

query_prompt_template = ChatPromptTemplate(
    [("system", system_message), ("user", user_prompt)]
)

from typing_extensions import Annotated


class QueryOutput(TypedDict):
    """Generated SQL query."""
    query: Annotated[str, ..., "Syntactically valid SQL query."]

for message in query_prompt_template.messages:
    message.pretty_print()

from typing_extensions import Annotated


class QueryOutput(TypedDict):
    """Generated SQL query."""

    query: Annotated[str, ..., "Syntactically valid SQL query."]


def write_query(state: State):
    """Generate SQL query to fetch information."""
    prompt = query_prompt_template.invoke(
        {
            "dialect": db.dialect,
            "top_k": 10,
            "table_info": db.get_table_info(),
            "input": state["question"],
        }
    )
    structured_llm = llm.with_structured_output(QueryOutput)
    result = structured_llm.invoke(prompt)
    return {"query": result["query"]}


def sql_agent(query):
    try:
        sql = write_query({"question": query})
        data = db.run(sql["query"])
        
        table = table_dict(sql, data)

        charts = graph_suggestion(data, query, sql["query"])

        print(charts)
        return table, charts
    except Exception as e:
        print("Error::::::", str(e))
        return f"Error:{str(e)}"
    


def graph_suggestion(data, query, sql):
    try:

        structured_llm = llm.with_structured_output(chart_data, method="function_calling")
        print("1__________________________")

        chart_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant that returns chart configuration as structured JSON."),
            ("user", """
            You are a data visualization assistant. Based on the user's question, the table data and the SQL query, you need to
            suggest the most appropriate chart type (one of: `bar_chart`, `line_chart`, or `pie_chart`) to visualize the data.

            Return only the JSON object with the following keys:
            - "chart": chart type as a string — must be one of "bar_chart", "line_chart", "pie_chart" or "NULL" if no chart is appropriate.
            - "x": name of the column to use as the x-axis (string) — or null if not applicable.
            - "y": name of the column to use as the y-axis (string) — or null if not applicable.

            Your response must strictly follow this JSON schema:
            {{
              "chart": "bar_chart",  
              "x": "column_name",    
              "y": "column_name"     
            }}

            Only return the JSON object. Do not include any explanation or additional text.

            User Query: {query}
            sql Query: {sql}
            Table Data: {data}
            """)
        ])
        
        formatted_prompt = chart_prompt.invoke({"query": query, "sql": sql, "data": data})
        response = structured_llm.invoke(formatted_prompt)
        return response

    except Exception as e:
        print("Chart Suggestion Error:", str(e))
        return str(e)




def table_dict(sql, data):
        
        sql_to_dict_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that formats SQL query results."),
        ("user", """Given the SQL query and the data obtained by executing the query, convert the data into a Python dictionary where:
            - Each key is a column name
            - Each value is a list of all values under that column

            ### Now use this input:
            sql = {sql}
            data = {data}

            ### Output only the dictionary.
            """)
            ])

        formatted_prompt = sql_to_dict_prompt.invoke({
            "sql": sql["query"],
            "data": data
        })

        # Run the prompt through the model
        response = llm.invoke(formatted_prompt)
        response = response.content.strip()
        response = literal_eval(response)
        
        # response = literal_eval(response)
        print(response)
        return response
