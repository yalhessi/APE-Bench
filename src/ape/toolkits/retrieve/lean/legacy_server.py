#!/usr/bin/env python
"""
Legacy-Compatible Lean Retrieval HTTP Server

Usage:
    python -m ape.toolkits.retrieve.lean.legacy_server --target_repo "url@@commit@@target" --reference_repo "url@@commit@@target"
"""

import argparse
import asyncio
import sys
import os
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import logging
import json

from ape.toolkits.retrieve.lean.utils import create_lean_retrieve_tools
from ape.toolkits.retrieve.lean.config import LeanRetrieveToolConfig
from ape.utils.logging import create_logger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

os.environ.update({'no_proxy': '', 'http_proxy': '', 'https_proxy': ''})

# Global provider
provider = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.error_500_count = 0
    yield
app = FastAPI(title="Mathlib Search API", lifespan=lifespan)


def parse_workspaces(target_repo, reference_repos):
    """Parse workspace configurations from CLI arguments."""
    workspaces = []

    def parse_spec(spec):
        parts = spec.split("@@")
        if len(parts) < 2:
            raise ValueError(f"Invalid spec: {spec}. Expected: repo_url@@commit@@target")
        return parts[0], parts[1], parts[2] if len(parts) > 2 else None

    if target_repo:
        url, commit, target = parse_spec(target_repo)
        ws = {"repo_url": url, "commit_hash": commit, "name": "target"}
        if target:
            ws["default_target"] = target
        workspaces.append(ws)
        logger.info(f"Target: {url}@{commit[:8]}")

    if reference_repos:
        for spec in reference_repos:
            url, commit, target = parse_spec(spec)
            name = url.split('/')[-1].replace('.git', '').lower()
            ws = {"repo_url": url, "commit_hash": commit, "name": name}
            if target:
                ws["default_target"] = target
            workspaces.append(ws)
            logger.info(f"Reference: {url}@{commit[:8]}")

    if not workspaces:
        logger.info("Using default Mathlib4")
        workspaces = [{
            "repo_url": "https://github.com/leanprover-community/mathlib4.git",
            "commit_hash": "2df2f0150c275ad53cb3c90f7c98ec15a56a1a67",
            "name": "mathlib4",
            "default_target": "Mathlib",
        }]

    return workspaces


# Legacy request models
class SyntacticSearchRequest(BaseModel):
    query: str
    limit: int = 10
    module: str = "Mathlib"
    workspace: Optional[str] = None
    include_def_proof: bool = False
    include_theorem_proof: bool = False


class SemanticSearchRequest(BaseModel):
    query: str
    limit: int = 10
    similarity_threshold: float = 0.7
    workspace: Optional[str] = None
    include_def_proof: bool = False
    include_theorem_proof: bool = False


class NameSearchRequest(BaseModel):
    target_name: str
    limit: int = 10
    workspace: Optional[str] = None
    include_def_proof: bool = False
    include_theorem_proof: bool = False


class KeywordSearchRequest(BaseModel):
    keyword: str
    limit: int = 10
    workspace: Optional[str] = None
    include_def_proof: bool = False
    include_theorem_proof: bool = False


def handle_500_error(app):
    app.state.error_500_count += 1
    count = app.state.error_500_count
    if count >= 10:
        os.execv(sys.executable, [sys.executable] + sys.argv)


@app.post("/syntactic-search")
async def syntactic_search(request: SyntacticSearchRequest):
    try:
        result = await provider.lean_retrieve_impl(
            workspace=request.workspace,
            natural_language_query=None,
            lean_name=None,
            keywords=request.query,
            limit=request.limit,
            include_def_proof=request.include_def_proof,
            include_theorem_proof=request.include_theorem_proof
        )
        return Response(content=json.dumps(result, ensure_ascii=False), media_type="application/json")
    except Exception as e:
        handle_500_error(app)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/semantic-search")
async def semantic_search(request: SemanticSearchRequest):
    try:
        result = await provider.lean_retrieve_impl(
            workspace=request.workspace,
            natural_language_query=request.query,
            lean_name=None,
            keywords=None,
            limit=request.limit,
            include_def_proof=request.include_def_proof,
            include_theorem_proof=request.include_theorem_proof
        )
        return Response(content=json.dumps(result, ensure_ascii=False), media_type="application/json")
    except Exception as e:
        handle_500_error(app)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/name-search")
async def name_search(request: NameSearchRequest):
    try:
        result = await provider.lean_retrieve_impl(
            workspace=request.workspace,
            natural_language_query=None,
            lean_name=request.target_name,
            keywords=None,
            limit=request.limit,
            include_def_proof=request.include_def_proof,
            include_theorem_proof=request.include_theorem_proof
        )
        return Response(content=json.dumps(result, ensure_ascii=False), media_type="application/json")
    except Exception as e:
        handle_500_error(app)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/keyword-search")
async def keyword_search(request: KeywordSearchRequest):
    try:
        result = await provider.lean_retrieve_impl(
            workspace=request.workspace,
            natural_language_query=None,
            lean_name=None,
            keywords=request.keyword,
            limit=request.limit,
            include_def_proof=request.include_def_proof,
            include_theorem_proof=request.include_theorem_proof
        )
        return Response(content=json.dumps(result, ensure_ascii=False), media_type="application/json")
    except Exception as e:
        handle_500_error(app)
        raise HTTPException(status_code=500, detail=str(e))


async def main():
    global provider

    parser = argparse.ArgumentParser(description="Lean Retrieval Server")
    parser.add_argument("--target_repo", help="Target repo: url@@commit@@target")
    parser.add_argument("--reference_repo", action='append', help="Reference repo (repeatable)")
    parser.add_argument("--host", default="::", help="Host (default: ::)")
    parser.add_argument("--port", type=int, default=8000, help="HTTP port (default: 8000)")
    args = parser.parse_args()

    workspaces = parse_workspaces(args.target_repo, args.reference_repo)

    logger.info("Creating provider...")
    provider = create_lean_retrieve_tools(
        workspaces,
        config=LeanRetrieveToolConfig(),
        logger=create_logger()
    )

    logger.info("Initializing backends...")
    for ws_name, backend in provider.backends.items():
        await backend.initialize()
        logger.info(f"  {ws_name}: {len(backend._allowed_item_ids)} items")

    import uvicorn
    await uvicorn.Server(
        uvicorn.Config(app, host=args.host, port=args.port, log_level="info")
    ).serve()


if __name__ == "__main__":
    asyncio.run(main())
