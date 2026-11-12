"""Reject releases outside the protected default branch or without their tag; read-only GitHub access."""
import argparse
import json
import re
import subprocess
from urllib.parse import quote

GITHUB_ACTIONS_APP_ID = 15368
REQUIRED_CHECKS = {
    "security / Secrets and workflow security",
    "checks (ubuntu-latest)", "checks (macos-latest)", "checks (windows-latest)",
    "Conventional PR title",
}
SHA = re.compile(r"[a-f0-9]{40}")


def verify_rules(prefix, branch, api):
    # This metadata-readable endpoint returns only active rules applying to this
    # exact branch, including inherited rules. No administrative token is needed.
    rules = []
    for page in range(1, 11):
        batch = api(prefix + "/rules/branches/" + quote(branch, safe="") +
                    f"?per_page=100&page={page}")
        if not isinstance(batch, list) or not all(isinstance(rule, dict) for rule in batch):
            raise ValueError("Invalid active branch rules; release blocked")
        rules.extend(batch)
        if len(batch) < 100:
            break
    else:
        raise ValueError("Too many branch rules to verify; release blocked")

    types = {rule.get("type") for rule in rules if isinstance(rule.get("type"), str)}
    if not {"deletion", "non_fast_forward"} <= types:
        raise ValueError("Active rules must prevent branch deletion and force pushes")
    pull_requests_required = False
    checks = set()
    for rule in rules:
        parameters = rule.get("parameters")
        if not isinstance(parameters, dict):
            continue
        if rule.get("type") == "pull_request":
            count = parameters.get("required_approving_review_count")
            # The owner chose sole-maintainer operation: a PR and passing checks
            # are mandatory, but self-authored PRs cannot obtain self-approval.
            pull_requests_required |= (type(count) is int and count >= 0 and
                (count == 0 or parameters.get("require_code_owner_review") is True) and
                all(parameters.get(key) is True for key in (
                    "dismiss_stale_reviews_on_push", "required_review_thread_resolution")))
        if (rule.get("type") == "required_status_checks" and
                parameters.get("strict_required_status_checks_policy") is True):
            required = parameters.get("required_status_checks")
            if not isinstance(required, list):
                raise ValueError("Invalid required checks; release blocked")
            for check in required:
                if (isinstance(check, dict) and isinstance(check.get("context"), str) and
                        type(check.get("integration_id")) is int and
                        check["integration_id"] == GITHUB_ACTIONS_APP_ID):
                    checks.add(check["context"])
    if not pull_requests_required:
        raise ValueError("Active rules must require pull requests, stale-review dismissal, and resolved threads")
    if not REQUIRED_CHECKS <= checks:
        raise ValueError("Active rules must require all five current GitHub Actions checks with strict status checking")


def github_json(endpoint):
    result = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True,
                            encoding="utf-8", timeout=30)
    if result.returncode:
        raise RuntimeError("Could not verify release source with GitHub; release blocked")
    return json.loads(result.stdout)


def verify(repository, commit, version, workflow_ref, api=github_json):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Use an owner/repository identifier")
    if not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise ValueError("Use a full source commit SHA")
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Use a package version without v")
    prefix = "repos/" + repository
    default = api(prefix)["default_branch"]
    if not default or workflow_ref != "refs/heads/" + default:
        raise ValueError("Run the release workflow from the default branch")
    branch = api(prefix + "/branches/" + quote(default, safe=""))
    if branch.get("protected") is not True:
        raise ValueError("Releases require a protected default branch")
    verify_rules(prefix, default, api)
    head = branch["commit"]["sha"]
    if not re.fullmatch(r"[a-f0-9]{40}", head):
        raise ValueError("Invalid default branch revision")
    # Compare against the just-read immutable head, not a moving branch name.
    comparison = api(prefix + "/compare/" + commit + "..." + head)
    if (comparison.get("status") not in ("identical", "ahead")
            or comparison.get("merge_base_commit", {}).get("sha") != commit):
        raise ValueError("Release commit must already be on the default branch")
    verify_tag(prefix, version, commit, api)
    return default


def verify_tag(prefix, version, commit, api):
    # The Version workflow tags the release commit before it starts a draft.
    # A missing tag, or one at another commit, blocks the draft; nothing here writes.
    tag = "v" + version
    refs = api(prefix + "/git/matching-refs/tags/" + quote(tag, safe=""))
    if not isinstance(refs, list):
        raise ValueError("Invalid tag response; release blocked")
    matches = [ref for ref in refs if isinstance(ref, dict) and ref.get("ref") == "refs/tags/" + tag]
    if not matches:
        raise ValueError(f"Tag {tag} must exist before a draft release")
    target = matches[0].get("object")
    if isinstance(target, dict) and target.get("type") == "tag" and SHA.fullmatch(str(target.get("sha"))):
        target = api(prefix + "/git/tags/" + target["sha"]).get("object")
    if not isinstance(target, dict) or target.get("type") != "commit" or target.get("sha") != commit:
        raise ValueError(f"Tag {tag} must point at the release commit")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "commit", "version", "workflow-ref"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    try:
        branch = verify(args.repository, args.commit, args.version, args.workflow_ref)
        print(f"Release source verified on protected branch {branch}")
        return 0
    except (ValueError, RuntimeError) as error:
        print(str(error) if not isinstance(error, json.JSONDecodeError) else
              "Invalid GitHub response; release blocked")
    except (OSError, subprocess.SubprocessError, KeyError, TypeError):
        print("Release source verification could not complete; release blocked")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
