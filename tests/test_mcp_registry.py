"""MCP Registry publishing logic with synthetic manifests and records; no network, no sign-in."""
import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/mcp_registry.py"
WORKFLOW = ROOT / ".github/workflows/publish-mcp.yml"
spec = importlib.util.spec_from_file_location("mcp_registry", SCRIPT)
registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(registry)

OFFICIAL = registry.OFFICIAL
PYTHON_CALL = re.compile(r"(?<![\w./-])python[\d.]*\s+(-?[\w./-]+)")


def manifest(name="com.voiceflow/docs", **changes):
    data = {"$schema": registry.SCHEMA, "name": name, "title": "Example", "description": "Synthetic entry.",
            "version": "1.0.0", "websiteUrl": "https://example.invalid/docs",
            "remotes": [{"type": "streamable-http", "url": "https://example.invalid/mcp"}]}
    return data | changes


def record(data, status="active"):
    return {"server": copy.deepcopy(data), "_meta": {OFFICIAL: {"status": status, "isLatest": True}}}


def pair():
    return {Path("/x/docs/server.json"): manifest(),
            Path("/x/voiceflow/server.json"): manifest("com.voiceflow/voiceflow")}


class NoNetwork(unittest.TestCase):
    def setUp(self):
        blocker = patch("urllib.request.urlopen", side_effect=AssertionError("tests must not use the network"))
        blocker.start()
        self.addCleanup(blocker.stop)


class AllowlistTests(NoNetwork):
    def test_repository_manifests_pass(self):
        manifests = registry.load_manifests()
        self.assertEqual(registry.manifest_problems(manifests), [])
        self.assertEqual(sorted(item["name"] for item in manifests.values()), sorted(registry.ALLOWED_NAMES))

    def test_every_allowed_name_has_a_smoke_test(self):
        self.assertEqual(set(registry.SMOKE_TESTS), set(registry.ALLOWED_NAMES))

    def test_names_outside_the_allowlist_are_refused(self):
        manifests = pair()
        manifests[Path("/x/docs/server.json")]["name"] = "com.voiceflow/knowledge"
        problems = registry.manifest_problems(manifests)
        self.assertIn("docs/server.json: com.voiceflow/knowledge is not allowed; this workflow publishes only "
                      "com.voiceflow/docs, com.voiceflow/voiceflow", problems)
        self.assertIn("no manifest for com.voiceflow/docs", problems)

    def test_duplicate_and_missing_entries_are_refused(self):
        manifests = {Path("/x/a/server.json"): manifest(), Path("/x/b/server.json"): manifest()}
        self.assertEqual(registry.manifest_problems(manifests), [
            "com.voiceflow/docs appears in more than one manifest", "no manifest for com.voiceflow/voiceflow"])

    def test_field_problems_are_reported(self):
        cases = [
            (dict(packages=[]), "docs/server.json: unexpected fields packages"),
            (dict(version="^1.0.0"), "docs/server.json: version must look like 1.2.3"),
            (dict(description="x" * 101), "docs/server.json: description must be 1 to 100 characters"),
            (dict(websiteUrl="http://example.invalid"), "docs/server.json: websiteUrl must be https"),
            (dict(remotes=[{"type": "sse", "url": "https://example.invalid/sse"}]),
             "docs/server.json: give exactly one streamable-http remote with an https URL"),
            (dict(remotes=[manifest()["remotes"][0]] * 2),
             "docs/server.json: give exactly one streamable-http remote with an https URL"),
        ]
        for change, message in cases:
            with self.subTest(message=message):
                manifests = pair()
                manifests[Path("/x/docs/server.json")].update(change)
                self.assertEqual(registry.manifest_problems(manifests), [message])


