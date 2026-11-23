# Other listings

## awesome-copilot (VS Code and GitHub Copilot)

- Submitted as https://github.com/github/awesome-copilot/issues/6477, an
  external plugin request. Automated intake passed, with the labels
  `external-plugin`, `ready-for-review`, and `third party`.
- A maintainer approves it and opens the pull request. Nothing to do until then.
- When a release changes the plugin, update the tag in the issue and check that
  intake passes again: `gh issue view 6477 -R github/awesome-copilot`.
- Copilot connects the account server with `dynamic=true`, because VS Code
  Copilot caps tools at 128.

## skills.sh

- There is no submission step. skills.sh lists repositories from install
  activity, and `skills.sh.json` points the skills CLI at `voiceflow/skills`.
- Test an install with a pinned CLI version, never `@latest`, for example
  `npx skills@1.8.1 add voiceflow/agent-plugins`.

## Status updates

When the owner asks for a status update, post a new message in the team channel
named in `.submissions/private.md`. Lead with the milestone, then give one line
per listing that is waiting, and on whom.
