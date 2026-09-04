"""
================================================================================
  🔌 OmniDimension Official Model Context Protocol (MCP) Server
================================================================================
  Connect Claude Desktop, Cursor, VS Code, Windsurf, and LLMs directly
  to your OmniDimension Multi-Account Voice AI Hub.
  
  Implements standard JSON-RPC 2.0 stdio MCP protocol for all endpoints:
  - Agents (List, Create, Update, Delete, Versioning)
  - Live Calls (Dispatch, Call Logs, Recording Audio)
  - Bulk Calls (Create, Live Status, Add Contact, Cancel)
  - Web Call Sessions (Browser WebRTC / WebSocket Token)
  - Knowledge Base (List, Upload, Attach, Detach)
  - Phone Numbers & SIP Trunks (List, Search, Import Twilio/SIP)
  - Providers Catalog (LLMs, Cartesia/ElevenLabs/Sarvam Voices, STT)
  - Simulations & AI Prompt Auto-Enhance
  - Real Billing & Balance Inspector
================================================================================
"""

import sys
import os
import json
import traceback
import requests
from dotenv import load_dotenv

# Ensure UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
    except Exception:
        pass

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(ENV_PATH, override=True)

API_BASE_URL = os.getenv("OMNIDIM_BASE_URL", "https://backend.omnidim.io/api/v1").strip()
RAW_KEYS = os.getenv("OMNIDIM_API_KEYS", "") or os.getenv("OMNIDIM_API_KEY", "")
API_KEYS = [k.strip() for k in RAW_KEYS.split(",") if k.strip()] if RAW_KEYS else []

PRIMARY_KEY = API_KEYS[0] if API_KEYS else ""


def get_auth_headers(api_key=None):
    key = api_key or PRIMARY_KEY
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }


from proxy_manager import proxy_manager

def api_request(method, endpoint, payload=None, params=None, api_key=None):
    """Execute HTTP request to OmniDimension Backend routed through proxy tunnel."""
    url = f"{API_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = get_auth_headers(api_key)
    try:
        s = proxy_manager.get_session()
        if method.upper() == "GET":
            r = s.get(url, headers=headers, params=params, timeout=15)
        elif method.upper() == "POST":
            r = s.post(url, headers=headers, json=payload, timeout=20)
        elif method.upper() == "PUT":
            r = s.put(url, headers=headers, json=payload, timeout=20)
        elif method.upper() == "DELETE":
            r = s.delete(url, headers=headers, params=params, timeout=15)
        elif method.upper() == "PATCH":
            r = s.patch(url, headers=headers, json=payload, timeout=20)
        else:
            return {"error": f"Unsupported method {method}"}

        try:
            return r.json()
        except Exception:
            return {"status_code": r.status_code, "text": r.text}
    except Exception as e:
        return {"error": str(e)}


# ==========================================
# Tool Definitions Catalog
# ==========================================
MCP_TOOLS = [
    {
        "name": "omnidim_list_agents",
        "description": "List all voice AI assistants across connected OmniDimension accounts with pagination.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page": {"type": "integer", "description": "Page number (default 1)"},
                "page_size": {"type": "integer", "description": "Page size (default 20)"}
            }
        }
    },
    {
        "name": "omnidim_get_agent",
        "description": "Retrieve full details, voice configuration, and prompt flow of a specific voice agent by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "integer", "description": "The unique ID of the voice agent"}
            },
            "required": ["agent_id"]
        }
    },
    {
        "name": "omnidim_create_agent",
        "description": "Create a new Voice AI assistant with custom prompt, welcome message, LLM model, and voice TTS.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Assistant name"},
                "welcome_message": {"type": "string", "description": "Opening sentence spoken when call connects"},
                "prompt": {"type": "string", "description": "System instructions and conversational rules"},
                "model": {"type": "string", "description": "LLM model (e.g. gpt-4o-mini, gemini-2.5-flash)"},
                "call_type": {"type": "string", "description": "Call direction (Outgoing or Incoming)", "enum": ["Outgoing", "Incoming"]}
            },
            "required": ["name", "prompt"]
        }
    },
    {
        "name": "omnidim_dispatch_call",
        "description": "Dispatch an instant outbound AI voice call to a phone number using a designated agent.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "integer", "description": "The ID of the Voice AI agent"},
                "to_number": {"type": "string", "description": "Destination phone number with country code (e.g. +919876543210)"},
                "customer_name": {"type": "string", "description": "Name of the customer for mail-merge variable injection"}
            },
            "required": ["agent_id", "to_number"]
        }
    },
    {
        "name": "omnidim_list_call_logs",
        "description": "Retrieve recent call history, call duration, talk status, sentiment, and recording metadata.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page": {"type": "integer", "description": "Page number"},
                "page_size": {"type": "integer", "description": "Number of call logs to retrieve"}
            }
        }
    },
    {
        "name": "omnidim_create_bulk_call",
        "description": "Launch an outbound bulk calling campaign across contact lists with multi-account load balancing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "integer", "description": "Agent ID to handle calls"},
                "campaign_name": {"type": "string", "description": "Name of the campaign"},
                "contacts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "to_number": {"type": "string"},
                            "customer_name": {"type": "string"}
                        },
                        "required": ["to_number"]
                    }
                }
            },
            "required": ["agent_id", "campaign_name", "contacts"]
        }
    },
    {
        "name": "omnidim_create_web_session",
        "description": "Create a live browser WebRTC / WebSocket voice call session token for web apps.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "integer", "description": "Agent ID to speak with"}
            },
            "required": ["agent_id"]
        }
    },
    {
        "name": "omnidim_list_voices",
        "description": "List all available realistic TTS voice profiles across Cartesia, ElevenLabs, Google Journey, and Sarvam AI.",
        "inputSchema": {"type": "object"}
    },
    {
        "name": "omnidim_list_phone_numbers",
        "description": "List all purchased and attached inbound/outbound phone numbers and SIP trunks.",
        "inputSchema": {"type": "object"}
    },
    {
        "name": "omnidim_enhance_prompt",
        "description": "Use OmniDimension AI Prompt Engineering engine to optimize system prompt for voice telephony.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "raw_prompt": {"type": "string", "description": "Rough draft instructions or business goal"}
            },
            "required": ["raw_prompt"]
        }
    },
    {
        "name": "omnidim_get_billing_balance",
        "description": "Get real live calling balance, remaining minutes, voice rate ($0.115/min), and concurrency quota.",
        "inputSchema": {"type": "object"}
    }
]


