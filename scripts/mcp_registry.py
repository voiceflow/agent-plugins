"""Check, plan, and verify Voiceflow's MCP Registry entries in mcp-registry/.

The publish workflow runs this file in the job that holds the registry signing
key. It therefore uses only the Python standard library and imports nothing
from this repository. It never reads the key and never publishes: the workflow
runs mcp-publisher for that.

  check   Allowlist and manifest checks, then read-only smoke tests of each live server.
  plan    Print the manifests whose version is new. Fail when a version is already
          published with different content or is not active.
  verify  Read back each public record and compare it with its manifest.
  audit   List every published version in the namespace. Fail on a name outside the allowlist.

Run it with `python3 -I`, so Python imports nothing from the checkout but this file.
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
from urllib.parse import quote, urlencode
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "mcp-registry"
# The DNS key can publish any com.voiceflow/* name, and any name under a subdomain, such as
# com.voiceflow.example/*. This list keeps the workflow to these two servers.
ALLOWED_NAMES = ("com.voiceflow/docs", "com.voiceflow/voiceflow")
NAMESPACE_PREFIXES = ("com.voiceflow/", "com.voiceflow.")
REGISTRY = "https://registry.modelcontextprotocol.io"
AUDIT_PAGE_SIZE, AUDIT_MAX_PAGES = 100, 100
SCHEMA = "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"
FIELDS = ("$schema", "name", "title", "description", "version", "websiteUrl", "remotes")
OFFICIAL = "io.modelcontextprotocol.registry/official"
VERSION = re.compile(r"\d+\.\d+\.\d+")
USER_AGENT = "voiceflow-mcp-registry-check/1.0"
TIMEOUT = 30
VERIFY_ATTEMPTS, VERIFY_DELAY = 3, 10
PROTOCOL_VERSION = "2025-06-18"
# One synthetic question to the docs server's read-only ask tool. The listed URL has no logging=off,
# so the server logs this call; `why` says that it is an automated check.
DOCS_TOOL = "ask_voiceflow"
DOCS_ARGUMENTS = {
    "initiator": "agent",
    "purpose": "answers",
    "why": "Automated MCP Registry listing check from the voiceflow/agent-plugins publish workflow.",
    "question": "How do I connect an AI assistant to the Voiceflow docs MCP server?",
}
DOCS_CITATION = "https://www.voiceflow.com/docs/"


class CheckError(Exception):
    """A check failed; the message says what to fix."""


def load_manifests():
    return {path: json.loads(path.read_text(encoding="utf-8")) for path in sorted(MANIFESTS.glob("*/server.json"))}


def label(path):
    return f"{path.parent.name}/server.json"


def manifest_problems(manifests):
    """Return each reason these manifests must not be published. The names must be exactly ALLOWED_NAMES."""
    problems, names = [], []
    for path, manifest in manifests.items():
        where, name = label(path), manifest.get("name")
        names.append(name)
        if name not in ALLOWED_NAMES:
            problems.append(f"{where}: {name} is not allowed; this workflow publishes only {', '.join(ALLOWED_NAMES)}")
        extra = sorted(set(manifest) - set(FIELDS))
        if extra:
            problems.append(f"{where}: unexpected fields {', '.join(extra)}")
        if manifest.get("$schema") != SCHEMA:
            problems.append(f"{where}: $schema must be {SCHEMA}")
        for field in ("title", "description"):
            if not isinstance(manifest.get(field), str) or not 0 < len(manifest[field]) <= 100:
                problems.append(f"{where}: {field} must be 1 to 100 characters")
        if not isinstance(manifest.get("version"), str) or not VERSION.fullmatch(manifest["version"]):
            problems.append(f"{where}: version must look like 1.2.3")
        if not str(manifest.get("websiteUrl", "")).startswith("https://"):
            problems.append(f"{where}: websiteUrl must be https")
        remotes = manifest.get("remotes")
        if not (isinstance(remotes, list) and len(remotes) == 1 and isinstance(remotes[0], dict)
                and remotes[0].get("type") == "streamable-http"
                and str(remotes[0].get("url", "")).startswith("https://")):
            problems.append(f"{where}: give exactly one streamable-http remote with an https URL")
    for name in sorted({name for name in names if names.count(name) > 1}, key=str):
        problems.append(f"{name} appears in more than one manifest")
    for name in ALLOWED_NAMES:
        if name not in names:
            problems.append(f"no manifest for {name}")
    return problems


def require_valid(manifests):
    problems = manifest_problems(manifests)
    if problems:
        raise CheckError("manifests failed the checks:\n  " + "\n  ".join(problems))


def request(method, url, body=None, headers=None):
    """Send one request. Return (status, headers, body) for every HTTP status, including errors."""
    data = None if body is None else json.dumps(body).encode()
    headers = {"User-Agent": USER_AGENT, **({"Content-Type": "application/json"} if data else {}), **(headers or {})}
    try:
        response = urllib.request.urlopen(urllib.request.Request(url, data, headers, method=method), timeout=TIMEOUT)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, response.headers, response.read()


# Registry read API: GET /v0.1/servers/{url-encoded name}/versions/{url-encoded version}.

def record_url(name, version, registry=REGISTRY):
    return f"{registry}/v0.1/servers/{quote(name, safe='')}/versions/{quote(version, safe='')}?include_deleted=true"


def fetch_record(name, version):
    """Return the registry's record of one exact version, with deleted versions included, or None."""
    status, _, body = request("GET", record_url(name, version), headers={"Accept": "application/json"})
    if status == 404:
        return None
    if status != 200:
        raise CheckError(f"registry returned HTTP {status} for {name} {version}")
    return json.loads(body)