class PlanTests(NoNetwork):
    def test_decisions(self):
        local = manifest()
        newer_schema = record(local)
        newer_schema["server"]["$schema"] = registry.SCHEMA.replace("2025-12-11", "2030-01-01")
        changed = record(local)
        changed["server"]["remotes"][0]["url"] = "https://example.invalid/other"
        cases = [
            (None, "new"),
            (record(local), "identical"),
            (newer_schema, "identical"),
            (changed, "conflict"),
            (record(manifest(description="Other text.")), "conflict"),
            (record(local | {"repository": {"url": "https://example.invalid"}}), "conflict"),
            (record(local, status="deprecated"), "conflict"),
            (record(local, status="deleted"), "conflict"),
            ({"server": local}, "conflict"),
        ]
        for found, expected in cases:
            with self.subTest(found=found, expected=expected):
                self.assertEqual(registry.decide(local, found)[0], expected)
        self.assertEqual(registry.decide(local, changed)[1],
                         "this version is published with a different remotes")

    def test_record_url_encodes_the_name_and_version(self):
        self.assertEqual(registry.record_url("com.voiceflow/docs", "1.0.0+a"),
                         "https://registry.modelcontextprotocol.io/v0.1/servers/com.voiceflow%2Fdocs"
                         "/versions/1.0.0%2Ba?include_deleted=true")

    def run_plan(self, records):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            for item in (manifest(), manifest("com.voiceflow/voiceflow")):
                (folder / item["name"].split("/")[1]).mkdir()
                (folder / item["name"].split("/")[1] / "server.json").write_text(json.dumps(item), encoding="utf-8")
            out, err = io.StringIO(), io.StringIO()

            def fetch(name, version):
                return records.get(name)

            with patch.object(registry, "MANIFESTS", folder), patch.object(registry, "ROOT", folder.parent), \
                    patch.object(registry, "fetch_record", fetch), \
                    patch.dict("os.environ", {"GITHUB_STEP_SUMMARY": ""}), \
                    contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = registry.main(["plan"])
            return code, out.getvalue().splitlines(), err.getvalue(), folder.name

    def test_plan_prints_only_new_manifests(self):
        code, out, err, folder = self.run_plan({"com.voiceflow/docs": record(manifest())})
        self.assertEqual((code, out), (0, [f"{folder}/voiceflow/server.json"]))
        self.assertIn("com.voiceflow/docs 1.0.0: identical", err)
        self.assertIn("com.voiceflow/voiceflow 1.0.0: new", err)

    def test_plan_fails_on_a_conflict_and_prints_nothing_to_publish(self):
        code, out, err, _ = self.run_plan({"com.voiceflow/docs": record(manifest(title="Changed"))})
        self.assertEqual((code, out), (1, []))
        self.assertIn("com.voiceflow/docs 1.0.0: conflict, this version is published with a different title", err)


class VerifyTests(NoNetwork):
    def test_read_back_compares_status_and_every_field(self):
        local = manifest()
        self.assertEqual(registry.verify_problems(local, record(local)), [])
        self.assertEqual(registry.verify_problems(local, None), ["not found in the registry"])
        self.assertEqual(registry.verify_problems(local, record(local, status="deleted")),
                         ["status is deleted, not active"])
        for field in ("name", "version", "title", "description", "websiteUrl"):
            with self.subTest(field=field):
                self.assertEqual(registry.verify_problems(local, record(local | {field: "other"})),
                                 [f"{field} differs from the manifest"])
        self.assertEqual(registry.verify_problems(local, record(local | {"remotes": []})),
                         ["remotes differs from the manifest"])

    def test_verify_retries_then_fails(self):
        calls = []

        def fetch(name, version):
            calls.append(name)
            return None

        out = io.StringIO()
        with patch.object(registry, "load_manifests", pair), patch.object(registry, "fetch_record", fetch), \
                patch.object(registry.time, "sleep") as sleep, contextlib.redirect_stdout(out):
            self.assertEqual(registry.main(["verify"]), 1)
        self.assertEqual(len(calls), 2 * registry.VERIFY_ATTEMPTS)
        self.assertEqual(sleep.call_count, 2 * (registry.VERIFY_ATTEMPTS - 1))
        self.assertIn("FAIL com.voiceflow/docs 1.0.0: not found in the registry", out.getvalue())


