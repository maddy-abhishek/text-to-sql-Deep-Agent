# api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import create_sql_deep_agent
import uvicorn
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = FastAPI(
    title="Text-to-SQL Deep Agent API",
    description="Natural language to SQL powered by LangChain Deep Agents",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create agent once at startup
agent = create_sql_deep_agent()
executor = ThreadPoolExecutor(max_workers=4)


class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    question: str
    answer: str
    success: bool


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        # Run agent in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            lambda: agent.invoke({
                "messages": [{"role": "user", "content": request.question}]
            })
        )

        final_message = result["messages"][-1]
        answer = (
            final_message.content
            if hasattr(final_message, "content")
            else str(final_message)
        )

        return QueryResponse(
            question=request.question,
            answer=answer,
            success=True
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)