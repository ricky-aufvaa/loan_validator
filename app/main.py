from fastapi import FastAPI, HTTPException
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage,AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_groq import ChatGroq


import json
import os

# Internal imports
from preprocess import *
from paths import *
from qna_tool import answerQuestion
from validator import validateLoanApplication
from prompts import *

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize LLM (Gemini)
google_api_key = os.getenv("GOOGLE_API_KEY")
# groq_api_key = os.getenv("GROQ_API_KEY")
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=google_api_key)
# model = ChatGroq(model="llama-3.1-8b-instant", api_key=groq_api_key)

# PRECHECKS ----------------------------
#Initial check to ensure if faiss already exists, to faster responses.
if not check_faiss_exists(db_path=DB_PATH, collection_name=COLLECTION_NAME):
        print("FAISS does not exist or is empty. Processing PDF.....")
        text = load_pdf(PDF_PATH)
        chunks = chunk_text(text)
        chunks_with_metadata = extract_keywords_bm25(chunks)
        embed_and_store(chunks_with_metadata, DB_PATH, COLLECTION_NAME)
        print("PDF processed and embedded successfully.")
    
else:
        print("FAISS embeddings already exists locally, skipping PDF preprocessing....")

# -----------------------------------------

# Define State
class FinanceState(TypedDict):
    query: str | dict
    general: str
    loan: dict
    decision: str

# Nodes

# Node -1 DECIDER NODE -----------------------
def decider_node(state: FinanceState) -> FinanceState:
    """
    This node decides which node to route to next based on the input.
    if input - JSON/JSON-like --> decision="validation" |
    if input - financial question --> decision="general"
    """
    query = state['query']
    prompt = decider_node_prompt.format(
        query=query
    )
   
    response = model.invoke([HumanMessage(content=prompt)])
    # return FinanceState(general=response) #for Ollama response
    return FinanceState(decision=response.content) #validation/general



# Node -2 QNA NODE -----------------------
def qna_node(state: FinanceState) -> FinanceState:
    """
    This node iniates the response to the financial query asked by the user.
    response - answer to the query
    """
    query = state['query']
    print("QNA_NODE TRIGGERED")
    response = answerQuestion(question=query, db_path=DB_PATH,llm=model)
    return {"general": response}




# Node -3 LOAN NODE -----------------------

def loan_node(state: FinanceState) -> FinanceState:
    """
    Thsi node initates the loan validation process of the user, returns validation JSON response 
    """
    query = state['query']
    print("LOAN_NODE TRIGGERED")
    result = validateLoanApplication(query, model)
    return {"loan": result}

# -----------------------------------------



# GRAPH CREATION --------------------------

# Define Graph Nodes
graph = StateGraph(FinanceState)
graph.add_node("decider_node", decider_node)
graph.add_node("qna_node", qna_node)
graph.add_node("loan_node", loan_node)

# Build Graph
graph.set_entry_point("decider_node")
graph.add_conditional_edges(
    "decider_node",
    lambda state: state["decision"],
    {"finance": "qna_node", "validation": "loan_node"}
)
graph.add_edge("qna_node", END)
graph.add_edge("loan_node", END)

compiled_graph = graph.compile()

# START → decider_node → [finance] → qna_node → END  
#                   ↘ [validation] → loan_node → END

# -----------------------------------------



# FastAPI Setup ---------------------

app = FastAPI(title="DSCR Agent API")

@app.post("/agent")
async def run_agent(payload: dict):
    # {"query":"input"}
    input_query = payload.get("query")
    if not input_query:
        raise HTTPException(status_code=400, detail="Missing 'query' field in request body.")

    initial_state = {"query": input_query}

    try:
        final_state = compiled_graph.invoke(initial_state)

        #"general" in response -------response from the qna_node => a string
        if "general" in final_state:
            aimessage = final_state["general"]  # This is an AIMessage object
            answer = aimessage.content  # Extract content safely
            return {"response": answer}

        # "loan" in response ------------response from the loan_node => a JSON
        elif "loan" in final_state:
            loan_result = final_state["loan"]  # This is a dict from loan_node
            print("loan result is ------",str(loan_result))
            return {"validation_result": loan_result}

            
        else:
            return {"error": "No valid response generated."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------