class IsolationTests(NoNetwork):
    def test_every_python_call_in_the_workflow_and_its_docs_is_isolated(self):
        files = (WORKFLOW, ROOT / "mcp-registry/README.md",
                 ROOT / ".claude/skills/marketplace-submissions/references/mcp-registry.md")
        calls = [(path.name, flag) for path in files for flag in PYTHON_CALL.findall(path.read_text(encoding="utf-8"))]
        self.assertGreaterEqual(sum(name == WORKFLOW.name for name, _ in calls), 4)
        self.assertEqual([call for call in calls if call[1] != "-I"], [])

    def test_isolated_mode_ignores_modules_planted_beside_the_script(self):
        planted = ("from pathlib import Path\n"
                   "Path(__file__).with_name('planted-ran').write_text('x')\n"
                   "raise SystemExit(97)\n")
        env = {key: value for key, value in os.environ.items() if not key.startswith("PYTHON")}
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            script = folder / "mcp_registry.py"
            shutil.copyfile(SCRIPT, script)
            for name in ("json.py", "argparse.py"):
                (folder / name).write_text(planted, encoding="utf-8")

            def run(*flags):
                return subprocess.run([sys.executable, *flags, str(script), "--help"], cwd=folder, env=env,
                                      capture_output=True, text=True, timeout=60)

            isolated = run("-I")
            self.assertEqual(isolated.returncode, 0, isolated.stderr)
            self.assertIn("audit", isolated.stdout)
            self.assertFalse((folder / "planted-ran").exists())
            # Without -I the planted module runs, which proves that the files above would be imported.
            self.assertEqual(run().returncode, 97)
            self.assertTrue((folder / "planted-ran").exists())


class FakeResponse:
    def __init__(self, data, status=200):
        self.status, self.headers, self.body = status, {}, json.dumps(data).encode()

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


def listing(*names, cursor=None):
    servers = [{"server": {"name": name, "version": "1.0.0"}, "_meta": {OFFICIAL: {"status": "active"}}}
               for name in names]
    return {"servers": servers, "metadata": {"count": len(servers), **({"nextCursor": cursor} if cursor else {})}}


