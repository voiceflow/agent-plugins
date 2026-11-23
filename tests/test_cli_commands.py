import contextlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import cli_commands  # noqa: E402
import skill_references  # noqa: E402

SURFACE = {
    "schema": 1,
    "mcp": {
        "source": "voiceflow/cli v9.9.9 .speakeasy/out.openapi.yaml",
        "tools": {
            "voiceflow_agent": ["get", "update"],
            "voiceflow_environment": ["export"],
            "voiceflow_secret": ["create", "set_value"],
            "voiceflow_test": ["create_many_runs", "create_run", "get_run"],
        },
        "refused": {
            "voiceflow_secret.set_value": {"when": "always", "cli": "secret set-value", "guidance": "Use the UI."},
            "voiceflow_secret.create": {"when": "conditional", "cli": "secret create", "guidance": "No values.",
                                        "condition": "Only when the body carries a `defaultValue`."},
        },
    },
    "cli": {
        "version": "9.9.9",
        "source": "voiceflow/cli v9.9.9 .speakeasy/out.openapi.yaml",
        "commands": {
            "agent get": "voiceflow_agent.get",
            "agent update": "voiceflow_agent.update",
            "secret create": "voiceflow_secret.create",
            "secret set-value": "voiceflow_secret.set_value",
            "test run create": "voiceflow_test.create_run",
            "test run get": "voiceflow_test.get_run",
            "version": None,
        },
    },
    "docs_mcp": {"tools": []},
}


def surface(**changes):
    data = json.loads(json.dumps(SURFACE))
    for path, value in changes.items():
        section, key = path.split("__")
        data[section][key] = value
    return data


class PlanTests(unittest.TestCase):
    def test_each_served_tool_gets_its_command_and_refused_tools_are_kept_apart(self):
        rows, missing, conditional, user_only = cli_commands.plan(surface())
        self.assertEqual(rows, [("vf_agent_get", "agent get"), ("vf_agent_update", "agent update"),
                                ("vf_secret_create", "secret create"), ("vf_test_create_run", "test run create"),
                                ("vf_test_get_run", "test run get")])
        self.assertEqual(missing, [("vf_environment_export", None), ("vf_test_create_many_runs", "test run create")])
        self.assertEqual(conditional, [("vf_secret_create", "Only when the body carries a `defaultValue`.")])
        self.assertEqual(user_only, ["secret set-value"])

    def test_two_commands_for_one_operation_are_refused(self):
        commands = dict(SURFACE["cli"]["commands"], **{"agent read": "voiceflow_agent.get"})
        with self.assertRaisesRegex(ValueError, "voiceflow_agent.get"):
            cli_commands.plan(surface(cli__commands=commands))

    def test_a_batch_create_maps_to_the_single_create(self):
        cases = {"voiceflow_tool.create_many": "voiceflow_tool.create",
                 "voiceflow_test.create_many_runs": "voiceflow_test.create_run",
                 "voiceflow_function.create_many_variables": "voiceflow_function.create_variable",
                 "voiceflow_tool.create_manyx": None, "voiceflow_tool.get": None}
        for slug, expected in cases.items():
            with self.subTest(slug=slug):
                self.assertEqual(cli_commands.single_create(slug), expected)


class RenderTests(unittest.TestCase):
    def test_render_is_stable_and_lists_every_section(self):
        text = cli_commands.render(surface())
        self.assertEqual(text, cli_commands.render(surface()))
        self.assertTrue(text.endswith("\n") and not text.endswith("\n\n"))
        self.assertIn("The table matches CLI 9.9.9 and the MCP tools of the same release.", text)
        self.assertIn("| `vf_agent_get` | `vf agent get` |", text)
        self.assertIn("| `vf_test_create_many_runs` | `vf test run create`, once per item |", text)
        self.assertIn("| `vf_environment_export` | No CLI command |", text)
        self.assertIn("| `vf_secret_create` | Only when the body carries a `defaultValue`. |", text)
        self.assertIn("- `vf secret set-value`", text)
        self.assertNotIn("`vf_secret_set_value`", text)

    def test_a_different_mcp_release_is_named(self):
        mcp = dict(SURFACE["mcp"], source="voiceflow/cli v9.8.0 .speakeasy/out.openapi.yaml")
        text = cli_commands.render(surface(mcp__source=mcp["source"]))
        self.assertIn("The table matches CLI 9.9.9 and the MCP tools of the CLI 9.8.0 release.", text)

    def test_cell_text_stays_on_one_line_and_inside_its_cell(self):
        refused = dict(SURFACE["mcp"]["refused"])
        refused["voiceflow_secret.create"] = dict(refused["voiceflow_secret.create"],
                                                  condition="A value | or\n  a header.")
        text = cli_commands.render(surface(mcp__refused=refused))
        self.assertIn("| `vf_secret_create` | A value \\| or a header. |", text)

    def test_empty_sections_are_left_out(self):
        tools = {"voiceflow_agent": ["get", "update"]}
        text = cli_commands.render(surface(mcp__tools=tools, mcp__refused={}))
        for heading in ("## Tools with no CLI command", "## Tools the MCP refuses in some cases",
                        "## Commands only the user runs"):
            self.assertNotIn(heading, text)


class DriftTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        fixture = self.root / skill_references.SURFACE
        fixture.parent.mkdir(parents=True)
        fixture.write_text(json.dumps(SURFACE), encoding="utf-8")
        self.output = self.root / cli_commands.OUTPUT

    def run_main(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = cli_commands.main(list(args), root=self.root)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_check_reports_a_missing_table_and_writes_nothing(self):
        code, _, stderr = self.run_main("--check")
        self.assertEqual(code, 1)
        self.assertIn("missing; run python3 scripts/cli_commands.py", stderr)
        self.assertFalse(self.output.exists())

    def test_a_run_writes_the_table_and_a_second_run_changes_nothing(self):
        self.assertEqual(self.run_main()[0], 0)
        self.assertEqual(self.output.read_text(encoding="utf-8"), cli_commands.render(SURFACE))
        code, stdout, _ = self.run_main()
        self.assertEqual(code, 0)
        self.assertIn("already up to date", stdout)
        self.assertEqual(self.run_main("--check")[0], 0)
        self.assertEqual(cli_commands.drift_problems(self.root), [])

    def test_a_hand_edit_is_drift(self):
        self.run_main()
        self.output.write_text(self.output.read_text(encoding="utf-8").replace("agent get", "agent read"),
                               encoding="utf-8")
        problems = cli_commands.drift_problems(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("differs from tests/fixtures/voiceflow-surface.json", problems[0])
        self.assertEqual(self.run_main("--check")[0], 1)

    def test_a_changed_snapshot_is_drift(self):
        self.run_main()
        commands = dict(SURFACE["cli"]["commands"], **{"agent get": None, "agent show": "voiceflow_agent.get"})
        (self.root / skill_references.SURFACE).write_text(json.dumps(surface(cli__commands=commands)),
                                                          encoding="utf-8")
        self.assertEqual(len(cli_commands.drift_problems(self.root)), 1)


class ValidateTests(unittest.TestCase):
    def test_validate_fails_when_the_committed_table_differs_from_the_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            for folder in ("voiceflow", "scripts", "tests/fixtures", "docs", "evals",
                           ".claude-plugin", ".cursor-plugin", ".agents", "mcp-registry"):
                shutil.copytree(ROOT / folder, root / folder, ignore=shutil.ignore_patterns("__pycache__"))
            for document in [*ROOT.glob("*.md"), ROOT / "LICENSE", ROOT / "skills.sh.json",
                             ROOT / "package-files.txt"]:
                shutil.copyfile(document, root / document.name)
            table = root / cli_commands.OUTPUT
            # A row with real names, so only the generated-table check can catch it. The sync keeps the copies equal.
            text = table.read_text(encoding="utf-8").replace(
                "| `vf_agent_get` | `vf agent get` |\n", "| `vf_agent_get` | `vf agent get` |\n" * 2, 1)
            table.write_text(text, encoding="utf-8")
            run = dict(cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=60)
            sync = subprocess.run([sys.executable, str(root / "scripts/sync_shared_references.py")], **run)
            self.assertEqual(sync.returncode, 0, sync.stderr)
            result = subprocess.run([sys.executable, str(root / "scripts/validate.py")], **run)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertEqual(result.stderr.splitlines(), [
                f"{cli_commands.OUTPUT.as_posix()}: differs from tests/fixtures/voiceflow-surface.json; "
                f"run {cli_commands.COMMAND}, then {cli_commands.SYNC}"])


class CommittedTableTests(unittest.TestCase):
    def test_committed_table_matches_the_snapshot(self):
        self.assertEqual(cli_commands.drift_problems(ROOT), [])

    def test_every_served_operation_has_exactly_one_row(self):
        current = skill_references.load_surface(ROOT)
        text = (ROOT / cli_commands.OUTPUT).read_text(encoding="utf-8")
        # The command table and the no-command table; the refusal table repeats some tools on purpose.
        tables = text.partition("## Tools the MCP refuses in some cases")[0]
        listed = re.findall(r"^\| `(vf_[a-z0-9_]+)` \|", tables, re.M)
        served = skill_references.v3_names(current) - skill_references.V3_META_TOOLS
        self.assertEqual(len(listed), len(set(listed)))
        self.assertEqual(set(listed), served)


if __name__ == "__main__":
    unittest.main()
