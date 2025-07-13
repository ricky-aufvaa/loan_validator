#external imports
import json
import re
from typing import Dict, List, Any, Union
from langchain_core.messages import HumanMessage

#internal imports
from preprocess import *
from paths import *
from prompts import validator_prompt_template



# ----------------------------------------------------------------------------------

def validateLoanApplication(query: Union[str, dict], model, db_path: str = DB_PATH, collection_name: str = COLLECTION_NAME) -> dict:
    """
    Validates a loan application against DSCR loan guidelines using FAISS embeddings and LLM
    
    Args:
        query: JSON string or dict containing loan application data
        model: Language model instance
        db_path: Path to FAISS database
        collection_name: FAISS collection name
    
    Returns:
        dict: Validation result with eligibility status and detailed checks
    """
    
    # Parse JSON if string   --------------------------------------
    if isinstance(query, str):
        try:
            loan_data = json.loads(query)
        except json.JSONDecodeError:
            return {
                "is_eligible": False,
                "validation_summary": [{
                    "rule_checked": "JSON Format Validation",
                    "applicant_value": query,
                    "required_value": "Valid JSON format",
                    "status": "FAIL",
                    "reasoning": "The input provided is not in valid JSON format"
                }]
            }
    # -------------------------------------------------------------


    else:
        loan_data = query
    
    
    db = load_local_faiss(db_path)
    
    # Get relevant loan guidelines from FAISS
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    guidelines_docs = retriever.invoke(json.dumps(loan_data))
    # guidelines_docs = db.similarity_search(guidelines_query, k=10)
    guidelines_context = " ".join([doc.page_content for doc in guidelines_docs])
    question = json.dumps(loan_data,indent=2)
    # Create comprehensive validation prompt
    validation_prompt = validator_prompt_template.format(
        guidelines_context=guidelines_context,
        question=question
    )

    try:
        response = model.invoke([HumanMessage(content=validation_prompt)])
        
        # Extract JSON from response
        response_text = response.content.strip()
        
        # Try to find JSON in the response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start != -1 and json_end != -1:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            # Validate the structure
            if "is_eligible" in result and "validation_summary" in result:
                return result
            else:
                raise ValueError("Invalid JSON structure")
        else:
            raise ValueError("No JSON found in response")
            
    except (json.JSONDecodeError, ValueError) as e:
        # Fallback response if JSON parsing fails
        return {
            "is_eligible": False,
            "validation_summary": [{
                "rule_checked": "System Error",
                "applicant_value": "N/A",
                "required_value": "Valid system response",
                "status": "FAIL",
                "reasoning": f"Error processing validation: {str(e)}"
            }]
        }

# ----------------------------------------------------------------------------------