def record_status(record):
    return ((record.get("_meta") or {}).get(OFFICIAL) or {}).get("status")


def differences(manifest, server):
    """Name each field that differs between a manifest and a registry record. $schema is not content."""
    return sorted(key for key in (set(manifest) | set(server)) - {"$schema"} if manifest.get(key) != server.get(key))


def decide(manifest, record):
    """Return (decision, reason). The decision is new, identical, or conflict."""
    if record is None:
        return "new", "this version is not in the registry"
    changed = differences(manifest, record.get("server") or {})
    if changed:
        return "conflict", f"this version is published with a different {', '.join(changed)}"
    status = record_status(record)
    if status != "active":
        return "conflict", f"this version is published with status {status}"
    return "identical", "this version is published and active with the same content"


def verify_problems(manifest, record):
    """Return what is wrong with the public record of a manifest: status, or any field but $schema."""
    if record is None:
        return ["not found in the registry"]
    status = record_status(record)
    problems = [] if status == "active" else [f"status is {status}, not active"]
    changed = differences(manifest, record.get("server") or {})
    return problems + [f"{field} differs from the manifest" for field in changed]


# Streamable HTTP: a POST returns either one JSON body or a text/event-stream of JSON-RPC messages.

def sse_events(lines):
    """Yield the data of each server-sent event, one string per event."""
    data = []
    for line in lines:
        line = line.rstrip("\r\n")
        if not line:
            if data:
                yield "\n".join(data)
            data = []
            continue
        field, _, value = line.partition(":")
        if field == "data":
            data.append(value[1:] if value.startswith(" ") else value)
    if data:
        yield "\n".join(data)


def rpc_result(payloads, request_id):
    """Return the result of the JSON-RPC response to request_id among JSON payloads."""
    for payload in payloads:
        if not payload.strip():
            continue
        message = json.loads(payload)
        for item in message if isinstance(message, list) else [message]:
            if isinstance(item, dict) and item.get("id") == request_id:
                if "error" in item:
                    error = item["error"] if isinstance(item["error"], dict) else {}
                    raise CheckError(f"JSON-RPC error {error.get('code')}: {error.get('message')}")
                return item.get("result")
    raise CheckError(f"no JSON-RPC response to request {request_id}")


