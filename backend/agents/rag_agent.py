from ..services.rag_service import rag_service
from ..models.schemas import ChatMessage, ChatResponse


class RAGAgent:
    name = "rag_agent"

    async def handle(self, message: ChatMessage) -> ChatResponse:
        answer, docs = await rag_service.answer_question(message.message)

        return ChatResponse(
            reply=answer,
            agent=self.name,
            intent="faq",
            context_documents=docs,
            metadata={"source": "rag"}
        )


rag_agent = RAGAgent()
