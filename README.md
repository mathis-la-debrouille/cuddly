# cuddly

Local knowledge graph for AI coding agents. Indexes a codebase into a knowledge graph with embeddings, then serves optimized context to Claude Code via MCP.

## Install

```bash
pip install -e .
```

## Quickstart

```bash
# Index your project
cuddly index /path/to/project

# Search
cuddly search "how does authentication work"

# Start MCP server (add to Claude Code config)
cuddly serve --mcp
```

## Claude Code integration

Add to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "cuddly": {
      "command": "cuddly",
      "args": ["serve", "--mcp"]
    }
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "cuddly index --file $CLAUDE_FILE_PATH --quiet"
      }
    ]
  }
}
```

## MCP tools

| Tool | Description |
|------|-------------|
| `cuddly_search` | Semantic search across the codebase |
| `cuddly_context` | Budget-aware context assembly for a task |
| `cuddly_graph` | Explore the knowledge graph around a symbol |
| `cuddly_summary` | Project overview: files, entities, coverage |

## Config

Set via environment variables (prefix `CUDDLY_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `CUDDLY_DB_PATH` | `~/.cuddly/cuddly.db` | SQLite database path |
| `CUDDLY_EMBED_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformers model |
| `CUDDLY_EMBED_DEVICE` | `cpu` | Torch device (`cpu`, `cuda`, `mps`) |
| `CUDDLY_PROJECT_ROOT` | cwd | Default project root for indexing |
