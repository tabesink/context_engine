"""
This module contains all query-related routes for the LightRAG API.
"""

import json
import logging
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from lightrag.base import DocStatus, QueryParam
from lightrag.document_graph import build_document_graph
from ..utils_api import get_combined_auth_dependency
from pydantic import BaseModel, Field, field_validator

from ascii_colors import trace_exception

router = APIRouter(tags=["query"])


class QueryRequest(BaseModel):
    query: str = Field(
        min_length=1,
        description="The query text",
    )

    mode: Literal["local", "global", "hybrid", "naive", "mix", "bypass"] = Field(
        default="hybrid",
        description="Query mode",
    )

    only_need_context: Optional[bool] = Field(
        default=None,
        description="If True, only returns the retrieved context without generating a response.",
    )

    only_need_prompt: Optional[bool] = Field(
        default=None,
        description="If True, only returns the generated prompt without producing a response.",
    )

    response_type: Optional[str] = Field(
        min_length=1,
        default=None,
        description="Defines the response format. Examples: 'Multiple Paragraphs', 'Single Paragraph', 'Bullet Points'.",
    )

    top_k: Optional[int] = Field(
        ge=1,
        default=None,
        description="Number of top items to retrieve. Represents entities in 'local' mode and relationships in 'global' mode.",
    )

    chunk_top_k: Optional[int] = Field(
        ge=1,
        default=None,
        description="Number of text chunks to retrieve initially from vector search.",
    )

    chunk_rerank_top_k: Optional[int] = Field(
        ge=1,
        default=None,
        description="Number of text chunks to keep after reranking.",
    )

    max_token_for_text_unit: Optional[int] = Field(
        gt=1,
        default=None,
        description="Maximum number of tokens allowed for each retrieved text chunk.",
    )

    enable_parent_context: Optional[bool] = Field(
        default=None,
        description="If True, expand retrieved chunks with parent/neighbor document-graph context.",
    )

    parent_context_window: Optional[int] = Field(
        ge=0,
        le=3,
        default=None,
        description="Number of previous/next blocks to include in parent-context expansion.",
    )

    include_parent_section: Optional[bool] = Field(
        default=None,
        description="If True, include parent section metadata in parent-context expansion.",
    )

    max_token_for_global_context: Optional[int] = Field(
        gt=1,
        default=None,
        description="Maximum number of tokens allocated for relationship descriptions in global retrieval.",
    )

    max_token_for_local_context: Optional[int] = Field(
        gt=1,
        default=None,
        description="Maximum number of tokens allocated for entity descriptions in local retrieval.",
    )

    conversation_history: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Stores past conversation history to maintain context. Format: [{'role': 'user/assistant', 'content': 'message'}].",
    )

    history_turns: Optional[int] = Field(
        ge=0,
        default=None,
        description="Number of complete conversation turns (user-assistant pairs) to consider in the response context.",
    )

    ids: list[str] | None = Field(
        default=None, description="List of ids to filter the results."
    )

    user_prompt: Optional[str] = Field(
        default=None,
        description="User-provided prompt for the query. If provided, this will be used instead of the default value from prompt template.",
    )

    @field_validator("query", mode="after")
    @classmethod
    def query_strip_after(cls, query: str) -> str:
        return query.strip()

    @field_validator("conversation_history", mode="after")
    @classmethod
    def conversation_history_role_check(
        cls, conversation_history: List[Dict[str, Any]] | None
    ) -> List[Dict[str, Any]] | None:
        if conversation_history is None:
            return None
        for msg in conversation_history:
            if "role" not in msg or msg["role"] not in {"user", "assistant"}:
                raise ValueError(
                    "Each message must have a 'role' key with value 'user' or 'assistant'."
                )
        return conversation_history

    def to_query_params(self, is_stream: bool) -> "QueryParam":
        """Converts a QueryRequest instance into a QueryParam instance."""
        # Use Pydantic's `.model_dump(exclude_none=True)` to remove None values automatically
        request_data = self.model_dump(exclude_none=True, exclude={"query"})

        # Ensure `mode` and `stream` are set explicitly
        param = QueryParam(**request_data)
        param.stream = is_stream
        return param


class QueryResponse(BaseModel):
    response: str = Field(
        description="The generated response",
    )


