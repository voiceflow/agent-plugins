import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / "voiceflow/skills/voiceflow-setup/scripts"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sys.path.insert(0, str(ROOT / "scripts"))
installer = load("installer", SETUP / "install_skills.py")
connection = load("connection", SETUP / "check_connection.py")
builder = load("builder", ROOT / "scripts/build.py")
validator = load("validator", ROOT / "scripts/validate.py")
release = load("release", ROOT / "scripts/prepare_release.py")


class SkillInstallTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.base = Path(self.scratch.name)
        self.source = self.base / "source"
        self.target = self.base / "target"
        self.skill = self.source / "voiceflow/SKILL.md"
        self.skill.parent.mkdir(parents=True)
        self.skill.write_text("original")
        self.skill.with_name("LICENSE").write_bytes((ROOT / "LICENSE").read_bytes())

    def test_repeat_and_uninstall_preserve_unrelated_files(self):
        self.assertEqual(installer.install(self.source, self.target), "installed")
        unrelated = self.target / "another-skill.txt"
        unrelated.write_text("keep")
        self.assertEqual(installer.install(self.source, self.target), "unchanged")
        self.assertEqual(installer.install(self.source, self.target, uninstall=True), "removed")
        self.assertEqual(unrelated.read_text(encoding="utf-8"), "keep")
        self.assertFalse((self.target / "voiceflow/SKILL.md").exists())
        self.assertFalse((self.target / "voiceflow/LICENSE").exists())

    def test_missing_license_fails_before_installing_any_file(self):
        self.skill.with_name("LICENSE").unlink()
        with self.assertRaisesRegex(ValueError, "Missing license"):
            installer.install(self.source, self.target)
        self.assertFalse(self.target.exists())

    def test_upgrade_adds_license_to_a_legacy_install(self):
        installer.install(self.source, self.target)
        receipt_path = self.target / installer.RECEIPT
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        del receipt["files"]["voiceflow/LICENSE"]
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        (self.target / "voiceflow/LICENSE").unlink()
        self.assertEqual(installer.install(self.source, self.target, update=True), "installed")
        self.assertEqual((self.target / "voiceflow/LICENSE").read_bytes(), (ROOT / "LICENSE").read_bytes())
        (self.target / "voiceflow/LICENSE").write_text("local notice", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Local change"):
            installer.install(self.source, self.target, update=True)
        self.assertEqual((self.target / "voiceflow/LICENSE").read_text(encoding="utf-8"), "local notice")

    def test_conflict_fails_before_any_write(self):
        self.target.mkdir()
        existing = self.target / "voiceflow/SKILL.md"
        existing.parent.mkdir()
        existing.write_text("custom")
        (self.source / "voiceflow/new.md").write_text("new")
        with self.assertRaisesRegex(ValueError, "Existing file"):
            installer.install(self.source, self.target)
        self.assertEqual(existing.read_text(encoding="utf-8"), "custom")
        self.assertFalse((self.target / "voiceflow/new.md").exists())

    def test_edited_file_blocks_update_and_removal(self):
        installer.install(self.source, self.target)
        (self.target / "voiceflow/SKILL.md").write_text("custom")
        for options in ({"update": True}, {"uninstall": True}):
            with self.assertRaisesRegex(ValueError, "Local change"):
                installer.install(self.source, self.target, **options)
        self.assertEqual((self.target / "voiceflow/SKILL.md").read_text(encoding="utf-8"), "custom")

    def test_intentional_update_replaces_only_managed_files(self):
        installer.install(self.source, self.target)
        self.skill.write_text("updated")
        with self.assertRaisesRegex(ValueError, "--update"):
            installer.install(self.source, self.target)
        self.assertEqual(installer.install(self.source, self.target, update=True), "installed")
        self.assertEqual((self.target / "voiceflow/SKILL.md").read_text(encoding="utf-8"), "updated")

    def test_removed_file_is_not_silently_restored(self):
        installer.install(self.source, self.target)
        (self.target / "voiceflow/SKILL.md").unlink()
        with self.assertRaisesRegex(ValueError, "Local change"):
            installer.install(self.source, self.target, update=True)

    def test_receipt_cannot_escape_target(self):
        self.target.mkdir()
        (self.target / installer.RECEIPT).write_text(json.dumps({"files": {"../secret": "fake"}}))
        with self.assertRaisesRegex(ValueError, "Invalid managed"):
            installer.install(self.source, self.target, uninstall=True)

    def test_symlink_destination_refused(self):
        self.target.mkdir()
        outside = self.base / "outside"
        outside.mkdir()
        try:
            (self.target / "voiceflow").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("Symlink creation unavailable on this host")
        with self.assertRaisesRegex(ValueError, "Symlink"):
            installer.install(self.source, self.target)
        self.assertEqual(list(outside.iterdir()), [])

    def test_partial_failure_rolls_back_written_files(self):
        installer.install(self.source, self.target)
        receipt_before = (self.target / installer.RECEIPT).read_bytes()
        self.skill.write_text("updated")
        (self.source / "voiceflow/new.md").write_text("new")
        original = os.replace
        calls = 0

        def fail_second(source, target):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("simulated disk failure")
            return original(source, target)

        with patch.object(installer.os, "replace", side_effect=fail_second):
            with self.assertRaises(OSError):
                installer.install(self.source, self.target, update=True)
        self.assertEqual((self.target / "voiceflow/SKILL.md").read_text(encoding="utf-8"), "original")
        self.assertEqual((self.target / installer.RECEIPT).read_bytes(), receipt_before)
        self.assertFalse((self.target / "voiceflow/new.md").exists())

    def test_complete_packaged_skill_tree_installs(self):
        installer.install(ROOT / "voiceflow/skills", self.target)
        self.assertEqual(len(list(self.target.glob("*/SKILL.md"))), 16)
        self.assertTrue((self.target / "voiceflow-setup/references/setup.md").is_file())
        metadata = (self.target / "voiceflow/references/documentation.md").read_text(encoding="utf-8").split("---", 2)[1]
        record = dict(line.split(": ", 1) for line in metadata.strip().splitlines())
        manifest = json.loads((ROOT / "voiceflow/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(record, {"package": manifest["name"], "version": manifest["version"]})
        for source in (ROOT / "voiceflow/skills").rglob("*.md"):
            installed = self.target / source.relative_to(ROOT / "voiceflow/skills")
            self.assertEqual(installed.read_bytes(), source.read_bytes())
        for skill in self.target.glob("*/SKILL.md"):
            self.assertEqual(skill.with_name("LICENSE").read_bytes(), (ROOT / "LICENSE").read_bytes())


class ConnectionTests(unittest.TestCase):
    def test_empty_and_populated_accounts_are_ready(self):
        for data in ({"workspaces": []}, {"workspaces": [{"id": "private", "name": "private"}]}):
            self.assertEqual(connection.classify(0, json.dumps(data), ""), "connected")

    def test_structured_failures_are_distinct(self):
        for kind, expected in {
            "authentication_error": "authentication_required",
            "authorization_error": "permission_denied",
            "connection_error": "temporarily_unavailable",
            "rate_limit_error": "temporarily_unavailable",
            "server_error": "temporarily_unavailable",
            "validation_error": "request_failed",
        }.items():
            with self.subTest(kind=kind):
                payload = json.dumps({"error_type": kind, "message": "private token"})
                self.assertEqual(connection.classify(1, "", payload), expected)

    def test_bad_success_is_not_connected(self):
        for output in ("", "<html>proxy</html>", "{}", "null", '{"error":"unauthorized"}'):
            self.assertNotEqual(connection.classify(0, output, ""), "connected")
        self.assertNotEqual(connection.classify(1, '{"workspaces":[]}', ""), "connected")

    def test_truncated_malformed_and_stderr_only_success_are_rejected(self):
        for output in ('{"workspaces":[', '{"workspaces":[]} trailing',
                       'workspaces[1]{id,name}:\n',
                       'workspaces[1]{id,name}:\n  invalid', 'workspaces[0]:',
                       '{"workspaces":[null]}', '{"workspaces":[{}]}',
                       '{"workspaces":[{"id":""}]}', '{"workspaces":[{"id":12}]}',
                       '{"workspaces":null,"workspaces":[]}',
                       '{"workspaces":[],"value":NaN}'):
            with self.subTest(output=output):
                self.assertEqual(connection.classify(0, output, ""), "unexpected_response")
        self.assertEqual(connection.classify(0, "", '{"workspaces":[]}'), "unexpected_response")

    def test_structured_error_overrides_a_success_body(self):
        self.assertEqual(connection.classify(0, '{"workspaces":[]}',
                         '{"error_type":"authentication_error"}'), "authentication_required")

    def test_probe_is_read_only_bounded_and_does_not_echo_output(self):
        result = subprocess.CompletedProcess([], 0, '{"workspaces":[{"id":"fixture-workspace"}]}', "")
        with patch.object(connection.subprocess, "run", return_value=result) as run:
            self.assertEqual(connection.check("/path/to/vf"), "connected")
        args, kwargs = run.call_args
        self.assertEqual(args[0][1:3], ["workspace", "list"])
        self.assertEqual(kwargs["timeout"], 25)
        self.assertNotIn("--debug", args[0])
        self.assertEqual(args[0][-2:], ["-o", "json"])
        self.assertNotIn("--timeout", args[0])

    def test_missing_cli_and_timeout(self):
        for error, expected in ((FileNotFoundError(), "cli_missing"),
                                (subprocess.TimeoutExpired("vf", 25), "temporarily_unavailable")):
            with patch.object(connection.subprocess, "run", side_effect=error):
                self.assertEqual(connection.check("vf"), expected)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        shutil.copyfile(ROOT / "package-files.txt", self.root / "package-files.txt")
        shutil.copytree(ROOT / "voiceflow", self.root / "voiceflow",
                        ignore=shutil.ignore_patterns("__pycache__"))

    def test_archive_and_site_are_reproducible_and_complete(self):
        site = builder.build(self.root)
        first = {p.relative_to(site): p.read_bytes() for p in site.rglob("*") if p.is_file()}
        manifest = json.loads((site / "manifest.json").read_text(encoding="utf-8"))
        for name, expected in manifest["files"].items():
            self.assertEqual(builder.sha((site / name).read_bytes()), expected)
        self.assertTrue(manifest["hasUncommittedChanges"])
        with zipfile.ZipFile(site / "voiceflow.zip") as archive:
            self.assertEqual(archive.namelist(), sorted(archive.namelist()))
            self.assertEqual(len([n for n in archive.namelist() if n.endswith("/SKILL.md")]), 16)
            licenses = [n for n in archive.namelist() if n.endswith("/LICENSE")]
            self.assertEqual(len(licenses), 17)
            for name in licenses:
                self.assertEqual(archive.read(name), (ROOT / "LICENSE").read_bytes())
                self.assertEqual((site / name).read_bytes(), (ROOT / "LICENSE").read_bytes())
            for source in (self.root / "voiceflow/skills").rglob("*.md"):
                name = source.relative_to(self.root).as_posix()
                self.assertEqual(archive.read(name), source.read_bytes())
                self.assertEqual((site / name).read_bytes(), source.read_bytes())
            for config in ("mcp.json", ".mcp.json"):
                name = "voiceflow/" + config
                expected = (self.root / name).read_bytes()
                self.assertEqual(archive.read(name), expected)
                self.assertEqual((site / name).read_bytes(), expected)
            for info in archive.infolist():
                self.assertTrue(info.filename.startswith("voiceflow/"))
                self.assertNotIn("..", info.filename.split("/"))
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                self.assertEqual(info.create_system, 3)
        for link in validator.markdown_links((site / "setup.md").read_text(encoding="utf-8")):
            if "://" not in link and not link.startswith("#"):
                self.assertTrue((site / link.split("#")[0]).is_file(), link)
        builder.build(self.root)
        second = {p.relative_to(site): p.read_bytes() for p in site.rglob("*") if p.is_file()}
        self.assertEqual(first, second)

    def test_rewriter_preserves_code_and_external_links(self):
        source = self.root / "voiceflow/skills/voiceflow-setup/references/setup.md"
        sample = "[client](clients.md#codex)\n```md\n[do not change](missing.md)\n```\n[x](https://example.com)\n"
        rewritten = builder.rewrite_setup(sample, source, self.root)
        self.assertIn("voiceflow/skills/voiceflow-setup/references/clients.md#codex", rewritten)
        self.assertIn("[do not change](missing.md)", rewritten)
        self.assertIn("[x](https://example.com)", rewritten)

    def test_rewriter_refuses_missing_or_escaping_references(self):
        source = self.root / "voiceflow/skills/voiceflow-setup/references/setup.md"
        for link in ("missing.md", "../../../../../../outside.md"):
            with self.assertRaises(ValueError):
                builder.rewrite_setup(f"[link]({link})", source, self.root)

    def test_arbitrary_output_refused_without_deletion(self):
        protected = self.root / "keep"
        protected.mkdir()
        with self.assertRaises(ValueError):
            builder.build(self.root, protected)
        self.assertTrue(protected.is_dir())

    def test_extra_local_file_blocks_publication_before_replacing_output(self):
        site = builder.build(self.root)
        previous = (site / "voiceflow.zip").read_bytes()
        for name in (".env", "credentials.json", "notes.md", "private.key"):
            with self.subTest(name=name):
                extra = self.root / "voiceflow" / name
                extra.write_text("synthetic local material", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "inventory mismatch"):
                    builder.build(self.root)
                self.assertEqual((site / "voiceflow.zip").read_bytes(), previous)
                extra.unlink()

    def test_inventory_cannot_escape_plugin_or_duplicate_files(self):
        inventory = self.root / "package-files.txt"
        for name in ("../outside", "voiceflow/../outside", "/absolute", "voiceflow/a\\b",
                     "voiceflow/a:b", "voiceflow//file", "voiceflow/LICENSE\nvoiceflow/LICENSE"):
            inventory.write_text(name + "\n", encoding="utf-8")
            with self.subTest(name=name), self.assertRaises(ValueError):
                builder.build(self.root)
        self.assertFalse((self.root / "dist").exists())

    def test_symlink_in_package_or_output_is_refused(self):
        outside = self.root / "outside"
        outside.mkdir()
        marker = outside / "keep"
        marker.write_text("preserve", encoding="utf-8")
        link = self.root / "dist"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("Symlink creation unavailable on this host")
        with self.assertRaisesRegex(ValueError, "symlink"):
            builder.build(self.root)
        self.assertEqual(marker.read_text(encoding="utf-8"), "preserve")
        link.unlink()
        (self.root / "voiceflow/shortcut").symlink_to(marker)
        with self.assertRaisesRegex(ValueError, "Symlinks"):
            builder.build(self.root)


class RepositoryTests(unittest.TestCase):
    def test_all_manifests_and_skill_links(self):
        self.assertEqual(validator.validate(), 16)

    def test_stale_standalone_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "voiceflow", root / "voiceflow",
                            ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copyfile(ROOT / "LICENSE", root / "LICENSE")
            record = root / "voiceflow/skills/voiceflow/references/documentation.md"
            body = record.read_text().split("---", 2)[2]
            record.write_text("---\npackage: voiceflow\nversion: 0.0.0\n---" + body)
            with self.assertRaisesRegex(AssertionError, "Skill package version differs"):
                validator.validate(root)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        shutil.copyfile(ROOT / "package-files.txt", self.root / "package-files.txt")
        shutil.copytree(ROOT / "voiceflow", self.root / "voiceflow",
                        ignore=shutil.ignore_patterns("__pycache__"))
        self.site = builder.build(self.root)
        self.manifest_path = self.site / "manifest.json"
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.commit = "a" * 40
        self.version = self.manifest["version"]
        self.manifest.update(sourceCommit=self.commit, hasUncommittedChanges=False)
        self.save_manifest()
        self.output = self.root / "release"
        self.changelog = f"# Changelog\n\n## {self.version} — Unreleased\n\n- A tested change.\n"

    def save_manifest(self):
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")

    def prepare(self, **options):
        args = dict(site=self.site, output=self.output, changelog=self.changelog,
                    expected_version=self.version, expected_commit=self.commit)
        return release.prepare_assets(**(args | options))

    def test_assets_are_complete_verified_and_reproducible(self):
        self.prepare()
        for line in (self.output / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
            checksum, name = line.split("  ")
            self.assertEqual(release.sha((self.output / name).read_bytes()), checksum)
        with zipfile.ZipFile(self.output / f"voiceflow-site-{self.version}.zip") as archive:
            self.assertEqual(archive.read("agents/manifest.json"), self.manifest_path.read_bytes())
            self.assertEqual(archive.read("agents/voiceflow/LICENSE"), (ROOT / "LICENSE").read_bytes())
        self.assertEqual((self.output / f"voiceflow-{self.version}.zip").read_bytes(),
                         (self.site / "voiceflow.zip").read_bytes())
        other = self.root / "repeat"
        self.prepare(output=other)
        self.assertEqual({p.name: p.read_bytes() for p in self.output.iterdir()},
                         {p.name: p.read_bytes() for p in other.iterdir()})

    def test_dirty_or_mismatched_source_is_rejected_before_output(self):
        self.manifest["hasUncommittedChanges"] = True
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "clean"):
            self.prepare()
        self.manifest["hasUncommittedChanges"] = False
        self.save_manifest()
        for options in ({"expected_version": "9.9.9"}, {"expected_commit": "b" * 40}):
            with self.assertRaises(ValueError):
                self.prepare(**options)
        self.assertFalse(self.output.exists())

    def test_tampered_asset_and_missing_notes_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "CHANGELOG"):
            self.prepare(changelog="# Empty\n")
        (self.site / "voiceflow.zip").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "verification failed"):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_existing_output_is_preserved(self):
        self.output.mkdir()
        marker = self.output / "keep"
        marker.write_text("existing", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.prepare()
        self.assertEqual(marker.read_text(encoding="utf-8"), "existing")


@unittest.skipIf(os.name == "nt", "Unix installer; Windows installer runs in Windows CI")
class UnixInstallerTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.base = Path(self.scratch.name)
        self.commands = self.base / "commands"
        self.commands.mkdir()
        self.target = self.base / "install"
        self.env = dict(os.environ, VF_INSTALL_DIR=str(self.target),
                        PATH=str(self.commands) + os.pathsep + os.environ["PATH"])

    def run_installer(self):
        return subprocess.run(["bash", str(SETUP / "install-vf.sh")], env=self.env,
                              capture_output=True, text=True, encoding="utf-8", timeout=10)

    def fake_curl(self, script):
        path = self.commands / "curl"
        path.write_text("#!/bin/bash\n" + script)
        path.chmod(0o755)

    def test_checksum_failure_never_installs(self):
        self.fake_curl('for last; do :; done\nprintf "tampered" > "$last"\n')
        result = self.run_installer()
        self.assertEqual(result.returncode, 4, result.stderr)
        self.assertFalse(self.target.exists())

    def test_download_failure_never_installs(self):
        self.fake_curl("exit 22\n")
        self.assertEqual(self.run_installer().returncode, 22)
        self.assertFalse(self.target.exists())

    def test_existing_executable_is_untouched(self):
        self.target.mkdir()
        binary = self.target / "vf"
        binary.write_bytes(b"existing")
        self.assertEqual(self.run_installer().returncode, 3)
        self.assertEqual(binary.read_bytes(), b"existing")


if __name__ == "__main__":
    unittest.main()
