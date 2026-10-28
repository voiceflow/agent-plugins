# Hand a refused action to the user

The Voiceflow MCP lists a few operations that it then refuses, because they
carry a credential or spend money. The refusal comes with guidance; it is not
a permission problem to retry. Prepare the exact command, let the user run it
in their own terminal, then continue with reads.

| Action                              | Why the MCP refuses it                        | Handoff                                              |
| ----------------------------------- | --------------------------------------------- | ---------------------------------------------------- |
| Set a secret value                  | The value would pass through the conversation | [CLI](#set-a-secret-value)                           |
| Connect an api-key integration      | Same                                          | [CLI](#connect-an-api-key-integration)               |
| Connect an OAuth or app integration | Needs a browser sign-in                       | [Voiceflow UI](#connect-an-oauth-or-app-integration) |
| Add a phone number                  | Spends money or takes carrier credentials     | [CLI or UI](#add-a-phone-number)                     |
| MCP server header as literal text   | A header value can be a credential            | [Secret reference or CLI](#mcp-server-headers)       |

## Ground rules

- Never ask for a secret value, API key, token, or carrier credential in the
  conversation. Never run these commands yourself: you would need the value.
- If the user pastes a credential anyway, do not use or repeat it. Tell them it
  is now in the conversation history and should be rotated, then hand over.
- Fill in IDs from live reads. Capitalized placeholders such as `PROJECT_ID`
  are yours to replace; variables such as `"$VF_SECRET_VALUE"` stay as written.
- The user needs the Voiceflow CLI signed in to the same workspace. If they do
  not have it, point them to [setup](../../voiceflow-setup/SKILL.md) or the UI step.
- Afterwards, confirm with a read. Handing over a command is not a success.

## Read a value without showing it

In bash or zsh, the value is typed without echo and stays out of shell history:

```sh
printf 'Secret value: '; read -rs VF_SECRET_VALUE; printf '\n'
```

In PowerShell:

```powershell
$secure = Read-Host 'Secret value' -AsSecureString
$VF_SECRET_VALUE = [System.Net.NetworkCredential]::new('', $secure).Password
```

The [operation contract](operations.md) keeps secrets out of command arguments.
These handoffs keep the value out of the conversation and shell history, and
the JSON ones pipe it in. A value passed as an argument, as with `--value`, is
still visible in the process list to other users of the same computer while
the command runs. Clear the variable after use: `unset VF_SECRET_VALUE`, or
`Remove-Variable VF_SECRET_VALUE, secure`.
Values that contain a double quote or a backslash do not fit the JSON
templates below; send the user to the Voiceflow UI for those.

## Set a secret value

Create the secret first if it does not exist: `voiceflow_secret.create` with a
`name` only. Never send `defaultValue`; a create that carries a value is
refused. The result gives the secret ID. Then hand over:

```sh
printf 'Value for ORDERS_API_KEY: '; read -rs VF_SECRET_VALUE; printf '\n'
vf secret set-value --secret-id SECRET_ID --project-id PROJECT_ID --value "$VF_SECRET_VALUE"
unset VF_SECRET_VALUE
```

```powershell
vf secret set-value --secret-id SECRET_ID --project-id PROJECT_ID --value $VF_SECRET_VALUE
```

Without environment flags the value goes to the `main` environment's published
version, which serves live traffic; `--version-variant draft` alone sets the
`main` draft. To set another environment, add
`--environment-alias ALIAS --version-variant draft` (or `published`). Each
version keeps its own value, and publishing does not copy a draft value, so set
every version the tool runs in. The UI step is Agent settings → Secrets.
Confirm with `voiceflow_secret.list`: the secret reports `hasValue`.

## Connect an api-key integration

`voiceflow_integration.list` reports each integration's `connectionType` and
`connectableViaAPI`. For `api-key`, read the connect operation's schema for this
integration's `credentials` shape: a string for some, an object for others.
Build the body with one variable per secret field, then pipe it in. A piped body
stays out of the process list.

```sh
printf 'API key: '; read -rs VF_CREDENTIAL; printf '\n'
printf '{"integration":"INTEGRATION","credentials":"%s"}' "$VF_CREDENTIAL" | vf integration connect --integration INTEGRATION --project-id PROJECT_ID
unset VF_CREDENTIAL
```

```powershell
$body = @{ integration = 'INTEGRATION'; credentials = $VF_CREDENTIAL } | ConvertTo-Json -Compress
$body | vf integration connect --integration INTEGRATION --project-id PROJECT_ID
```

The UI step is Agent settings → Integrations. Confirm with
`voiceflow_integration.list`: the integration reports `connected: true`.

## Connect an OAuth or app integration

These connect only through a browser sign-in. Tell the user: in Voiceflow, open
Agent settings → Integrations, choose the integration, and select Connect; a tab
opens at the provider. When they are done, read `voiceflow_integration.list`
again and check `connected`. A connection is not yet an agent tool.

## Add a phone number

The UI step: open the agent in Voiceflow and select Phone numbers in the
sidebar, under Deploy, then Create number. For a chat agent the item is called
SMS.

To connect a number the user already holds with the CLI, read the operation's
schema for their carrier's fields. A Twilio number, for example:

```sh
printf 'Twilio account SID: '; read -r VF_TWILIO_SID
printf 'Twilio auth token: '; read -rs VF_TWILIO_TOKEN; printf '\n'
printf '{"workspaceID":"WORKSPACE_ID","provider":"twilio","name":"Support line","value":"+15555550100","twilioAccountSID":"%s","twilioAuthToken":"%s"}' "$VF_TWILIO_SID" "$VF_TWILIO_TOKEN" | vf phone-number create
unset VF_TWILIO_SID VF_TWILIO_TOKEN
```

Buying a new number through Voiceflow charges the workspace. Offer it only when
the user asks to buy one and accepts the cost. Hand over the command with
`--dry-run` first, so the user can check the request it prints, then the same
command without that flag:

```sh
vf phone-number create --dry-run --stable-phone-number-create-request '{"workspaceID":"WORKSPACE_ID","provider":"voiceflow-telnyx","country":"US","areaCode":415,"name":"Support line"}'
```

Then find the number with `voiceflow_phone_number.list` and connect it with
`voiceflow_phone_number.assign`. Ask the user whether the agent takes calls or
texts: the project read does not say, and the server refuses a side that does
not fit the number or the project. Assigning, moving, renaming, and deleting a
number work over the MCP.

## MCP server headers

The MCP refuses a header value that is literal text with no `{name}` reference.
For a credential header, store the credential in a secret (see
[above](#set-a-secret-value)) and send the header value as `{ORDERS_API_KEY}`,
or `Bearer {ORDERS_API_KEY}`, with `voiceflow_mcp_server.create` or
`voiceflow_mcp_server.update`.

A header that is not a credential, such as a region, goes in Agent settings →
MCP servers, or in this command. Send the complete list: read the server first
and keep its existing headers.

```sh
vf mcp-server update --server-id SERVER_ID --project-id PROJECT_ID --environment-alias ALIAS --headers '[{"key":"X-Region","value":"eu-west"}]'
```
