def task_run_probe():
    "run mcp-probe to explore the mcp"
    return {
        "actions": ['bunx --bun @modelcontextprotocol/inspector']
    }

def task_lint():
    "run linters"
    return {
        "task_dep": ['ruff', 'ty'],
        "actions": None
    }

def task_ruff():
    "run ruff"
    return {
        "actions": ['ruff check']
    }

def task_ty():
    "run ty"
    return {
        "actions": ['ty check']
    }
