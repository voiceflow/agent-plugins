# Contributing

Contributions that make real customer tasks easier are welcome: clearer setup,
better recovery, corrected product guidance, focused skills, and reproducible
regression cases. Read the [code of conduct](CODE_OF_CONDUCT.md) and use
[support](SUPPORT.md) to choose the right place for a question or bug.

## Make a change locally

Fork or clone the repository, check out the implementation or release you want
to improve, and create a feature branch. Start from the default branch for the
development preview or a specific release tag for a released version.
Use Python 3.10+; no package installation or Voiceflow account is required for
the default checks.

```sh
git switch -c codex/describe-your-change
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
python3 scripts/build.py
```

| Location | Purpose |
| --- | --- |
| `voiceflow/skills/` | Customer instructions, linked references, and installers |
| `voiceflow/skills/voiceflow-setup/references/setup.md` | Canonical setup guide; edit this before generating website content |
| `scripts/` and `tests/` | Package validation, build, release preparation, and offline tests |
| `tests/fixtures/voiceflow-surface.json` | MCP and CLI names the skill checks accept; not packaged |
| `evals/` | Behavioral cases, protocols, and sanitized evidence |
| `docs/` | Compatibility, release, provenance, and measurement guidance |
| `dist/` | Generated output; do not commit it |
| `package-files.txt` | Reviewed list of files allowed into published packages |
| `AGENTS.md` and `CLAUDE.md` | Shared contributor rules and Claude Code entrypoint |

## Keep changes focused

Describe the customer problem and expected behavior. Keep setup focused on
connection and the user's next request. Product guidance must cite current
Voiceflow website documentation; exact operation fields must match released
CLI help or the connected MCP schema. Consult the docs MCP for new Voiceflow
troubleshooting issues and unresolved how-tos.

Use short skill entrypoints and conditional references. Preserve relative links,
normal host permissions, user edits, and the shared skill tree. Do not add private
repository dependencies, internal helpers, or approval-bypass hooks.
Keep the Voiceflow, Inc. MIT notice in every distributed skill and package.
When adding a packaged file, review it and add its exact path to
`package-files.txt`. Unexpected local files must fail packaging, even if ignored
by Git. Do not regenerate this inventory just to bypass that failure.

## Check skill references

`python3 scripts/validate.py` also checks that skill text names only things that
exist. It prints one `file:line: reason` line per problem and fails when a skill:

- names an MCP tool or operation that does not exist;
- names an MCP operation that the MCP always refuses, where the skill must
  give the `vf` command instead;
- names a `vf` command that the pinned CLI does not have;
- links to a missing file or heading, or names a missing `voiceflow-*` skill
  or `references/*.md` file;
- uses an internal tool or product name that is not public.

Write an MCP operation as `` `voiceflow_<tool>.<operation>` `` and a CLI command
as `` `vf <command> --flag` ``. In CI, `scripts/verify_cli.py` also runs
`--help` for every `vf` command the skills name and checks each flag they use.

The accepted names live in `tests/fixtures/voiceflow-surface.json`. MCP tools
come from the latest voiceflow/cli release, because that release tracks the
hosted MCP. CLI commands come from the pinned CLI version. Refresh the file
when either changes, then review the diff:

```sh
python3 scripts/refresh_surface.py
```

The script downloads public release files from GitHub and uses `GITHUB_TOKEN`
when it is set. Pass `--mcp-ref` or `--cli-ref` to choose other release tags, or
`--mcp-spec` and `--cli-spec` to read a downloaded spec. A refresh with no
upstream change leaves the file unchanged.

## Verify the right things

The three commands above run offline tests with temporary directories and fake
credentials. They never sign in or mutate a Voiceflow account. A missing live
account must not block an ordinary documentation contribution.

Before pushing, install Gitleaks and run `python3 scripts/scan_secrets.py` after
the build. See [security checks](docs/security-checks.md) for coverage, versions,
and private handling of findings. CI requires the scanner and tests it against
synthetic leaks before scanning history, source, and generated archives.

For installer or host packaging changes, maintainers also run the three-OS CI
jobs and `python3 scripts/verify_hosts.py` with installed Codex/Claude clients;
it uses disposable configurations. CLI contract checks use a localhost fixture.
For behavioral changes, update the relevant [acceptance cases](evals/README.md)
and describe the evidence you could collect. Live OAuth, paid model evaluations,
customer-account actions, and website deployment are separate, explicitly
scoped acceptance work. If you cannot run them, mark them unrun; maintainers
arrange the needed acceptance before expanding a support claim.

Never attach credentials, authorization URLs, customer transcripts, or private
source. Record model, host, package version, fixture, actions, and limitations
for model evaluations. Static checks do not prove model behavior.

## Submit and review

Open a focused pull request describing the problem, resulting behavior, checks,
and any unrun acceptance work. Maintainers review compatibility and evidence;
small changes are easier to assess. Version changes and the corresponding
[CHANGELOG](CHANGELOG.md) entry are coordinated by maintainers before release.
See [release policy](docs/releasing.md) for the release checklist.

By contributing, you agree to provide your contribution under this repository's
MIT license. Submit only material you have the right to contribute; preserve
any applicable third-party notices. No separate contributor agreement is
required by this repository.
