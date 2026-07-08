import os
import math
from pathlib import Path
from typing import Any, Dict, List, TypedDict

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langchain_core.tools import tool
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph import START, END, StateGraph


load_dotenv()

app = FastAPI(title="Network Troubleshooting Agent")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
diagnosis_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
DOCS_DIR = Path("docs")

class ChatRequest(BaseModel):
    question: str
    session_id: str = "default"


class DiagnosisResult(BaseModel):
    problem_type: str = Field(description="네트워크 장애 유형")
    possible_causes: List[str] = Field(description="가능한 원인 후보 목록")
    recommended_commands: List[str] = Field(description="사용자가 확인할 수 있는 점검 명령어 목록")
    next_question: str = Field(description="추가 진단을 위해 사용자에게 물어볼 다음 질문")

parser = PydanticOutputParser(pydantic_object=DiagnosisResult)

memory_stores: dict[str, InMemoryChatMessageHistory] = {}


def get_memory_history(session_id: str) -> InMemoryChatMessageHistory:
    """
    session_id별 대화 이력을 가져옴
    없으면 새로 생성
    """
    if session_id not in memory_stores:
        memory_stores[session_id] = InMemoryChatMessageHistory()
    return memory_stores[session_id]


def messages_to_json(messages: List[BaseMessage]) -> List[dict]:
    """
    Langchain Message 객체를 API 응답용 JSON 형태로 반환
    """
    return [
        {
            "role": message.type,
            "content": message.content,
        }
        for message in messages
    ]


def build_memory_context(messages: List[BaseMessage], max_messages: int = 4, max_content_length: int = 180) -> str:
    """
    최근 대화 이력을 LLM 프롬프트에 넣기 좋은 짧은 문자열로 변환
    """
    recent_messages = messages[-max_messages:]

    if not recent_messages:
        return "이전 대화 이력이 없습니다."
    lines = []

    for message in recent_messages:
        role = "사용자" if message.type == "human" else "AI"
        content = message.content

        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."

        lines.append(f"{role}: {content}")

    return "\n".join(lines)


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


class SimpleVectorStore:
    def __init__(self):
        self.docs: List[dict] = []

    @staticmethod
    def _cosine_sim(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return dot / (na * nb + 1e-10)

    def add_documents(self, docs: List[Document]) -> int:
        texts = [doc.page_content for doc in docs]
        embeddings = embedding_model.embed_documents(texts)

        for doc, embedding in zip(docs, embeddings):
            self.docs.append(
                {
                    "page_content": doc.page_content,
                    "metadata": doc.metadata,
                    "embedding": embedding,
                }
            )

        return len(self.docs)

    def similarity_search(self, query: str, k: int = 3) -> List[Document]:
        if not self.docs:
            return []

        query_embedding = embedding_model.embed_query(query)

        scored_docs = [
            (self._cosine_sim(query_embedding, doc["embedding"]), doc)
            for doc in self.docs
        ]

        scored_docs.sort(key=lambda x: x[0], reverse=True)

        return [
            Document(
                page_content=doc["page_content"],
                metadata=doc["metadata"],
            )
            for _, doc in scored_docs[:k]
        ]

    def clear(self):
        self.docs = []


rag_store = SimpleVectorStore()
rag_ready = False


def load_rag_documents():
    """
    docs 폴더의 Markdown 문서를 읽고 SimpleVectorStore에 저장한다.
    """
    global rag_ready

    if not DOCS_DIR.exists():
        rag_ready = False
        return 0

    documents = []

    for file_path in DOCS_DIR.glob("*.md"):
        content = file_path.read_text(encoding="utf-8")

        documents.append(
            Document(
                page_content=content,
                metadata={"source": file_path.name},
            )
        )

    if not documents:
        rag_ready = False
        return 0

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
    )

    split_documents = text_splitter.split_documents(documents)

    rag_store.clear()
    count = rag_store.add_documents(split_documents)
    rag_ready = True

    return count


rag_document_count = load_rag_documents()


