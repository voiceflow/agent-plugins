import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("refresh_surface", ROOT / "scripts/refresh_surface.py")
refresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refresh)

SPEC = """openapi: 3.0.0
paths:
  /v2/stable/agent:
    parameters:
      - name: ignored
    get:
      operationId: AgentController_get
      x-vf:
        mcp:
          tool: voiceflow_agent
          toolDescription: |-
            The agent: one per project.
            ## Not a key: still description
              indented: also description
          operation: get
          operationDescription: >-
            Read the agent
            in one call.
        cli:
          command: agent get
      summary: Get agent
      parameters:
        - name: projectID
          in: query
          schema: { type: string }
      responses:
        "200":
          description: OK
    patch:
      operationId: AgentController_update
      x-vf:
        mcp:
          tool: voiceflow_agent
          operation: update
        cli:
          command: agent update
  '/v2/stable/secret/{secretID}/value':
    put:
      operationId: SecretController_setValue
      x-vf:
        mcp:
          tool: voiceflow_secret
          operation: set_value
        cli:
          command: secret set-value
      x-vf-client-restriction:
        deniedClientTypes:
          - mcp
        guidance: Secret values cannot be set from an MCP client. Set the value in the UI.
  /v2/stable/secret:
    post:
      operationId: SecretController_create
      x-vf:
        mcp:
          tool: voiceflow_secret
          operation: create
        cli:
          command: secret create
      x-vf-client-restriction:
        deniedClientTypes: [mcp]
        guidance: 'A secret value cannot be set: create it without `defaultValue`, it''s fine.'
        condition: "Only when the body carries a non-empty \\"defaultValue\\"."
  /v2/stable/transcript-property:
    get:
      operationId: TranscriptPropertyController_list
      x-vf:
        mcp:
          tool: voiceflow_transcript_property
          operation: list
        cli:
          command: transcript-property list
      x-vf-client-restriction:
        deniedClientTypes:
        - sdk
        guidance: Not for this client.
  /v2/stable/cli-only:
    get:
      operationId: CliOnlyController_get
      x-vf:
        cli:
          command: cli-only get
  /v2/stable/agent/export:
    get:
      operationId: AgentController_export
      x-vf:
        mcp:
          tool: voiceflow_agent
          operation: export
        cli:
          command: agent export
      x-speakeasy-ignore: true
info:
  title: Synthetic
"""

WORKFLOW = """workflowVersion: 1.0.0
sources:
    Voiceflow:
        inputs:
            - location: ./openapi.stable.json
        transformations:
            - filterOperations:
                operations: AgentController_update, SecretController_create
                exclude: true
            - cleanup:
                enabled: true
        output: .speakeasy/out.openapi.yaml
"""


class ParseBlockTests(unittest.TestCase):
    def test_scalars_sequences_and_block_text(self):
        block = refresh.parse_block([
            "x-vf:",
            "  plain: a value",
            "    that folds",
            "  single: 'it''s: quoted'",
            "  double: \"line\\nnext \\u00e9\"",
            "  multi: 'first",
            "    second'",
            "  literal: |",
            "    one",
            "      two",
            "",
            "  folded: >-",
            "    one",
            "    two",
            "  empty: {}",
            "  flow: [mcp, 'sdk']",
            "  list:",
            "  - one",
            "  - 'two: three'",
            "  comment: value # trailing note",
        ])["x-vf"]
        self.assertEqual(block["plain"], "a value that folds")
        self.assertEqual(block["single"], "it's: quoted")
        self.assertEqual(block["double"], "line\nnext \u00e9")
        self.assertEqual(block["multi"], "first second")
        self.assertEqual(block["literal"], "one\n  two\n")
        self.assertEqual(block["folded"], "one two")
        self.assertEqual(block["empty"], {})
        self.assertEqual(block["flow"], ["mcp", "sdk"])
        self.assertEqual(block["list"], ["one", "two: three"])
        self.assertEqual(block["comment"], "value")

    def test_unsupported_shapes_fail_loudly(self):
        for lines in (["a: {b: c}"], ["a:", "  - b: c"], ["a: 'open"], ["a: b", "a: c"],
                      ["a: [b,", "  c]"], ["\ta: b"]):
            with self.subTest(lines=lines), self.assertRaises(refresh.SpecError):
                refresh.parse_block(lines)


class SurfaceTests(unittest.TestCase):
    def test_operations_read_only_the_wanted_blocks(self):
        operations = list(refresh.operations(SPEC))
        self.assertEqual([op["operationId"] for op in operations], [
            "AgentController_get", "AgentController_update", "SecretController_setValue",
            "SecretController_create", "TranscriptPropertyController_list", "CliOnlyController_get",
            "AgentController_export"])
        self.assertTrue(operations[0]["x-vf"]["mcp"]["toolDescription"].startswith("The agent"))
        self.assertEqual(operations[0]["x-vf"]["mcp"]["operationDescription"], "Read the agent in one call.")
        self.assertNotIn("summary", operations[0])

    def test_surface_marks_always_and_conditional_refusals(self):
        surface = refresh.build_surface(SPEC, "v9.9.9", SPEC, "v1.2.3")
        self.assertEqual(surface["mcp"]["tools"], {
            "voiceflow_agent": ["export", "get", "update"], "voiceflow_secret": ["create", "set_value"],
            "voiceflow_transcript_property": ["list"]})
        refused = surface["mcp"]["refused"]
        self.assertEqual(refused["voiceflow_secret.set_value"], {
            "when": "always", "cli": "secret set-value",
            "guidance": "Secret values cannot be set from an MCP client. Set the value in the UI."})
        self.assertEqual(refused["voiceflow_secret.create"]["when"], "conditional")
        self.assertEqual(refused["voiceflow_secret.create"]["condition"],
                         'Only when the body carries a non-empty "defaultValue".')
        self.assertEqual(refused["voiceflow_secret.create"]["guidance"],
                         "A secret value cannot be set: create it without `defaultValue`, it's fine.")
        self.assertNotIn("voiceflow_transcript_property.list", refused)
        self.assertEqual(surface["mcp"]["source"], "voiceflow/cli v9.9.9 .speakeasy/out.openapi.yaml")
        self.assertEqual(surface["cli"]["version"], "1.2.3")
        commands = surface["cli"]["commands"]
        self.assertEqual(commands["agent get"], "voiceflow_agent.get")
        self.assertIsNone(commands["cli-only get"])
        self.assertNotIn("agent export", commands)
        for command in refresh.HAND_WRITTEN_COMMANDS:
            self.assertIsNone(commands[command])
        self.assertEqual(surface["docs_mcp"]["tools"], sorted(refresh.DOCS_MCP_TOOLS))

    def test_workflow_filters_drop_cli_commands_but_not_mcp_operations(self):
        self.assertEqual(refresh.operation_filters(WORKFLOW),
                         [({"AgentController_update", "SecretController_create"}, True)])
        surface = refresh.build_surface(SPEC, "v9.9.9", SPEC, "v1.2.3", WORKFLOW)
        self.assertNotIn("agent update", surface["cli"]["commands"])
        self.assertNotIn("secret create", surface["cli"]["commands"])
        self.assertIn("agent get", surface["cli"]["commands"])
        self.assertIn("update", surface["mcp"]["tools"]["voiceflow_agent"])
        include_only = ("sources:\n  Voiceflow:\n    transformations:\n      - filterOperations:\n"
                        "          operations:\n            - AgentController_get\n          include: true\n")
        commands = refresh.build_surface(SPEC, "v9.9.9", SPEC, "v1.2.3", include_only)["cli"]["commands"]
        self.assertEqual(set(commands) - set(refresh.HAND_WRITTEN_COMMANDS), {"agent get"})

    def test_render_is_sorted_and_stable(self):
        surface = refresh.build_surface(SPEC, "v9.9.9", SPEC, "v1.2.3")
        rendered = refresh.render(surface)
        self.assertEqual(rendered, refresh.render(json.loads(rendered)))
        self.assertTrue(rendered.endswith("}\n"))
        self.assertLess(rendered.index('"cli"'), rendered.index('"docs_mcp"'))

    def test_duplicate_commands_and_empty_specs_are_rejected(self):
        with self.assertRaisesRegex(refresh.SpecError, "Duplicate CLI command"):
            refresh.build_surface(SPEC, "v1.0.0", SPEC.replace("command: agent update", "command: agent get"), "v1.0.0")
        with self.assertRaisesRegex(refresh.SpecError, "no tools"):
            refresh.build_surface("paths:\ninfo:\n", "v1.0.0", SPEC, "v1.0.0")
        with self.assertRaises(refresh.SpecError):
            list(refresh.operations("openapi: 3.0.0\n"))

    def test_local_specs_write_the_snapshot_without_network(self):
        with tempfile.TemporaryDirectory() as temporary:
            spec_path = Path(temporary) / "spec.yaml"
            spec_path.write_text(SPEC, encoding="utf-8")
            workflow_path = Path(temporary) / "workflow.yaml"
            workflow_path.write_text(WORKFLOW, encoding="utf-8")
            output = Path(temporary) / "nested" / "surface.json"
            command = [sys.executable, str(ROOT / "scripts/refresh_surface.py"), "--mcp-ref", "v9.9.9",
                       "--mcp-spec", str(spec_path), "--cli-ref", "v1.2.3", "--cli-spec", str(spec_path),
                       "--cli-workflow", str(workflow_path), "--output", str(output)]
            result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            first = output.read_bytes()
            subprocess.run(command, capture_output=True, timeout=30, check=True)
            self.assertEqual(output.read_bytes(), first)
            self.assertEqual(json.loads(first)["cli"]["version"], "1.2.3")
            self.assertNotIn("agent update", json.loads(first)["cli"]["commands"])
            unlabeled = subprocess.run(command[:2] + ["--mcp-spec", str(spec_path)],
                                       capture_output=True, text=True, encoding="utf-8", timeout=30)
            self.assertEqual(unlabeled.returncode, 2)
            self.assertIn("--mcp-ref", unlabeled.stderr)

    def test_committed_snapshot_is_canonical(self):
        path = ROOT / "tests/fixtures/voiceflow-surface.json"
        surface = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(path.read_bytes().decode("utf-8"), refresh.render(surface))
        self.assertEqual(surface["schema"], 1)
        self.assertEqual(surface["cli"]["version"],
                         (ROOT / "voiceflow/skills/voiceflow-setup/scripts/cli-version.txt")
                         .read_text(encoding="utf-8").strip())
        for command in refresh.HAND_WRITTEN_COMMANDS:
            self.assertIsNone(surface["cli"]["commands"][command])
        for reference, refusal in surface["mcp"]["refused"].items():
            tool, operation = reference.split(".")
            self.assertIn(operation, surface["mcp"]["tools"][tool])
            self.assertIn(refusal["when"], ("always", "conditional"))


if __name__ == "__main__":
    unittest.main()
