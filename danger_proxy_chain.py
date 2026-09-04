"""
================================================================================
  🔥 Danger Mode Multi-Hop Proxy Chaining Gateway (FastAPI Standalone Engine)
================================================================================
  - Dynamic 6-Hop Circuit Formation
  - Pure Socket-Level Nested CONNECT Forwarding
  - Auto-shuffles proxy nodes on every incoming request
  - Complete Header Sanitization (strips X-Forwarded-For, Via, Client IP)
================================================================================
"""

import os
import random
import time
import requests
from fastapi import FastAPI, Request, Response
from multi_hop_chain_engine import multi_hop_engine

app = FastAPI(title="Danger Mode Multi-Hop Proxy Gateway", version="2.0")

@app.get("/health")
async def health_check():
    circ = multi_hop_engine.get_active_circuit()
    return {
        "status": "HEALTHY",
        "circuit_layers": circ.get("layers", 6),
        "exit_ip": circ.get("exit_ip"),
        "country": circ.get("country"),
        "latency_ms": circ.get("latency_ms")
    }

@app.api_route("/danger-proxy/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def danger_mode_proxy_gateway(request: Request, path: str):
    """
    Receives an incoming request, builds a fresh 6-hop dynamic circuit,
    strips origin signatures, and forwards it through 6 distinct proxy layers.
    """
    target_base = os.getenv("DANGER_TARGET_BACKEND", "https://backend.omnidim.io")
    target_url = f"{target_base}/{path}"
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"

    # 1. Dynamically build & shuffle a fresh 6-layer circuit
    circuit = multi_hop_engine.build_shuffled_circuit(6)
    sess = multi_hop_engine.create_chained_session(circuit)

    # 2. Sanitize and prepare headers
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("x-forwarded-for", None)
    headers.pop("x-real-ip", None)
    headers.pop("via", None)
    body = await request.body()

    try:
        # 3. Forward strictly through 6-layer chain
        resp = sess.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=body,
            timeout=20.0
        )
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers)
        )
    except Exception as e:
        return Response(content=f"6-Layer Chain Forwarding Error: {str(e)}", status_code=502)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
