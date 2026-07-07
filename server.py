import os


from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI


load_dotenv()

app = FastAPI(title="Network Troubleshooting Agent")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

class ChatRequest(BaseModel):
    question: str



@app.get("/api/health")
async def health():
    return {
        "success": True,
        "message":"Network Troubleshooting Agent server is running",
    }

@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        messages = [
            SystemMessage(
                content=(
                    "당신은 네트워크 트러블슈팅을 도와주는 AI Assistant입니다. "
                    "사용자의 네트워크 장애 상황을 듣고 가능한 원인과 다음 확인 단계를 "
                    "쉽고 간단하게 설명하세요. "
                    "아직 LangGraph, Tool, RAG, Memory는 연결되지 않았으므로 "
                    "기본적인 진단 답변만 제공합니다"
                )
            ),
            HumanMessage(content=req.question),
        ]
        response = await llm.ainvoke(messages)

        return{
            "success": True,
            "question": req.question,
            "answer": response.content,
            "model": "gpt-4o-mini",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
    

