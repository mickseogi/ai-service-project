import os
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langchain_openai import ChatOpenAI


load_dotenv()

app = FastAPI(title="Network Troubleshooting Agent")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

class ChatRequest(BaseModel):
    question: str


class DiagnosisResult(BaseModel):
    problem_type: str = Field(description="네트워크 장애 유형")
    possible_causes: List[str] = Field(description="가능한 원인 후보 목록")
    recommended_commands: List[str] = Field(description="사용자가 확인할 수 있는 점검 명령어 목록")
    next_question: str = Field(description="추가 진단을 위해 사용자에게 물어볼 다음 질문")

parser = PydanticOutputParser(pydantic_object=DiagnosisResult)

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
                    "기본적인 진단 답변만 제공합니다.\n\n"
                    "응답은 반드시 아래 형식 지침을 따르세요.\n"
                    f"{parser.get_format_instructions()}\n\n"
                    "주의사항:\n"
                    "- 반드시 JSON 형식으로만 답변하세요.\n"
                    "- 마크다운 코드블록은 사용하지 마세요.\n"
                    "- recommended_commands에는 실제 점검에 사용할 수 있는 명령어를 넣으세요.\n"
                    "- next_question에는 추가 진단을 위해 사용자에게 물어볼 질문을 넣으세요."
                )
            ),
            HumanMessage(content=req.question),
        ]
        response = await llm.ainvoke(messages)

        parsed_result = parser.parse(response.content)

        answer = (
            f"진단 유형은 {parsed_result.problem_type}입니다. "
            f"가능한 원인은 {', '.join(parsed_result.possible_causes)}입니다. "
            f"먼저 {', '.join(parsed_result.recommended_commands)} 명령어를 확인해보세요. "
            f"추가로 확인할 점은 다음과 같습니다: {parsed_result.next_question}"
        )

        return{
            "success": True,
            "question": req.question,
            "answer": answer,
            "structured_result": parsed_result.model_dump(),
            "model": "gpt-4o-mini",
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }

