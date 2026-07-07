import os
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


load_dotenv()

app = FastAPI(title="Network Troubleshooting Agent")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
diagnosis_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

class ChatRequest(BaseModel):
    question: str


class DiagnosisResult(BaseModel):
    problem_type: str = Field(description="네트워크 장애 유형")
    possible_causes: List[str] = Field(description="가능한 원인 후보 목록")
    recommended_commands: List[str] = Field(description="사용자가 확인할 수 있는 점검 명령어 목록")
    next_question: str = Field(description="추가 진단을 위해 사용자에게 물어볼 다음 질문")

parser = PydanticOutputParser(pydantic_object=DiagnosisResult)

PROBLEM_TYPES = [
    "SSH_CONNECTION_FAILED",
    "DHCP_LEASE_FAILED",
    "DNS_RESOLUTION_FAILED",
    "PING_CONNECTIVITY_CHECK",
    "INTERNET_CONNECTION_FAILED",
    "FIREWALL_OR_PORT_BLOCKED",
    "GATEWAY_OR_ROUTING_ISSUE",
    "UNKNOWN_NETWORK_ISSUE",
]


@tool
def network_diagnosis_tool(question: str) -> str:
    """
    사용자의 네트워크 장애 질문을 기반으로 문제 유형 1차 분류
    """
    messages = [
        SystemMessage(
            content=(
                "당신은 네트워크 장애 유형을 분류하는 도구입니다. "
                "사용자의 문장 전체 의미를 보고 가장 적절한 장애 유형 하나만 선택하세요.\n\n"
                "중요 규칙:\n"
                "- 단순 키워드 포함 여부만 보지 마세요.\n"
                "- '~문제는 없다', '~는 된다', '~는 아님' 같은 부정 표현을 고려하세요.\n"
                "- 오타가 있어도 문맥상 의미를 추론하세요. 예: 게이드웨이 → 게이트웨이\n"
                "- 반드시 아래 목록 중 하나만 출력하세요.\n"
                "- 설명 문장은 쓰지 말고, 유형 이름만 출력하세요.\n"
                "- 네트워크 장애와 관련 없거나 분류가 어렵다면 UNKNOWN_NETWORK_ISSUE를 출력하세요.\n\n"
                f"선택 가능한 유형: {PROBLEM_TYPES}"
            )
        ),
        HumanMessage(content=question),
    ]
    response = diagnosis_llm.invoke(messages)

    result = (
        response.content
        .strip()
        .replace("`", "")
        .replace('"', "")
        .replace("'", "")
    )

    for problem_type in PROBLEM_TYPES:
        if problem_type in result:
            return problem_type
        
    return "UNKNOWN_NETWORK_ISSUE"

@app.get("/api/health")
async def health():
    return {
        "success": True,
        "message":"Network Troubleshooting Agent server is running",
    }

@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        diagnosis_type = network_diagnosis_tool.invoke({"question": req.question})
        messages = [
            SystemMessage(
                content=(
                    "당신은 네트워크 트러블슈팅을 도와주는 AI Assistant입니다. "
                    "사용자의 네트워크 장애 상황을 듣고 가능한 원인과 다음 확인 단계를 "
                    "쉽고 간단하게 설명하세요. "
                    "아직 LangGraph, RAG, Memory는 연결되지 않았으므로 "
                    "기본적인 진단 답변만 제공합니다.\n\n"
                    f"Network Diagnosis Tool이 분류한 장애 유형은 다음과 같습니다: {diagnosis_type}\n"
                    "반드시 problem_type에는 위 장애 유형을 그대로 사용하세요.\n\n"
                    "응답은 반드시 아래 형식 지침을 따르세요.\n"
                    f"{parser.get_format_instructions()}\n\n"
                    "주의사항:\n"
                    "- 반드시 JSON 형식으로만 답변하세요.\n"
                    "- 마크다운 코드블록은 사용하지 마세요.\n"
                    "- recommended_commands에는 실제 점검에 사용할 수 있는 명령어를 넣으세요.\n"
                    "- next_question에는 추가 진단을 위해 사용자에게 물어볼 질문을 넣으세요.\n"
                    "- problem_type이 UNKNOWN_NETWORK_ISSUE인 경우, 원인을 단정하지 말고 정보가 부족하다고 설명하세요.\n"
                    "- problem_type이 UNKNOWN_NETWORK_ISSUE인 경우, next_question에는 구체적인 증상, 오류 메시지, OS, 네트워크 상황을 물어보세요.\n"
                    "- problem_type이 UNKNOWN_NETWORK_ISSUE인 경우, possible_causes는 추측하지 말고 정보 부족으로 작성하세요.\n"
                    "- problem_type이 UNKNOWN_NETWORK_ISSUE인 경우, recommended_commands는 최소화하고 next_question을 중심으로 작성하세요.\n"
                )
            ),
            HumanMessage(content=req.question),
        ]
        response = await llm.ainvoke(messages)

        parsed_result = parser.parse(response.content)
        parsed_result.problem_type = diagnosis_type

        if parsed_result.problem_type == "UNKNOWN_NETWORK_ISSUE":
            answer = (
                "현재 질문만으로는 정확한 네트워크 장애 유형을 판단하기 어렵습니다. "
                "어떤 상황에서 문제가 발생하는지 조금 더 구체적으로 알려주세요. "
                f"추가로 확인할 점은 다음과 같습니다: {parsed_result.next_question}"
            )
        else:
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
            "diagnosis_tool_result": diagnosis_type,
            "model": "gpt-4o-mini",
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }

