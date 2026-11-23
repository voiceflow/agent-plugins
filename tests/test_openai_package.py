import copy
import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
OPENAI = ROOT / "scripts/openai"
SURFACE = ROOT / "tests/fixtures/voiceflow-surface.json"

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

    def test_mcp_config_connects_only_the_plain_account_server(self):
        config = json.loads((OPENAI / "mcp.json").read_text(encoding="utf-8"))
        urls = [server["url"] for server in config["mcpServers"].values()]
        self.assertEqual(urls, ["https://mcp.voiceflow.com/mcp?version=3"])


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
