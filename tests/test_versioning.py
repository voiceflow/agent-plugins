"""Version bumps from pull request titles, with temporary Git repositories; no pushes."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


import check_pr_title as title_check  # noqa: E402
import next_version  # noqa: E402
import validate as validator  # noqa: E402
import versioning  # noqa: E402

MANIFEST = '{\n  "name": "voiceflow",\n  "version": "%s",\n  "description": "Synthetic."\n}\n'
METADATA = "---\npackage: voiceflow\nversion: %s\n---\nSynthetic body.\n"


class GitRepository:
    """A disposable repository holding only the version files and CHANGELOG.md."""

    def __init__(self, test):
        scratch = tempfile.TemporaryDirectory()
        test.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "release-test@example.invalid")
        self.git("config", "user.name", "Synthetic test")
        self.write_version("0.5.0")
        self.write(versioning.CHANGELOG, "# Changelog\n\n## Unreleased\n\n## 0.5.0\n\n- Older.\n")
        self.commit("chore: start")

    def git(self, *args):
        return subprocess.run(
            ["git", "-c", "core.hooksPath=" + str(self.root / "no-hooks"), "-c", "commit.gpgsign=false",
             "-c", "tag.gpgsign=false", "-c", "core.autocrlf=false", *args],
            cwd=self.root, capture_output=True, check=True, text=True, encoding="utf-8", timeout=20).stdout

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode("utf-8"))

    def write_version(self, version):
        for path in versioning.VERSION_FILES:
            self.write(path, (MANIFEST if path.endswith(".json") else METADATA) % version)

    def commit(self, message, path="notes.txt"):
        if path:
            self.write(path, message + "\n" + (self.root / path).read_text(encoding="utf-8")
                       if (self.root / path).exists() else message + "\n")
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD").strip()

    def merge(self, branch, message):
        self.git("merge", "-q", "--no-ff", branch, "-m", message)
        return self.git("rev-parse", "HEAD").strip()


class TitleTests(unittest.TestCase):
    def test_conventional_titles_are_parsed(self):
        parsed = versioning.parse_title("feat(setup)!: pin the account MCP URL (#12)")
        self.assertEqual(parsed, versioning.Title("feat", "setup", True, "pin the account MCP URL (#12)"))
        self.assertEqual(versioning.parse_title("fix: correct a link"), versioning.Title("fix", None, False, "correct a link"))
        for kind in versioning.TYPES:
            with self.subTest(kind=kind):
                self.assertIsNotNone(versioning.parse_title(kind + ": summary"))

    def test_other_shapes_are_not_titles(self):
        for title in ("Add a skill", "feat:missing space", "feature: unknown type", "Feat: capital type",
                      "feat(): empty scope", "feat: ", "feat(a b): space in scope", "Merge pull request #2"):
            with self.subTest(title=title):
                self.assertIsNone(versioning.parse_title(title))

    def test_each_type_maps_to_one_bump(self):
        cases = {"feat: a": "minor", "fix: a": "patch", "docs: a": "none", "ci: a": "none", "perf: a": "none",
                 "feat!: a": "major", "fix(setup)!: a": "major", "refactor!: a": "major", "Not a title": "none"}
        for message, level in cases.items():
            with self.subTest(message=message):
                self.assertEqual(versioning.commit_level(message), level)

    def test_a_breaking_footer_is_major_even_without_the_mark(self):
        self.assertEqual(versioning.commit_level("fix: a\n\nDetails.\n\nBREAKING CHANGE: drops X"), "major")
        self.assertEqual(versioning.commit_level("docs: a\n\nBREAKING-CHANGE: drops X"), "major")
        self.assertEqual(versioning.commit_level("fix: a\n\nNot a BREAKING CHANGE: mid-line"), "patch")


class BumpTests(unittest.TestCase):
    def test_bump_math(self):
        self.assertEqual(versioning.bump("1.2.3", "patch"), "1.2.4")
        self.assertEqual(versioning.bump("1.2.3", "minor"), "1.3.0")
        self.assertEqual(versioning.bump("1.2.3", "major"), "2.0.0")
        self.assertEqual(versioning.bump("1.2.3", "none"), "1.2.3")
        for version in ("1.2", "v1.2.3", "01.2.3"):
            with self.subTest(version=version), self.assertRaises(ValueError):
                versioning.bump(version, "patch")

    def test_the_largest_bump_in_a_range_wins(self):
        messages = ["docs: a", "fix: b", "feat: c", "ci: d"]
        self.assertEqual(versioning.largest(map(versioning.commit_level, messages)), "minor")
        self.assertEqual(versioning.largest(map(versioning.commit_level, messages + ["fix!: e"])), "major")
        self.assertEqual(versioning.largest(map(versioning.commit_level, ["docs: a", "test: b"])), "none")
        self.assertEqual(versioning.largest([]), "none")

    def test_release_commits_never_count(self):
        self.assertIsNone(versioning.commit_level("chore(release): 2.0.0"))
        self.assertIsNone(versioning.commit_level("chore(release)!: 2.0.0\n\nBREAKING CHANGE: synthetic"))
        levels = map(versioning.commit_level, ["chore(release)!: 2.0.0", "fix: a"])
        self.assertEqual(versioning.largest(levels), "patch")


class ChangelogTests(unittest.TestCase):
    TEXT = "# Changelog\n\nIntro.\n\n## Unreleased\n\n- New skill.\n- Fixed link.\n\n## 1.0.0\n\n- Old.\n"

    def test_unreleased_is_renamed_and_a_new_one_starts(self):
        released = versioning.release_changelog(self.TEXT, "1.1.0")
        self.assertEqual(released, "# Changelog\n\nIntro.\n\n## Unreleased\n\n## 1.1.0\n\n"
                                   "- New skill.\n- Fixed link.\n\n## 1.0.0\n\n- Old.\n")
        self.assertIsNone(versioning.changelog_problem(released, "1.1.0"))
        self.assertEqual(versioning.unreleased_entries(released), [])

    def test_release_refuses_an_empty_missing_or_repeated_section(self):
        cases = {"empty": ("# Changelog\n\n## Unreleased\n\n## 1.0.0\n\n- Old.\n", "1.1.0"),
                 "start with": ("# Changelog\n\n## 1.0.0\n\n- Old.\n", "1.1.0"),
                 "already has": (self.TEXT, "1.0.0")}
        for reason, (text, version) in cases.items():
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                versioning.release_changelog(text, version)

    def test_headings_must_be_unreleased_then_the_package_version(self):
        self.assertIsNone(versioning.changelog_problem(self.TEXT, "1.0.0"))
        for text, version in ((self.TEXT, "1.1.0"), ("# Changelog\n\n## 1.0.0\n", "1.0.0"),
                              ("# Changelog\n\n## Unreleased\n\n## 1.0.0 — 2026-11-12\n", "1.0.0")):
            with self.subTest(text=text):
                self.assertIn("must start with", versioning.changelog_problem(text, version))

    def test_only_new_lines_under_unreleased_count_as_added(self):
        before = "## Unreleased\n\n- Kept.\n\n## 1.0.0\n\n- Old.\n"
        after = "## Unreleased\n\n- Kept.\n- New.\n\n## 1.0.0\n\n- Old.\n- Misplaced.\n"
        self.assertEqual(versioning.added_entries(before, after), ["- New."])
        self.assertEqual(versioning.added_entries(before, before), [])
        self.assertEqual(versioning.added_entries("", after), ["- Kept.", "- New."])


class RewriteTests(unittest.TestCase):
    def copy_repository(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        root = Path(scratch.name) / "repo"
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", ".worktrees", "dist", "__pycache__"))
        return root

    def test_rewritten_files_change_only_the_version_and_still_validate(self):
        root = self.copy_repository()
        changelog = root / versioning.CHANGELOG
        old = versioning.package_version(root)
        text = changelog.read_text(encoding="utf-8").replace("## Unreleased\n", "## Unreleased\n\n- A tested change.\n", 1)
        changelog.write_bytes(text.encode("utf-8"))
        before = {path: (root / path).read_text(encoding="utf-8") for path in versioning.VERSION_FILES}
        new = versioning.bump(old, "minor")
        next_version.apply(root, {"mode": "release", "version": new})
        self.assertEqual(validator.validate(root), len(validator.SKILL_NAMES))
        for path in versioning.VERSION_FILES:
            with self.subTest(path=path):
                after = (root / path).read_text(encoding="utf-8")
                self.assertEqual(versioning.version_in(path, after), new)
                changed = [pair for pair in zip(before[path].splitlines(), after.splitlines()) if pair[0] != pair[1]]
                self.assertEqual(len(changed), 1)
                self.assertEqual(len(before[path].splitlines()), len(after.splitlines()))
        released = changelog.read_text(encoding="utf-8")
        self.assertIn(f"## Unreleased\n\n## {new}\n\n- A tested change.\n", released)

    def test_validate_rejects_a_changelog_without_unreleased_first(self):
        root = self.copy_repository()
        changelog = root / versioning.CHANGELOG
        changelog.write_text(changelog.read_text(encoding="utf-8").replace("## Unreleased\n\n", "", 1), encoding="utf-8")
        with self.assertRaisesRegex(AssertionError, "must start with ## Unreleased"):
            validator.validate(root)

    def test_a_json_file_with_two_matching_versions_is_refused(self):
        text = '{"version": "1.0.0", "nested": {"version": "1.0.0"}}'
        with self.assertRaisesRegex(ValueError, "only the package version"):
            versioning.replace_version("voiceflow/plugin.json", text, "1.0.0", "1.1.0")

    def test_versions_that_differ_are_refused_before_any_write(self):
        repository = GitRepository(self)
        repository.write(versioning.VERSION_FILES[1], MANIFEST % "0.4.0")
        with self.assertRaisesRegex(ValueError, "versions differ"):
            versioning.set_version(repository.root, "0.6.0")
        self.assertEqual(versioning.read_version(repository.root, versioning.VERSION_FILES[0]), "0.5.0")

    def test_the_write_job_allows_exactly_the_version_files(self):
        workflow = (ROOT / ".github/workflows/version.yml").read_text(encoding="utf-8")
        block = re.search(r"ALLOWED_FILES: \|\n((?: {12}\S.*\n)+)", workflow)
        self.assertIsNotNone(block, "version.yml must list ALLOWED_FILES")
        allowed = [line.strip() for line in block.group(1).splitlines()]
        self.assertEqual(sorted(allowed), sorted([versioning.CHANGELOG, *versioning.VERSION_FILES]))


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.repository = GitRepository(self)
        self.repository.git("switch", "-q", "-c", "major-release")
        self.repository.write_version("1.0.0")
        self.repository.write(versioning.CHANGELOG, "# Changelog\n\n## Unreleased\n\n## 1.0.0\n\n- New.\n\n## 0.5.0\n\n- Older.\n")
        self.repository.commit("feat!: set 1.0.0 on a branch")
        self.repository.git("switch", "-q", "main")
        self.release_commit = self.repository.merge("major-release", "feat!: release 1.0.0 (#11)")
        self.repository.commit("ci: add the version workflow")

    def plan(self):
        warnings = []
        return next_version.plan(self.repository.root, warn=warnings.append), warnings

    def test_without_a_tag_the_first_run_tags_the_commit_that_set_the_version(self):
        self.assertEqual(self.plan()[0], {"mode": "tag", "version": "1.0.0", "target": self.release_commit})
        self.repository.commit("feat: merged before the first tag")
        self.assertEqual(self.plan()[0]["target"], self.release_commit)

    def test_with_a_tag_the_largest_first_parent_bump_wins(self):
        self.repository.git("tag", "v1.0.0", self.release_commit)
        self.assertEqual(self.plan()[0]["mode"], "none")
        self.repository.git("switch", "-q", "-c", "side")
        self.repository.commit("feat!: a branch commit that the merge title replaces")
        self.repository.git("switch", "-q", "main")
        self.repository.merge("side", "fix: merged with a merge commit")
        self.assertEqual(self.plan()[0], {"mode": "release", "version": "1.0.1", "target": "", "level": "patch"})
        self.repository.commit("Not a conventional title")
        result, warnings = self.plan()
        self.assertEqual(result["version"], "1.0.1")
        self.assertTrue(any("no conventional title" in warning for warning in warnings))
        self.repository.commit("feat(setup): add a skill")
        self.assertEqual(self.plan()[0]["version"], "1.1.0")
        self.repository.commit("docs: explain\n\nBREAKING CHANGE: synthetic footer")
        self.assertEqual(self.plan()[0]["version"], "2.0.0")

    def test_a_release_commit_ends_the_range(self):
        self.repository.git("tag", "v1.0.0", self.release_commit)
        self.repository.commit("feat: add a skill")
        self.repository.write_version("1.1.0")
        self.repository.git("tag", "v1.1.0", self.repository.commit("chore(release): 1.1.0", path=None))
        self.assertEqual(self.plan()[0]["mode"], "none")
        self.repository.commit("fix: correct a link")
        self.assertEqual(self.plan()[0]["version"], "1.1.1")

    def test_a_package_version_that_differs_from_the_tag_stops_the_run(self):
        self.repository.git("tag", "v0.9.0", self.release_commit)
        with self.assertRaisesRegex(ValueError, "does not match the last tag v0.9.0"):
            self.plan()


class PullRequestTitleTests(unittest.TestCase):
    ENTRY = ["- Add the widget skill."]

    def check(self, title, paths=("README.md",), entries=(), edits=(), body=""):
        return title_check.problems(title, body, title_check.Changes(list(paths), list(edits), list(entries)))

    def assertOneProblem(self, found, text):
        self.assertEqual(len(found), 1, found)
        self.assertIn(text, found[0])

    def test_passing_titles(self):
        self.assertEqual(self.check("ci: pin an action", paths=[".github/workflows/check.yml"]), [])
        self.assertEqual(self.check("docs: explain releases"), [])
        self.assertEqual(self.check("feat(widget): add a skill", ["voiceflow/skills/x/SKILL.md"], self.ENTRY), [])
        self.assertEqual(self.check("fix: correct a link", ["voiceflow/skills/x/SKILL.md"], self.ENTRY), [])
        migrate = ["- Breaking: drops X. To migrate, reinstall the plugin."]
        self.assertEqual(self.check("refactor!: drop X", ["voiceflow/a.md"], migrate,
                                    body="Text.\n\nBREAKING CHANGE: drops X"), [])

    def test_a_title_that_is_not_conventional_fails(self):
        for title in ("Add a skill", "feature: add a skill", "feat:add"):
            with self.subTest(title=title):
                self.assertOneProblem(self.check(title), "type(scope)!: summary")

    def test_release_titles_are_reserved_for_the_workflow(self):
        self.assertOneProblem(self.check("chore(release): 9.9.9"), "chore(release)")

    def test_package_changes_need_feat_fix_or_breaking(self):
        for title in ("docs: reword a skill", "chore: tidy", "perf: faster"):
            with self.subTest(title=title):
                self.assertOneProblem(self.check(title, ["voiceflow/skills/x/SKILL.md"]), "voiceflow/")

    def test_version_edits_fail(self):
        self.assertOneProblem(self.check("ci: bump", edits=["voiceflow/plugin.json"]), "Do not change the package version")

    def test_feat_and_fix_need_an_unreleased_line(self):
        for title in ("feat: add", "fix: correct"):
            with self.subTest(title=title):
                self.assertOneProblem(self.check(title, ["voiceflow/a.md"]), "## Unreleased")

    def test_breaking_changes_need_a_migration_line(self):
        self.assertOneProblem(self.check("feat!: drop X", ["voiceflow/a.md"], self.ENTRY), "migrate")

    def test_a_breaking_footer_needs_the_mark_in_the_title(self):
        found = self.check("feat: drop X", ["voiceflow/a.md"], self.ENTRY, body="Why.\n\nBREAKING CHANGE: drops X")
        self.assertOneProblem(found, "BREAKING CHANGE:")

    def test_changes_are_read_from_git(self):
        repository = GitRepository(self)
        base = repository.git("rev-parse", "HEAD").strip()
        repository.write(versioning.VERSION_FILES[2], MANIFEST % "0.6.0")
        repository.write(versioning.CHANGELOG, "# Changelog\n\n## Unreleased\n\n- New line.\n\n## 0.5.0\n\n- Older.\n")
        head = repository.commit("feat: synthetic", path="voiceflow/skills/x.md")
        changes = title_check.changes_between(base, head, root=repository.root)
        self.assertIn("voiceflow/skills/x.md", changes.paths)
        self.assertEqual(changes.version_edits, [versioning.VERSION_FILES[2]])
        self.assertEqual(changes.added_entries, ["- New line."])

    def test_the_event_file_drives_the_check(self):
        repository = GitRepository(self)
        base = repository.git("rev-parse", "HEAD").strip()
        head = repository.commit("docs: synthetic", path="voiceflow/skills/x.md")
        event = repository.root / "event.json"
        event.write_text(json.dumps({"pull_request": {"title": "docs: reword", "body": None}}), encoding="utf-8")
        original = title_check.ROOT
        title_check.ROOT = repository.root
        self.addCleanup(setattr, title_check, "ROOT", original)
        with mock.patch("builtins.print") as printed:
            code = title_check.main(["--event", str(event), "--base", base, "--head", head])
        self.assertEqual(code, 1)
        self.assertIn("voiceflow/", printed.call_args_list[0].args[0])


if __name__ == "__main__":
    unittest.main()
