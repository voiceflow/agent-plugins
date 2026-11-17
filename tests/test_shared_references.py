import contextlib
import io
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import sync_shared_references as sync  # noqa: E402

SOURCE = "voiceflow/skills/voiceflow/references"
FIX = f"run {sync.COMMAND}"


class SharedTree:
    """A small synthetic repository: three shared files, one skill per kind of need."""

    def __init__(self, test):
        scratch = tempfile.TemporaryDirectory()
        test.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name).resolve()
        self.write("voiceflow/skills/voiceflow/SKILL.md", "Read [ops](references/ops.md).\n")
        self.write(f"{SOURCE}/docs.md", "---\npackage: voiceflow\nversion: 1.0.0\n---\n\n# Docs\n")
        self.write(f"{SOURCE}/ops.md", "# Ops\n\nSee [docs](docs.md#docs).\n")
        self.write(f"{SOURCE}/handoffs.md", "# Handoffs\n\nThe [contract](ops.md).\n")
        self.write("voiceflow/skills/voiceflow-build/SKILL.md", "Read [ops](references/ops.md).\n")
        self.write("voiceflow/skills/voiceflow-wiring/SKILL.md", "Read [own](references/own.md).\n")
        self.write("voiceflow/skills/voiceflow-wiring/references/own.md", "Use [handoffs](<handoffs.md>).\n")
        self.write("voiceflow/skills/voiceflow-knowledge/SKILL.md", "Name the `voiceflow-build` skill.\n")
        files = sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*") if path.is_file())
        self.write("package-files.txt", "\n".join(files) + "\n")

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
        return path

    def inventory(self):
        return (self.root / "package-files.txt").read_text(encoding="utf-8").splitlines()


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tree = SharedTree(self)
        self.root = self.tree.root

    def copy(self, skill, name):
        return self.root / f"voiceflow/skills/{skill}/references/{name}"

    def test_each_skill_gets_what_it_links_and_what_those_files_link(self):
        before = self.tree.inventory()
        changes = sync.sync(self.root)
        expected = {"voiceflow-build": {"docs.md", "ops.md"},
                    "voiceflow-wiring": {"docs.md", "handoffs.md", "ops.md"}}
        for skill, names in expected.items():
            for name in names:
                with self.subTest(skill=skill, name=name):
                    copy = self.copy(skill, name)
                    self.assertEqual(copy.read_bytes(), sync.NOTICE + (self.root / SOURCE / name).read_bytes())
                    if os.name != "nt":
                        self.assertEqual(stat.S_IMODE(copy.stat().st_mode), 0o644)
        self.assertFalse((self.root / "voiceflow/skills/voiceflow-knowledge/references").exists())
        self.assertFalse(self.copy("voiceflow-wiring", "own.md").read_bytes().startswith(sync.NOTICE))
        added = sorted(f"voiceflow/skills/{skill}/references/{name}" for skill, names in expected.items()
                       for name in names)
        self.assertEqual(self.tree.inventory(), sorted(before + added))
        self.assertEqual(sorted(line for line in changes if line.startswith("created ")),
                         [f"created {line}" for line in added])
        self.assertEqual(sync.drift_problems(self.root), [])
        self.assertEqual(sync.sync(self.root), [])

    def test_notice_is_one_fixed_line_without_a_path(self):
        self.assertEqual(sync.NOTICE.count(b"\n"), 1)
        self.assertTrue(sync.NOTICE.endswith(b"-->\n") and sync.NOTICE.startswith(b"<!--"))
        self.assertNotIn(b"voiceflow/skills", sync.NOTICE)
        self.assertNotIn(b"../", sync.NOTICE)

    def check(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            return sync.main(["--check"], self.root), output.getvalue()

    def test_check_mode_writes_nothing(self):
        before = self.tree.inventory()
        status, output = self.check()
        self.assertEqual(status, 1)
        self.assertIn(f"voiceflow/skills/voiceflow-build/references/ops.md: missing copy of {SOURCE}/ops.md", output)
        self.assertFalse(self.copy("voiceflow-build", "ops.md").exists())
        self.assertEqual(self.tree.inventory(), before)
        sync.sync(self.root)
        self.assertEqual(self.check(), (0, "Shared reference copies match their sources.\n"))

    def test_missing_copy_and_inventory_line_fail(self):
        sync.sync(self.root)
        self.copy("voiceflow-build", "ops.md").unlink()
        self.tree.write("package-files.txt", "\n".join(
            line for line in self.tree.inventory() if not line.endswith("voiceflow-wiring/references/docs.md")) + "\n")
        self.assertEqual(sync.drift_problems(self.root), [
            f"voiceflow/skills/voiceflow-build/references/ops.md: missing copy of {SOURCE}/ops.md; {FIX}",
            f"package-files.txt: missing voiceflow/skills/voiceflow-wiring/references/docs.md; {FIX}"])

    def test_hand_edited_copy_fails(self):
        sync.sync(self.root)
        copy = self.copy("voiceflow-build", "ops.md")
        copy.write_bytes(copy.read_bytes() + b"Local note.\n")
        self.assertEqual(sync.drift_problems(self.root), [
            "voiceflow/skills/voiceflow-build/references/ops.md: differs from its source; "
            f"edit the source at {SOURCE}/ops.md and {FIX}"])
        self.assertEqual(sync.sync(self.root), ["rewrote voiceflow/skills/voiceflow-build/references/ops.md"])
        self.assertEqual(sync.drift_problems(self.root), [])

    def test_copy_with_an_old_version_fails(self):
        sync.sync(self.root)
        source = self.root / SOURCE / "docs.md"
        source.write_bytes(source.read_bytes().replace(b"version: 1.0.0", b"version: 1.0.1"))
        self.assertEqual(sync.drift_problems(self.root), [
            f"voiceflow/skills/{skill}/references/docs.md: differs from its source; "
            f"edit the source at {SOURCE}/docs.md and {FIX}" for skill in ("voiceflow-build", "voiceflow-wiring")])
        sync.sync(self.root)
        self.assertIn(b"version: 1.0.1", self.copy("voiceflow-wiring", "docs.md").read_bytes())

    def test_stale_copy_fails_and_sync_deletes_it_with_its_inventory_line(self):
        sync.sync(self.root)
        self.tree.write("voiceflow/skills/voiceflow-build/SKILL.md", "Name the `voiceflow-wiring` skill.\n")
        stale = [f"voiceflow/skills/voiceflow-build/references/{name}" for name in ("docs.md", "ops.md")]
        self.assertEqual(sync.drift_problems(self.root), [
            f"{stale[0]}: stale copy; this skill no longer links docs.md; {FIX}",
            f"{stale[1]}: stale copy; this skill no longer links ops.md; {FIX}",
            f"package-files.txt: lists {stale[0]}, which is not a needed copy; {FIX}",
            f"package-files.txt: lists {stale[1]}, which is not a needed copy; {FIX}"])
        changes = sync.sync(self.root)
        self.assertIn(f"deleted {stale[0]}", changes)
        self.assertIn(f"package-files.txt: removed {stale[1]}", changes)
        self.assertFalse(any((self.root / name).exists() for name in stale))
        self.assertFalse(set(stale) & set(self.tree.inventory()))
        self.assertEqual(sync.drift_problems(self.root), [])

    def test_unlinked_file_with_a_shared_name_keeps_its_inventory_line(self):
        own = self.tree.write("voiceflow/skills/voiceflow-knowledge/references/ops.md", "# Knowledge ops\n")
        self.tree.write("package-files.txt", "\n".join(sorted(self.tree.inventory() + [
            own.relative_to(self.root).as_posix()])) + "\n")
        sync.sync(self.root)
        self.assertIn("voiceflow/skills/voiceflow-knowledge/references/ops.md", self.tree.inventory())
        self.assertEqual(own.read_text(encoding="utf-8"), "# Knowledge ops\n")
        self.assertEqual(sync.drift_problems(self.root), [])

    def test_copy_of_a_deleted_source_is_stale(self):
        sync.sync(self.root)
        (self.root / SOURCE / "handoffs.md").unlink()
        self.tree.write("voiceflow/skills/voiceflow-wiring/references/own.md", "No links.\n")
        self.assertIn("voiceflow/skills/voiceflow-wiring/references/handoffs.md: stale copy; "
                      f"this skill no longer links handoffs.md; {FIX}", sync.drift_problems(self.root))
        sync.sync(self.root)
        self.assertFalse(self.copy("voiceflow-wiring", "handoffs.md").exists())
        self.assertEqual(sync.drift_problems(self.root), [])

    def test_hand_written_file_with_a_shared_name_is_never_replaced(self):
        self.tree.write("voiceflow/skills/voiceflow-build/references/ops.md", "# My own ops\n")
        before = self.tree.inventory()
        reason = (f"voiceflow/skills/voiceflow-build/references/ops.md: this name is reserved for a copy of "
                  f"{SOURCE}/ops.md; rename the file, or delete it if it is an old copy without the notice")
        self.assertIn(reason, sync.drift_problems(self.root))
        with self.assertRaisesRegex(sync.Conflict, "reserved"):
            sync.sync(self.root)
        self.assertEqual(self.copy("voiceflow-build", "ops.md").read_text(encoding="utf-8"), "# My own ops\n")
        self.assertFalse(self.copy("voiceflow-build", "docs.md").exists())
        self.assertEqual(self.tree.inventory(), before)

    def test_symlinked_references_folder_is_refused_and_nothing_outside_is_deleted(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        victim = Path(outside.name) / "docs.md"
        victim.write_bytes(sync.NOTICE + b"# Not ours\n")
        os.symlink(outside.name, self.root / "voiceflow/skills/voiceflow-knowledge/references")
        link = "voiceflow/skills/voiceflow-knowledge/references"
        self.assertEqual(sync.drift_problems(self.root), [
            f"{link}: is a symlink; the skills tree may hold only regular files and folders"])
        with self.assertRaisesRegex(sync.Conflict, "is a symlink"):
            sync.sync(self.root)
        self.assertTrue(victim.exists())
        self.assertFalse(self.copy("voiceflow-build", "docs.md").exists())

    def test_symlinked_skill_folder_is_refused(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        os.symlink(outside.name, self.root / "voiceflow/skills/voiceflow-extra")
        with self.assertRaisesRegex(sync.Conflict, "voiceflow-extra: is a symlink"):
            sync.sync(self.root)


class RepositoryCopiesTests(unittest.TestCase):
    def test_repository_copies_match_their_sources(self):
        self.assertEqual(sync.drift_problems(ROOT), [])


if __name__ == "__main__":
    unittest.main()
