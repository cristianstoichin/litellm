"""
What is this? 

Provider-specific Pass-Through Endpoints

Use litellm with Anthropic SDK, Vertex AI SDK, Cohere SDK, etc.
"""

from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response

import litellm
from litellm.constants import BEDROCK_AGENT_RUNTIME_PASS_THROUGH_ROUTES
from litellm.proxy._types import *
from litellm.proxy.auth.user_api_key_auth import user_api_key_auth
from litellm.proxy.pass_through_endpoints.pass_through_endpoints import (
    create_pass_through_route,
)
from litellm.secret_managers.main import get_secret_str

from .passthrough_endpoint_router import PassthroughEndpointRouter

router = APIRouter()
default_vertex_config = None

passthrough_endpoint_router = PassthroughEndpointRouter()


def create_request_copy(request: Request):
    return {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "cookies": request.cookies,
        "query_params": dict(request.query_params),
    }


@router.api_route(
    "/gemini/{endpoint:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    tags=["Google AI Studio Pass-through", "pass-through"],
)
async def gemini_proxy_route(
    endpoint: str,
    request: Request,
    fastapi_response: Response,
):
    """
    [Docs](https://docs.litellm.ai/docs/pass_through/google_ai_studio)
    """
    ## CHECK FOR LITELLM API KEY IN THE QUERY PARAMS - ?..key=LITELLM_API_KEY
    google_ai_studio_api_key = request.query_params.get("key") or request.headers.get(
        "x-goog-api-key"
    )

    user_api_key_dict = await user_api_key_auth(
        request=request, api_key=f"Bearer {google_ai_studio_api_key}"
    )

    base_target_url = "https://generativelanguage.googleapis.com"
    encoded_endpoint = httpx.URL(endpoint).path

    # Ensure endpoint starts with '/' for proper URL construction
    if not encoded_endpoint.startswith("/"):
        encoded_endpoint = "/" + encoded_endpoint

    # Construct the full target URL using httpx
    base_url = httpx.URL(base_target_url)
    updated_url = base_url.copy_with(path=encoded_endpoint)

    # Add or update query parameters
    gemini_api_key: Optional[str] = passthrough_endpoint_router.get_credentials(
        custom_llm_provider="gemini",
        region_name=None,
    )
    if gemini_api_key is None:
        raise Exception(
            "Required 'GEMINI_API_KEY' in environment to make pass-through calls to Google AI Studio."
        )
    # Merge query parameters, giving precedence to those in updated_url
    merged_params = dict(request.query_params)
    merged_params.update({"key": gemini_api_key})

    ## check for streaming
    is_streaming_request = False
    if "stream" in str(updated_url):
        is_streaming_request = True

    ## CREATE PASS-THROUGH
    endpoint_func = create_pass_through_route(
        endpoint=endpoint,
        target=str(updated_url),
    )  # dynamically construct pass-through endpoint based on incoming path
    received_value = await endpoint_func(
        request,
        fastapi_response,
        user_api_key_dict,
        query_params=merged_params,  # type: ignore
        stream=is_streaming_request,  # type: ignore
    )

    return received_value


@router.api_route(
    "/cohere/{endpoint:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    tags=["Cohere Pass-through", "pass-through"],
)
async def cohere_proxy_route(
    endpoint: str,
    request: Request,
    fastapi_response: Response,
    user_api_key_dict: UserAPIKeyAuth = Depends(user_api_key_auth),
):
    """
    [Docs](https://docs.litellm.ai/docs/pass_through/cohere)
    """
    base_target_url = "https://api.cohere.com"
    encoded_endpoint = httpx.URL(endpoint).path

    # Ensure endpoint starts with '/' for proper URL construction
    if not encoded_endpoint.startswith("/"):
        encoded_endpoint = "/" + encoded_endpoint

    # Construct the full target URL using httpx
    base_url = httpx.URL(base_target_url)
    updated_url = base_url.copy_with(path=encoded_endpoint)

    # Add or update query parameters
    cohere_api_key = passthrough_endpoint_router.get_credentials(
        custom_llm_provider="cohere",
        region_name=None,
    )

    ## check for streaming
    is_streaming_request = False
    if "stream" in str(updated_url):
        is_streaming_request = True

    ## CREATE PASS-THROUGH
    endpoint_func = create_pass_through_route(
        endpoint=endpoint,
        target=str(updated_url),
        custom_headers={"Authorization": "Bearer {}".format(cohere_api_key)},
    )  # dynamically construct pass-through endpoint based on incoming path
    received_value = await endpoint_func(
        request,
        fastapi_response,
        user_api_key_dict,
        stream=is_streaming_request,  # type: ignore
    )

    return received_value


