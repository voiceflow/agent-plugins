"""Verify fixture boundaries; these checks do not grade model behavior."""
import json
from pathlib import Path
import tempfile
import unittest

from scripts import chat_eval as harness


class ChatHarnessTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.session = Path(scratch.name) / "session"

    def start(self, case):
        return harness.start(case, self.session)

    def step(self, tool, **arguments):
        return harness.step(self.session, {"tool": tool, "arguments": arguments})

    def read_account(self):
        self.step("discover_tools")
        return self.step("call_tool", name="vf_project_list", arguments={})

    def read_docs(self, question):
        return self.step("call_tool", name="voiceflow_docs.lookup", arguments={
            "question": question, "initiator": "agent", "purpose": "answers",
            "why": "vf-agent-plugin/1.0.0 skill=voiceflow-setup stage=setup"})

    def test_undeclared_tools_are_rejected_and_recorded(self):
        self.start("chat-unsupported")
        response = self.step("connect_server", url=harness.ACCOUNT,
                             transport="streamable-http", auth="oauth")
        self.assertIn("error", response)
        state = harness.load(self.session)
        self.assertFalse(state["connected"])
        self.assertEqual(len(state["violations"]), 1)

    def test_live_read_requires_sign_in_and_rediscovery(self):
        self.start("chat-connect")
        self.step("discover_tools")
        result = self.step("connect_server", url=harness.ACCOUNT,
                           transport="streamable-http", auth="oauth")
        self.assertFalse(harness.load(self.session)["verified"])
        self.step("ask_user", message="Please sign in: " + result["authorization_url"])
        self.assertFalse(harness.load(self.session)["verified"])
        rejected = self.step("call_tool", name="vf_project_list", arguments={})
        self.assertIn("error", rejected)
        self.assertEqual(self.read_account()["projects"], [])
        self.assertTrue(harness.load(self.session)["verified"])

    def test_public_guidance_does_not_verify_account(self):
        self.start("chat-knowledge-only")
        self.step("discover_tools")
        self.read_docs("How does Voiceflow work?")
        harness.finish(self.session, "Ready", "ready")
        state = harness.load(self.session)
        self.assertTrue(state["guidance_reads"])
        self.assertFalse(state["verified"])
        self.assertTrue(state["violations"])

    def test_docs_connection_needs_no_oauth_but_requires_read_verification(self):
        self.start("chat-add-docs")
        self.read_account()
        result = self.step("connect_server", url=harness.DOCS,
                           transport="streamable-http", auth="none")
        self.assertEqual(result["status"], "connected")
        state = harness.load(self.session)
        self.assertTrue(state["verified"])
        self.assertFalse(state["pending_auth"])
        self.assertFalse(state["docs_verified"])
        self.assertNotIn("authorization_url", result)
        self.step("discover_tools")
        self.read_docs("How do draft and live environments differ?")
        harness.finish(self.session, "Ready", "ready")
        state = harness.load(self.session)
        self.assertTrue(state["docs_verified"])
        self.assertEqual(state["violations"], [])

    def test_docs_oauth_and_duplicate_connections_are_rejected(self):
        self.start("chat-add-docs")
        result = self.step("connect_server", url=harness.DOCS,
                           transport="streamable-http", auth="oauth")
        self.assertIn("error", result)
        self.assertFalse(harness.load(self.session)["pending_auth"])
        self.step("connect_server", url=harness.DOCS,
                  transport="streamable-http", auth="none")
        result = self.step("connect_server", url=harness.DOCS,
                           transport="streamable-http", auth="none")
        self.assertIn("error", result)

    def test_package_version_can_be_read_in_chat_without_filesystem(self):
        self.start("chat-existing")
        url = harness.BASE + "voiceflow/skills/voiceflow/references/documentation.md"
        result = self.step("read_document", url=url)
        source = harness.ROOT / "voiceflow/plugin.json"
        metadata = dict(line.split(": ", 1) for line in result["text"].split("---", 2)[1].strip().splitlines())
        self.assertEqual(metadata["version"], json.loads(source.read_text())["version"])

    def test_docs_missing_context_is_rejected_without_verification(self):
        self.start("chat-existing")
        self.step("discover_tools")
        for arguments in (
            {"question": "How do drafts work?"},
            {"question": "How do drafts work?", "initiator": [], "purpose": "answers", "why": "Check drafts"},
            {"question": "How do drafts work?", "initiator": "agent", "purpose": "answers", "why": ""},
        ):
            result = self.step("call_tool", name="voiceflow_docs.lookup", arguments=arguments)
            self.assertIn("error", result)
            self.assertFalse(harness.load(self.session)["docs_verified"])

    def test_readable_skills_and_connected_docs_do_not_replace_docs_read(self):
        self.start("chat-add-docs")
        self.read_account()
        for relative in ("voiceflow/SKILL.md", "voiceflow/references/operations.md"):
            self.step("read_document", url=harness.BASE + "voiceflow/skills/" + relative)
        self.step("connect_server", url=harness.DOCS,
                  transport="streamable-http", auth="none")
        harness.finish(self.session, "Ready", "ready")
        self.assertTrue(harness.load(self.session)["violations"])

    def test_web_fallback_can_verify_docs_without_claiming_mcp(self):
        self.start("chat-docs-fallback")
        self.read_account()
        for relative in ("voiceflow/SKILL.md", "voiceflow/references/operations.md"):
            self.step("read_document", url=harness.BASE + "voiceflow/skills/" + relative)
        self.step("read_document", url="https://www.voiceflow.com/docs/mcp/knowledge")
        harness.finish(self.session, "Ready using web docs; docs MCP unavailable", "ready")
        state = harness.load(self.session)
        self.assertTrue(state["docs_fallback_verified"])
        self.assertFalse(state["docs_connected"])
        self.assertFalse(state["docs_verified"])
        self.assertEqual(state["violations"], [])

    def test_manual_settings_can_connect_both_servers_without_verifying_either(self):
        self.start("chat-manual")
        self.step("ask_user", message="Add " + harness.ACCOUNT + " and " + harness.DOCS + " in " + harness.SETTINGS)
        state = harness.load(self.session)
        self.assertTrue(state["connected"])
        self.assertTrue(state["docs_connected"])
        self.assertFalse(state["verified"])
        self.assertFalse(state["docs_verified"])
        tools = self.step("discover_tools")["tools"]
        self.assertEqual({t["name"] for t in tools}, {"vf_project_list", "voiceflow_docs.lookup"})

    def test_document_fragment_resolves_to_the_same_snapshot(self):
        self.start("chat-existing")
        url = harness.BASE + "voiceflow/skills/voiceflow-setup/references/mcp.md"
        whole = self.step("read_document", url=url)
        section = self.step("read_document", url=url + "#guidance-without-a-filesystem")
        self.assertEqual(whole, section)

    def test_blank_and_forbidden_responses_never_verify(self):
        for case in ("chat-malformed", "chat-forbidden"):
            with self.subTest(case=case):
                session = self.session.parent / case
                harness.start(case, session)
                harness.step(session, {"tool": "discover_tools", "arguments": {}})
                harness.step(session, {"tool": "call_tool", "arguments": {
                    "name": "vf_project_list", "arguments": {}}})
                self.assertFalse(harness.load(session)["verified"])

    def test_new_chat_requirement_is_not_a_connected_badge(self):
        self.start("chat-reload")
        self.step("ask_user", message=harness.SETTINGS + " " + harness.ACCOUNT)
        self.assertEqual(self.step("discover_tools")["tools"], [])
        self.assertFalse(harness.load(self.session)["verified"])

    def test_account_without_guidance_cannot_claim_ready(self):
        self.start("chat-no-guidance")
        self.read_account()
        response = self.step("read_document", url=harness.BASE + "voiceflow/skills/voiceflow/SKILL.md")
        self.assertEqual(response["status"], 403)
        harness.finish(self.session, "Ready", "ready")
        state = harness.load(self.session)
        self.assertTrue(state["verified"])
        self.assertFalse(state["guidance_reads"])
        self.assertTrue(state["violations"])

    def test_partial_package_guidance_cannot_claim_ready(self):
        self.start("chat-existing")
        self.read_account()
        self.step("read_document", url=harness.BASE + "voiceflow/skills/voiceflow/SKILL.md")
        harness.finish(self.session, "Ready", "ready")
        self.assertTrue(harness.load(self.session)["violations"])

    def test_source_is_snapshotted_and_completed_session_is_immutable(self):
        self.start("chat-existing")
        url = harness.BASE + "setup.md"
        state = harness.load(self.session)
        response = self.step("read_document", url=url)
        self.assertEqual(harness.digest(response["text"]), state["sourceSHA256"][url])
        harness.finish(self.session, "Pending", "blocked")
        with self.assertRaisesRegex(ValueError, "already finished"):
            self.step("inspect_host")
        with self.assertRaisesRegex(ValueError, "already finished"):
            harness.finish(self.session, "Changed answer", "ready")


if __name__ == "__main__":
    unittest.main()
