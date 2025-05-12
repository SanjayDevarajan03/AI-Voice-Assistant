from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

def batch():
    chat = ChatGroq(temperature=0.9, model_name="deepseek-r1-distill-llama-70b", groq_api_key=os.getenv("GROQ_API_KEY"))

    system_prompt = """
    You are a helpful and friendly customer service assistant for a cell phone provider.
    Your goal is to help customers with issues like:
    - Billing questions
    - Troubleshooting their mobile devices
    - Explaining data plans and features
    - Activating or deactivating services
    - Transferring them to appropriate departments for further assistance

    Maintain a polite and professional tone in your responses. Always make the customer feel valued and heard.
    """

    human = "{text}"
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", human)])

    chain = prompt | chat

    print(chain.invoke({"text": "Explain the importance of low latency LLMs."}))

def streaming():
    chat = ChatGroq(temperature=0, model_name="deepseek-r1-distill-llama-70b", groq_api_key=os.getenv("GROQ_API_KEY"))
    prompt = ChatPromptTemplate.from_messages([("human", "Write a poem about {topic}")])
    chain = prompt | chat
    for chunk in chain.stream({"topic": "The Moon"}):
        print(chunk.content, end="", flush=True)

if __name__ == "__main__":
    #batch()
    streaming()

