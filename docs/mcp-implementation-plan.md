# Read-only MCP delivery

Scope: implement the approved architecture phases 1–2 for catalog reads, without changing the existing collection worker or verification work.

1. Add a real stdio client test for search → exact item → evidence history, source listing, partial-run reporting and invalid inputs. Observe failure before implementation.
2. Extract validated catalog queries shared by HTTP and MCP; retain stable item IDs and evidence fields.
3. Register five read-only tools with the official MCP Python SDK v1 compatibility line. No scheduler or recovery runs in the MCP process.
4. Run the complete test suite; document local client configuration and remaining model-integration work.

Completion boundary: real MCP protocol calls against a temporary SQLite database. This does not establish QwenPaw or domestic model acceptance.