@router.api_route(
    "/anthropic/{endpoint:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    tags=["Anthropic Pass-through", "pass-through"],
)
async def anthropic_proxy_route(
    endpoint: str,
    request: Request,
    fastapi_response: Response,
    user_api_key_dict: UserAPIKeyAuth = Depends(user_api_key_auth),
):
    """
    [Docs](https://docs.litellm.ai/docs/anthropic_completion)
    """
    base_target_url = "https://api.anthropic.com"
    encoded_endpoint = httpx.URL(endpoint).path

    # Ensure endpoint starts with '/' for proper URL construction
    if not encoded_endpoint.startswith("/"):
        encoded_endpoint = "/" + encoded_endpoint

    # Construct the full target URL using httpx
    base_url = httpx.URL(base_target_url)
    updated_url = base_url.copy_with(path=encoded_endpoint)

    # Add or update query parameters
    anthropic_api_key = passthrough_endpoint_router.get_credentials(
        custom_llm_provider="anthropic",
        region_name=None,
    )

    ## check for streaming
    is_streaming_request = False
    # anthropic is streaming when 'stream' = True is in the body
    if request.method == "POST":
        _request_body = await request.json()
        if _request_body.get("stream"):
            is_streaming_request = True

    ## CREATE PASS-THROUGH
    endpoint_func = create_pass_through_route(
        endpoint=endpoint,
        target=str(updated_url),
        custom_headers={"x-api-key": "{}".format(anthropic_api_key)},
        _forward_headers=True,
    )  # dynamically construct pass-through endpoint based on incoming path
    received_value = await endpoint_func(
        request,
        fastapi_response,
        user_api_key_dict,
        stream=is_streaming_request,  # type: ignore
    )

    return received_value


@router.api_route(
    "/bedrock/{endpoint:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    tags=["Bedrock Pass-through", "pass-through"],
)
async def bedrock_proxy_route(
    endpoint: str,
    request: Request,
    fastapi_response: Response,
    user_api_key_dict: UserAPIKeyAuth = Depends(user_api_key_auth),
):
    """
    [Docs](https://docs.litellm.ai/docs/pass_through/bedrock)
    """
    create_request_copy(request)

    try:
        from botocore.auth import SigV4Auth
        from botocore.awsrequest import AWSRequest
        from botocore.credentials import Credentials
    except ImportError:
        raise ImportError("Missing boto3 to call bedrock. Run 'pip install boto3'.")

    aws_region_name = litellm.utils.get_secret(secret_name="AWS_REGION_NAME")
    if _is_bedrock_agent_runtime_route(endpoint=endpoint):  # handle bedrock agents
        base_target_url = (
            f"https://bedrock-agent-runtime.{aws_region_name}.amazonaws.com"
        )
    else:
        base_target_url = f"https://bedrock-runtime.{aws_region_name}.amazonaws.com"
    encoded_endpoint = httpx.URL(endpoint).path

    # Ensure endpoint starts with '/' for proper URL construction
    if not encoded_endpoint.startswith("/"):
        encoded_endpoint = "/" + encoded_endpoint

    # Construct the full target URL using httpx
    base_url = httpx.URL(base_target_url)
    updated_url = base_url.copy_with(path=encoded_endpoint)

    # Add or update query parameters
    from litellm.llms.bedrock.chat import BedrockConverseLLM

    credentials: Credentials = BedrockConverseLLM().get_credentials()
    sigv4 = SigV4Auth(credentials, "bedrock", aws_region_name)
    headers = {"Content-Type": "application/json"}
    # Assuming the body contains JSON data, parse it
    try:
        data = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": e})
    _request = AWSRequest(
        method="POST", url=str(updated_url), data=json.dumps(data), headers=headers
    )
    sigv4.add_auth(_request)
    prepped = _request.prepare()

    ## check for streaming
    is_streaming_request = False
    if "stream" in str(updated_url):
        is_streaming_request = True

    ## CREATE PASS-THROUGH
    endpoint_func = create_pass_through_route(
        endpoint=endpoint,
        target=str(prepped.url),
        custom_headers=prepped.headers,  # type: ignore
    )  # dynamically construct pass-through endpoint based on incoming path
    received_value = await endpoint_func(
        request,
        fastapi_response,
        user_api_key_dict,
        stream=is_streaming_request,  # type: ignore
        custom_body=data,  # type: ignore
        query_params={},  # type: ignore
    )

    return received_value


def _is_bedrock_agent_runtime_route(endpoint: str) -> bool:
    """
    Return True, if the endpoint should be routed to the `bedrock-agent-runtime` endpoint.
    """
    for _route in BEDROCK_AGENT_RUNTIME_PASS_THROUGH_ROUTES:
        if _route in endpoint:
            return True
    return False


