from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes_candidates, routes_feedback, routes_webhooks
from app.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Candidate Feedback Automation API",
    description="HR system for generating and sending structured candidate rejection feedback",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_candidates.router, prefix="/api/candidates", tags=["Candidates"])
app.include_router(routes_feedback.router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(routes_webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])


@app.get("/")
def root():
    return {"status": "ok", "message": "Candidate Feedback Automation API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}
