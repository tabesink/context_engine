import copy
import os
import json
from typing import Any, Dict, List, Optional
from urllib.parse import unquote

import pipmaster as pm  # Pipmaster for dynamic library install

if not pm.is_installed("aioboto3"):
    pm.install("aioboto3")
import aioboto3
import numpy as np
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from lightrag.utils import (
    locate_json_string_body_from_string,
)


class BedrockError(Exception):
    """Generic error for issues related to Amazon Bedrock"""


def _resolve_region(explicit_region: Optional[str] = None) -> str:
    """Resolve AWS region from explicit arg, env vars, or default."""
    return (
        explicit_region
        or os.getenv("AWS_REGION")
        or os.getenv("AWS_DEFAULT_REGION")
        or "us-east-1"
    )


def _build_inference_config_from_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Map generic params to Bedrock Converse API format.

    Supports: max_tokens, temperature, top_p, top_k, stop_sequences
    """
    inference_params_map = {
        "max_tokens": "maxTokens",
        "temperature": "temperature",
        "top_p": "topP",
        "top_k": "topK",
        "stop_sequences": "stopSequences",
    }
    used_keys = set(kwargs) & set(inference_params_map.keys())
    if not used_keys:
        return {}
    cfg: Dict[str, Any] = {}
    for key in used_keys:
        cfg[inference_params_map[key]] = kwargs.pop(key)
    return {"inferenceConfig": cfg}


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, max=60),
    retry=retry_if_exception_type((BedrockError)),
)
async def bedrock_complete_if_cache(
    model,
    prompt,
    system_prompt=None,
    history_messages=[],
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None,
    aws_profile: Optional[str] = None,
    aws_region: Optional[str] = None,
    endpoint_url: Optional[str] = None,
    **kwargs,
) -> str:
    """Call Bedrock Converse API using aioboto3 with robust config resolution."""

    region_name = _resolve_region(aws_region)

    # Normalize model id in case it comes URL-encoded (e.g. "%3A" instead of ":")
    try:
        normalized_model = unquote(model).strip()
    except Exception:
        normalized_model = model

    kwargs.pop("hashing_kv", None)
    kwargs.pop("stream", None)
    # passthrough advanced fields when provided
    pass_through_fields = [
        "additionalModelRequestFields",
        "toolConfig",
        "guardrailConfig",
        "inputModalities",
        "outputModalities",
    ]
    # Fix message history format
    messages = []
    for history_message in history_messages:
        message = copy.copy(history_message)
        message["content"] = [{"text": message["content"]}]
        messages.append(message)

    # Add user prompt
    messages.append({"role": "user", "content": [{"text": prompt}]})

    # Initialize Converse API arguments
    args = {"modelId": normalized_model, "messages": messages}

    # Define system prompt
    if system_prompt:
        args["system"] = [{"text": system_prompt}]

    # Map and set up inference parameters
    args.update(_build_inference_config_from_kwargs(kwargs))

    for key in pass_through_fields:
        if key in kwargs:
            args[key] = kwargs.pop(key)

    """ # NOTE: connecting to bedrock via aioboto3
    # Call model via Converse API
    session = aioboto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
        region_name=os.getenv("AWS_REGION"),

    )
    async with session.client("bedrock-runtime") as bedrock_async_client:
        try:
            response = await bedrock_async_client.converse(**args, **kwargs)
        except Exception as e:
            raise BedrockError(e) """
    

     # Call model via Converse API
    try:
        # Prefer explicit credentials if provided; otherwise fall back to profile; then env
        if aws_access_key_id or aws_secret_access_key or aws_session_token:
            session = aioboto3.Session(
                aws_access_key_id=aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY"),
                aws_session_token=aws_session_token or os.getenv("AWS_SESSION_TOKEN"),
                region_name=region_name,
            )
        elif aws_profile:
            session = aioboto3.Session(profile_name=aws_profile, region_name=region_name)
        else:
            session = aioboto3.Session(region_name=region_name)

        async with session.client("bedrock-runtime", region_name=region_name, endpoint_url=endpoint_url) as bedrock_async_client:
            response = await bedrock_async_client.converse(**args, **kwargs)
    except Exception as e:
        raise BedrockError(e)
        

    return response["output"]["message"]["content"][0]["text"]







# Generic Bedrock completion function
async def bedrock_model_complete(
    prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs
) -> str:
    keyword_extraction = kwargs.pop("keyword_extraction", None)
    model_name = kwargs["hashing_kv"].global_config["llm_model_name"]
    result = await bedrock_complete_if_cache(
        model_name,
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        **kwargs,
    )
    if keyword_extraction:  # TODO: use JSON API
        return locate_json_string_body_from_string(result)
    return result


# @wrap_embedding_func_with_attrs(embedding_dim=1024, max_token_size=8192)
# @retry(
#     stop=stop_after_attempt(3),
#     wait=wait_exponential(multiplier=1, min=4, max=10),
#     retry=retry_if_exception_type((RateLimitError, APIConnectionError, Timeout)),  # TODO: fix exceptions
# )
async def bedrock_embed(
    texts: List[str],
    model: str = "amazon.titan-embed-text-v2:0",
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None,
    aws_profile: Optional[str] = None,
    aws_region: Optional[str] = None,
    endpoint_url: Optional[str] = None,
) -> np.ndarray:
    """Create embeddings with Bedrock embedding models (Titan, Cohere) using async client.

    Supports explicit credentials/profile/region and robust response parsing.
    """

    region_name = _resolve_region(aws_region)

    try:
        if aws_profile:
            session = aioboto3.Session(profile_name=aws_profile, region_name=region_name)
        else:
            session = aioboto3.Session(
                aws_access_key_id=aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY"),
                aws_session_token=aws_session_token or os.getenv("AWS_SESSION_TOKEN"),
                region_name=region_name,
            )

        async with session.client("bedrock-runtime", region_name=region_name, endpoint_url=endpoint_url) as bedrock_async_client:
            model_provider = model.split(".")[0]
            embed_texts: List[List[float]] = []

            if model_provider == "amazon":
                for text in texts:
                    if "v2" in model:
                        body = json.dumps(
                            {
                                "inputText": text,
                                # Optional: "dimensions": embedding_dim,
                                "embeddingTypes": ["float"],
                            }
                        )
                    elif "v1" in model:
                        body = json.dumps({"inputText": text})
                    else:
                        raise ValueError(f"Model {model} is not supported!")

                    response = await bedrock_async_client.invoke_model(
                        modelId=model,
                        body=body,
                        accept="application/json",
                        contentType="application/json",
                    )

                    body_bytes = await response["body"].read()
                    response_body = json.loads(
                        body_bytes.decode("utf-8") if isinstance(body_bytes, (bytes, bytearray)) else body_bytes
                    )

                    embedding_field = response_body.get("embedding")
                    if isinstance(embedding_field, dict):
                        vector = (
                            embedding_field.get("float")
                            or embedding_field.get("vector")
                            or next((v for v in embedding_field.values() if isinstance(v, list)), None)
                        )
                    else:
                        vector = embedding_field

                    if not isinstance(vector, list):
                        raise BedrockError(
                            f"Unexpected embedding response format from model {model}: {response_body}"
                        )
                    embed_texts.append(vector)

            elif model_provider == "cohere":
                body = json.dumps(
                    {"texts": texts, "input_type": "search_document", "truncate": "NONE"}
                )

                response = await bedrock_async_client.invoke_model(
                    modelId=model,
                    body=body,
                    accept="application/json",
                    contentType="application/json",
                )

                body_bytes = await response["body"].read()
                response_body = json.loads(
                    body_bytes.decode("utf-8") if isinstance(body_bytes, (bytes, bytearray)) else body_bytes
                )

                embeddings_obj = response_body.get("embeddings")
                if isinstance(embeddings_obj, list) and embeddings_obj and isinstance(embeddings_obj[0], dict):
                    embed_texts = [e.get("embedding") for e in embeddings_obj]
                else:
                    embed_texts = embeddings_obj

                if not isinstance(embed_texts, list) or not isinstance(embed_texts[0], list):
                    raise BedrockError(
                        f"Unexpected Cohere embedding response format: {response_body}"
                    )
            else:
                raise ValueError(f"Model provider '{model_provider}' is not supported!")

            return np.array(embed_texts)
    except Exception as e:
        raise BedrockError(e)
