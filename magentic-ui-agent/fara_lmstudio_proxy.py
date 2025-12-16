"""
FARA LM Studio Proxy Server
Converts FARA's <tool_call> XML format to OpenAI function calling JSON format
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import re
import json
import logging
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("fara-proxy")

app = FastAPI(title="FARA LM Studio Proxy")

# LM Studio endpoint
LM_STUDIO_BASE_URL = "http://127.0.0.1:1234/v1"


def extract_tool_calls(content: str) -> tuple[str, List[Dict[str, Any]] | None]:
    """
    Extract <tool_call> blocks from FARA's response and convert to OpenAI format

    Returns:
        tuple: (cleaned_content, tool_calls_list or None)
    """
    # Find all <tool_call> blocks
    pattern = r'<tool_call>(.*?)</tool_call>'
    matches = list(re.finditer(pattern, content, re.DOTALL))

    if not matches:
        return content, None

    tool_calls = []
    for i, match in enumerate(matches):
        try:
            # Extract JSON from tool_call block
            tool_json_str = match.group(1).strip()
            tool_json = json.loads(tool_json_str)

            # Convert to OpenAI format
            tool_call = {
                "id": f"call_{hash(tool_json_str) & 0x7FFFFFFF}_{i}",  # Positive hash
                "type": "function",
                "function": {
                    "name": tool_json.get("name", ""),
                    "arguments": json.dumps(tool_json.get("arguments", {}))
                }
            }
            tool_calls.append(tool_call)
            logger.info(f"Extracted tool call: {tool_call['function']['name']}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse tool_call JSON: {e}")
            logger.error(f"Content: {match.group(1)}")
            continue

    # Remove <tool_call> blocks from content
    cleaned_content = re.sub(pattern, '', content, flags=re.DOTALL).strip()

    return cleaned_content, tool_calls if tool_calls else None


@app.post("/v1/chat/completions")
async def proxy_chat_completions(request: Request):
    """
    Proxy chat completions requests to LM Studio and convert tool calls
    """
    try:
        # Get request body
        body = await request.json()
        logger.info(f"Received request for model: {body.get('model', 'unknown')}")

        # Forward request to LM Studio
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{LM_STUDIO_BASE_URL}/chat/completions",
                json=body,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code != 200:
                logger.error(f"LM Studio error: {response.status_code}")
                return JSONResponse(
                    status_code=response.status_code,
                    content=response.json()
                )

            # Parse LM Studio response
            data = response.json()

            # Process each choice
            for choice in data.get("choices", []):
                message = choice.get("message", {})
                content = message.get("content", "")

                if content:
                    # Extract and convert tool calls
                    cleaned_content, tool_calls = extract_tool_calls(content)

                    # Update message
                    message["content"] = cleaned_content
                    if tool_calls:
                        message["tool_calls"] = tool_calls
                        logger.info(f"Converted {len(tool_calls)} tool call(s)")
                    else:
                        # Ensure empty list if no tool calls
                        message["tool_calls"] = message.get("tool_calls", [])

            return JSONResponse(content=data)

    except httpx.RequestError as e:
        logger.error(f"Request to LM Studio failed: {e}")
        raise HTTPException(status_code=502, detail=f"LM Studio connection error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/models")
async def proxy_models():
    """
    Proxy models endpoint to LM Studio
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{LM_STUDIO_BASE_URL}/models")
            return JSONResponse(content=response.json())
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{LM_STUDIO_BASE_URL}/models")
            lm_studio_ok = response.status_code == 200
    except:
        lm_studio_ok = False

    return {
        "status": "healthy" if lm_studio_ok else "degraded",
        "proxy": "running",
        "lm_studio": "connected" if lm_studio_ok else "disconnected",
        "lm_studio_url": LM_STUDIO_BASE_URL
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FARA LM Studio Proxy on http://127.0.0.1:5000")
    logger.info(f"Proxying to LM Studio at {LM_STUDIO_BASE_URL}")
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info")
