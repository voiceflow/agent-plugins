# Maintain and release

## Ownership and maintenance

The repository is owned by the [Voiceflow organization](https://github.com/voiceflow/agent-plugins).
The package is MIT-licensed, copyright Voiceflow, Inc. Braden Ream
([@Bradenream](https://github.com/Bradenream)) remains a maintainer with write
access; `.github/CODEOWNERS` routes reviews to that account. Changes to team
access, administrator permissions, and repository security settings belong to
the organization's administrators.

This is beta software. Fixes target the newest tagged release; older releases
and edited forks have no guaranteed backports. Before the first release, the
default branch is a development preview. Package versions follow SemVer:
patches correct guidance or compatible behavior, minors add capabilities, and
majors are breaking changes with a migration note. The pull request title picks
the change; see [how versions change](#how-versions-change). Use
[CHANGELOG](../CHANGELOG.md) for customer-visible changes. Package versions and
the pinned CLI version are independent.

Support is best effort with no response SLA. Report vulnerabilities through
[SECURITY](../SECURITY.md) and package/product problems through [SUPPORT](../SUPPORT.md).

## How versions change

Every merge to `main` can release a new package version. The pull request title
decides the version change, so nobody edits version numbers by hand.

Titles follow [Conventional Commits](https://www.conventionalcommits.org/):
`type(scope)!: summary`. The scope and the `!` are optional.

| Title | Version change |
| --- | --- |
| `!` after the type, or a `BREAKING CHANGE:` footer in the description | Major |
| `feat` | Minor |
| `fix` | Patch |
| `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert` | None |

The **Conventional PR title** check fails a pull request when:

- the title does not have that shape, or uses another type;
- the title uses `chore(release)`, which only the release workflow uses;
- it changes files under `voiceflow/` but is not `feat`, `fix`, or breaking;
- it changes the package version;
- a `feat`, `fix`, or breaking change adds no line under `## Unreleased` in the changelog;
- a breaking change adds no changelog line with the word migrate or migration;
- the description has a `BREAKING CHANGE:` footer but the title has no `!`.

Merges are squash merges. The squash commit takes the pull request title and
description, so the commit on `main` carries the title that passed the check.
Keep that default message when you merge. The Version workflow reads the commit
on `main`, and a commit without a conventional title changes no version.

After each push to `main`, the **Version** workflow runs two jobs:

1. A read-only job reads the commit titles and descriptions on `main` since the
   last `v*` tag. It skips `chore(release)` commits, and the largest change wins.
   If nothing changes the version, the run stops here. Otherwise the job writes
   the new version into every version file. It renames `## Unreleased` in the
   changelog to the new version and adds a new, empty `## Unreleased` above it.
   It runs `scripts/validate.py` and saves the change as a patch.
2. A write job in the `release` environment runs no repository code. It gets a
   short-lived token from the release GitHub App. It checks that the patch
   changes only the version files and the changelog. Then it pushes the commit
   `chore(release): X.Y.Z` and the tag `vX.Y.Z` together in one atomic push,
   and starts **Prepare draft package release** for that tag.

Runs never overlap. If `main` moves while a run works, the run pushes nothing,
and the next run covers both merges. If the App secrets are missing, the write
job fails and changes nothing. A maintainer can also start the workflow by hand
from `main`, for example after the App is set up.

The first run finds no `v*` tag. It tags the current version, without a change,
at the commit that set that version, and starts its draft. For 1.0.0 that commit
is the merge of pull request #11.

`VERSION_FILES` in `scripts/versioning.py` lists every file that holds the
package version. `scripts/validate.py` checks that they agree, and that the
changelog starts with `## Unreleased` and then the current version. The write
job repeats the list, and a unit test keeps the two lists equal.

## Before merging

Read current Voiceflow website docs and released CLI help for changed product
behavior. Run structural validation, unit tests, build, and isolated native host
verification. Require the security scan and Linux, macOS, and Windows CI jobs to pass. Inspect the
archive for license notices, complete references, and unintended material.
Behavioral changes also require the relevant [acceptance cases](../evals/README.md),
with unrun checks recorded honestly.

Use feature branches and obtain the owner's approval before merging. Do not
edit package versions; the Version workflow sets them. Add customer-facing changes
under `## Unreleased` in the changelog. Update the compatibility matrix when support
changes; never rewrite old evaluation reports to imply a rerun.

For a CLI baseline change, review release notes and auth changes, update all six
pinned checksums from the official release, and rerun installers and localhost
contracts. Do not replace checksums merely to bypass a failed download.

## Public repository protections

The public repository uses the following protections. Verify them after a
transfer or settings change:

- Create **active branch rulesets** covering the default branch. Classic branch
  protection alone is not sufficient for the automated release check below.
- Require a pull request for the default/release branch, dismiss stale reviews,
  and require resolved review threads. The owner chose sole-maintainer operation:
  zero approving reviews and no mandatory code-owner or last-pusher approval.
  The owner can merge their own passing PR; direct pushes remain blocked.
  Agent-driven merges still require the owner's explicit approval. When adding
  another maintainer or transferring ownership, revisit this policy and require
  approving code-owner review if independent review becomes available.
- Require these exact checks from the **GitHub Actions** app (integration ID
  `15368`), with strict/up-to-date checks enabled: `checks (ubuntu-latest)`,
  `checks (macos-latest)`, `checks (windows-latest)`,
  `security / Secrets and workflow security`, and `Conventional PR title`.
- Keep the branch rules in two rulesets. The first blocks force pushes and
  branch deletion, and its bypass list stays empty. The second requires the pull
  request and the five checks. Its only bypass is the release GitHub App, so the
  Version workflow can push the release commit. Verify bypass lists as an
  administrator rather than inferring them from read-only API output.
- Allow squash merges only, in the repository settings and in the ruleset's
  allowed merge methods. The squash commit message is the pull request title and
  description.
- Protect `v*` tags. Nobody may update or delete them, and only the release App
  may create them. A bypass applies to a whole ruleset, so the create rule needs
  a ruleset of its own.
- The release GitHub App has Contents write access to this repository only. Its
  client ID and private key are secrets in the `release` environment, which only
  `main` may use.
- Require workflow approval for all outside contributors.
- Verify CODEOWNERS resolves to a maintainer with repository access.
- Enable private vulnerability reporting as an additional route; keep the verified
  security email available independently.
- Enable and verify GitHub secret scanning and push protection. CI catches
  committed leaks after upload; push protection helps stop supported secrets before upload.

Confirm the rules in GitHub after enabling them. Written policy or a CODEOWNERS
file alone is not enforcement. Publication, transfer, and changing a paid plan
are separate owner decisions.

The required GitHub Actions policy permits GitHub-owned actions and repository-local
workflows, requires full commit-SHA action pins, keeps default tokens read-only,
and disallows workflow approval of pull requests. Expand the allowed publishers
only after reviewing a concrete dependency. Approval for all outside-contributor
workflows, native secret scanning/push protection, and private vulnerability
reporting must remain enabled. An organization administrator must verify settings
that are not visible to write-access maintainers after a transfer; a successful
CI run does not prove those settings. These settings do not create a paid subscription.

## Prepare a release

A release starts from an approved, clean commit whose package version matches
the changelog. Rebuild from that commit; never reuse local dirty artifacts.
The workflow must run from the current default branch, that branch must be
protected, and the selected commit must already be in its history. The guard
checks the actual active rules applying to that branch: required pull requests,
stale-review dismissal, resolved threads, all five strict checks bound
to GitHub Actions, and deletion/force-push prevention. Weak, missing, malformed,
or unreadable rules block the release. Zero required approvals is accepted for
the owner's sole-maintainer policy; a policy requiring positive approvals must
also require code-owner review. Disabled/evaluation rules do not qualify.
The guard is loaded from the default branch and rejects API errors,
feature-branch dispatches, and unmerged commits before running candidate code.
It uses GitHub's [active branch rules API](https://docs.github.com/en/rest/repos/rules#get-rules-for-a-branch),
which requires only metadata read access; no administrative CI secret is added.
This API covers rulesets, not classic branch protection. The administrator must
also verify bypass policy at launch. Write-capable maintainers remain trusted:
this workflow cannot prevent them from changing another workflow or repository settings.
Removing branch protection blocks GitHub draft releases; local asset preparation
remains available for review. The guard also requires the tag `vX.Y.Z` to
exist already at the selected commit; the Version workflow creates it.

```sh
python3 scripts/prepare_release.py --expected-version VERSION --expected-commit FULL_COMMIT_SHA
```

Replace VERSION and FULL_COMMIT_SHA with a tagged release. Preparation verifies
version, clean-source provenance, and file hashes, then writes to `dist/release/`:

- `voiceflow-VERSION.zip`: the portable plugin and native adapters.
- `voiceflow-site-VERSION.zip`: the complete `agents/` website payload.
- `manifest.json`: source commit, package version, and payload hashes.
- `SHA256SUMS`: hashes for both archives, manifest, and release notes.
- `release-notes.md`: the matching changelog entry and source revision.

Preparation does not create a tag, release, or deployment. It rejects stale or
tampered content and an existing output directory. Rebuilding replaces only the
repository's generated `dist/` directory.

The Version workflow starts **Prepare draft package release** after it pushes
a tag. A maintainer can also run it from the default branch with a tagged commit
and its version, for example after a failed run. It reruns security and
three-platform checks for that commit, prepares and scans the exact assets with
read-only permissions, and creates an **unpublished beta draft** in a separate
write-enabled job that does not execute repository code. That job never creates,
moves, or deletes a tag, and never replaces an existing release or draft.
No workflow publishes a release automatically. Review its notes, compatibility
limits, checksums, source commit, and all assets before the owner publishes it.
For a failed or ambiguous run, inspect existing drafts before retrying.

Changelog headings are bare version numbers; the GitHub release records the
date. Keep released tags and assets immutable; correct mistakes with a new version. GitHub
releases provide the persistent download record; short-lived CI artifacts are
for review only. This repo has not yet published its first release.

## Upgrade, rollback, and transfer

Follow [client updates and removal](../voiceflow/skills/voiceflow-setup/references/clients.md).
Use native host update commands or the standalone installer's `--update`, which
refuses user-edited files. Review changes before updating and preserve local edits.

If a release fails, keep the previous approved website bundle for atomic rollback
and publish a corrective package version. Customers can intentionally reinstall
an earlier package using the same conflict-preserving process, but a website
rollback does not downgrade installed plugins or revoke OAuth access.

Test anonymous retrieval and fresh installation of the setup guide and its
references after repository publication, transfer, or URL changes. Keep experimental paths labeled;
only expand claims after actual host acceptance. Use the
[website publishing contract](website-publishing.md) for the separate site rollout.

After any future transfer or rename, update repository/issue links, reviewer
ownership, and GitHub metadata, then verify redirects and fresh installs. Keep
plugin name `voiceflow`, marketplace name `voiceflow-plugins`, and skill names
stable. Do not recreate the repository at its previous location: that removes
GitHub's redirect. Marketplace submission is independent of repository publication.

Docs requests use the existing Knowledge MCP logging, as explained in
[measurement](measurement.md); releases do not add a separate analytics service.
