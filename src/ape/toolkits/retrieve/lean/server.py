#!/usr/bin/env python
"""
Lean Retrieval HTTP Server

Simple HTTP API that directly calls provider implementation.

Usage:
    python -m ape.toolkits.retrieve.lean.server
    python -m ape.toolkits.retrieve.lean.server --target_repo "url@@commit@@target" --reference_repo "url@@commit@@target"
"""

import argparse
import asyncio
import sys
import os
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
import logging

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
    """Lifespan event handler for startup and shutdown."""
    # Startup
    app.state.error_count = 0
    logger.info("HTTP API ready")
    yield
    # Shutdown (if needed)
    pass


app = FastAPI(title="Lean Retrieval API", lifespan=lifespan)


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


from pydantic import BaseModel

class LeanRetrieveRequest(BaseModel):
    workspace: Optional[str] = None
    natural_language_query: Optional[str] = None
    lean_name: Optional[str] = None
    keywords: Optional[str] = None
    limit: int = 10
    include_def_proof: bool = False
    include_theorem_proof: bool = False

@app.post("/lean-retrieve")
async def lean_retrieve(request: LeanRetrieveRequest):
    """Unified retrieval endpoint - calls provider.lean_retrieve_impl()."""
    try:
        result = await provider.lean_retrieve_impl(
            workspace=request.workspace,
            natural_language_query=request.natural_language_query,
            lean_name=request.lean_name,
            keywords=request.keywords,
            limit=request.limit,
            include_def_proof=request.include_def_proof,
            include_theorem_proof=request.include_theorem_proof
        )
        return result
    except Exception as e:
        app.state.error_count += 1
        if app.state.error_count >= app.state.error_threshold:
            logger.critical("Error threshold reached, restarting...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        logger.exception("Error in lean_retrieve")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "provider_initialized": provider is not None,
        "backends": list(provider.backends.keys()) if provider else [],
        "error_count": getattr(app.state, "error_count", 0)
    }


async def main():
    global provider

    # Parse arguments
    parser = argparse.ArgumentParser(description="Lean Retrieval Server")
    parser.add_argument("--target_repo", help="Target repo: url@@commit@@target")
    parser.add_argument("--reference_repo", action='append', help="Reference repo (repeatable)")
    parser.add_argument("--host", default="::", help="Host (default: ::)")
    parser.add_argument("--port", type=int, default=8000, help="HTTP port (default: 8000)")
    parser.add_argument("--error_threshold", type=int, default=10, help="Error threshold (default: 10)")
    args = parser.parse_args()

    # Build workspace config
    workspaces = parse_workspaces(args.target_repo, args.reference_repo)

    # Create provider
    logger.info("Creating provider...")
    provider = create_lean_retrieve_tools(
        workspaces,
        config=LeanRetrieveToolConfig(),
        logger=create_logger()
    )

    # Initialize backends
    logger.info("Initializing backends...")
    for ws_name, backend in provider.backends.items():
        await backend.initialize()
        logger.info(f"  {ws_name}: {len(backend._allowed_item_ids)} items")

    logger.info("Provider ready")

    # Store config
    app.state.error_threshold = args.error_threshold

    # Run HTTP server
    import uvicorn
    logger.info(f"Starting HTTP server on {args.host}:{args.port}")
    await uvicorn.Server(
        uvicorn.Config(app, host=args.host, port=args.port, log_level="info")
    ).serve()


if __name__ == "__main__":
    asyncio.run(main())