def rpc(url, message, session):
    """Send one JSON-RPC message to a Streamable HTTP server and return the result, or None for a notification."""
    headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json",
               "User-Agent": USER_AGENT}
    headers.update({key: value for key, value in (("Mcp-Session-Id", session.get("id")),
                                                    ("MCP-Protocol-Version", session.get("protocol"))) if value})
    data = json.dumps(message).encode()
    try:
        response = urllib.request.urlopen(urllib.request.Request(url, data, headers, method="POST"), timeout=TIMEOUT)
    except urllib.error.HTTPError as error:
        raise CheckError(f"{message['method']} returned HTTP {error.code}") from None
    with response:
        session["id"] = response.headers.get("Mcp-Session-Id") or session.get("id")
        if "id" not in message:
            return None
        if response.headers.get_content_type() == "text/event-stream":
            return rpc_result(sse_events(line.decode("utf-8") for line in response), message["id"])
        return rpc_result([response.read().decode("utf-8")], message["id"])


def initialize_message(request_id=1):
    return {"jsonrpc": "2.0", "id": request_id, "method": "initialize",
            "params": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {},
                       "clientInfo": {"name": "voiceflow-mcp-registry-check", "version": "1.0"}}}


def smoke_docs(url):
    """Initialize, list tools, and ask one synthetic question. The answer must cite the docs."""
    session = {}
    result = rpc(url, initialize_message(), session) or {}
    session["protocol"] = result.get("protocolVersion")
    rpc(url, {"jsonrpc": "2.0", "method": "notifications/initialized"}, session)
    tools = {tool.get("name"): tool for tool in (rpc(url, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                                                     session) or {}).get("tools", [])}
    tool = tools.get(DOCS_TOOL)
    if tool is None:
        raise CheckError(f"tools/list has no {DOCS_TOOL}; it lists {', '.join(sorted(map(str, tools)))}")
    if not (tool.get("annotations") or {}).get("readOnlyHint"):
        raise CheckError(f"{DOCS_TOOL} is not marked read-only, so the check will not call it")
    schema = tool.get("inputSchema") or {}
    missing = sorted(set(schema.get("required", [])) - set(DOCS_ARGUMENTS))
    if missing:
        raise CheckError(f"{DOCS_TOOL} now requires {', '.join(missing)}; update DOCS_ARGUMENTS")
    arguments = {key: value for key, value in DOCS_ARGUMENTS.items() if key in schema.get("properties", {})}
    answer = rpc(url, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                       "params": {"name": DOCS_TOOL, "arguments": arguments}}, session) or {}
    if answer.get("isError"):
        raise CheckError(f"{DOCS_TOOL} returned an error result")
    text = "\n".join(item.get("text", "") for item in answer.get("content", []) if isinstance(item, dict))
    if DOCS_CITATION not in text + json.dumps(answer.get("structuredContent") or {}):
        raise CheckError(f"{DOCS_TOOL} answered without a {DOCS_CITATION} citation")
    if session.get("id"):
        try:
            request("DELETE", url, headers={"Mcp-Session-Id": session["id"]})
        except OSError:
            pass
    return f"{len(tools)} tools; {DOCS_TOOL} answered with a docs citation"


def resource_metadata_url(challenges):
    """Return the resource_metadata URL from WWW-Authenticate header values, or None."""
    for challenge in challenges:
        match = re.search(r'resource_metadata\s*=\s*(?:"([^"]*)"|([^\s,]+))', challenge)
        if match:
            return match.group(1) or match.group(2)
    return None


def smoke_oauth(url):
    """Send initialize without credentials. Expect 401 and protected-resource metadata. Never sign in."""
    status, headers, _ = request("POST", url, initialize_message(),
                                 {"Accept": "application/json, text/event-stream"})
    if status != 401:
        raise CheckError(f"initialize without sign-in returned HTTP {status}, not 401")
    metadata_url = resource_metadata_url(headers.get_all("WWW-Authenticate") or [])
    if not metadata_url or not metadata_url.startswith("https://"):
        raise CheckError("the 401 response has no https resource_metadata in WWW-Authenticate")
    status, _, body = request("GET", metadata_url, headers={"Accept": "application/json"})
    if status != 200:
        raise CheckError(f"protected-resource metadata returned HTTP {status}")
    servers = json.loads(body).get("authorization_servers")
    if not (isinstance(servers, list) and servers and all(str(item).startswith("https://") for item in servers)):
        raise CheckError("protected-resource metadata has no https authorization_servers")
    return f"401 without sign-in; metadata names {len(servers)} authorization server(s)"


SMOKE_TESTS = {"com.voiceflow/docs": smoke_docs, "com.voiceflow/voiceflow": smoke_oauth}


