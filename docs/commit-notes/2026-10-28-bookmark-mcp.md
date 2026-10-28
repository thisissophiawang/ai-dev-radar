# Idempotent bookmark MCP operations

The assistant can now save and remove bookmarks through MCP using the same service as the dashboard. A request key and payload are recorded atomically with the mutation. Identical retries return the original receipt; conflicting key reuse fails. Replaying an old deletion does not remove a later re-save. Clients should retrieve the item to report its current state.

This delivery also corrects the product scope to a local personal AI development intelligence assistant, replaces CRM-specific examples, adds an ordered roadmap, and requires PROJECT_STATUS.md updates with every development change.

Validation: 14 tests passed, including real stdio SDK calls, persistence across store reopening, concurrent identical requests, conflict handling and read-back. One existing Starlette/httpx deprecation warning remains. Git diff whitespace checks passed.

Remaining: business Skill runtime loading, QwenPaw and domestic-model integration, persistent conversations, collection-start MCP ownership and multi-day unattended collection validation. Restart the dashboard process to load the updated Python code. This delivery does not merge the feature branch into main.
