"""Read-only connection probe. Never echo service output or credentials.

classify() is the pass rule that voiceflow-setup/references/cli.md gives for a JSON workspace read.
scripts/verify_cli.py runs it against the pinned CLI and localhost fixtures. It is not shipped.
"""
import argparse
import json
import subprocess


def parse_json(stream):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate response field")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError("Invalid JSON constant")

    try:
        return json.loads(stream, object_pairs_hook=unique_object, parse_constant=invalid_constant)
    except (ValueError, TypeError):
        return None


def classify(returncode, stdout, stderr):
    payloads = [parse_json(stdout), parse_json(stderr)]
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        kind = payload.get("error_type")
        if kind == "authentication_error":
            return "authentication_required"
        if kind == "authorization_error":
            return "permission_denied"
        if kind in ("connection_error", "rate_limit_error", "server_error"):
            return "temporarily_unavailable"
        if kind or payload.get("error"):
            return "request_failed"
    if returncode == 0:
        payload = payloads[0]
        workspaces = payload.get("workspaces") if isinstance(payload, dict) else None
        if isinstance(workspaces, list) and all(
                isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"].strip()
                for item in workspaces):
            return "connected"
    return "unexpected_response"


def check(binary, timeout=25):
    try:
        result = subprocess.run(
            [binary, "workspace", "list", "--agent-mode", "--no-interactive",
             "--color", "never", "-o", "json"],
            # CLI 0.287.0 through 0.337.0 can cancel JSON body reading with their inner --timeout.
            # Bound the whole process instead; truncated output never verifies access.
            capture_output=True, text=True, encoding="utf-8", timeout=timeout, check=False,
        )
    except FileNotFoundError:
        return "cli_missing"
    except subprocess.TimeoutExpired:
        return "temporarily_unavailable"
    except OSError:
        return "cli_unavailable"
    return classify(result.returncode, result.stdout, result.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vf", default="vf", help="Path to the verified Voiceflow CLI")
    args = parser.parse_args()
    status = check(args.vf)
    print(json.dumps({"status": status}))
    return 0 if status == "connected" else 1


if __name__ == "__main__":
    raise SystemExit(main())