def check(_args):
    manifests = load_manifests()
    require_valid(manifests)
    print(f"{len(manifests)} manifests pass the allowlist and field checks")
    failures = 0
    for manifest in manifests.values():
        name, url = manifest["name"], manifest["remotes"][0]["url"]
        try:
            print(f"pass {name} at {url}: {SMOKE_TESTS[name](url)}")
        except (CheckError, OSError, ValueError) as error:
            failures += 1
            print(f"FAIL {name} at {url}: {error}")
    return 1 if failures else 0


def plan_manifests(manifests):
    """Return (rows, paths to publish, conflict count) for valid manifests."""
    rows, publish, conflicts = [], [], 0
    for path, manifest in manifests.items():
        decision, reason = decide(manifest, fetch_record(manifest["name"], manifest["version"]))
        rows.append((manifest["name"], manifest["version"], decision, reason))
        if decision == "new":
            publish.append(path)
        elif decision == "conflict":
            conflicts += 1
    return rows, publish, conflicts


def plan(_args):
    manifests = load_manifests()
    require_valid(manifests)
    rows, publish, conflicts = plan_manifests(manifests)
    for row in rows:
        print("{} {}: {}, {}".format(*row), file=sys.stderr)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write("| Server | Version | Plan | Reason |\n| --- | --- | --- | --- |\n")
            handle.writelines("| `{}` | {} | {} | {} |\n".format(*row) for row in rows)
    if conflicts:
        print(f"error: {conflicts} conflict(s). Raise the version in the manifest, or ask the owner.", file=sys.stderr)
        return 1
    for path in publish:
        print(path.relative_to(ROOT).as_posix())
    return 0


def verify(_args):
    manifests = load_manifests()
    require_valid(manifests)
    failures = 0
    for manifest in manifests.values():
        for attempt in range(1, VERIFY_ATTEMPTS + 1):
            problems = verify_problems(manifest, fetch_record(manifest["name"], manifest["version"]))
            if not problems or attempt == VERIFY_ATTEMPTS:
                break
            time.sleep(VERIFY_DELAY)
        failures += bool(problems)
        print(f"{'FAIL' if problems else 'pass'} {manifest['name']} {manifest['version']}: "
              f"{'; '.join(problems) or 'active and identical to the manifest'}")
    return 1 if failures else 0


def namespace_records():
    """Return every version in the namespace, deleted ones included, following each page cursor."""
    records, cursor, seen = [], None, set()
    for _ in range(AUDIT_MAX_PAGES):
        query = {"search": "com.voiceflow", "include_deleted": "true", "limit": AUDIT_PAGE_SIZE}
        if cursor:
            query["cursor"] = cursor
        status, _, body = request("GET", f"{REGISTRY}/v0.1/servers?{urlencode(query)}",
                                  headers={"Accept": "application/json"})
        if status != 200:
            raise CheckError(f"registry list returned HTTP {status}")
        page = json.loads(body)
        records += [item for item in page.get("servers") or []
                    if str((item.get("server") or {}).get("name", "")).startswith(NAMESPACE_PREFIXES)]
        cursor = (page.get("metadata") or {}).get("nextCursor")
        if not cursor:
            return records
        if cursor in seen:
            raise CheckError("the registry returned the same page cursor twice; the listing is incomplete")
        seen.add(cursor)
    raise CheckError(f"the listing has more than {AUDIT_MAX_PAGES} pages; the audit stopped")


def audit(_args):
    failures = 0
    rows = sorted((str(item["server"].get("name")), str(item["server"].get("version")), str(record_status(item)))
                  for item in namespace_records())
    for name, version, status in rows:
        unexpected = name not in ALLOWED_NAMES
        failures += unexpected
        print(f"{'FAIL unexpected name' if unexpected else 'ok'} {name} {version} {status}")
    print(f"{len(rows)} versions under com.voiceflow; {failures} outside the allowlist")
    return 1 if failures else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    for name, function in (("check", check), ("plan", plan), ("verify", verify), ("audit", audit)):
        commands.add_parser(name).set_defaults(run=function)
    args = parser.parse_args(argv)
    try:
        return args.run(args)
    except (CheckError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