class RetrievalResponse(BaseModel):
    query: str = Field(description="The query text used for retrieval")
    mode: Literal["local", "global", "hybrid", "naive", "mix"] = Field(
        description="The retrieval mode that was executed"
    )
    entities: List[Dict[str, Any]] = Field(
        default_factory=list, description="Retrieved knowledge graph entities"
    )
    relationships: List[Dict[str, Any]] = Field(
        default_factory=list, description="Retrieved knowledge graph relationships"
    )
    chunks: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Retrieved document chunks with structural citation metadata",
    )
    retrieval_meta: Dict[str, Any] = Field(
        default_factory=dict, description="Counts, keywords, and retrieval diagnostics"
    )


class NavigationContextRequest(BaseModel):
    chunk_id: Optional[str] = Field(
        default=None,
        description="Retrieved chunk id to expand through its chunk_metadata.block_ids.",
    )
    block_id: Optional[str] = Field(
        default=None,
        description="Direct Docling block id to expand. Requires artifact_manifest_path.",
    )
    artifact_manifest_path: Optional[str] = Field(
        default=None,
        description="Structural artifact manifest path. Optional when chunk_id resolves one.",
    )
    window: int = Field(
        default=1,
        ge=0,
        le=3,
        description="Number of previous/next blocks to include within the same section.",
    )
    include_parent_section: bool = Field(
        default=True,
        description="Include parent section metadata for the center block(s).",
    )


def _namespace_document_graph(
    *,
    doc_id: str,
    graph: dict[str, Any],
    include_blocks: bool,
    section_id: str | None,
) -> dict[str, Any]:
    nodes = graph.get("nodes") or {}
    edges = graph.get("edges") or []
    include_section = _normalize_structural_id(section_id)
    block_counts = _section_block_counts(nodes)

    selected_node_ids: set[str] = set()
    for node_id, node in nodes.items():
        kind = node.get("kind")
        normalized_node_id = _normalize_structural_id(str(node_id))
        if kind in {"document", "section"}:
            selected_node_ids.add(str(node_id))
        elif include_blocks:
            parent_section = f"section:{node.get('section_node_id')}" if node.get("section_node_id") else ""
            if not include_section or include_section in {
                normalized_node_id,
                _normalize_structural_id(parent_section),
                _normalize_structural_id(str(node.get("section_node_id") or "")),
            }:
                selected_node_ids.add(str(node_id))

    namespaced_nodes: dict[str, dict[str, Any]] = {}
    for node_id in selected_node_ids:
        node = dict(nodes.get(node_id) or {})
        namespaced_id = _namespaced_id(doc_id, node_id)
        original_id = str(node_id)
        node["id"] = namespaced_id
        node["original_id"] = original_id
        node["doc_id"] = doc_id
        if node.get("kind") == "section":
            counts = block_counts.get(original_id, {})
            node["block_count"] = counts.get("total", 0)
            node["artifact_count"] = counts.get("artifact", 0)
        namespaced_nodes[namespaced_id] = node

    namespaced_edges = []
    for edge in edges:
        src_id = str(edge.get("src_id") or "")
        tgt_id = str(edge.get("tgt_id") or "")
        if src_id in selected_node_ids and tgt_id in selected_node_ids:
            namespaced_edges.append(
                {
                    **edge,
                    "src_id": _namespaced_id(doc_id, src_id),
                    "tgt_id": _namespaced_id(doc_id, tgt_id),
                    "original_src_id": src_id,
                    "original_tgt_id": tgt_id,
                }
            )

    return {
        "doc_id": doc_id,
        "artifact_manifest_path": graph.get("artifact_manifest_path"),
        "nodes": namespaced_nodes,
        "edges": namespaced_edges,
        "section_children": graph.get("section_children") or {},
    }


