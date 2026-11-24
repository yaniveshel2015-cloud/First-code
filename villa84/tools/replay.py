"""Rebuild the villa84 source files from the session transcript.

Replays, in order: Write/Edit tool calls on villa84 files, Python heredoc patches run from Bash, and `python3 patch_*.py` runs.
Also dumps Read/sed outputs of partially-seen files (model.py, draw.py, symbols.py, vlib.py) for manual assembly.
"""
import ast
import json
import os
import re
import subprocess
import sys

JSONL = sys.argv[1]
STOP_TEXT = sys.argv[2]            # first user message of the new request: replay stops there
SP = "/tmp/claude-0/-home-user-First-code/bd5e9e04-ec04-58b0-88a8-01d35cd61986/scratchpad"
V = os.path.join(SP, "villa84")
DUMP = os.path.join(SP, "recover")
os.makedirs(V, exist_ok=True)
os.makedirs(DUMP, exist_ok=True)

events, uses = [], {}
for line in open(JSONL, encoding="utf-8"):
    d = json.loads(line)
    msg = d.get("message") or {}
    c = msg.get("content")
    if d.get("type") == "user":
        txt = c if isinstance(c, str) else " ".join(x.get("text", "") for x in (c or []) if isinstance(x, dict) and x.get("type") == "text")
        if STOP_TEXT in (txt or ""):
            break
    if not isinstance(c, list):
        continue
    for x in c:
        if not isinstance(x, dict):
            continue
        if x.get("type") == "tool_use":
            uses[x["id"]] = x
            events.append(("use", x))
        elif x.get("type") == "tool_result":
            u = uses.get(x.get("tool_use_id"))
            content = x.get("content")
            if isinstance(content, list):
                content = "".join(y.get("text", "") for y in content if isinstance(y, dict))
            events.append(("result", (u, content or "")))


def tolerant(src):
    """Wrap each top-level statement in try/except so one failing file patch does not stop the others."""
    tree = ast.parse(src)
    body = []
    for st in tree.body:
        if isinstance(st, (ast.Import, ast.ImportFrom, ast.FunctionDef)):
            body.append(st)
            continue
        h = ast.ExceptHandler(type=ast.Name("Exception", ast.Load()), name="_e",
                              body=[ast.Expr(ast.Call(ast.Name("print", ast.Load()), [ast.Constant("  stmt failed:"), ast.Call(ast.Name("repr", ast.Load()), [ast.Name("_e", ast.Load())], [])], []))])
        body.append(ast.Try(body=[st], handlers=[h], orelse=[], finalbody=[]))
    tree.body = body
    ast.fix_missing_locations(tree)
    return compile(tree, "<patch>", "exec")


log = open(os.path.join(DUMP, "replay.log"), "w", encoding="utf-8")
n_dump = 0
for kind, ev in events:
    if kind == "use":
        name, inp = ev["name"], ev.get("input", {})
        fp = inp.get("file_path", "")
        if name == "Write" and "/scratchpad/villa84/" in fp:
            open(fp, "w", encoding="utf-8").write(inp["content"])
            log.write(f"WRITE {os.path.basename(fp)}\n")
        elif name == "Edit" and "/scratchpad/villa84/" in fp:
            if os.path.exists(fp):
                s = open(fp, encoding="utf-8").read()
                if inp["old_string"] in s:
                    s = s.replace(inp["old_string"], inp["new_string"]) if inp.get("replace_all") else s.replace(inp["old_string"], inp["new_string"], 1)
                    open(fp, "w", encoding="utf-8").write(s)
                    log.write(f"EDIT ok {os.path.basename(fp)}\n")
                else:
                    log.write(f"EDIT miss {os.path.basename(fp)}\n")
        elif name == "Bash":
            cmd = inp.get("command", "")
            for m in re.finditer(r"python3? - <<'PY'\n(.*?)\nPY", cmd, re.S):
                code = m.group(1)
                if "/root/.claude/projects" in code or "jsonl" in code:
                    continue
                log.write("HEREDOC " + code.splitlines()[0][:80] + "\n")
                cwd = os.getcwd()
                os.chdir(V)
                try:
                    exec(tolerant(code), {"__name__": "__patch__", "print": lambda *a, **k: log.write("  " + " ".join(map(str, a)) + "\n")})
                except Exception as e:
                    log.write(f"  heredoc failed: {e!r}\n")
                os.chdir(cwd)
            for m in re.finditer(r"python3 (patch_\w+\.py)", cmd):
                r = subprocess.run([sys.executable, m.group(1)], cwd=V, capture_output=True, text=True)
                log.write(f"RUN {m.group(1)} rc={r.returncode} {r.stdout.strip()[:80]} {r.stderr.strip()[-200:]}\n")
    else:
        u, content = ev
        if not u:
            continue
        inp = u.get("input", {})
        tag = None
        if u["name"] == "Read" and any(k in inp.get("file_path", "") for k in ("model.py", "draw.py", "symbols.py", "sheets.py", "vlib.py")):
            tag = f'read_{os.path.basename(inp["file_path"])}_{inp.get("offset")}_{inp.get("limit")}'
        elif u["name"] == "Bash" and re.search(r"sed -n '?\d+,\d+p'? \S*(model|draw|symbols|vlib|sheets)\.py", inp.get("command", "")):
            tag = "sed_" + "_".join(re.findall(r"sed -n '?(\d+,\d+)p'? \S*?(\w+\.py)", inp["command"])[0]).replace(",", "-")
        if tag == "read_sheets.py_None_None":
            body = []
            for ln in content.splitlines():
                mm = re.match(r"^\s*(\d+)\t(.*)$", ln)
                if mm:
                    body.append(mm.group(2))
            open(os.path.join(V, "sheets.py"), "w", encoding="utf-8").write("\n".join(body) + "\n")
            log.write(f"BASE sheets.py from Read ({len(body)} lines)\n")
        if tag:
            n_dump += 1
            open(os.path.join(DUMP, f"{n_dump:03d}_{tag}.txt"), "w", encoding="utf-8").write(inp.get("command", "") + "\n=====\n" + content)
log.close()
print("dumped", n_dump)