@tool
def network_diagnosis_tool(question: str) -> str:
    """
    사용자의 네트워크 장애 질문을 기반으로 문제 유형 분류
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


@tool
def command_recommendation_tool(problem_type: str) -> List[str]:
    """
    네트워크 장애 유형에 따라 사용자가 확인할 수 있는 점검 명령어를 추천한다.
    """
    command_map = {
        "SSH_CONNECTION_FAILED": [
            "ping <server_ip>",
            "systemctl status sshd",
            "ss -tulnp | grep :22",
            "firewall-cmd --list-all",
        ],
        "DHCP_LEASE_FAILED": [
            "ipconfig /all",
            "ip addr",
            "nmcli dev show",
            "journalctl -u NetworkManager --no-pager",
        ],
        "DNS_RESOLUTION_FAILED": [
            "nslookup google.com",
            "ping 8.8.8.8",
            "cat /etc/resolv.conf",
            "systemd-resolve --status",
        ],
        "PING_CONNECTIVITY_CHECK": [
            "ping <target_ip>",
            "tracert <target_ip>",
            "ipconfig /all",
            "route print",
        ],
        "INTERNET_CONNECTION_FAILED": [
            "ping 8.8.8.8",
            "nslookup google.com",
            "ipconfig /all",
            "tracert google.com",
        ],
        "FIREWALL_OR_PORT_BLOCKED": [
            "firewall-cmd --list-all",
            "ss -tulnp",
            "netstat -ano",
            "telnet <server_ip> <port>",
        ],
        "GATEWAY_OR_ROUTING_ISSUE": [
            "ip route",
            "route print",
            "ping <gateway_ip>",
            "traceroute 8.8.8.8",
        ],
        "UNKNOWN_NETWORK_ISSUE": [
            "ipconfig /all",
            "ip addr",
            "ping 8.8.8.8",
        ],
    }
    return command_map.get(problem_type, command_map["UNKNOWN_NETWORK_ISSUE"])


@tool
def rag_search_tool(question: str) -> str:
    """
    사용자의 질문과 관련된 네트워크 트러블슈팅 문서 검색
    """
    if not rag_ready:
        return "검색 가능한 RAG 문서가 없습니다."
    
    documents = rag_store.similarity_search(question, k=2)

    if not documents:
        return "관련 문서를 찾지 못했습니다."
    
    results = []

    for index, document in enumerate(documents, start=1):
        source = document.metadata.get("source", "unknown")
        content = document.page_content.strip()

        results.append(
            f"[문서 {index}] source: {source}\n{content}"
        )
    return "\n\n".join(results)


class AgentState(TypedDict, total=False):
    question: str
    session_id: str
    memory_context: str
    chat_history: List[dict]
    should_save_memory: bool
    memory_saved: bool
    graph_flow: List[str]
    problem_type: str
    recommended_commands: List[str]
    rag_result: str
    answer: str
    structured_result: Dict[str, Any]
    diagnosis_tool_result: str
    command_tool_result: List[str]


def append_graph_flow(state: AgentState, node_name: str) -> List[str]:
    """
    실제 실행된 LangGraph 노드 흐름 기록
    """
    current_flow = state.get("graph_flow", ["START"])
    return current_flow + [node_name]


def memory_node(state: AgentState) -> dict:
    """
    session_id에 해당하는 이전 대화 이력을 불러오는 노드
    """
    session_id = state.get("session_id", "default")
    history = get_memory_history(session_id)
    memory_context = build_memory_context(history.messages)

    return{
        "session_id": session_id,
        "memory_context": memory_context,
        "chat_history": messages_to_json(history.messages),
        "graph_flow": append_graph_flow(state, "memory_node"),
    }



def diagnose_node(state: AgentState) -> dict:
    """
    사용자 질문과 이전 대화 이력을 기반으로 네트워크 장애 유형을 분류하는 노드
    """
    diagnosis_input = (
        f"이전 대화 이력:\n{state.get('memory_context','')}\n\n"
        f"현재 질문:\n{state['question']}"
    )
    diagnosis_type = network_diagnosis_tool.invoke(
        {"question": diagnosis_input}
    )
    return{
        "problem_type": diagnosis_type,
        "diagnosis_tool_result": diagnosis_type,
        "graph_flow": append_graph_flow(state, "diagnose_node"),
    }


def route_by_problem_type(state: AgentState) -> str:
    """
    장애 유형에 따라 다음 노드를 결정하는 조건부 분기 함수
    """
    if state["problem_type"] == "UNKNOWN_NETWORK_ISSUE":
        return "clarification"
    return "known_problem"


def rag_node(state: AgentState) -> dict:
    """
    사용자 질문과 이전 대화 이력을 함께 사용하여 RAG 문서를 검색하는 노드
    """
    rag_query =(
        f"이전 대화 이력:\n{state.get('memory_context', '')}\n\n"
        f"현재 질문:\n{state['question']}\n\n"
        f"진단 유형:\n{state['problem_type']}"
    )
    rag_result = rag_search_tool.invoke(
        {"question": rag_query}
    )
    return{
        "rag_result": rag_result,
        "graph_flow": append_graph_flow(state, "conditional_edge:known_problem") + ["rag_node"],
    }


def command_node(state: AgentState) -> dict:
    """
    장애 유형에 따라 점검 명령어를 추천하는 노드
    """
    recommended_commands = command_recommendation_tool.invoke(
        {"problem_type": state["problem_type"]}
    )
    return{
        "recommended_commands": recommended_commands,
        "command_tool_result": recommended_commands,
        "graph_flow": append_graph_flow(state, "command_node"),
    }


async def generate_answer_node(state: AgentState) -> dict:
    """
    진단 결과, RAG 검색 결과, 추천 명령어를 바탕으로 최종 답변을 생성하는 노드
    """
    messages = [
        SystemMessage(
            content=(
                "당신은 네트워크 트러블슈팅을 도와주는 AI Assistant입니다. "
                "사용자의 네트워크 장애 상황을 듣고 가능한 원인과 다음 확인 단계를 "
                "쉽고 간단하게 설명하세요. "
                "Memory를 사용하여 이전 대화 이력을 참고하고, "
                "LangGraph 기반 진단 흐름과 RAG 검색 결과를 함께 활용합니다.\n\n"
                f"이전 대화 이력은 다음과 같습니다:\n{state.get('memory_context', '이전 대화 이력이 없습니다.')}\n\n"
                f"Network Diagnosis Tool이 분류한 장애 유형은 다음과 같습니다: {state['problem_type']}\n"
                "반드시 problem_type에는 위 장애 유형을 그대로 사용하세요.\n\n"
                f"Command Recommendation Tool이 추천한 명령어는 다음과 같습니다: {state['recommended_commands']}\n"
                "반드시 recommended_commands에는 위 명령어 목록을 그대로 사용하세요.\n\n"
                f"RAG Search Tool이 검색한 문서 내용은 다음과 같습니다:\n{state['rag_result']}\n\n"
                "가능한 원인과 다음 확인 단계는 위 RAG 검색 결과를 참고해서 작성하세요.\n\n"
                "응답은 반드시 아래 형식 지침을 따르세요.\n"
                f"{parser.get_format_instructions()}\n\n"
                "주의사항:\n"
                "- 반드시 JSON 형식으로만 답변하세요.\n"
                "- 마크다운 코드블록은 사용하지 마세요.\n"
                "- recommended_commands에는 실제 점검에 사용할 수 있는 명령어를 넣으세요.\n"
                "- next_question에는 추가 진단을 위해 사용자에게 물어볼 질문을 넣으세요.\n"
                "- 이전 대화에서 이미 확인된 정보는 다시 묻지 마세요.\n"
                "- 사용자가 ping이 된다고 말했거나 방화벽 가능성을 물어보면, 서버 IP보다 SSH 서비스 상태, 포트 리스닝 여부, 방화벽 허용 여부를 우선 질문하세요.\n"
            )
        ),
        HumanMessage(content=state["question"]),
    ]

    response = await llm.ainvoke(messages)

    parsed_result = parser.parse(response.content)
    parsed_result.problem_type = state["problem_type"]
    parsed_result.recommended_commands = state["recommended_commands"]

    answer = (
        f"진단 유형은 {parsed_result.problem_type}입니다. "
        f"가능한 원인은 {', '.join(parsed_result.possible_causes)}입니다. "
        f"먼저 {', '.join(parsed_result.recommended_commands)} 명령어를 확인해보세요. "
        f"추가로 확인할 점은 다음과 같습니다: {parsed_result.next_question}"
    )
    return {
        "answer": answer,
        "structured_result": parsed_result.model_dump(),
        "should_save_memory": True,
        "graph_flow": append_graph_flow(state, "generate_answer_node"),
    }


def clarification_node(state: AgentState) -> dict:
    """
    장애 유형을 판단하기 어려운 경우 추가 정보를 요청하는 노드
    """
    recommended_commands = command_recommendation_tool.invoke(
        {"problem_type": "UNKNOWN_NETWORK_ISSUE"}
    )

    structured_result = DiagnosisResult(
        problem_type="UNKNOWN_NETWORK_ISSUE",
        possible_causes=[
            "질문 정보가 부족하여 원인을 특정할 수 없습니다."
        ],
        recommended_commands = recommended_commands,
        next_question = "구체적인 증상, 오류 메시지, 사용 중인 OS, 네트워크 연결 상황을 알려주세요."
    )

    answer = (
        "현재 질문만으로는 정확한 네트워크 장애 유형을 판단하기 어렵습니다. "
        "어떤 상황에서 문제가 발생하는지 조금 더 구체적으로 알려주세요. "
        f"추가로 확인할 점은 다음과 같습니다: {structured_result.next_question}"
    )

    return{
        "problem_type": "UNKNOWN_NETWORK_ISSUE",
        "recommended_commands": recommended_commands,
        "command_tool_result": recommended_commands,
        "rag_result": "",
        "answer": answer,
        "structured_result": structured_result.model_dump(),
        "should_save_memory": False,
        "graph_flow": append_graph_flow(state, "conditional_edge:clarification") + ["clarification_node"],
    }


def save_memory_node(state: AgentState) -> dict:
    """
    현재 사용자 질문과 최종 답변을 session memory에 저장하는 노드
    """
    session_id = state.get("session_id", "default")
    history = get_memory_history(session_id)

    if not state.get("should_save_memory", True):
        return{
            "chat_history": messages_to_json(history.messages),
            "memory_saved": False,
            "graph_flow": append_graph_flow(state, "save_memory_node") + ["END"],
        }

    history.add_message(HumanMessage(content=state["question"]))
    history.add_message(AIMessage(content=state.get("answer", "")))

    return{
        "chat_history": messages_to_json(history.messages),
        "memory_saved": True,
        "graph_flow": append_graph_flow(state, "save_memory_node") + ["END"],
    }


workflow = StateGraph(AgentState)

workflow.add_node("memory_node", memory_node)
workflow.add_node("diagnose_node", diagnose_node)
workflow.add_node("rag_node", rag_node)
workflow.add_node("command_node", command_node)
workflow.add_node("generate_answer_node", generate_answer_node)
workflow.add_node("clarification_node", clarification_node)
workflow.add_node("save_memory_node", save_memory_node)

workflow.add_edge(START, "memory_node")
workflow.add_edge("memory_node", "diagnose_node")

workflow.add_conditional_edges(
    "diagnose_node",
    route_by_problem_type,
    {
        "known_problem": "rag_node",
        "clarification": "clarification_node"
    },
)

workflow.add_edge("rag_node", "command_node")
workflow.add_edge("command_node", "generate_answer_node")
workflow.add_edge("generate_answer_node", "save_memory_node")
workflow.add_edge("clarification_node", "save_memory_node")
workflow.add_edge("save_memory_node", END)

agent_graph = workflow.compile()


@app.get("/api/health")
async def health():
    return {
        "success": True,
        "message":"Network Troubleshooting Agent server is running",
    }

@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        final_state = await agent_graph.ainvoke(
            {
                "question": req.question,
                "session_id": req.session_id,
            }
        )
        return{
            "success": True,
            "question": req.question,
            "session_id": req.session_id,
            "memory_used": True,
            "memory_saved": final_state.get("memory_saved", False),
            "chat_history": final_state.get("chat_history", []),
            "answer": final_state.get("answer", ""),
            "structured_result": final_state.get("structured_result", {}),
            "diagnosis_tool_result": final_state.get(
                "diagnosis_tool_result",
                final_state.get("problem_type", "UNKNOWN_NETWORK_ISSUE"),
            ),
            "command_tool_result": final_state.get(
                "command_tool_result",
                final_state.get("recommended_commands", []),
            ),
            "rag_result": final_state.get("rag_result", ""),
            "rag_document_count": rag_document_count,
            "graph_used": True,
            "graph_flow": final_state.get("graph_flow", []),
            "model": "gpt-4o-mini",
        }
        
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


class ResetMemoryRequest(BaseModel):
    session_id: str = "default"

@app.post("/api/memory/reset")
async def reset_memory(req: ResetMemoryRequest):
    memory_stores.pop(req.session_id, None)

    return{
        "success": True,
        "message": f"{req.session_id} 세션 메모리가 초기화되었습니다."
    }
