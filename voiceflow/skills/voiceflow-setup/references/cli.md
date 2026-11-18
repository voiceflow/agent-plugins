# Connect through the CLI

Use this path only when the [setup guide](setup.md) selected a terminal that
can install and run tools in the customer's persistent environment. A temporary
chat sandbox is not such an environment.

Locate `vf`, then run `vf version` and `vf auth login --help`.
The tested baseline is **0.287.0**, with `--agent-mode`, `--no-browser`,
`--login-timeout`, and `workspace list`. Retain a newer compatible installation.
If an existing version lacks these capabilities, explain the needed upgrade;
preserve its location and do not overwrite an unrelated executable.

If absent, follow [the verified CLI install steps](installation.md). Use the
absolute path they print for the rest of this session if it is not on PATH.

Make this live read:

```sh
vf workspace list --agent-mode --no-interactive --timeout 20s --color never -o toon
```

Do not use `whoami` or stored credentials as proof of connection. Do not print
workspace details unless asked. An empty list is a connected account, not a
reason to create a workspace. Classify failures before acting:

Use TOON for this read on CLI 0.287.0. Its JSON passthrough can produce empty
output when a timeout cancels the response before the body is consumed; TOON
uses the fully decoded response. Empty output is not an empty workspace list.

- Missing/expired authentication or HTTP 401: continue to browser sign-in.
- HTTP 403: explain insufficient access; repeated login is not a permission fix.
- Network, rate limit, or service failure: retry a read once after a short
  indicated delay, otherwise report the blocker. Do not erase credentials.
- Invalid response or missing command: inspect help and the failure; do not
  claim connected.

To decide the result from parsed output, run the read as JSON instead:

```sh
vf workspace list --agent-mode --no-interactive --color never -o json
```

Leave out `--timeout` here. Stop the whole command after 25 seconds with the
host's command timeout instead, which avoids the body-cancellation issue. The
read passes only when all of these hold:

- The command exits with status 0.
- Standard output is one complete JSON object, with nothing after it.
- Its `workspaces` value is a list, and each item has a non-empty string `id`.
  An empty list passes.
- Neither standard output nor standard error is a JSON object with an
  `error_type` or `error` field.

A truncated, malformed, or empty response does not pass. Neither does JSON that
appears only on standard error. A JSON failure names its kind in `error_type`:

- `authentication_error`: continue to browser sign-in.
- `authorization_error`: explain insufficient access.
- `connection_error`, `rate_limit_error`, or `server_error`: a temporary
  failure; retry once as above.
- Any other `error_type`, or an `error` field: the request failed.

This check does not install, sign in, or repair anything.

## Sign in only if needed

Run as a background task with a bounded 15-minute lifetime. Read JSON events
from stderr while it runs:

```sh
vf auth login --agent-mode --no-browser --login-timeout 15m
```

Show the exact `authorization_url` from `awaiting_authorization`. Ask the user
to sign in or create a Voiceflow account in the browser and approve access.
Wait for that process; do not start competing login flows. Do not save auth URLs
or credentials in the repository. Wait for `signed_in`, then repeat the live
workspace read. A closed browser, expired link, or cancelled login is not success.
Offer one fresh login attempt if needed.

The callback runs on the CLI's machine. For SSH or containers, first establish
supported loopback port forwarding using the current CLI instructions. If the
user's browser cannot reach that listener, explain the limitation and offer
local setup. Never claim a remote loopback URL has completed authentication.

Never ask for passwords, tokens, or secret values in chat. `VF_TOKEN` overrides
stored OAuth credentials; inspect only its presence, not its value. Explain a
stale override before changing it.

Return to [guidance and completion](setup.md#3-make-guidance-available-in-this-host).