@router.api_route(
    "/assemblyai/{endpoint:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    tags=["AssemblyAI Pass-through", "pass-through"],
)
@router.api_route(
    "/eu.assemblyai/{endpoint:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    tags=["AssemblyAI EU Pass-through", "pass-through"],
)
async def assemblyai_proxy_route(
    endpoint: str,
    request: Request,
    fastapi_response: Response,
    user_api_key_dict: UserAPIKeyAuth = Depends(user_api_key_auth),
):
    """
    [Docs](https://api.assemblyai.com)
    """
    # Set base URL based on the route
    is_eu_route = "eu.assemblyai" in str(request.url)
    base_target_url = (
        "https://api.eu.assemblyai.com" if is_eu_route else "https://api.assemblyai.com"
    )
    encoded_endpoint = httpx.URL(endpoint).path
    # Ensure endpoint starts with '/' for proper URL construction
    if not encoded_endpoint.startswith("/"):
        encoded_endpoint = "/" + encoded_endpoint

    # Construct the full target URL using httpx
    base_url = httpx.URL(base_target_url)
    updated_url = base_url.copy_with(path=encoded_endpoint)

    # Add or update query parameters
    assemblyai_api_key = passthrough_endpoint_router.get_credentials(
        custom_llm_provider="assemblyai",
        region_name="eu" if is_eu_route else None,
    )

    ## check for streaming
    is_streaming_request = False
    # assemblyai is streaming when 'stream' = True is in the body
    if request.method == "POST":
        _request_body = await request.json()
        if _request_body.get("stream"):
            is_streaming_request = True

    ## CREATE PASS-THROUGH
    endpoint_func = create_pass_through_route(
        endpoint=endpoint,
        target=str(updated_url),
        custom_headers={"Authorization": "{}".format(assemblyai_api_key)},
    )  # dynamically construct pass-through endpoint based on incoming path
    received_value = await endpoint_func(
        request=request,
        fastapi_response=fastapi_response,
        user_api_key_dict=user_api_key_dict,
        stream=is_streaming_request,  # type: ignore
    )

    return received_value


@router.api_route(
    "/azure/{endpoint:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    tags=["Azure Pass-through", "pass-through"],
)
async def azure_proxy_route(
    endpoint: str,
    request: Request,
    fastapi_response: Response,
    user_api_key_dict: UserAPIKeyAuth = Depends(user_api_key_auth),
):
    """
    Call any azure endpoint using the proxy.

    Just use `{PROXY_BASE_URL}/azure/{endpoint:path}`
    """
    base_target_url = get_secret_str(secret_name="AZURE_API_BASE")
    if base_target_url is None:
        raise Exception(
            "Required 'AZURE_API_BASE' in environment to make pass-through calls to Azure."
        )
    # Add or update query parameters
    azure_api_key = passthrough_endpoint_router.get_credentials(
        custom_llm_provider="azure",
        region_name=None,
    )
    if azure_api_key is None:
        raise Exception(
            "Required 'AZURE_API_KEY' in environment to make pass-through calls to Azure."
        )

    return await _base_openai_pass_through_handler(
        endpoint=endpoint,
        request=request,
        fastapi_response=fastapi_response,
        user_api_key_dict=user_api_key_dict,
        base_target_url=base_target_url,
        api_key=azure_api_key,
    )


@router.api_route(
    "/openai/{endpoint:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    tags=["OpenAI Pass-through", "pass-through"],
)
async def openai_proxy_route(
    endpoint: str,
    request: Request,
    fastapi_response: Response,
    user_api_key_dict: UserAPIKeyAuth = Depends(user_api_key_auth),
):
    """
    Simple pass-through for OpenAI. Use this if you want to directly send a request to OpenAI.


    """
    base_target_url = "https://api.openai.com"
    # Add or update query parameters
    openai_api_key = passthrough_endpoint_router.get_credentials(
        custom_llm_provider="openai",
        region_name=None,
    )
    if openai_api_key is None:
        raise Exception(
            "Required 'OPENAI_API_KEY' in environment to make pass-through calls to OpenAI."
        )

    return await _base_openai_pass_through_handler(
        endpoint=endpoint,
        request=request,
        fastapi_response=fastapi_response,
        user_api_key_dict=user_api_key_dict,
        base_target_url=base_target_url,
        api_key=openai_api_key,
    )


async def _base_openai_pass_through_handler(
    endpoint: str,
    request: Request,
    fastapi_response: Response,
    user_api_key_dict: UserAPIKeyAuth,
    base_target_url: str,
    api_key: str,
):
    encoded_endpoint = httpx.URL(endpoint).path

    # Ensure endpoint starts with '/' for proper URL construction
    if not encoded_endpoint.startswith("/"):
        encoded_endpoint = "/" + encoded_endpoint

    # Construct the full target URL using httpx
    base_url = httpx.URL(base_target_url)
    updated_url = base_url.copy_with(path=encoded_endpoint)

    ## check for streaming
    is_streaming_request = False
    if "stream" in str(updated_url):
        is_streaming_request = True

    ## CREATE PASS-THROUGH
    endpoint_func = create_pass_through_route(
        endpoint=endpoint,
        target=str(updated_url),
        custom_headers={
            "authorization": "Bearer {}".format(api_key),
            "api-key": "{}".format(api_key),
        },
    )  # dynamically construct pass-through endpoint based on incoming path
    received_value = await endpoint_func(
        request,
        fastapi_response,
        user_api_key_dict,
        stream=is_streaming_request,  # type: ignore
        query_params=dict(request.query_params),  # type: ignore
    )

    return received_value