class AuditTests(NoNetwork):
    def run_audit(self, pages, status=200):
        """Serve pages by cursor, with None for the first page, through a patched urlopen."""
        urls = []

        def urlopen(request, timeout=None):
            urls.append(request.full_url)
            return FakeResponse(pages[parse_qs(urlsplit(request.full_url).query).get("cursor", [None])[0]], status)

        out, err = io.StringIO(), io.StringIO()
        with patch("urllib.request.urlopen", urlopen), contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(err):
            code = registry.main(["audit"])
        return code, out.getvalue(), err.getvalue(), [parse_qs(urlsplit(url).query) for url in urls]

    def test_audit_follows_every_page(self):
        code, out, _, queries = self.run_audit({
            None: listing("com.voiceflow/docs", cursor="c1"),
            "c1": listing("com.voiceflow/voiceflow", cursor="c2"),
            "c2": listing("com.voiceflow/docs")})
        self.assertEqual(code, 0)
        self.assertEqual(out.count("ok com.voiceflow/"), 3)
        self.assertIn("3 versions under com.voiceflow; 0 outside the allowlist", out)
        self.assertEqual(queries[0], {"search": ["com.voiceflow"], "include_deleted": ["true"], "limit": ["100"]})
        self.assertEqual([query.get("cursor") for query in queries], [None, ["c1"], ["c2"]])

    def test_audit_keeps_only_the_namespace(self):
        code, out, _, _ = self.run_audit({None: listing(
            "com.voiceflow/docs", "io.github.someone/com.voiceflow-tools", "com.voiceflowx/other")})
        self.assertEqual(code, 0)
        self.assertNotIn("io.github", out)
        self.assertNotIn("voiceflowx", out)
        self.assertIn("1 versions under com.voiceflow", out)

    def test_audit_fails_on_an_unexpected_name(self):
        code, out, _, _ = self.run_audit({None: listing(
            "com.voiceflow/docs", "com.voiceflow/evil", "com.voiceflow.labs/demo")})
        self.assertEqual(code, 1)
        self.assertIn("FAIL unexpected name com.voiceflow/evil 1.0.0 active", out)
        self.assertIn("FAIL unexpected name com.voiceflow.labs/demo 1.0.0 active", out)
        self.assertIn("2 outside the allowlist", out)

    def test_audit_stops_on_a_repeated_cursor(self):
        code, _, err, queries = self.run_audit({None: listing(cursor="c1"), "c1": listing(cursor="c1")})
        self.assertEqual((code, len(queries)), (1, 2))
        self.assertIn("same page cursor twice", err)

    def test_audit_stops_after_the_page_cap(self):
        pages = {None: listing(cursor="c1"), **{f"c{n}": listing(cursor=f"c{n + 1}") for n in range(1, 10)}}
        with patch.object(registry, "AUDIT_MAX_PAGES", 3):
            code, _, err, queries = self.run_audit(pages)
        self.assertEqual((code, len(queries)), (1, 3))
        self.assertIn("more than 3 pages", err)

    def test_audit_fails_on_an_http_error(self):
        code, _, err, _ = self.run_audit({None: {}}, status=500)
        self.assertEqual(code, 1)
        self.assertIn("registry list returned HTTP 500", err)


class StreamableHttpTests(NoNetwork):
    def test_sse_events_join_data_lines_and_skip_comments(self):
        lines = [": keep-alive\n", "event: message\r\n", "id: 7\n", "data: {\"a\":\n", "data:1}\n", "\n",
                 "event: ping\n", "\n", "data: {\"b\": 2}"]
        self.assertEqual(list(registry.sse_events(lines)), ['{"a":\n1}', '{"b": 2}'])

    def test_rpc_result_finds_the_matching_response(self):
        payloads = ['{"jsonrpc":"2.0","method":"notifications/message","params":{}}', "",
                    '{"jsonrpc":"2.0","id":2,"result":{"other":true}}',
                    '{"jsonrpc":"2.0","id":3,"result":{"content":[]}}']
        self.assertEqual(registry.rpc_result(payloads, 3), {"content": []})
        self.assertEqual(registry.rpc_result(['[{"jsonrpc":"2.0","id":1,"result":{"ok":1}}]'], 1), {"ok": 1})
        with self.assertRaisesRegex(registry.CheckError, "no JSON-RPC response to request 9"):
            registry.rpc_result(payloads, 9)
        with self.assertRaisesRegex(registry.CheckError, "JSON-RPC error -32602: bad"):
            registry.rpc_result(['{"jsonrpc":"2.0","id":1,"error":{"code":-32602,"message":"bad"}}'], 1)

    def test_sse_stream_feeds_rpc_result(self):
        stream = ["event: message\n", 'data: {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"x"}}\n', "\n"]
        self.assertEqual(registry.rpc_result(registry.sse_events(stream), 1), {"protocolVersion": "x"})

    def test_resource_metadata_url(self):
        quoted = 'Bearer error="invalid_token", resource_metadata="https://example.invalid/.well-known/x"'
        bare = "Bearer resource_metadata=https://example.invalid/meta, scope=\"a\""
        self.assertEqual(registry.resource_metadata_url(["Basic realm=x", quoted]),
                         "https://example.invalid/.well-known/x")
        self.assertEqual(registry.resource_metadata_url([bare]), "https://example.invalid/meta")
        self.assertIsNone(registry.resource_metadata_url(['Bearer realm="x"']))


if __name__ == "__main__":
    unittest.main()