def _section_block_counts(nodes: dict[str, Any]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for node in nodes.values():
        if node.get("kind") != "block":
            continue
        section_id = node.get("section_node_id")
        if not section_id:
            continue
        key = f"section:{section_id}"
        bucket = counts.setdefault(key, {"total": 0, "artifact": 0})
        bucket["total"] += 1
        if node.get("block_type") in {"table", "figure", "code"}:
            bucket["artifact"] += 1
    return counts


def _namespaced_id(doc_id: str, node_id: str) -> str:
    return f"{doc_id}::{node_id}"


def _normalize_structural_id(value: str | None) -> str:
    if not value:
        return ""
    return value.split("::", 1)[1] if "::" in value else value


def create_query_routes(rag, api_key: Optional[str] = None, top_k: int = 60):
    combined_auth = get_combined_auth_dependency(api_key)

    @router.post(
        "/query", response_model=QueryResponse, dependencies=[Depends(combined_auth)]
    )
    async def query_text(request: QueryRequest):
        """
        Handle a POST request at the /query endpoint to process user queries using RAG capabilities.

        Parameters:
            request (QueryRequest): The request object containing the query parameters.
        Returns:
            QueryResponse: A Pydantic model containing the result of the query processing.
                       If a string is returned (e.g., cache hit), it's directly returned.
                       Otherwise, an async generator may be used to build the response.

        Raises:
            HTTPException: Raised when an error occurs during the request handling process,
                       with status code 500 and detail containing the exception message.
        """
        try:
            param = request.to_query_params(False)
            response = await rag.aquery(request.query, param=param)

            # If response is a string (e.g. cache hit), return directly
            if isinstance(response, str):
                return QueryResponse(response=response)

            if isinstance(response, dict):
                result = json.dumps(response, indent=2)
                return QueryResponse(response=result)
            else:
                return QueryResponse(response=str(response))
        except Exception as e:
            trace_exception(e)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post(
        "/query/context",
        response_model=RetrievalResponse,
        dependencies=[Depends(combined_auth)],
    )
    async def query_context(request: QueryRequest):
        """
        Return structured retrieval context without generating an LLM response.
        """
        try:
            param = request.to_query_params(False)
            if "mode" not in request.model_fields_set:
                param.mode = "mix"
            if param.mode == "bypass":
                raise HTTPException(
                    status_code=400,
                    detail="Mode 'bypass' does not perform retrieval.",
                )
            return await rag.aretrieve_context(request.query, param=param)
        except HTTPException:
            raise
        except Exception as e:
            trace_exception(e)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post(
        "/query/navigation_context",
        dependencies=[Depends(combined_auth)],
    )
    async def navigation_context(request: NavigationContextRequest):
        """
        Return a small previous/current/next document-navigation window.
        """
        try:
            if not request.chunk_id and not request.block_id:
                raise HTTPException(
                    status_code=400,
                    detail="Either chunk_id or block_id must be provided.",
                )
            return await rag.aexpand_navigation_context(
                chunk_id=request.chunk_id,
                block_id=request.block_id,
                artifact_manifest_path=request.artifact_manifest_path,
                window=request.window,
                include_parent_section=request.include_parent_section,
            )
        except HTTPException:
            raise
        except Exception as e:
            trace_exception(e)
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/document-graph", dependencies=[Depends(combined_auth)])
    async def document_graph(include_blocks: bool = False, section_id: Optional[str] = None):
        """
        Return a section-first structural document graph built from stored Docling manifests.
        """
        try:
            processed_docs = await rag.doc_status.get_docs_by_status(DocStatus.PROCESSED)
            documents = []
            for doc_id, doc_status in processed_docs.items():
                metadata = doc_status.metadata or {}
                if not metadata.get("structure"):
                    continue
                graph = build_document_graph(metadata)
                documents.append(
                    _namespace_document_graph(
                        doc_id=str(doc_id),
                        graph=graph,
                        include_blocks=include_blocks,
                        section_id=section_id,
                    )
                )
            return {"documents": documents}
        except Exception as e:
            trace_exception(e)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/query/stream", dependencies=[Depends(combined_auth)])
    async def query_text_stream(request: QueryRequest):
        """
        This endpoint performs a retrieval-augmented generation (RAG) query and streams the response.

        Args:
            request (QueryRequest): The request object containing the query parameters.
            optional_api_key (Optional[str], optional): An optional API key for authentication. Defaults to None.

        Returns:
            StreamingResponse: A streaming response containing the RAG query results.
        """
        try:
            param = request.to_query_params(True)
            response = await rag.aquery(request.query, param=param)

            from fastapi.responses import StreamingResponse

            async def stream_generator():
                if isinstance(response, str):
                    # If it's a string, send it all at once
                    yield f"{json.dumps({'response': response})}\n"
                elif response is None:
                    # Handle None response (e.g., when only_need_context=True but no context found)
                    yield f"{json.dumps({'response': 'No relevant context found for the query.'})}\n"
                else:
                    # If it's an async generator, send chunks one by one
                    try:
                        async for chunk in response:
                            if chunk:  # Only send non-empty content
                                yield f"{json.dumps({'response': chunk})}\n"
                    except Exception as e:
                        logging.error(f"Streaming error: {str(e)}")
                        yield f"{json.dumps({'error': str(e)})}\n"

            return StreamingResponse(
                stream_generator(),
                media_type="application/x-ndjson",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "application/x-ndjson",
                    "X-Accel-Buffering": "no",  # Ensure proper handling of streaming response when proxied by Nginx
                },
            )
        except Exception as e:
            trace_exception(e)
            raise HTTPException(status_code=500, detail=str(e))

    return router
