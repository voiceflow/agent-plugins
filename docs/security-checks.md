# Security checks

## Run the same secret checks locally

Install [Gitleaks](https://github.com/gitleaks/gitleaks) 8.30.1 and use a full
clone. CI pins its binary and checksum in `scripts/install_ci_tools.sh`; the CLI
needs no service account, paid action license, or upload of repository contents.

```sh
git fetch --all --tags
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 scripts/scan_secrets.py
```

For a shallow clone, fetch its full history first. The scanner refuses shallow
history or a missing package build. It scans all fetched Git refs (including
deleted content in earlier commits), current working files, and `dist/`, with
archive traversal to three levels and decoding to five levels. Unfetched refs,
GitHub comments, external services, encrypted files, and unknown credential
formats are outside this check. Pattern scanning cannot prove absence of secrets.

The wrapper prints rule, file, line, and commit only. Tool output is captured;
redacted reports stay in a temporary directory and are deleted after each scan. CI
does not upload scanner reports. A scanner error fails the check. Do not attach
raw tool logs when investigating a failure.

The upstream rule set remains enabled, supplemented by a Voiceflow API key rule.
Inline allow comments and local
`.gitleaksignore` files do not suppress this check. Do not add broad exclusions
or a baseline that hides historical findings. A verified false positive needs a
maintainer-reviewed, narrowly scoped rule exception and regression evidence.

`tests/test_security.py` creates temporary synthetic credentials and proves that
an ignored `.env`, a deleted historical credential, and an encoded credential
inside an archive are detected. It also checks Voiceflow key formats, clean files,
and scanner failure.
These tests require Gitleaks in the security job; ordinary offline tests skip
them when the executable is absent. No canary is sent to a provider or committed.

## CI and release boundaries

- Pushes and pull requests run security checks before the three-platform package
  checks and artifact uploads. Manual checks and draft releases use the same gate.
- A weekly security scan becomes active once the workflow is on the default branch.
- CI actions are pinned to commit SHAs. Downloaded Gitleaks and actionlint binaries
  are version- and checksum-pinned. Dependabot proposes GitHub Actions updates;
  maintainers review binary pins and upstream security releases separately.
- PR jobs use read-only repository permissions, no persisted checkout credentials,
  no customer secrets, and no `pull_request_target` execution of contributor code.
- Release assets are built and scanned in a read-only job. The write-enabled
  draft job downloads only the assets from that same workflow run and does not
  check out or execute repository code. It creates an unpublished draft only.

Workflow syntax is checked with [actionlint](https://github.com/rhysd/actionlint).
That is not a complete security audit of arbitrary workflow behavior: changes to
workflows, scanners, pinned tools, inventory, and release scripts need human review.

## Prevent local files entering packages

`package-files.txt` lists every file allowed in the plugin and website payload.
The build fails before replacing output if the source tree has extra or missing
files, an unsafe inventory path, or a symlink. This also catches ignored local
credentials accidentally placed in `voiceflow/`. Review new resources and add
their exact paths deliberately. Never regenerate the inventory blindly on error.

The inventory does not inspect file contents; secret scanning supplies a separate
check. `.gitignore` reduces accidental staging of common credentials and local
host settings, but is neither a scanner exclusion nor a publication allowlist.

## Respond to a finding

Stop publication. If a credential is real, revoke/rotate it through its provider
and notify the owner privately before relying on removal. Deleting the latest
file does not remove Git history or revoke a key. Follow [SECURITY](../SECURITY.md),
then coordinate history/artifact cleanup with the maintainer. Never automatically
rewrite shared history, paste the secret into an issue, or suppress the finding
to make CI green. Rerun the full scan after remediation.

## GitHub protections

CI starts after a push; it cannot block the initial upload of a secret. Require
GitHub secret scanning, push protection, and private vulnerability reporting.
The default branch requires a pull request, the security and three-platform
checks, and resolved review threads; force pushes and deletion are blocked.
The owner's sole-maintainer policy does not require an independent approval.
Require approval before running all outside contributors' workflows.
See [release policy](releasing.md). These settings are separate from this code
and are not enforced by a policy file or CODEOWNERS alone. After a transfer,
an administrator must confirm any settings hidden from write-access maintainers;
see the [transfer verification](../evals/reports/2026-10-17-transfer.md).
