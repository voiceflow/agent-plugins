"""Verify native plugin discovery in disposable host configurations."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run(command, env, cwd):
    result = subprocess.run(command, env=env, cwd=cwd, capture_output=True, text=True, encoding="utf-8", timeout=60)
    if result.returncode:
        raise RuntimeError(f"{command[:3]} failed: {result.stderr[-1000:]}")
    return result.stdout


def main():
    skills = ROOT / "voiceflow/skills"
    expected = {path.parent.name for path in skills.glob("*/SKILL.md")}
    with tempfile.TemporaryDirectory(prefix="voiceflow-hosts-") as temporary:
        directory = Path(temporary)
        for host in ("codex", "claude"):
            if not shutil.which(host):
                print(f"{host}: unavailable; native verification not run")
                continue
            config = directory / host
            config.mkdir()
            key = "CODEX_HOME" if host == "codex" else "CLAUDE_CONFIG_DIR"
            env = dict(os.environ, **{key: str(config)})
            run([host, "plugin", "marketplace", "add", str(ROOT)], env, directory)
            operation = "add" if host == "codex" else "install"
            run([host, "plugin", operation, "voiceflow@voiceflow-plugins"], env, directory)
            inventory = json.loads(run([host, "plugin", "list", "--json"], env, directory))
            entries = inventory["installed"] if host == "codex" else inventory
            assert any(e.get("pluginId", e.get("id")) == "voiceflow@voiceflow-plugins" for e in entries)
            cached = list((config / "plugins/cache").glob("voiceflow-plugins/voiceflow/*/skills"))
            assert len(cached) == 1
            assert {path.parent.name for path in cached[0].glob("*/SKILL.md")} == expected
            assert (cached[0] / "voiceflow-setup/references/setup.md").is_file()
            for source in skills.rglob("*"):
                if source.is_file() and (source.suffix == ".md" or source.name == "LICENSE"):
                    assert (cached[0] / source.relative_to(skills)).read_bytes() == source.read_bytes()
            assert (cached[0].parent / "LICENSE").read_bytes() == (ROOT / "LICENSE").read_bytes()
            for name in ("mcp.json", ".mcp.json", ".codex-plugin/mcp.json"):
                assert (cached[0].parent / name).read_bytes() == (ROOT / "voiceflow" / name).read_bytes()
            if host == "codex":
                # Codex counts the tools of every server that installed plugins bundle against one shared budget,
                # so the plugin must bundle only the docs server there. Setup adds the account server to Codex's
                # own configuration, which does not count. Listing reads configuration; it does not sign in.
                servers = json.loads(run([host, "mcp", "list", "--json"], env, directory))
                assert [server["name"] for server in servers] == ["voiceflow-knowledge"], servers
            print(f"{host}: installed, enabled, all {len(expected)} skills/references and MCP configurations match source")
    print("Cursor runtime discovery must be tested in Cursor; no global configuration was changed.")


if __name__ == "__main__":
    main()
