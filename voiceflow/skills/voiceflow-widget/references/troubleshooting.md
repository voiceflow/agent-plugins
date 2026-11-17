# Find the failing stage

For each new Voiceflow widget issue, use the
[docs MCP workflow](documentation.md) before choosing
a fix, including symptoms covered below. Inspect the actual install first when
needed to focus the question; reuse the answer while resolving the same issue.

Start with one affected URL, expected result, observed result, and whether this
is an editor preview, site preview, or live site. Inspect the existing install
and browser evidence before asking the user to paste code again.

| Symptom | Check first | Corrective direction |
| --- | --- | --- |
| No launcher at all | Actual page has script, platform permits it, page scope, consent, network/console | Fix the missing/blocked load. Don't rewrite the agent. |
| Launcher but no messages | Requested environment/version is available; runtime request succeeds | Check published versus draft targeting. Do not publish unrelated work. |
| Old colors or copy | Draft versus published settings, local `assistant` overrides, stylesheet/cache | Change the layer actually winning; read back before retrying. |
| Two launchers or repeated greetings | Site and page code, plugin/app embed, tag manager, multiple `load()` calls | Retain one owner and remove the duplicate path. |
| Disappears after navigation | DOM replaced, embedded target gone, SDK loaded but widget destroyed | Repair lifecycle/remount handling; SDK presence alone is not mount state. |
| Conversation resets on every route | Repeated initialization/destruction, persistence choice, changing user ID | Preserve the intended session; do not add more storage hacks. |
| Widget is cropped/tiny | Iframe versus outer page, embedded container dimensions, overflow | Use a page-level loader for floating mode or a real sized embedded target. |
| Styles don't apply | URL returns CSS, correct MIME/CSP, documented selectors, actual stylesheet hook | Prefer supported options; inspect the widget, not just page CSS. |
| Update fails with 403 | Access scopes versus a gated requested field | Explain which failed; repeating OAuth doesn't add an entitlement. |
| Custom button does nothing | SDK/widget ready, handler attached once, floating versus embedded mode | Open the existing initialized overlay; don't initialize on each click. |
| Wrong visitor details | Launch payload capture versus transcript metadata, stable intended identity | Trace the data flow; browser values do not authorize private access. |

For a CSP failure, identify the blocked resource and directive from the console.
Allow only the necessary resource through the site's existing policy; do not
disable CSP or add broad wildcards/`unsafe-inline` as a generic remedy. Likewise,
do not clear approved domains or bypass the site's consent handling to hide a
configuration error. Preserve the generated public/private-cloud endpoints.

If a platform strips JavaScript or lacks custom code on the current plan, say
so and give the supported account/platform step. If the agent lacks site access,
provide one concrete check for the user and resume from their result; do not
request passwords or private tokens in chat.

After a fix, repeat the failed check and one relevant regression check, such as
navigation after duplicate-loader removal. State whether a real conversation
was observed or only installation/configuration was inspected. See the
[verification sequence](installation.md#verify-the-browser-not-just-the-setting).
