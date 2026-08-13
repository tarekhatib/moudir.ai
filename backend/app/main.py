"""
Touch MTC Productivity Monitor — Backend entrypoint.

Owns: ingestion API (from agent), config API (admin GUI), scoring engine,
report generation. See /docs/api-contract.md for the full endpoint list
once Day 2 planning is finalized.
"""

from fastapi import FastAPI

app = FastAPI(
    title="Touch MTC Productivity Monitor API",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


# Routers get wired in here as they're built, e.g.:
# from app.routers import ingestion, config, reports
# app.include_router(ingestion.router, prefix="/ingest", tags=["ingestion"])
# app.include_router(config.router, prefix="/config", tags=["config"])
# app.include_router(reports.router, prefix="/reports", tags=["reports"])
