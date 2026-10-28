import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import skill_references as references  # noqa: E402
import verify_cli  # noqa: E402

SURFACE = {
    "schema": 1,
    "mcp": {
        "source": "synthetic",
        "tools": {"voiceflow_agent": ["get", "update"], "voiceflow_secret": ["create", "set_value"],
                  "voiceflow_transcript": ["get"], "voiceflow_transcript_property": ["list"]},
        "refused": {
            "voiceflow_secret.set_value": {"when": "always", "cli": "secret set-value", "guidance": "Use the CLI."},
            "voiceflow_secret.create": {"when": "conditional", "cli": "secret create", "guidance": "No value."},
        },
    },
    "cli": {"version": "0.0.1", "source": "synthetic", "commands": {
        "agent get": "voiceflow_agent.get", "secret set-value": "voiceflow_secret.set_value",
        "auth login": None, "docs search": None, "version": None}},
    "docs_mcp": {"tools": ["ask_voiceflow", "read_voiceflow_page"]},
}


class SkillTree:
    def __init__(self, test):
        scratch = tempfile.TemporaryDirectory()
        test.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        self.skills = self.root / "voiceflow/skills"
        for name in ("voiceflow-build", "voiceflow-knowledge"):
            self.write(f"{name}/SKILL.md", "# Skill\n")

    def write(self, name, text):
        path = self.skills / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def check(self, name, text):
        self.write(name, text)
        return references.Checker(self.root, SURFACE).check()


