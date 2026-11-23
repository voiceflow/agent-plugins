import copy
import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
OPENAI = ROOT / "scripts/openai"
SURFACE = ROOT / "tests/fixtures/voiceflow-surface.json"
# Tools the account MCP lists whatever the toolsets value (realtime agent-tools-options.util.ts).
ALWAYS_LISTED = {"vf_describe_operations", "vf_search_operations", "vf_get_started", "vf_skill_list",
                 "vf_skill_load", "vf_docs_ask", "vf_docs_search", "vf_docs_read_page"}

spec = importlib.util.spec_from_file_location("package_tools", OPENAI / "package_tools.py")
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)


def review_report(openai, version):
    report = tools.Report()
    tools.check_review(openai, version, SURFACE, report)
    return report


class OpenAIReviewDataTest(unittest.TestCase):
    def setUp(self):
        self.review = json.loads((OPENAI / "review.json").read_text(encoding="utf-8"))
        self.version = self.review["package_version"]

    def test_review_cases_pass_and_name_only_served_tools(self):
        report = review_report(self.review, self.version)
        self.assertEqual(report.errors, [])
        self.assertEqual(report.blockers, [])

    def test_a_case_that_names_an_unserved_tool_fails(self):
        review = copy.deepcopy(self.review)
        review["review"]["test_cases"]["positive"][0]["tools_triggered"] = "vf_call_read_operation"
        report = review_report(review, self.version)
        self.assertTrue(any("vf_call_read_operation" in error for error in report.errors))

    def test_reviewer_credentials_are_refused(self):
        review = copy.deepcopy(self.review)
        review["review"]["test_credentials"] = {"email": "reviewer@example.com"}
        report = review_report(review, self.version)
        self.assertTrue(any("test_credentials" in error for error in report.errors))

    def test_release_notes_must_name_the_package_version(self):
        notes = self.review["publication"]["release_notes"]
        self.assertIn(self.version, notes)
        report = review_report(self.review, "9.9.9")
        self.assertTrue(any("9.9.9" in blocker for blocker in report.blockers))

    def test_mcp_config_connects_one_account_server_without_dynamic_mode(self):
        config = json.loads((OPENAI / "mcp.json").read_text(encoding="utf-8"))
        urls = [server["url"] for server in config["mcpServers"].values()]
        self.assertEqual(len(urls), 1)
        url = urlparse(urls[0])
        self.assertEqual((url.scheme, url.netloc, url.path), ("https", "mcp.voiceflow.com", "/mcp"))
        query = parse_qs(url.query)
        self.assertEqual(query["version"], ["3"])
        # OpenAI forbids a generic executor, and dynamic mode adds one.
        self.assertNotIn("dynamic", query)

    def test_every_case_tool_is_in_a_listed_toolset(self):
        # The desktop app hides tools past its budget, so the URL lists only some groups.
        # A case that names a tool outside them would fail for the reviewer.
        config = json.loads((OPENAI / "mcp.json").read_text(encoding="utf-8"))
        url = next(iter(config["mcpServers"].values()))["url"]
        toolsets = parse_qs(urlparse(url).query)["toolsets"][0].split(",")
        surface = json.loads(SURFACE.read_text(encoding="utf-8"))["mcp"]["tools"]
        group_of = {f"vf_{group.removeprefix('voiceflow_')}_{operation}": group.removeprefix("voiceflow_")
                    for group, operations in surface.items() for operation in operations}
        for group in toolsets:
            self.assertIn(f"voiceflow_{group}", surface)
        for case in self.review["review"]["test_cases"]["positive"]:
            for name in tools.VF_TOOL.findall(case["tools_triggered"]):
                if name in ALWAYS_LISTED:
                    continue
                self.assertIn(group_of.get(name), toolsets, f"{name} is outside the toolsets in mcp.json")


class OpenAIMergeTest(unittest.TestCase):
    def test_merge_sets_the_package_version_and_review_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            plugin = Path(folder, "plugin.json")
            plugin.write_text(json.dumps({"name": "voiceflow", "version": "1.0.0"}), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                tools.merge(str(plugin), str(OPENAI / "review.json"))
            merged = json.loads(plugin.read_text(encoding="utf-8"))
        review = json.loads((OPENAI / "review.json").read_text(encoding="utf-8"))
        self.assertEqual(merged["version"], review["package_version"])
        self.assertEqual(merged["extensions"]["com.openai"]["review"], review["review"])

    def test_merge_refuses_a_manifest_that_already_has_review_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            plugin = Path(folder, "plugin.json")
            plugin.write_text(json.dumps({"extensions": {"com.openai": {"review": {}}}}), encoding="utf-8")
            with self.assertRaises(SystemExit):
                tools.merge(str(plugin), str(OPENAI / "review.json"))


if __name__ == "__main__":
    unittest.main()
