## graphify

This project has a graphify knowledge graph at graphify-out/.
An additional ecosystem graph is available at `C:\install\projects\codex_tools\graphify-out\`.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- If the question touches shared codex libraries, scaffolds, blueprints, or cross-repo ecosystem links, also read `C:\install\projects\codex_tools\graphify-out\GRAPH_REPORT.md`
- If a wiki exists under `C:\install\projects\codex_tools\graphify-out\wiki\`, navigate it before reading raw files in `codex_tools`
- If the graphify MCP server is active, utilize tools like `query_graph`, `get_node`, and `shortest_path` for precise architecture navigation instead of falling back to `grep`
- If the MCP server is not active, the CLI equivalents are `graphify query "<question>"`, `graphify path "<A>" "<B>"`, and `graphify explain "<concept>"` — prefer these over grep for cross-module questions
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)
