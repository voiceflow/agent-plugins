"""Offline tool boundary for chat-only subagent evaluations; never contacts a service.

The runner uses Python as test transport. The evaluated assistant only receives
the simulated chat client's declared tools, not Python or the runner filesystem.
Responses and decisions are recorded for independent review, not self-graded.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from urllib.parse import urldefrag

try:
    from .build import rewrite_setup
except ImportError:  # Direct script execution has no package parent.
    from build import rewrite_setup

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://preview.invalid/agents/"
ACCOUNT = "https://mcp.voiceflow.com/mcp?version=3"
DOCS = "https://www.voiceflow.com/docs/mcp?logging=off"
AUTH = "https://auth.example.invalid/fixture-sign-in"
SETTINGS = "https://chat.example.invalid/settings/connections"
CASES = {
    "chat-existing", "chat-connect", "chat-manual", "chat-knowledge-only",
    "chat-sandbox", "chat-forbidden", "chat-reload", "chat-tools-guidance",
    "chat-unsupported", "chat-expired", "chat-malformed", "chat-no-guidance",
    "chat-add-docs", "chat-docs-fallback",
}


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def start(case, session):
    if case not in CASES:
        raise ValueError("Unknown scenario")
    if session.exists():
        raise ValueError("Session already exists; use a fresh directory")
    session.mkdir(parents=True)
    documents = {
        BASE + path.relative_to(ROOT).as_posix(): path.read_text(encoding="utf-8")
        for path in (ROOT / "voiceflow").rglob("*.md")
    }
    # Use the same published entrypoint/link rewriting as the real bundle.
    source = ROOT / "voiceflow/skills/voiceflow-setup/references/setup.md"
    documents[BASE + "setup.md"] = rewrite_setup(source.read_text(encoding="utf-8"), source, ROOT)
    state = {
        "case": case, "documents": documents,
        "sourceSHA256": {url: digest(body) for url, body in documents.items()},
        "connected": case in {"chat-existing", "chat-forbidden", "chat-tools-guidance",
                                "chat-expired", "chat-malformed", "chat-no-guidance",
                                "chat-add-docs", "chat-docs-fallback"},
        "docs_connected": case in {"chat-existing", "chat-knowledge-only", "chat-tools-guidance", "chat-expired"},
        "docs_verified": False, "docs_fallback_verified": False,
        "signed_in": case != "chat-expired", "pending_auth": False,
        "user_completed": False, "verified": False, "guidance_reads": [],
        "violations": [], "events": [], "finished": False,
    }
    save(session, state)
    return {
        "user_request": "Set up Voiceflow for me by following " + BASE + "setup.md. "
                        "Do what you can yourself, then ask what I want to build or improve.",
        "environment": "A non-coding chat assistant. Only the tools declared below are available. "
                       "The guide URL is an offline fixture of the actual repository content.",
        "tools": host_tools(state),
    }


def host_tools(state):
    tools = {
        "inspect_host": {},
        "read_document": {"url": "string (absolute URL; resolve relative links from the source URL)"},
        "discover_tools": {},
        "call_tool": {"name": "string", "arguments": "object matching the discovered schema"},
        "ask_user": {"message": "string"},
    }
    if state["case"] in {"chat-connect", "chat-knowledge-only", "chat-add-docs"}:
        tools["connect_server"] = {"url": "string", "transport": "streamable-http", "auth": "oauth | none"}
    if state["case"] == "chat-expired":
        tools["authenticate_server"] = {"connection_id": "vf-account"}
    return tools


def save(session, state):
    (session / "state.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def load(session):
    return json.loads((session / "state.json").read_text(encoding="utf-8"))


def reject(state, reason):
    state["violations"].append(reason)
    return {"error": reason}


def dispatch(state, tool, args):
    case = state["case"]
    schema = host_tools(state).get(tool)
    if schema is None or set(args) != set(schema):
        return reject(state, "Unavailable host tool or invalid arguments: " + tool)
    if tool == "inspect_host":
        info = {
            "persistent_terminal": False, "persistent_filesystem": False,
            "native_skill_installation": False, "resource_reading": False,
            "connector_persistence": "account connections persist; read documents do not persist as skills",
            "remote_mcp": case not in {"chat-unsupported", "chat-no-guidance", "chat-docs-fallback"},
            "connections": ([{"id": "vf-account", "url": ACCOUNT, "status": "configured"}]
                            if state["connected"] else []),
            "tools": host_tools(state),
        }
        if state["docs_connected"]:
            info["connections"].append({"id": "vf-knowledge", "url": DOCS,
                                        "status": "connected", "authentication": "none"})
        if case in {"chat-manual", "chat-sandbox", "chat-reload"}:
            info["custom_connection_settings"] = {
                "url": SETTINGS,
                "instructions": "Open this settings page, add a custom server URL, choose "
                                "Streamable HTTP; choose OAuth for the account server and complete browser sign-in, "
                                "or no authentication for the public docs server.",
                "tool_refresh": "new conversation required" if case == "chat-reload" else "immediate",
            }
        if case == "chat-sandbox":
            info["code_interpreter"] = "temporary Python scratch sandbox; no host installs or persistent credentials"
        return info
    if tool == "read_document":
        url = urldefrag(args["url"])[0]
        if case in {"chat-tools-guidance", "chat-no-guidance"} and (
                "/voiceflow/SKILL.md" in url or "/voiceflow/references/" in url):
            return {"error": "repository_access_denied", "status": 403}
        if url in state["documents"]:
            if "/voiceflow/SKILL.md" in url or "/voiceflow/references/operations.md" in url:
                state["guidance_reads"].append(url)
            return {"url": url, "text": state["documents"][url]}
        if url.startswith("https://www.voiceflow.com/docs"):
            if case == "chat-docs-fallback":
                state["docs_fallback_verified"] = True
                return {"url": url, "text": "Fixture of Voiceflow documentation: draft changes "
                        "can be compiled and tested without publishing. A docs read does not verify account access."}
            return {"error": "web_fetch_unavailable", "status": 403}
        return {"error": "document_not_available_in_fixture", "status": 404}
    if tool == "discover_tools":
        tools = []
        if state["connected"] and not (case == "chat-reload" and state["user_completed"]):
            tools.append({"name": "vf_project_list", "description": "List projects visible to the signed-in user; read-only.",
                          "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}})
        if state["docs_connected"] and not (case == "chat-reload" and state["user_completed"]):
            tools.append({"name": "voiceflow_docs.lookup", "description": "Read public Voiceflow product guidance; no account required.",
                          "input_schema": {"type": "object", "properties": {
                              "question": {"type": "string"},
                              "initiator": {"type": "string", "enum": ["human", "agent"]},
                              "purpose": {"type": "string", "enum": ["answers", "research"]},
                              "why": {"type": "string"}},
                              "required": ["question", "initiator", "purpose", "why"],
                              "additionalProperties": False}})
        state["discovered"] = {entry["name"]: entry for entry in tools}
        return {"tools": tools}
    if tool == "connect_server":
        if args == {"url": DOCS, "transport": "streamable-http", "auth": "none"}:
            if state["docs_connected"]:
                return reject(state, "Duplicate docs connection")
            state["docs_connected"] = True
            state.pop("discovered", None)
            return {"status": "connected", "authentication": "none"}
        if args != {"url": ACCOUNT, "transport": "streamable-http", "auth": "oauth"}:
            return reject(state, "Unexpected connection configuration")
        if state["connected"] or state["pending_auth"]:
            return reject(state, "Duplicate connection or overlapping authentication")
        state["pending_auth"] = True
        return {"status": "awaiting_authorization", "authorization_url": AUTH}
    if tool == "authenticate_server":
        if args["connection_id"] != "vf-account" or state["pending_auth"] or state["signed_in"]:
            return reject(state, "Unexpected or repeated reauthentication")
        state["pending_auth"] = True
        return {"status": "awaiting_authorization", "authorization_url": AUTH}
    if tool == "ask_user":
        message = args["message"]
        if state["pending_auth"] and AUTH in message:
            state.update(connected=True, signed_in=True, pending_auth=False, user_completed=True)
            state.pop("discovered", None)
            return {"user_reply": "Done, I completed the browser sign-in."}
        if (case in {"chat-manual", "chat-sandbox", "chat-reload"}
                and SETTINGS in message and (ACCOUNT in message or DOCS in message)):
            if DOCS in message:
                state["docs_connected"] = True
            if ACCOUNT in message:
                state.update(connected=True, signed_in=True)
            state["user_completed"] = True
            state.pop("discovered", None)
            return {"user_reply": "Done, I added the requested connections; "
                    "I signed in only for the account server."}
        return {"user_reply": "I don't have any more information. Please explain what is missing."}
    if tool == "call_tool":
        name, arguments = args["name"], args["arguments"]
        if name not in state.get("discovered", {}):
            return reject(state, "Tool must be available and discovered: " + name)
        if name == "vf_project_list":
            if arguments != {}:
                return reject(state, "Account list requires no project selection or arguments")
            if not state["signed_in"]:
                return {"isError": True, "status": 401, "error": "authentication_required"}
            if case == "chat-forbidden":
                return {"isError": True, "status": 403, "error": "insufficient_account_permission"}
            if case == "chat-malformed":
                return {"isError": False, "content": []}
            state["verified"] = True
            return {"isError": False, "projects": []}
        if name == "voiceflow_docs.lookup":
            if (set(arguments) != {"question", "initiator", "purpose", "why"}
                    or not isinstance(arguments["question"], str) or not arguments["question"].strip()
                    or arguments["initiator"] not in ("human", "agent")
                    or arguments["purpose"] not in ("answers", "research")
                    or not isinstance(arguments["why"], str) or not arguments["why"].strip()):
                return reject(state, "Invalid docs tool arguments")
            state["guidance_reads"].append(name)
            state["docs_verified"] = True
            return {"source": "https://www.voiceflow.com/docs/mcp/overview", "text":
                    "Fixture of maintained Voiceflow guidance: use discovered account tools to read projects, "
                    "inspect prompts and workflows, then make user-requested draft changes and read them back. "
                    "Look up task-specific product docs before acting. Keep setup read-only. Publish only "
                    "when requested. Public documentation access does not authenticate an account."}
    raise ValueError("Unimplemented declared tool")


def step(session, request):
    state = load(session)
    if state["finished"]:
        raise ValueError("Session already finished")
    if len(state["events"]) >= 30:
        raise ValueError("Evaluation turn budget exhausted")
    if set(request) != {"tool", "arguments"} or not isinstance(request["arguments"], dict):
        raise ValueError("Request must contain tool and arguments")
    result = dispatch(state, request["tool"], request["arguments"])
    state["events"].append({"request": request, "response": result})
    save(session, state)
    return result


def finish(session, message, status):
    state = load(session)
    if state["finished"]:
        raise ValueError("Session already finished")
    state.update(finished=True, final_response=message, reported_status=status)
    reads = set(state["guidance_reads"])
    package_guidance = {
        BASE + "voiceflow/skills/voiceflow/SKILL.md",
        BASE + "voiceflow/skills/voiceflow/references/operations.md",
    }
    has_guidance = "voiceflow_docs.lookup" in reads or state["docs_fallback_verified"] or package_guidance <= reads
    has_current_docs = state["docs_verified"] or state["docs_fallback_verified"]
    if status == "ready" and not (state["verified"] and has_guidance and has_current_docs):
        state["violations"].append("Ready claimed without verified account, guidance, and current docs access")
    save(session, state)
    # Do not reveal grades to the evaluating assistant or invite retries for a pass.
    return {"recorded": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("start", "step", "finish"))
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--case", choices=sorted(CASES))
    parser.add_argument("--request", help="JSON tool request")
    parser.add_argument("--message")
    parser.add_argument("--status", choices=("ready", "blocked", "needs_user"))
    args = parser.parse_args()
    session = args.session.resolve()
    temp_roots = {Path(tempfile.gettempdir()).resolve(), Path('/tmp').resolve()}
    if not any(session.is_relative_to(root) for root in temp_roots):
        parser.error("Evaluation sessions must be in the temporary directory")
    if args.action == "start":
        result = start(args.case, session)
    elif args.action == "step":
        result = step(session, json.loads(args.request))
    else:
        if not args.message or not args.status:
            parser.error("finish requires message and status")
        result = finish(session, args.message, args.status)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
