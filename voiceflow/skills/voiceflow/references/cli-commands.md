<!-- Generated from the MCP and CLI snapshot by python3 scripts/cli_commands.py. Run it instead of editing this file. -->
# Run an account tool with the CLI

Use this table only for an account MCP tool that your host does not list, as
the [operation contract](operations.md#use-the-cli-for-a-hidden-tool) says.
Each row gives the Voiceflow CLI command that runs the same operation.
The table matches CLI 0.335.0 and the MCP tools of the same release.

MCP fields and CLI flags differ, so read `vf <command> --help` before the
first call. Add `--agent-mode --no-interactive --color never -o json` to each command.

| MCP tool | CLI command |
| --- | --- |
| `vf_agent_add_tool_message` | `vf agent add-tool-message` |
| `vf_agent_delete_tool_message` | `vf agent delete-tool-message` |
| `vf_agent_get` | `vf agent get` |
| `vf_agent_get_initialization_workflow` | `vf agent get-initialization-workflow` |
| `vf_agent_patch_instructions` | `vf agent patch-instructions` |
| `vf_agent_patch_prompt` | `vf agent patch-prompt` |
| `vf_agent_patch_pronunciation` | `vf agent patch-pronunciation` |
| `vf_agent_patch_voices` | `vf agent patch-voices` |
| `vf_agent_read_instructions` | `vf agent read-instructions` |
| `vf_agent_read_prompt` | `vf agent read-prompt` |
| `vf_agent_search_instructions` | `vf agent search-instructions` |
| `vf_agent_search_prompt` | `vf agent search-prompt` |
| `vf_agent_search_voices` | `vf agent search-voices` |
| `vf_agent_set_initialization_workflow` | `vf agent set-initialization-workflow` |
| `vf_agent_update` | `vf agent update` |
| `vf_agent_update_tool_message` | `vf agent update-tool-message` |
| `vf_analytics_query_api_tool_usage` | `vf analytics query api-tool-usage` |
| `vf_analytics_query_call_count` | `vf analytics query call-count` |
| `vf_analytics_query_call_duration` | `vf analytics query call-duration` |
| `vf_analytics_query_category_token_usage` | `vf analytics query category-token-usage` |
| `vf_analytics_query_daily_token_usage` | `vf analytics query daily-token-usage` |
| `vf_analytics_query_entity_token_usage` | `vf analytics query entity-token-usage` |
| `vf_analytics_query_function_usage` | `vf analytics query function-usage` |
| `vf_analytics_query_hourly_organization_token_usage` | `vf analytics query hourly-organization-token-usage` |
| `vf_analytics_query_hourly_project_token_usage` | `vf analytics query hourly-project-token-usage` |
| `vf_analytics_query_integration_usage` | `vf analytics query integration-usage` |
| `vf_analytics_query_intent_usage` | `vf analytics query intent-usage` |
| `vf_analytics_query_knowledge_base_document_usage` | `vf analytics query knowledge-base-document-usage` |
| `vf_analytics_query_mcp_tool_usage` | `vf analytics query mcp-tool-usage` |
| `vf_analytics_query_objective_metrics` | `vf analytics query objective-metrics` |
| `vf_analytics_query_organization_token_usage` | `vf analytics query organization-token-usage` |
| `vf_analytics_query_playbook_usage` | `vf analytics query playbook-usage` |
| `vf_analytics_query_project_interaction_count` | `vf analytics query project-interaction-count` |
| `vf_analytics_query_project_token_usage` | `vf analytics query project-token-usage` |
| `vf_analytics_query_project_transcript_cost` | `vf analytics query project-transcript-cost` |
| `vf_analytics_query_project_transcript_count` | `vf analytics query project-transcript-count` |
| `vf_analytics_query_prompt_usage` | `vf analytics query prompt-usage` |
| `vf_analytics_query_unique_user_count` | `vf analytics query unique-user-count` |
| `vf_analytics_query_workflow_usage` | `vf analytics query workflow-usage` |
| `vf_analytics_query_workspace_interaction_count` | `vf analytics query workspace-interaction-count` |
| `vf_analytics_query_workspace_token_usage` | `vf analytics query workspace-token-usage` |
| `vf_analytics_query_workspace_transcript_count` | `vf analytics query workspace-transcript-count` |
| `vf_api_tool_create` | `vf api-tool create` |
| `vf_api_tool_create_variable` | `vf api-tool variable create` |
| `vf_api_tool_delete` | `vf api-tool delete` |
| `vf_api_tool_delete_variable` | `vf api-tool variable delete` |
| `vf_api_tool_execute` | `vf api-tool execute` |
| `vf_api_tool_get` | `vf api-tool get` |
| `vf_api_tool_get_schema` | `vf api-tool get-schema` |
| `vf_api_tool_get_variable` | `vf api-tool variable get` |
| `vf_api_tool_list` | `vf api-tool list` |
| `vf_api_tool_list_variables` | `vf api-tool variable list` |
| `vf_api_tool_update` | `vf api-tool update` |
| `vf_api_tool_update_variable` | `vf api-tool variable update` |
| `vf_conversation_delete_state` | `vf conversation state delete` |
| `vf_conversation_get_state` | `vf conversation state get` |
| `vf_conversation_run_script` | `vf conversation run-script` |
| `vf_conversation_send` | `vf conversation send` |
| `vf_conversation_update_state` | `vf conversation state update` |
| `vf_conversation_update_variables` | `vf conversation state update-variables` |
| `vf_document_create_folder` | `vf document folder create` |
| `vf_document_create_managed_sitemap` | `vf document create-managed-sitemap` |
| `vf_document_create_sitemap` | `vf document create-sitemap` |
| `vf_document_create_table` | `vf document create-table` |
| `vf_document_create_text` | `vf document create-text` |
| `vf_document_create_url` | `vf document create-url` |
| `vf_document_delete` | `vf document delete` |
| `vf_document_delete_folder` | `vf document folder delete` |
| `vf_document_get` | `vf document get` |
| `vf_document_list` | `vf document list` |
| `vf_document_list_changes` | `vf document list-changes` |
| `vf_document_list_folders` | `vf document folder list` |
| `vf_document_preview_sitemap` | `vf document preview-sitemap` |
| `vf_document_update` | `vf document update` |
| `vf_document_update_folder` | `vf document folder update` |
| `vf_document_update_managed_sitemap` | `vf document update-managed-sitemap` |
| `vf_environment_audit_wiring` | `vf environment audit-wiring` |
| `vf_environment_clone` | `vf environment clone` |
| `vf_environment_compile` | `vf environment compile` |
| `vf_environment_delete` | `vf environment delete` |
| `vf_environment_diff` | `vf environment diff` |
| `vf_environment_get` | `vf environment get` |
| `vf_environment_list` | `vf environment list` |
| `vf_environment_merge` | `vf environment merge` |
| `vf_environment_publish` | `vf environment publish` |
| `vf_environment_search_text` | `vf environment search-text` |
| `vf_environment_update` | `vf environment update` |
| `vf_environment_update_traffic_split` | `vf environment update-traffic-split` |
| `vf_evaluation_create` | `vf evaluation create` |
| `vf_evaluation_delete` | `vf evaluation delete` |
| `vf_evaluation_get` | `vf evaluation get` |
| `vf_evaluation_list` | `vf evaluation list` |
| `vf_evaluation_queue_runs` | `vf evaluation queue-runs` |
| `vf_evaluation_run` | `vf evaluation run` |
| `vf_evaluation_update` | `vf evaluation update` |
| `vf_function_check` | `vf function check` |
| `vf_function_create` | `vf function create` |
| `vf_function_create_path` | `vf function path create` |
| `vf_function_create_variable` | `vf function variable create` |
| `vf_function_delete` | `vf function delete` |
| `vf_function_delete_path` | `vf function path delete` |
| `vf_function_delete_variable` | `vf function variable delete` |
| `vf_function_execute` | `vf function execute` |
| `vf_function_get` | `vf function get` |
| `vf_function_get_path` | `vf function path get` |
| `vf_function_get_schema` | `vf function get-schema` |
| `vf_function_get_variable` | `vf function variable get` |
| `vf_function_list` | `vf function list` |
| `vf_function_list_paths` | `vf function path list` |
| `vf_function_list_variables` | `vf function variable list` |
| `vf_function_update` | `vf function update` |
| `vf_function_update_path` | `vf function path update` |
| `vf_function_update_variable` | `vf function variable update` |
| `vf_integration_add_tool` | `vf integration add-tool` |
| `vf_integration_disconnect` | `vf integration disconnect` |
| `vf_integration_execute` | `vf integration execute` |
| `vf_integration_get_schema` | `vf integration get-schema` |
| `vf_integration_list` | `vf integration list` |
| `vf_knowledge_base_query` | `vf knowledge-base query` |
| `vf_mcp_server_create` | `vf mcp-server create` |
| `vf_mcp_server_delete` | `vf mcp-server delete` |
| `vf_mcp_server_get` | `vf mcp-server get` |
| `vf_mcp_server_list` | `vf mcp-server list` |
| `vf_mcp_server_sync` | `vf mcp-server sync` |
| `vf_mcp_server_update` | `vf mcp-server update` |
| `vf_mcp_tool_execute` | `vf mcp-tool execute` |
| `vf_mcp_tool_get` | `vf mcp-tool get` |
| `vf_mcp_tool_get_schema` | `vf mcp-tool get-schema` |
| `vf_mcp_tool_list` | `vf mcp-tool list` |
| `vf_message_add_variant` | `vf message add-variant` |
| `vf_message_create` | `vf message create` |
| `vf_message_delete` | `vf message delete` |
| `vf_message_delete_variant` | `vf message delete-variant` |
| `vf_message_get` | `vf message get` |
| `vf_message_get_many` | `vf message get-many` |
| `vf_message_update` | `vf message update` |
| `vf_message_update_variant` | `vf message update-variant` |
| `vf_persona_create` | `vf persona create` |
| `vf_persona_delete` | `vf persona delete` |
| `vf_persona_get` | `vf persona get` |
| `vf_persona_list` | `vf persona list` |
| `vf_persona_update` | `vf persona update` |
| `vf_phone_number_assign` | `vf phone-number assign` |
| `vf_phone_number_delete` | `vf phone-number delete` |
| `vf_phone_number_get` | `vf phone-number get` |
| `vf_phone_number_list` | `vf phone-number list` |
| `vf_phone_number_unassign` | `vf phone-number unassign` |
| `vf_phone_number_update` | `vf phone-number update` |
| `vf_playbook_add_tool_message` | `vf playbook add-tool-message` |
| `vf_playbook_create` | `vf playbook create` |
| `vf_playbook_create_path` | `vf playbook path create` |
| `vf_playbook_delete` | `vf playbook delete` |
| `vf_playbook_delete_path` | `vf playbook path delete` |
| `vf_playbook_delete_tool_message` | `vf playbook delete-tool-message` |
| `vf_playbook_duplicate` | `vf playbook duplicate` |
| `vf_playbook_get` | `vf playbook get` |
| `vf_playbook_list` | `vf playbook list` |
| `vf_playbook_list_paths` | `vf playbook path list` |
| `vf_playbook_patch_instructions` | `vf playbook patch-instructions` |
| `vf_playbook_read_instructions` | `vf playbook read-instructions` |
| `vf_playbook_search_instructions` | `vf playbook search-instructions` |
| `vf_playbook_update` | `vf playbook update` |
| `vf_playbook_update_path` | `vf playbook path update` |
| `vf_playbook_update_tool_message` | `vf playbook update-tool-message` |
| `vf_project_create` | `vf project create` |
| `vf_project_delete` | `vf project delete` |
| `vf_project_get` | `vf project get` |
| `vf_project_list` | `vf project list` |
| `vf_project_update` | `vf project update` |
| `vf_prompt_create` | `vf prompt create` |
| `vf_prompt_delete` | `vf prompt delete` |
| `vf_prompt_get` | `vf prompt get` |
| `vf_prompt_get_many` | `vf prompt get-many` |
| `vf_prompt_update` | `vf prompt update` |
| `vf_prompt_update_settings` | `vf prompt update-settings` |
| `vf_secret_create` | `vf secret create` |
| `vf_secret_delete` | `vf secret delete` |
| `vf_secret_list` | `vf secret list` |
| `vf_secret_list_overrides` | `vf secret list-overrides` |
| `vf_test_cancel_runs` | `vf test run cancel` |
| `vf_test_create` | `vf test create` |
| `vf_test_create_check` | `vf test check create` |
| `vf_test_create_run` | `vf test run create` |
| `vf_test_create_turn` | `vf test turn create` |
| `vf_test_delete` | `vf test delete` |
| `vf_test_delete_check` | `vf test check delete` |
| `vf_test_delete_turn` | `vf test turn delete` |
| `vf_test_get` | `vf test get` |
| `vf_test_get_check` | `vf test check get` |
| `vf_test_get_run` | `vf test run get` |
| `vf_test_get_turn` | `vf test turn get` |
| `vf_test_list` | `vf test list` |
| `vf_test_list_checks` | `vf test check list` |
| `vf_test_list_turns` | `vf test turn list` |
| `vf_test_query_run_logs` | `vf test run query-logs` |
| `vf_test_search_runs` | `vf test run search` |
| `vf_test_update` | `vf test update` |
| `vf_test_update_check` | `vf test check update` |
| `vf_test_update_turn` | `vf test turn update` |
| `vf_test_wait_runs` | `vf test run wait` |
| `vf_tool_create` | `vf tool create` |
| `vf_tool_delete` | `vf tool delete` |
| `vf_tool_get` | `vf tool get` |
| `vf_tool_list` | `vf tool list` |
| `vf_tool_move` | `vf tool move` |
| `vf_tool_update` | `vf tool update` |
| `vf_transcript_files` | `vf transcript files` |
| `vf_transcript_get` | `vf transcript get` |
| `vf_transcript_grep` | `vf transcript grep` |
| `vf_transcript_property_create` | `vf transcript property create` |
| `vf_transcript_property_delete` | `vf transcript property delete` |
| `vf_transcript_property_get` | `vf transcript property get` |
| `vf_transcript_property_list` | `vf transcript property list` |
| `vf_transcript_property_set_value` | `vf transcript property set-value` |
| `vf_transcript_property_update` | `vf transcript property update` |
| `vf_transcript_query_logs` | `vf transcript query-logs` |
| `vf_transcript_search` | `vf transcript search` |
| `vf_variable_create` | `vf variable create` |
| `vf_variable_delete` | `vf variable delete` |
| `vf_variable_get` | `vf variable get` |
| `vf_variable_list` | `vf variable list` |
| `vf_variable_update` | `vf variable update` |
| `vf_widget_get` | `vf widget get` |
| `vf_widget_get_snippet` | `vf widget get-snippet` |
| `vf_widget_update` | `vf widget update` |
| `vf_workflow_add_actions` | `vf workflow add-actions` |
| `vf_workflow_add_blocks` | `vf workflow add-blocks` |
| `vf_workflow_add_branch` | `vf workflow add-branch` |
| `vf_workflow_arrange_blocks` | `vf workflow arrange-blocks` |
| `vf_workflow_create` | `vf workflow create` |
| `vf_workflow_create_block` | `vf workflow create-block` |
| `vf_workflow_delete` | `vf workflow delete` |
| `vf_workflow_delete_block` | `vf workflow delete-block` |
| `vf_workflow_delete_branch` | `vf workflow delete-branch` |
| `vf_workflow_delete_step` | `vf workflow delete-step` |
| `vf_workflow_duplicate` | `vf workflow duplicate` |
| `vf_workflow_get` | `vf workflow get` |
| `vf_workflow_get_raw` | `vf workflow get-raw` |
| `vf_workflow_get_step` | `vf workflow get-step` |
| `vf_workflow_insert_step` | `vf workflow insert-step` |
| `vf_workflow_link` | `vf workflow link` |
| `vf_workflow_link_many` | `vf workflow link-many` |
| `vf_workflow_list` | `vf workflow list` |
| `vf_workflow_reorder_actions` | `vf workflow reorder-actions` |
| `vf_workflow_replace_action` | `vf workflow replace-action` |
| `vf_workflow_split_block` | `vf workflow split-block` |
| `vf_workflow_unlink` | `vf workflow unlink` |
| `vf_workflow_update` | `vf workflow update` |
| `vf_workflow_update_block` | `vf workflow update-block` |
| `vf_workflow_update_branch` | `vf workflow update-branch` |
| `vf_workflow_update_step` | `vf workflow update-step` |
| `vf_workspace_create` | `vf workspace create` |
| `vf_workspace_delete` | `vf workspace delete` |
| `vf_workspace_get` | `vf workspace get` |
| `vf_workspace_list` | `vf workspace list` |
| `vf_workspace_update` | `vf workspace update` |

## Tools with no CLI command

These tools have no CLI command of their own. A `create_many` tool creates
several items in one call. Where this table names a command, run that
command once for each item instead. Those are separate calls: when one
fails, the items created before it stay.

| MCP tool | Instead |
| --- | --- |
| `vf_agent_add_workflow` | No CLI command |
| `vf_agent_remove_workflow` | No CLI command |
| `vf_agent_update_workflow` | No CLI command |
| `vf_api_tool_create_many` | `vf api-tool create`, once per item |
| `vf_api_tool_create_many_variables` | `vf api-tool variable create`, once per item |
| `vf_environment_export` | No CLI command |
| `vf_function_create_many` | `vf function create`, once per item |
| `vf_function_create_many_paths` | `vf function path create`, once per item |
| `vf_function_create_many_variables` | `vf function variable create`, once per item |
| `vf_message_create_many` | `vf message create`, once per item |
| `vf_playbook_create_many` | `vf playbook create`, once per item |
| `vf_test_create_many` | `vf test create`, once per item |
| `vf_test_create_many_checks` | `vf test check create`, once per item |
| `vf_test_create_many_runs` | `vf test run create`, once per item |
| `vf_test_create_many_turns` | `vf test turn create`, once per item |
| `vf_tool_create_many` | `vf tool create`, once per item |
| `vf_variable_create_many` | `vf variable create`, once per item |

## Tools the MCP refuses in some cases

Through the CLI, send only what the MCP would accept. When the MCP would
refuse the request, hand the action to the user.

| MCP tool | When the MCP refuses it |
| --- | --- |
| `vf_mcp_server_create` | Only when a header value is literal text that carries no `{name}` reference at all. |
| `vf_mcp_server_update` | Only when a header value is literal text that carries no `{name}` reference at all. |
| `vf_secret_create` | Only when the request body carries a non-empty `defaultValue`. |

## Commands only the user runs

These operations carry a credential or spend money, so they are never MCP
tools. Prepare the command and let the user run it in their own terminal.
Never run one yourself.

- `vf integration connect`
- `vf phone-number create`
- `vf secret set-value`
