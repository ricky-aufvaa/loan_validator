#external imports
from langchain_ollama import OllamaLLM
import os

#internal imports 
from prompts import *
from dotenv import load_dotenv
from preprocess import load_local_faiss


# ----------------------------------------------------------------------------------

def answerQuestion(question: str,db_path,llm):
    """
    Answer a question using similarity search in ChromaDB and an LLM.
    :param question: The user's question.
    :return: The answer generated by the LLM.
    """
    try:
        # Perform similarity search
        db = load_local_faiss(db_path)
        retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 5})
        docs = retriever.invoke(question)
        # Combine document contents as context
        context = "\n\n".join([doc.page_content for doc in docs])
        print(f"Context is ---{context}")

        # Format the prompt with  context, and question
        prompt = qa_prompt_template.format_messages(    
             #CHAT_HISTORY can be added but that would result in delayed response.
            # Since, it was not the requirement for this POC I've let that be.
            context=context,
            question=question
        )
        # # Get response from LLM
        answer = llm.invoke(prompt)

        return answer
    except Exception as e:
        print(f"Error answering question: {e}")
        return "An error occurred while processing your question."


# ----------------------------------------------------------------------------------