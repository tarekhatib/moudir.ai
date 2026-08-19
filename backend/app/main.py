"""
Touch MTC Productivity Monitor — Backend entrypoint.

Owns: ingestion API (from agent), config API (admin GUI), scoring engine,
report generation. See /docs/api-contract.md for the full endpoint list
once Day 2 planning is finalized.
"""

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import ingestion

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Touch MTC Productivity Monitor API",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(ingestion.router, prefix="/ingest", tags=["ingestion"])

# Routers get wired in here as they're built, e.g.:
# from app.routers import config, reports
# app.include_router(config.router, prefix="/config", tags=["config"])
# app.include_router(reports.router, prefix="/reports", tags=["reports"])
