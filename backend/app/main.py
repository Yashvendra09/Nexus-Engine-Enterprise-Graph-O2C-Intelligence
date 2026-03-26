from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import graph, query

app = FastAPI(
    title="Graph & LLM API Base",
    description="A foundational FastAPI skeleton for graph logic and an LLM layer.",
    version="0.1.0"
)

# Enable CORS for the local React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(graph.router)
app.include_router(query.router)

@app.get("/")
async def root():
    """
    Root endpoint to verify the service is running successfully.
    """
    return {"status": "ok", "message": "Service is running."}
