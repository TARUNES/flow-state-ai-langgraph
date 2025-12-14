from langchain_ollama import ChatOllama
import os

def get_llm():
    print("--- 🦙 Connecting to Ollama (gpt-oss:20b-cloud) ---")
    return ChatOllama(
        model="gpt-oss:20b-cloud",
        base_url="http://localhost:11434",
        temperature=0.7
    )