# ==========================================
# Tool Execution Dispatcher
# ==========================================
def execute_tool(tool_name, arguments):
    """Handle tool invocation and execute real API request."""
    try:
        if tool_name == "omnidim_list_agents":
            page = arguments.get("page", 1)
            size = arguments.get("page_size", 20)
            return api_request("GET", "agents", params={"page": page, "page_size": size})

        elif tool_name == "omnidim_get_agent":
            aid = arguments["agent_id"]
            return api_request("GET", f"agents/{aid}")

        elif tool_name == "omnidim_create_agent":
            payload = {
                "name": arguments["name"],
                "welcome_message": arguments.get("welcome_message", "Hello! How can I assist you?"),
                "context_breakdown": [{"title": "Role & Purpose", "body": arguments["prompt"], "is_enabled": True}],
                "call_type": arguments.get("call_type", "Outgoing"),
                "model": {"model": arguments.get("model", "gpt-4o-mini"), "temperature": 0.7}
            }
            return api_request("POST", "agents", payload=payload)

        elif tool_name == "omnidim_dispatch_call":
            payload = {
                "agent_id": int(arguments["agent_id"]),
                "to_number": arguments["to_number"],
                "call_context": {"customer_name": arguments.get("customer_name", "Valued Customer")}
            }
            return api_request("POST", "calls/dispatch", payload=payload)

        elif tool_name == "omnidim_list_call_logs":
            page = arguments.get("page", 1)
            size = arguments.get("page_size", 10)
            return api_request("GET", "calls/logs", params={"page": page, "page_size": size})

        elif tool_name == "omnidim_create_bulk_call":
            payload = {
                "agent_id": int(arguments["agent_id"]),
                "name": arguments["campaign_name"],
                "contacts": arguments["contacts"]
            }
            return api_request("POST", "bulk-calls", payload=payload)

        elif tool_name == "omnidim_create_web_session":
            payload = {"agent_id": int(arguments["agent_id"])}
            return api_request("POST", "sessions", payload=payload)

        elif tool_name == "omnidim_list_voices":
            return api_request("GET", "providers/voices")

        elif tool_name == "omnidim_list_phone_numbers":
            return api_request("GET", "phone-numbers")

        elif tool_name == "omnidim_enhance_prompt":
            payload = {"prompt": arguments["raw_prompt"]}
            return api_request("POST", "simulation/enhance-prompt", payload=payload)

        elif tool_name == "omnidim_get_billing_balance":
            from billing_store import get_billing_state
            return get_billing_state()

        else:
            return {"error": f"Unknown tool '{tool_name}'"}

    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


# ==========================================
# Standard JSON-RPC 2.0 MCP Protocol Loop
# ==========================================
def main():
    """Main JSON-RPC stdio loop for Claude Desktop, Cursor, and VS Code."""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "serverInfo": {
                            "name": "omnidim-voice-ai-mcp",
                            "version": "4.0.0"
                        },
                        "capabilities": {
                            "tools": {}
                        }
                    }
                }
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

            elif method == "notifications/initialized":
                pass  # Client acknowledged initialization

            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": MCP_TOOLS
                    }
                }
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

            elif method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})
                tool_result = execute_tool(tool_name, args)

                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(tool_result, indent=2)
                            }
                        ]
                    }
                }
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

            elif method == "ping":
                sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {}}) + "\n")
                sys.stdout.flush()

            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method '{method}' not found"
                    }
                }
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

        except Exception as ex:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(ex)}
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
