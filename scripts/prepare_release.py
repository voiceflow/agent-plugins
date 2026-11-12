"""Prepare versioned release assets from a clean commit; never publish them."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

from build import build
from validate import validate

ROOT = Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def prepare_assets(site, output, changelog, expected_version, expected_commit):
    manifest = json.loads((site / "manifest.json").read_text(encoding="utf-8"))
    version = manifest["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", expected_version) or version != expected_version:
        raise ValueError("Release version does not match the package")
    if not re.fullmatch(r"[a-f0-9]{40}", expected_commit) or manifest["sourceCommit"] != expected_commit:
        raise ValueError("Release commit does not match the built source")
    if manifest["hasUncommittedChanges"] is not False:
        raise ValueError("Release assets require a clean, committed source tree")
    files = manifest["files"]
    if manifest["contentSHA256"] != sha(json.dumps(files, sort_keys=True).encode()):
        raise ValueError("Invalid content manifest")
    for name, checksum in files.items():
        path = site / name
        if (not path.resolve().is_relative_to(site.resolve()) or path.is_symlink()
                or not path.is_file() or sha(path.read_bytes()) != checksum):
            raise ValueError(f"Release asset verification failed: {name}")
    heading = re.search(rf"^## {re.escape(version)}(?: — [^\n]+)?\n(.*?)(?=^## |\Z)",
                        changelog, re.M | re.S)
    if not heading:
        raise ValueError("Release version is missing from CHANGELOG.md")
    if output.exists():
        raise ValueError("Release output already exists; rebuild before preparing it again")
    output.mkdir(parents=True)
    shutil.copyfile(site / "voiceflow.zip", output / f"voiceflow-{version}.zip")
    shutil.copyfile(site / "manifest.json", output / "manifest.json")
    # Only verified manifest entries are shipped; unrelated local files stay out.
    with zipfile.ZipFile(output / f"voiceflow-site-{version}.zip", "w", compresslevel=9) as archive:
        for name in sorted([*files, "manifest.json"]):
            entry = zipfile.ZipInfo("agents/" + name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, (site / name).read_bytes())
    notes = (f"# Voiceflow {version} (beta)\n\nSource commit: `{expected_commit}`.\n\n"
             + heading.group(1).strip() + "\n\n"
             "See the repository compatibility matrix for tested and experimental paths.\n"
             "The plugin ZIP contains the complete package; the site ZIP contains the\n"
             "versioned website payload. Verify downloads against SHA256SUMS.\n")
    (output / "release-notes.md").write_bytes(notes.encode("utf-8"))
    checksums = "".join(f"{sha(p.read_bytes())}  {p.name}\n" for p in sorted(output.iterdir()))
    (output / "SHA256SUMS").write_bytes(checksums.encode("utf-8"))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--expected-commit", required=True)
    args = parser.parse_args()
    validate()
    site = build()
    print(prepare_assets(site, ROOT / "dist/release", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"),
                         args.expected_version, args.expected_commit))


if __name__ == "__main__":
    main()