class ParserTests(unittest.TestCase):
    def test_fences_continuations_and_headings(self):
        prose, fenced, headings = references.parse(
            "# Title\n\nText `a`\nmore\n\n   ```sh\nvf agent get \\\n  --project-id P\n# not a heading\n"
            "~~~\n```\n\n~~~~ps1\nvf version `\n  -o json\n~~~~\n## Next\n")
        self.assertEqual(prose, [(1, "# Title"), (3, "Text `a`\nmore"), (17, "## Next")])
        self.assertEqual(fenced, [(7, "vf agent get --project-id P"), (9, "# not a heading"), (10, "~~~"),
                                  (14, "vf version -o json")])
        self.assertEqual(headings, ["Title", "Next"])

    def test_code_spans_follow_commonmark_pairing(self):
        spans = [content for _, _, content in references.code_spans(
            "a `one`, ``two ` tick``, `` `x` ``, \\`not, `multi\nline` and `open")]
        self.assertEqual(spans, ["one", "two ` tick", "`x`", "multi line"])

    def test_cli_invocations_stop_at_arguments(self):
        cases = {
            "vf agent get --project-id <id> -o json": [("agent get", ["--project-id", "-o"])],
            "$ vf docs search \"how to\" --output-format=json": [("docs search", ["--output-format"])],
            "vf secret set-value --value \"$VALUE\" | jq . && vf version": [
                ("secret set-value", ["--value"]), ("version", [])],
            "vf <resource> <operation> --help": [("", ["--help"])],
            "vf widget get --project-id PROJECT_ID < patch.json": [("widget get", ["--project-id"])],
            "vf docs search '--not-a-flag inside quotes'": [("docs search", [])],
            "echo vf agent get": [],
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(list(references.cli_invocations(text)), expected)

    def test_slugs_follow_github_rules(self):
        self.assertEqual(references.slug("3. Make guidance available in this host"),
                         "3-make-guidance-available-in-this-host")
        self.assertEqual(references.slug("Use `vf` — the **CLI** [here](x.md)!"), "use-vf--the-cli-here")
        self.assertEqual(references.slug("snake_case and Ünïcode"), "snake_case-and-ünïcode")
        found = references.anchors("# Setup\n## Setup\n## Setup\n```\n# Fenced\n```\n<a id=\"custom\"></a>\n")
        self.assertEqual(found, {"setup", "setup-1", "setup-2", "custom"})


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.tree = SkillTree(self)

    def assertProblems(self, text, expected, name="voiceflow-build/SKILL.md"):
        self.assertEqual(self.tree.check(name, text), [f"voiceflow/skills/{name}:{line}: {reason}"
                                                       for line, reason in expected])

    def test_clean_references_pass(self):
        self.tree.write("voiceflow-build/references/shapes.md", "# Shapes\n## Agent body\n")
        self.assertProblems(
            "# Build\n\nCall `voiceflow_agent.get`, then MCP `voiceflow_agent` `update`,\n"
            "`voiceflow_transcript_property` / `list`, or `voiceflow_secret.create`.\n"
            "Docs: `ask_voiceflow` on `voiceflow-knowledge`. See `voiceflow-build`.\n"
            "Read `references/shapes.md` and [the body](references/shapes.md#agent-body),\n"
            "[top](#build), [site](https://example.com/x.md#y).\n"
            "Run `vf agent get -o json`, `vf auth login --help`, or CLI `secret set-value`.\n"
            "Groups work too: `vf agent --help`.\n\n```sh\nvf docs search \"agents\"\n```\n", [])

    def test_unknown_mcp_tool_and_operation(self):
        self.assertProblems(
            "Use `voiceflow_robot` and `voiceflow_agent.delete`.\nThen MCP `voiceflow_agent`\n`remove`.\n",
            [(1, "unknown MCP tool \"voiceflow_robot\""),
             (1, "unknown MCP operation \"voiceflow_agent.delete\""),
             (2, "unknown MCP operation \"voiceflow_agent.remove\"")])

    def test_always_refused_operation_names_the_cli_instead(self):
        self.assertProblems(
            "Never `voiceflow_secret.set_value`.\nAlso `voiceflow_secret` `set_value`.\n",
            [(1, "MCP always refuses \"voiceflow_secret.set_value\"; name the CLI command "
                 "\"vf secret set-value\" instead"),
             (2, "MCP always refuses \"voiceflow_secret.set_value\"; name the CLI command "
                 "\"vf secret set-value\" instead")])

    def test_unknown_cli_command_in_spans_and_fences(self):
        self.assertProblems(
            "Run `vf agent frob --x` or CLI `agent remove`.\n\n```bash\nvf secret show \\\n  --id 1\n"
            "echo ok && vf versions\n```\n",
            [(1, "unknown CLI command \"vf agent frob\""), (1, "unknown CLI command \"vf agent remove\""),
             (4, "unknown CLI command \"vf secret show\""), (6, "unknown CLI command \"vf versions\"")])

    def test_links_and_anchors(self):
        self.tree.write("voiceflow-build/references/shapes.md", "# Shapes\n")
        self.assertProblems(
            "# Here\n[a](missing.md) [b](references/shapes.md#nope) [c](#gone)\n"
            "[d](../../../outside.md) `[e](missing.md)`\n\n```\n[f](missing.md)\n```\n",
            [(2, "missing link target \"missing.md\""),
             (2, "missing anchor \"#nope\" in voiceflow/skills/voiceflow-build/references/shapes.md"),
             (2, "missing anchor \"#gone\" in voiceflow/skills/voiceflow-build/SKILL.md"),
             (3, "link leaves the plugin \"../../../outside.md\"")])

    def test_unknown_skill_name(self):
        self.assertProblems(
            "Use `voiceflow-buidl`, not `voiceflow-build` or `voiceflow-knowledge`.\n"
            "Read the `voiceflow-routing` skill, or skill `voiceflow-wiring`.\n",
            [(1, "unknown skill \"voiceflow-buidl\""), (2, "unknown skill \"voiceflow-routing\""),
             (2, "unknown skill \"voiceflow-wiring\"")])

    def test_values_shaped_like_skill_names_pass(self):
        self.assertProblems(
            "Set the phone provider to `voiceflow-telnyx` or `voiceflow-twilio`.\n"
            "Pick `voiceflow-plugins`; skills stay unchanged.\n", [])

    def test_backticked_markdown_paths_resolve_from_folder_or_skill_root(self):
        self.tree.write("voiceflow-build/references/shapes.md", "# Shapes\n")
        self.assertProblems(
            "From the reference: `shapes.md`, `../SKILL.md`, `references/shapes.md`, `references/gone.md`.\n",
            [(1, "missing file \"references/gone.md\"")], name="voiceflow-build/references/notes.md")

    def test_internal_names_are_denied(self):
        self.assertProblems(
            "Call `vf_agent_get` or describe_operations.\nAtlas uses GLM in Safe mode.\n\n"
            "```\nautonomous mode\n```\nAn atlas of maps and request_secrets stay public.\n",
            [(1, "internal name \"vf_agent_get\" is not public"),
             (1, "internal name \"describe_operations\" is not public"),
             (2, "internal name \"Atlas\" is not public"), (2, "internal name \"GLM\" is not public"),
             (2, "internal name \"Safe mode\" is not public"),
             (5, "internal name \"autonomous mode\" is not public")])


class ValidateOutputTests(unittest.TestCase):
    def test_validate_lists_every_problem_and_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            for folder in ("voiceflow", "scripts", "tests/fixtures", "docs", "evals",
                           ".claude-plugin", ".cursor-plugin", ".agents"):
                shutil.copytree(ROOT / folder, root / folder, ignore=shutil.ignore_patterns("__pycache__"))
            for document in [*ROOT.glob("*.md"), ROOT / "LICENSE"]:
                shutil.copyfile(document, root / document.name)
            skill = root / "voiceflow/skills/voiceflow-build/SKILL.md"
            lines = skill.read_text(encoding="utf-8").splitlines()
            lines[-1] += " Use `voiceflow_robot.get` and `vf robot run`."
            skill.write_text("\n".join(lines) + "\n", encoding="utf-8")
            result = subprocess.run([sys.executable, str(root / "scripts/validate.py")], cwd=root,
                                    capture_output=True, text=True, encoding="utf-8", timeout=60)
            self.assertEqual(result.returncode, 1, result.stdout)
            label = f"voiceflow/skills/voiceflow-build/SKILL.md:{len(lines)}"
            self.assertEqual(result.stderr.splitlines(), [
                f"{label}: unknown MCP tool \"voiceflow_robot\"", f"{label}: unknown CLI command \"vf robot run\""])


class VerifyCliTests(unittest.TestCase):
    def test_skill_commands_and_flags_are_checked_against_help(self):
        tree = SkillTree(self)
        (tree.root / "tests/fixtures").mkdir(parents=True)
        (tree.root / references.SURFACE).write_text(json.dumps(SURFACE), encoding="utf-8")
        tree.write("voiceflow-build/references/cli.md",
                   "Run `vf agent get -p P --environment-alias E -o json`, `vf agent get --bogus`,\n"
                   "`vf agent frob`, and `vf auth login --no-browser`.\n")
        log = tree.root / "calls.log"
        fake = tree.root / "fake_vf.py"
        fake.write_text(
            "import sys\n"
            f"open({str(log)!r}, 'a', encoding='utf-8').write(' '.join(sys.argv[1:]) + '\\n')\n"
            "words, option = tuple(sys.argv[1:-1]), sys.argv[-1]\n"
            "if option == '--usage':\n"
            "    print('cmd \"get\" {\\n  flag \"--environment-alias <alias>\"\\n}')\n"
            "    sys.exit(0)\n"
            "pages = {(): 'Usage:\\n  vf [flags]\\n\\nFlags:\\n  -h, --help   help\\n'\n"
            "             '  -o, --output-format string\\n',\n"
            "         ('agent',): 'Usage:\\n  vf agent [command]\\n',\n"
            "         ('agent', 'get'): 'Usage:\\n  vf agent get [flags]\\n\\n  -p, --project-id string\\n',\n"
            "         ('auth', 'login'): 'Usage:\\n  vf auth login [flags]\\n\\n      --no-browser\\n'}\n"
            "while words not in pages:\n"
            "    words = words[:-1]\n"
            "print(pages[words])\n", encoding="utf-8")
        with self.assertRaises(AssertionError) as raised:
            verify_cli.check_skill_commands([sys.executable, str(fake)], tree.root)
        location = "voiceflow/skills/voiceflow-build/references/cli.md"
        self.assertEqual(str(raised.exception).splitlines(), [
            f"{location}:2: `vf agent frob --help` does not describe that command",
            f"{location}:1: `vf agent get` has no --bogus flag"])
        calls = log.read_text(encoding="utf-8").splitlines()
        self.assertIn("agent get --usage", calls)
        self.assertNotIn("auth login --usage", calls)


if __name__ == "__main__":
    unittest.main()
