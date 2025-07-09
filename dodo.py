def task_run_probe():
    "run mcp-probe to explore the mcp"
    return {
        "actions": ['mcp-probe debug --stdio "uv run sb_mcp"']
    }
