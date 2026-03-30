#!/usr/bin/env python3
"""Ralph - AI-driven development loop"""

import sys
import os
import re
import json
import subprocess
import threading
import time
import resource
import tracemalloc
from datetime import datetime

# Memory monitoring (enabled via RALPH_MEMORY_DEBUG=1)
_MEM_DEBUG = os.environ.get("RALPH_MEMORY_DEBUG") == "1"
_mem_log = []
_mem_start_time = None

# Memray profiling (enabled via RALPH_MEMRAY=1)
# Install: pip install memray
# Output: ralph_profile_<timestamp>.bin  ->  memray flamegraph <file>
_MEMRAY = os.environ.get("RALPH_MEMRAY") == "1"
_memray_tracker = None
if _MEMRAY:
    try:
        import memray  # noqa: F401
    except ImportError:
        print("[MEMRAY] memray not installed. Run: pip install memray", flush=True)
        _MEMRAY = False


def _mem_rss() -> int:
    """Current RSS in KB. Reads /proc/self/status for live value on Linux
    (resource.getrusage ru_maxrss is a peak watermark, never decreases)."""
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1])  # already in kB
    except OSError:
        pass
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


def _mem_checkpoint(label: str) -> None:
    if not _MEM_DEBUG:
        return
    global _mem_start_time
    if _mem_start_time is None:
        _mem_start_time = time.monotonic()
    elapsed = time.monotonic() - _mem_start_time
    rss = _mem_rss()
    _mem_log.append((label, rss, elapsed))
    print(f"[MEM] {elapsed:6.1f}s  {rss:8d} KB  {label}", flush=True)


def _mem_snapshot(label: str, top_n: int = 5) -> None:
    if not _MEM_DEBUG or not tracemalloc.is_tracing():
        return
    snapshot = tracemalloc.take_snapshot()
    stats = snapshot.statistics("lineno")
    print(f"[MEM ALLOC] Top {top_n} at: {label}")
    for stat in stats[:top_n]:
        print(f"  {stat}")


def _mem_summary() -> None:
    if not _MEM_DEBUG or not _mem_log:
        return
    peak_rss = max(rss for _, rss, _ in _mem_log)
    print("\n[MEM SUMMARY] " + "\u2500" * 50)
    print(f"  {'Checkpoint':<50}  {'RSS (KB)':>10}  {'Time':>8}")
    print(f"  {'-'*50}  {'-'*10}  {'-'*8}")
    for label, rss, elapsed in _mem_log:
        marker = " <-- PEAK" if rss == peak_rss else ""
        print(f"  {label:<50}  {rss:>10}  {elapsed:>6.1f}s{marker}")
    print(f"\n  Peak: {peak_rss:,} KB ({peak_rss/1024:.1f} MB)")
    print("[MEM SUMMARY] " + "\u2500" * 50 + "\n")


def _memray_stop() -> None:
    if not _MEMRAY or _memray_tracker is None:
        return
    _memray_tracker.__exit__(None, None, None)
    print(f"[MEMRAY] Profile written to {_memray_output}", flush=True)
    print(f"[MEMRAY] View flame graph: memray flamegraph {_memray_output}", flush=True)
    print(f"[MEMRAY] View summary:     memray summary {_memray_output}", flush=True)


CYAN = "\033[36m"
YELLOW = "\033[33m"
RED = "\033[31m"
PINK = "\033[38;5;213m"
GREEN = "\033[32m"
RESET = "\033[0m"
BOLD = "\033[1m"
ITALIC = "\033[3m"
DIM = "\033[2m"
CLAUDE_HEADER = "\033[48;5;17m\033[97m\033[1m Claude > \033[0m"

SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
SPINNER_WORDS = ["thinking", "reasoning", "working", "computing", "pondering"]
SPINNER_INTENSITIES = [DIM, "", BOLD, ""]  # dim → normal → bold → normal


def print_logo():
    PALE = "\033[38;5;216m"   # pale orange #ffaf87

    # ANSI Shadow font (Spring Boot style) for FABRIKETS
    FONT = {
        'F': ["███████╗", "██╔════╝", "█████╗  ", "██╔══╝  ", "██║     ", "╚═╝     "],
        'A': [" █████╗ ", "██╔══██╗", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
        'B': ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔══██╗", "██████╔╝", "╚═════╝ "],
        'R': ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔══██╗", "██║  ██║", "╚═╝  ╚═╝"],
        'I': ["██╗", "██║", "██║", "██║", "██║", "╚═╝"],
        'K': ["██╗  ██╗", "██║ ██╔╝", "█████╔╝ ", "██╔═██╗ ", "██║  ██╗", "╚═╝  ╚═╝"],
        'E': ["███████╗", "██╔════╝", "█████╗  ", "██╔══╝  ", "███████╗", "╚══════╝"],
        'T': ["████████╗", "╚══██╔══╝", "   ██║   ", "   ██║   ", "   ██║   ", "   ╚═╝   "],
        'S': ["███████╗", "██╔════╝", "███████╗", "╚════██║", "███████║", "╚══════╝"],
    }

    for row in range(6):
        line = "  "
        for ch in "FABRIKETS":
            line += FONT[ch][row] + " "
        print(f"{PALE}{line}{RESET}")
    print()
    print(f"  {DIM}{ITALIC}welcome to your agentic factory{RESET}")
    print()


class Spinner:
    def __init__(self):
        self._running = False
        self._thread = None
        self._word_idx = 0

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()
        print(f"\r{' ' * 40}\r", end="", flush=True)

    def _spin(self):
        i = 0
        while self._running:
            frame = SPINNER_FRAMES[i % len(SPINNER_FRAMES)]
            word = SPINNER_WORDS[(i // 20) % len(SPINNER_WORDS)]
            intensity = SPINNER_INTENSITIES[i % len(SPINNER_INTENSITIES)]
            print(f"\r{intensity}{frame} {word}...{RESET}", end="", flush=True)
            time.sleep(0.08)
            i += 1


def ask(prompt_text: str) -> str:
    return input(prompt_text)


def render_markdown(text: str) -> str:
    """Convert basic markdown to ANSI terminal formatting."""
    lines = []
    for line in text.split("\n"):
        # Headings
        if line.startswith("### "):
            line = f"{BOLD}{line[4:]}{RESET}"
        elif line.startswith("## "):
            line = f"{BOLD}{line[3:]}{RESET}"
        elif line.startswith("# "):
            line = f"{BOLD}{line[2:]}{RESET}"
        # Inline: bold must come before italic (** before *)
        line = re.sub(r"\*\*(.+?)\*\*", f"{BOLD}\\1{RESET}", line)
        line = re.sub(r"\*(.+?)\*", f"{ITALIC}\\1{RESET}", line)
        line = re.sub(r"`(.+?)`", f"{DIM}\\1{RESET}", line)
        lines.append(line)
    return "\n".join(lines)

CONTEXT_WINDOW = 100_000  # target 50% of 200K hard limit to stay in the smart zone
CONFIG_FILE = "config.yaml"
DEFAULT_MODELS = {
    "spec": "claude-sonnet-4-6",
    "plan": "claude-opus-4-6",
    "plan_validation": "claude-haiku-4-5-20251001",
    "build": "claude-sonnet-4-6",
    "build_review": "claude-haiku-4-5-20251001",
    "bug": "claude-sonnet-4-6",
    "skills": "claude-haiku-4-5-20251001",
    "readme": "claude-haiku-4-5-20251001",
}

DEFAULT_PLAN_CONFIG = {
    "max_reflections": 3,
}

TIER_BUILD_THRESHOLDS = {
    "light": 80,
    "medium": 85,
    "heavy": 90,
}

DEFAULT_BUILD_CONFIG = {
    "max_reflections": 2,
}

TIER_THRESHOLDS = {
    "light": 85,
    "medium": 90,
    "heavy": 92,
}

TIER_AGENTS = {
    "light": ["file_mapping"],
    "medium": ["file_mapping", "pattern_analysis"],
    "heavy": ["file_mapping", "pattern_analysis", "dependency_analysis", "test_analysis"],
}

# Start memory tracing if enabled
if _MEM_DEBUG:
    tracemalloc.start()
    _mem_checkpoint("startup")

# Start memray profiling if enabled
if _MEMRAY:
    import memray
    _memray_output = f"ralph_profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bin"
    _memray_tracker = memray.Tracker(_memray_output, native_traces=True)
    _memray_tracker.__enter__()
    print(f"[MEMRAY] Profiling to {_memray_output}", flush=True)

# Parse arguments
mode = "spec"
max_iterations = 5
debug = False
project_name = None
message = None
bugs_only = False
cost_by_feature = False

def print_help():
    print("""
Usage: ralph.py <command> [options]

Commands:
  spec        Interview Claude to define a new feature spec (default)
  plan        Generate implementation plans from existing specs
  build       Implement tasks from implementation plans
  bug         Document a bug as a spec (opens $EDITOR, or use -m for inline)
  skills      Discover project tooling and create Claude Code skills
  readme      Create or update the project README.md
  bootstrap   Register a new project in config.yaml
  cost        Show cost breakdown (use -f for per-feature, -p for per-project)
  specs       List all specs for a project

Options:
  -p, --project NAME      Project to work on (as registered in config.yaml)
  -m, --message TEXT      Inline bug description (used with 'bug' to skip editor)
  --bugs                  Only process bug specs (used with 'build' or 'plan')
  --max-iterations N      Max number of specs/tasks to process per run (default: 5)
  -d, --debug             Show full tool call details from Claude
  -h, --help              Show this help message
""")

args = sys.argv[1:]
i = 0
while i < len(args):
    if args[i] in ("-h", "--help"):
        print_help()
        sys.exit(0)
    elif args[i] == "--max-iterations":
        i += 1
        max_iterations = int(args[i])
    elif args[i] in ("spec", "plan", "build", "bug", "skills", "readme", "bootstrap", "cost", "specs"):
        mode = args[i]
    elif args[i] in ("-d", "--debug"):
        debug = True
    elif args[i] in ("-p", "--project"):
        i += 1
        project_name = args[i]
    elif args[i] in ("-m", "--message"):
        i += 1
        message = args[i]
    elif args[i] == "--bugs":
        bugs_only = True
    elif args[i] == "-f":
        cost_by_feature = True
    else:
        print(f"Error: unknown argument '{args[i]}'", file=sys.stderr)
        print("Run './ralph.py --help' for usage.", file=sys.stderr)
        sys.exit(1)
    i += 1

prompt_files = {"spec": "prompt_spec.md", "plan": "prompt_plan.md", "build": "prompt_build.md", "bug": "prompt_bug.md", "skills": "prompt_skills.md", "readme": "prompt_readme.md"}
prompt_file = prompt_files.get(mode)

os.makedirs(".ralph", exist_ok=True)
print("\033[2J\033[H", end="", flush=True)  # clear screen, cursor to top
print_logo()


def load_config() -> dict:
    """Returns {"projects": {...}, "models": {...}, "plan": {...}, "build": {...}}"""
    config = {"projects": {}, "models": {}, "plan": {}, "build": {}}
    current_section = None
    with open(CONFIG_FILE) as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.endswith(":") and not line.startswith(" "):
                current_section = stripped[:-1]
                continue
            if current_section and line.startswith("  "):
                key, _, value = stripped.partition(":")
                val = value.strip()
                if current_section == "projects":
                    config["projects"][key.strip()] = os.path.expanduser(val)
                elif current_section == "models":
                    config["models"][key.strip()] = val
                elif current_section in ("plan", "build"):
                    # Convert numeric values
                    try:
                        val = int(val)
                    except (ValueError, TypeError):
                        pass
                    config[current_section][key.strip()] = val
            else:
                current_section = None
    return config


def save_config(config: dict) -> None:
    with open(CONFIG_FILE, "w") as f:
        f.write("projects:\n")
        for name, path in config["projects"].items():
            f.write(f"  {name}: {path}\n")
        if config.get("models"):
            f.write("\nmodels:\n")
            for mode_name, model_id in config["models"].items():
                f.write(f"  {mode_name}: {model_id}\n")
        if config.get("plan"):
            f.write("\nplan:\n")
            for key, val in config["plan"].items():
                f.write(f"  {key}: {val}\n")


def ask_choice(question: str, options: list) -> int:
    """Print a numbered menu and return the 0-based index of the chosen option."""
    print(f"\n{question}")
    for i, opt in enumerate(options, 1):
        print(f"  {DIM}{i}.{RESET} {opt}")
    while True:
        raw = ask("> ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        print(f"  Enter a number from 1 to {len(options)}")


def to_snake_case(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9\s]", "", name)
    name = re.sub(r"\s+", "_", name)
    return name.strip("_")


def run_bootstrap() -> str:
    """Register a new project interactively. Returns the resolved src path."""
    print("\nWelcome to Fabrikets! Let's register a project.\n")
    name = ask("Project name (e.g. my-app): ").strip()
    src = ask("Source directory: ").strip()

    config = load_config() if os.path.exists(CONFIG_FILE) else {"projects": {}, "models": {}}
    config["projects"][name] = src
    if not config.get("models"):
        config["models"] = dict(DEFAULT_MODELS)
    save_config(config)

    src_expanded = os.path.expanduser(src)
    os.makedirs(src_expanded, exist_ok=True)
    print(f"\nProject '{name}' registered → {src}")
    print("Run 'spec' to start defining features.\n")
    return src_expanded


def resolve_project() -> str:
    """Resolve the src directory for the active project. Exits on error."""
    global project_name
    if mode == "bootstrap":
        src = run_bootstrap()
        sys.exit(0)

    if not os.path.exists(CONFIG_FILE):
        if project_name:
            print(f"Error: no config found. Run 'ralph.py bootstrap' to register a project.", file=sys.stderr)
            sys.exit(1)
        return run_bootstrap()

    config = load_config()
    projects = config["projects"]

    if project_name:
        if project_name not in projects:
            print(f"Error: project '{project_name}' not found.", file=sys.stderr)
            print("Run 'ralph.py bootstrap' to register a new project.", file=sys.stderr)
            if projects:
                print("\nAvailable projects:", file=sys.stderr)
                for n, p in projects.items():
                    print(f"  {n}  →  {p}", file=sys.stderr)
            sys.exit(1)
        return os.path.expanduser(projects[project_name])

    if not projects:
        return run_bootstrap()

    if len(projects) == 1:
        name, path = next(iter(projects.items()))
        project_name = name
        print(f"Project: {name}  ({path})")
        return os.path.expanduser(path)

    print("Multiple projects registered. Select one with -p:\n", file=sys.stderr)
    for n, p in projects.items():
        print(f"  -p {n:<20} {p}", file=sys.stderr)
    sys.exit(1)


def run_cost():
    """Show cost breakdown from .ralph/costs.jsonl."""
    costs_file = ".ralph/costs.jsonl"
    if not os.path.exists(costs_file):
        print("No cost data yet.")
        sys.exit(0)

    entries = []
    with open(costs_file) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))

    if not entries:
        print("No cost data yet.")
        sys.exit(0)

    if cost_by_feature:
        # Group by project + spec
        groups = {}
        for e in entries:
            key = f"{e.get('project', 'unknown')}/{e.get('spec') or e.get('mode', 'unknown')}"
            if key not in groups:
                groups[key] = {"cost": 0, "input": 0, "output": 0, "calls": 0}
            groups[key]["cost"] += e.get("cost_usd", 0)
            groups[key]["input"] += e.get("input_tokens", 0)
            groups[key]["output"] += e.get("output_tokens", 0)
            groups[key]["calls"] += 1

        print(f"\n{'Feature':<40} {'Cost':>10} {'Input':>10} {'Output':>10} {'Calls':>6}")
        print("-" * 80)
        for key in sorted(groups):
            g = groups[key]
            print(f"{key:<40} ${g['cost']:>9.4f} {g['input']:>10,} {g['output']:>10,} {g['calls']:>6}")
        total_cost = sum(g["cost"] for g in groups.values())
        print("-" * 80)
        print(f"{'Total':<40} ${total_cost:>9.4f}")

    elif project_name:
        # Filter by project
        filtered = [e for e in entries if e.get("project") == project_name]
        if not filtered:
            print(f"No cost data for project '{project_name}'.")
            sys.exit(0)

        # Group by mode
        groups = {}
        for e in filtered:
            m = e.get("mode", "unknown")
            if m not in groups:
                groups[m] = {"cost": 0, "input": 0, "output": 0, "calls": 0}
            groups[m]["cost"] += e.get("cost_usd", 0)
            groups[m]["input"] += e.get("input_tokens", 0)
            groups[m]["output"] += e.get("output_tokens", 0)
            groups[m]["calls"] += 1

        print(f"\nProject: {project_name}")
        print(f"\n{'Mode':<20} {'Cost':>10} {'Input':>10} {'Output':>10} {'Calls':>6}")
        print("-" * 60)
        for m in sorted(groups):
            g = groups[m]
            print(f"{m:<20} ${g['cost']:>9.4f} {g['input']:>10,} {g['output']:>10,} {g['calls']:>6}")
        total_cost = sum(g["cost"] for g in groups.values())
        print("-" * 60)
        print(f"{'Total':<20} ${total_cost:>9.4f}")

    else:
        # Group by project
        groups = {}
        for e in entries:
            p = e.get("project", "unknown")
            if p not in groups:
                groups[p] = {"cost": 0, "input": 0, "output": 0, "calls": 0}
            groups[p]["cost"] += e.get("cost_usd", 0)
            groups[p]["input"] += e.get("input_tokens", 0)
            groups[p]["output"] += e.get("output_tokens", 0)
            groups[p]["calls"] += 1

        print(f"\n{'Project':<30} {'Cost':>10} {'Input':>10} {'Output':>10} {'Calls':>6}")
        print("-" * 70)
        for p in sorted(groups):
            g = groups[p]
            print(f"{p:<30} ${g['cost']:>9.4f} {g['input']:>10,} {g['output']:>10,} {g['calls']:>6}")
        total_cost = sum(g["cost"] for g in groups.values())
        print("-" * 70)
        print(f"{'Total':<30} ${total_cost:>9.4f}")

    print()
    sys.exit(0)


if mode == "cost":
    run_cost()

src = resolve_project()
os.makedirs(src, exist_ok=True)

TRACKED_FILES = [src]

# Specs list command
if mode == "specs":
    BG_CYAN = "\033[46m"
    specs_yaml = os.path.join(src, "specs", "specs.yaml")
    if not os.path.exists(specs_yaml):
        print("No specs found. Run 'spec' to create one.")
        sys.exit(0)

    specs = []
    current = {}
    with open(specs_yaml) as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("- id:"):
                if current:
                    specs.append(current)
                current = {"id": stripped[5:].strip()}
            elif stripped.startswith("domain:"):
                current["domain"] = stripped[7:].strip()
            elif stripped.startswith("feature:"):
                current["feature"] = stripped[8:].strip()
            elif stripped.startswith("description:"):
                current["description"] = stripped[12:].strip()
            elif stripped.startswith("status:"):
                current["status"] = stripped[7:].strip()
        if current:
            specs.append(current)

    if not specs:
        print("No specs found.")
        sys.exit(0)

    # Group by domain
    domains = {}
    for s in specs:
        d = s.get("domain", "unknown")
        domains.setdefault(d, []).append(s)

    for domain in sorted(domains):
        print(f"\n  {BOLD}{domain}{RESET}")
        for s in domains[domain]:
            name = s.get("feature", s.get("id", "?"))
            desc = s.get("description", "")
            status = s.get("status", "?")
            status_color = {
                "done": "\033[32m",      # green
                "todo": YELLOW,
                "blocked": RED,
            }.get(status, "")
            print(f"    {BG_CYAN}{BOLD} {name} {RESET}  {desc}")
            print(f"      {status_color}{status}{RESET}")
    print()
    sys.exit(0)

if not prompt_file or not os.path.exists(prompt_file):
    print(f"Error: prompt file for '{mode}' not found", file=sys.stderr)
    sys.exit(1)

print(f"Running in {mode} mode using {prompt_file}")
prompt = open(prompt_file).read()

if bugs_only:
    prompt = "**IMPORTANT: Only process specs where `domain: bugs`. Skip all other specs.**\n\n" + prompt

# Model selection per mode (configurable via config.yaml models section)
config = load_config() if os.path.exists(CONFIG_FILE) else {"projects": {}, "models": {}}
if os.path.exists(CONFIG_FILE) and not config.get("models"):
    config["models"] = dict(DEFAULT_MODELS)
    save_config(config)
config_models = config.get("models", {})
claude_model = config_models.get(mode) or DEFAULT_MODELS.get(mode)


def get_files_hash() -> str:
    try:
        result = subprocess.run(
            f"find {' '.join(TRACKED_FILES)} -not -path '*/.git/*' -type f 2>/dev/null | xargs md5sum 2>/dev/null | sort",
            shell=True, capture_output=True, text=True
        )
        return result.stdout
    except Exception:
        return ""


def format_tool_input(name: str, inp: dict) -> str:
    if name in ("Read", "Write", "Edit"):
        return str(inp.get("file_path", ""))
    if name == "Glob":
        return str(inp.get("pattern", ""))
    if name == "Grep":
        return f"{inp.get('pattern', '')} in {inp.get('path', '.')}"
    if name == "Bash":
        return str(inp.get("command", ""))[:80]
    return str(inp)[:80]


def run_claude(prompt: str, debug: bool = False, model: str = None) -> list:
    src_abs = os.path.abspath(src)
    context = f"<!-- fabrikets_src: {src_abs} -->\n<!-- Your working directory is the project src directory. All file paths are relative to here. -->\n\n"
    cmd = ["claude", "--dangerously-skip-permissions", "--output-format", "stream-json", "--print", "--verbose"]
    if model:
        cmd += ["--model", model]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=src_abs,
    )
    proc.stdin.write(context + prompt)
    proc.stdin.close()

    _mem_checkpoint(f"run_claude:start prompt={len(prompt)}chars")
    spinner = Spinner()
    spinner.start()

    objects = []
    try:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            objects.append(obj)

            obj_type = obj.get("type")
            printed_text = False
            if obj_type == "assistant":
                for block in obj.get("message", {}).get("content", []):
                    if block.get("type") == "text":
                        text = block.get("text", "")
                        if text:
                            spinner.stop()
                            print(render_markdown(text), end="", flush=True)
                            printed_text = True
                    elif block.get("type") == "tool_use":
                        spinner.stop()
                        name = block.get("name", "")
                        summary = format_tool_input(name, block.get("input", {}))
                        if debug:
                            print(f"{CYAN}[{name}] {summary}{RESET}")
                        else:
                            print(f"{DIM}  [{name}] {summary}{RESET}")
                        spinner.start()
            elif obj_type == "user":
                for block in obj.get("message", {}).get("content", []):
                    if block.get("type") == "tool_result" and block.get("is_error"):
                        spinner.stop()
                        content = block.get("content", "")
                        if isinstance(content, list):
                            content = " ".join(b.get("text", "") for b in content)
                        print(f"{RED}  ERROR: {str(content)[:150]}{RESET}")

            if not printed_text:
                spinner.start()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()
        spinner.stop()
        raise

    spinner.stop()
    proc.wait()
    _mem_checkpoint(f"run_claude:end objects={len(objects)}")
    _mem_snapshot("run_claude:end")
    return objects


def append_cost(objects: list, spec: str = None) -> None:
    for obj in objects:
        if obj.get("type") == "result":
            usage = obj.get("usage", {})
            entry = {
                "project": project_name or "unknown",
                "mode": mode,
                "spec": spec,
                "cost_usd": obj.get("total_cost_usd", 0),
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            }
            os.makedirs(".ralph", exist_ok=True)
            with open(".ralph/costs.jsonl", "a") as f:
                f.write(json.dumps(entry) + "\n")


def extract_usage(objects: list) -> dict:
    for obj in objects:
        if obj.get("type") == "result":
            return obj.get("usage", {})
    return {}


def total_context_tokens(usage: dict) -> int:
    """Total context window usage: input_tokens already includes cached tokens."""
    return usage.get("input_tokens", 0) + usage.get("output_tokens", 0)


def extract_text(objects: list) -> str:
    parts = []
    for obj in objects:
        if obj.get("type") == "assistant":
            for block in obj.get("message", {}).get("content", []):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
    return "".join(parts)


def show_file_diff(before: str, after: str) -> None:
    if before != after:
        print("Files modified:")
        before_set = set(before.splitlines())
        after_set = set(after.splitlines())
        for line in before_set - after_set:
            parts = line.split()
            if len(parts) >= 2:
                print(f"  removed: {parts[1]}")
        for line in after_set - before_set:
            parts = line.split()
            if len(parts) >= 2:
                print(f"  changed: {parts[1]}")
    else:
        print("No files modified")


def run_claude_quiet(prompt: str, model: str = None) -> tuple:
    """Run Claude without printing output. Returns (objects, text)."""
    src_abs = os.path.abspath(src)
    context = f"<!-- fabrikets_src: {src_abs} -->\n<!-- Your working directory is the project src directory. All file paths are relative to here. -->\n\n"
    cmd = ["claude", "--dangerously-skip-permissions", "--output-format", "stream-json", "--print", "--verbose"]
    if model:
        cmd += ["--model", model]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=src_abs,
    )
    proc.stdin.write(context + prompt)
    proc.stdin.close()

    _mem_checkpoint(f"run_claude_quiet:start prompt={len(prompt)}chars")
    objects = []
    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        objects.append(obj)

    proc.wait()
    if proc.returncode != 0 and not objects:
        raise RuntimeError(f"Claude CLI exited with code {proc.returncode}")
    text = extract_text(objects)
    _mem_checkpoint(f"run_claude_quiet:end objects={len(objects)}")
    return objects, text


def extract_json_block(text: str) -> dict | None:
    """Extract a JSON block from markdown-formatted text (```json ... ```)."""
    match = re.search(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
    # Try parsing the whole text as JSON
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return None


def read_file_safe(path: str) -> str:
    """Read a file, return empty string if it doesn't exist."""
    try:
        with open(path) as f:
            return f.read()
    except (FileNotFoundError, OSError):
        return ""


def run_plan():
    """Orchestrate the full plan lifecycle: assess → research → plan → validate → reflect."""
    import concurrent.futures

    config = load_config() if os.path.exists(CONFIG_FILE) else {"projects": {}, "models": {}, "plan": {}}
    config_models = config.get("models", {})
    plan_config = config.get("plan", {})
    max_reflections = plan_config.get("max_reflections", DEFAULT_PLAN_CONFIG["max_reflections"])

    plan_model = config_models.get("plan") or DEFAULT_MODELS["plan"]
    validation_model = config_models.get("plan_validation") or DEFAULT_MODELS["plan_validation"]

    fabrikets_dir = os.path.dirname(os.path.abspath(__file__))

    # === Phase 1: Assessment ===
    print(f"\n{BOLD}Phase 1: Assessment{RESET} — picking spec and evaluating complexity\n")
    print(f"{CLAUDE_HEADER}\n")

    _mem_checkpoint("phase1:assessment:start")
    assess_prompt = open(os.path.join(fabrikets_dir, "prompt_plan_assess.md")).read()
    objects = run_claude(assess_prompt, debug=debug, model=plan_model)
    append_cost(objects, spec="plan/assess")
    assess_text = extract_text(objects)
    _mem_checkpoint(f"phase1:assessment:end assess_len={len(assess_text)}")
    _mem_snapshot("phase1:assessment:end")
    print()

    assessment = extract_json_block(assess_text)
    if not assessment:
        print(f"{RED}ERROR: Could not parse assessment output as JSON.{RESET}")
        print("Raw output:")
        print(assess_text[-500:])
        sys.exit(1)

    if assessment.get("action") == "stop":
        print("\nAll specs are fully planned. Nothing to do.")
        return

    spec_id = assessment["spec_id"]
    domain = assessment["domain"]
    feature = assessment["feature"]
    spec_dir = assessment["spec_dir"]
    tier = assessment.get("tier", "medium")
    spec_dir_abs = os.path.join(src, spec_dir)

    print(f"  Spec: {BOLD}{domain}/{feature}{RESET}")
    print(f"  Tier: {BOLD}{tier}{RESET} — {assessment.get('rationale', '')}")

    # Create implementation_plan.md with initial status
    plan_file = os.path.join(spec_dir_abs, "implementation_plan.md")
    os.makedirs(spec_dir_abs, exist_ok=True)
    if not os.path.exists(plan_file):
        with open(plan_file, "w") as f:
            f.write(f"id: {spec_id}\noverview: pending\nstatus: wip\n")

    # Check current status to determine resume point
    current_status = "wip"
    plan_content_check = read_file_safe(plan_file)
    m = re.search(r"^status: (\S+)", plan_content_check, re.MULTILINE)
    if m:
        current_status = m.group(1)

    research_file = os.path.join(spec_dir_abs, "research.md")

    # Resume logic: skip phases that already completed
    # wip/research → start from research
    # planning     → research done, skip to planning
    # validation/reflection → research + planning done, skip to validation
    skip_research = current_status in ("planning", "validation", "reflection")
    skip_planning = current_status in ("validation", "reflection")

    if skip_research:
        print(f"  {DIM}Resuming from phase {'3 (planning)' if not skip_planning else '4 (validation)'} — previous status: {current_status}{RESET}")

    # === Phase 2: Research ===
    _mem_checkpoint("phase2:research:start")
    agents_to_run = TIER_AGENTS.get(tier, TIER_AGENTS["medium"])

    if skip_research:
        print(f"\n{BOLD}Phase 2: Research{RESET} — {DIM}skipped (already complete){RESET}")
    else:
        _update_plan_status(plan_file, "research")
        print(f"\n{BOLD}Phase 2: Research{RESET} — {len(agents_to_run)} agent(s): {', '.join(agents_to_run)}\n")

        research_template = open(os.path.join(fabrikets_dir, "prompt_plan_research.md")).read()
        research_focus = assessment.get("research_focus", {})
        key_dirs = assessment.get("key_directories", [])
        req_summary = assessment.get("key_requirements_summary", "")

        def run_research_agent(agent_name):
            focus_desc = research_focus.get(agent_name, f"Perform {agent_name} for this spec")
            agent_prompt = research_template.format(
                focus_area=f"Your focus: **{agent_name}**\n\n{focus_desc}",
                spec_id=spec_id,
                domain=domain,
                feature=feature,
                spec_dir=spec_dir,
                tier=tier,
                requirements_summary=req_summary,
                key_directories=", ".join(key_dirs),
            )
            _mem_checkpoint(f"phase2:agent:{agent_name}:start")
            objs, text = run_claude_quiet(agent_prompt, model=plan_model)
            append_cost(objs, spec=f"{domain}/{feature}")
            _mem_checkpoint(f"phase2:agent:{agent_name}:end text_len={len(text)}")
            return agent_name, text

        research_results = {}
        spinner = Spinner()
        spinner.start()
        try:
            if len(agents_to_run) == 1:
                name, text = run_research_agent(agents_to_run[0])
                research_results[name] = text
            else:
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                    futures = {executor.submit(run_research_agent, name): name for name in agents_to_run}
                    for future in concurrent.futures.as_completed(futures):
                        agent_name = futures[future]
                        try:
                            name, text = future.result()
                            if not text.strip():
                                print(f"\r{YELLOW}  WARNING: {name} returned empty research{RESET}")
                            research_results[name] = text
                        except Exception as e:
                            print(f"\r{RED}  ERROR: {agent_name} failed: {e}{RESET}")
        finally:
            spinner.stop()
            _mem_checkpoint(f"phase2:research:complete results={len(research_results)}")
            _mem_snapshot("phase2:research:complete")

        # Combine research results into research.md
        research_md = f"# Research: {domain}/{feature}\n\n"
        research_md += f"**Tier**: {tier}\n"
        research_md += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        for agent_name in agents_to_run:
            if agent_name in research_results:
                research_md += f"---\n\n# {agent_name.replace('_', ' ').title()}\n\n"
                research_md += research_results[agent_name] + "\n\n"

        with open(research_file, "w") as f:
            f.write(research_md)
        _mem_checkpoint(f"phase2:research:written md_len={len(research_md)}")

        print(f"  Research saved to {spec_dir}/research.md")
        for name in agents_to_run:
            status = f"{GREEN}done{RESET}" if name in research_results else f"{RED}failed{RESET}"
            print(f"    {name}: {status}")

    # === Phase 3: Planning ===
    if skip_planning:
        print(f"\n{BOLD}Phase 3: Planning{RESET} — {DIM}skipped (already complete){RESET}")
    else:
        _update_plan_status(plan_file, "planning")
        print(f"\n{BOLD}Phase 3: Planning{RESET} — generating implementation tasks\n")
        print(f"{CLAUDE_HEADER}\n")

        _mem_checkpoint("phase3:planning:start")
        plan_template = open(os.path.join(fabrikets_dir, "prompt_plan.md")).read()
        plan_prompt = plan_template.format(
            spec_dir=spec_dir,
            spec_id=spec_id,
        )
        objects = run_claude(plan_prompt, debug=debug, model=plan_model)
        append_cost(objects, spec=f"{domain}/{feature}")
        _mem_checkpoint(f"phase3:planning:end objects={len(objects)}")
        _mem_snapshot("phase3:planning:end")
        print()

    # === Phase 4: Validation Loop ===
    threshold = TIER_THRESHOLDS.get(tier, 90)
    print(f"\n{BOLD}Phase 4: Validation{RESET} — scoring plan (threshold: {threshold}%)\n")

    for reflection_round in range(max_reflections + 1):
        _update_plan_status(plan_file, "validation")
        _mem_checkpoint(f"phase4:validation:round={reflection_round}:start")

        # Read current state for validation
        overview_content = read_file_safe(os.path.join(spec_dir_abs, "overview.md"))
        requirements_content = read_file_safe(os.path.join(spec_dir_abs, "requirements.md"))
        research_content = read_file_safe(research_file)
        plan_content = read_file_safe(plan_file)
        _mem_checkpoint(f"phase4:validation:files_read overview={len(overview_content)} req={len(requirements_content)} research={len(research_content)} plan={len(plan_content)}")

        validate_template = open(os.path.join(fabrikets_dir, "prompt_plan_validate.md")).read()
        validate_prompt = (validate_template
            .replace("{overview}", overview_content)
            .replace("{requirements}", requirements_content)
            .replace("{research}", research_content)
            .replace("{plan}", plan_content)
        )

        print(f"  Scoring with {validation_model}...")
        val_objects, val_text = run_claude_quiet(validate_prompt, model=validation_model)
        append_cost(val_objects, spec=f"{domain}/{feature}")

        scores = extract_json_block(val_text)
        if not scores:
            print(f"{YELLOW}  WARNING: Could not parse validation scores. Proceeding anyway.{RESET}")
            _update_plan_status(plan_file, "done")
            break

        total_pct = scores.get("total_percent", 0)
        print(f"\n  {BOLD}Score: {total_pct}%{RESET} (threshold: {threshold}%)\n")

        # Print individual scores
        for criterion, data in scores.get("scores", {}).items():
            score = data.get("score", 0)
            max_score = data.get("max", 10)
            issues = data.get("issues", [])
            color = GREEN if score >= 8 else YELLOW if score >= 6 else RED
            label = criterion.replace("_", " ").title()
            print(f"    {color}{score}/{max_score}{RESET}  {label}")
            for issue in issues[:2]:  # Show max 2 issues per criterion
                print(f"          {DIM}{issue}{RESET}")

        summary = scores.get("summary", "")
        if summary:
            print(f"\n  {DIM}{summary}{RESET}")

        if total_pct >= threshold:
            print(f"\n  {GREEN}Plan passed validation.{RESET}")
            _update_plan_status(plan_file, "done")
            break

        # Need reflection
        if reflection_round >= max_reflections:
            # Max reflections reached — generate anyway with pink warning
            print(f"\n{PINK}{BOLD}  WARNING: Plan for {domain}/{feature} did not reach quality threshold")
            print(f"  after {max_reflections} reflection(s) (scored {total_pct}%, needed {threshold}%).")
            print(f"  Review {spec_dir}/implementation_plan.md before building.{RESET}")
            _update_plan_status(plan_file, "done")
            break

        # Reflection
        _update_plan_status(plan_file, "reflection")
        print(f"\n  {BOLD}Reflecting{RESET} (round {reflection_round + 1}/{max_reflections})...\n")
        print(f"{CLAUDE_HEADER}\n")

        # Format scores for the reflection prompt
        scores_text = json.dumps(scores, indent=2)
        reflect_template = open(os.path.join(fabrikets_dir, "prompt_plan_reflect.md")).read()
        reflect_prompt = (reflect_template
            .replace("{spec_dir}", spec_dir)
            .replace("{reflection_round}", str(reflection_round + 1))
            .replace("{max_reflections}", str(max_reflections))
            .replace("{validation_scores}", scores_text)
        )
        objects = run_claude(reflect_prompt, debug=debug, model=plan_model)
        append_cost(objects, spec=f"{domain}/{feature}")
        _mem_checkpoint(f"phase4:reflection:round={reflection_round + 1}:end objects={len(objects)}")
        _mem_snapshot(f"phase4:reflection:round={reflection_round + 1}:end")
        print()

    # Update specs.yaml status
    specs_yaml = os.path.join(src, "specs", "specs.yaml")
    if os.path.exists(specs_yaml):
        content = read_file_safe(specs_yaml)
        # Simple replacement: find this spec's status and set to wip
        # This is a basic approach — the spec status goes to wip when plan is done
        updated = re.sub(
            rf"(- id: {re.escape(spec_id)}\n(?:    \w+:.*\n)*?    status:) \w+",
            rf"\1 wip",
            content,
        )
        if updated != content:
            with open(specs_yaml, "w") as f:
                f.write(updated)

    # Final commit
    subprocess.run(
        ["git", "add", "specs/"],
        cwd=os.path.abspath(src),
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", f"plan: {domain}/{feature} - research + validated plan"],
        cwd=os.path.abspath(src),
        capture_output=True,
    )

    print(f"\n{GREEN}{BOLD}Plan complete for {domain}/{feature}.{RESET}")


def _update_plan_status(plan_file: str, new_status: str):
    """Update the top-level status field in an implementation_plan.md file.

    Only matches 'status:' lines that are not indented (top-level YAML keys),
    avoiding task-level status fields which are indented.
    """
    content = read_file_safe(plan_file)
    if not content:
        return
    # Match only non-indented status lines (top-level YAML)
    updated = re.sub(r"^status: \S+", f"status: {new_status}", content, count=1, flags=re.MULTILINE)
    if updated != content:
        with open(plan_file, "w") as f:
            f.write(updated)


# ─── Build mode helpers ────────────────────────────────────────────────────────

def _parse_specs_yaml(specs_yaml_path: str) -> list:
    """Parse specs.yaml into a list of dicts. Reuses the approach from 'specs' mode."""
    specs = []
    current = {}
    with open(specs_yaml_path) as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("- id:"):
                if current:
                    specs.append(current)
                current = {"id": stripped[5:].strip()}
            elif stripped.startswith("domain:"):
                current["domain"] = stripped[7:].strip()
            elif stripped.startswith("feature:"):
                current["feature"] = stripped[8:].strip()
            elif stripped.startswith("status:"):
                current["status"] = stripped[7:].strip()
    if current:
        specs.append(current)
    return specs


def _find_next_todo_task(plan_content: str) -> dict | None:
    """Parse tasks from implementation_plan.md and return the highest-priority todo task."""
    tasks = []
    # Split into task blocks on '  - task:' boundaries (2-space indent)
    task_blocks = re.split(r'(?=  - task:)', plan_content)
    for block in task_blocks:
        if not block.strip().startswith("- task:"):
            continue
        task_m = re.match(r'  - task: ?(.*)', block)
        if not task_m:
            continue
        task_text = task_m.group(1).strip().strip('"\'')
        # Handle YAML block scalar (>): collect indented continuation lines
        if task_text == ">":
            continuation = re.findall(r'\n      (.+)', block)
            task_text = " ".join(continuation)

        priority_m = re.search(r'\n    priority: (\S+)', block)
        status_m = re.search(r'\n    status: (\S+)', block)
        refs_ms = re.findall(r'\n      - (.+)', block)

        tasks.append({
            "task": task_text,
            "_block": block,
            "priority": priority_m.group(1) if priority_m else "medium",
            "status": status_m.group(1) if status_m else "todo",
            "refs": [r.strip().strip('"\'') for r in refs_ms],
        })

    todo_tasks = [t for t in tasks if t["status"] == "todo"]
    if not todo_tasks:
        return None
    priority_order = {"high": 0, "medium": 1, "low": 2}
    todo_tasks.sort(key=lambda t: priority_order.get(t["priority"], 1))
    return todo_tasks[0]


def _update_task_status_in_plan(plan_file: str, task: dict, new_status: str) -> None:
    """Update a specific task's status field in implementation_plan.md."""
    content = read_file_safe(plan_file)
    if not content or "_block" not in task:
        return
    old_block = task["_block"]
    new_block = re.sub(r'(\n    status: )\S+', rf'\g<1>{new_status}', old_block)
    updated = content.replace(old_block, new_block, 1)
    if updated != content:
        with open(plan_file, "w") as f:
            f.write(updated)


def find_next_build_task() -> dict | None:
    """Find the next todo task across all specs with validated plans.
    Returns a dict with spec/task info, or None if nothing to do.
    """
    specs_yaml = os.path.join(src, "specs", "specs.yaml")
    if not os.path.exists(specs_yaml):
        return None

    specs = _parse_specs_yaml(specs_yaml)
    if bugs_only:
        specs = [s for s in specs if s.get("domain") == "bugs"]

    for spec in specs:
        domain = spec.get("domain", "")
        feature = spec.get("feature", "")
        spec_id = spec.get("id", "")
        if not domain or not feature:
            continue

        spec_dir_abs = os.path.join(src, "specs", domain, feature)
        plan_file = os.path.join(spec_dir_abs, "implementation_plan.md")
        if not os.path.exists(plan_file):
            continue

        plan_content = read_file_safe(plan_file)

        # Top-level status must be "done" (plan validated and ready to build)
        m = re.search(r"^status: (\S+)", plan_content, re.MULTILINE)
        if not m or m.group(1) != "done":
            continue

        tier_m = re.search(r"^tier: (\S+)", plan_content, re.MULTILINE)
        tier = tier_m.group(1) if tier_m else "medium"

        task = _find_next_todo_task(plan_content)
        if task:
            return {
                "spec_id": spec_id,
                "domain": domain,
                "feature": feature,
                "tier": tier,
                "spec_dir_abs": spec_dir_abs,
                "plan_file": plan_file,
                "task": task,
            }
    return None


def write_build_context(build_info: dict) -> None:
    """Assemble and write build_context.md with all context needed by Claude phases."""
    domain = build_info["domain"]
    feature = build_info["feature"]
    spec_id = build_info["spec_id"]
    tier = build_info["tier"]
    spec_dir_abs = build_info["spec_dir_abs"]
    spec_dir_rel = os.path.join("specs", domain, feature)
    task = build_info["task"]

    overview = read_file_safe(os.path.join(spec_dir_abs, "overview.md"))
    requirements = read_file_safe(os.path.join(spec_dir_abs, "requirements.md"))
    research = read_file_safe(os.path.join(spec_dir_abs, "research.md"))
    architecture = read_file_safe(os.path.join(src, "specs", "architecture.md"))
    plan_content = read_file_safe(build_info["plan_file"])

    # Load extra ref files (skip those already included above)
    already_included = {overview, requirements, research, architecture}
    extra_refs = []
    for ref in task.get("refs", []):
        ref_path = os.path.join(src, ref)
        ref_content = read_file_safe(ref_path)
        if ref_content and ref_content not in already_included:
            extra_refs.append((ref, ref_content))
            already_included.add(ref_content)

    # Extract acceptance criteria block from plan
    ac_m = re.search(r'(acceptance_criteria:\n(?:  - .+\n?)+)', plan_content)
    acceptance_criteria = ac_m.group(1) if ac_m else ""

    # Summarise plan progress
    done_tasks = re.findall(r'  - task: (.+)', plan_content)
    done_statuses = re.findall(r'    status: (\S+)', plan_content)
    task_summaries = list(zip(done_tasks, done_statuses))
    done_list = [t for t, s in task_summaries if s == "done"]
    todo_list = [t for t, s in task_summaries if s == "todo"]

    lines = [
        "# Build Context",
        "",
        "## Task to Implement",
        f"**Spec**: {domain}/{feature}  |  **ID**: {spec_id}  |  **Tier**: {tier}  |  **Priority**: {task['priority']}",
        f"**Spec directory**: {spec_dir_rel}",
        "",
        "### Task Description",
        task["task"],
        "",
    ]

    if architecture:
        lines += ["## Architecture", architecture, ""]
    if overview:
        lines += ["## Spec: Overview", overview, ""]
    if requirements:
        lines += ["## Spec: Requirements", requirements, ""]
    if research:
        lines += ["## Research Findings", research, ""]
    for ref_name, ref_content in extra_refs:
        lines += [f"## Reference: {ref_name}", ref_content, ""]
    if acceptance_criteria:
        lines += ["## Acceptance Criteria", acceptance_criteria, ""]

    lines += ["## Plan Progress"]
    if done_list:
        lines.append("**Already done:**")
        for t in done_list[:8]:
            lines.append(f"- {t.strip()[:100]}")
    if todo_list:
        lines.append("**Remaining todo (after this task):**")
        for t in todo_list[1:6]:  # skip index 0 = current task
            lines.append(f"- {t.strip()[:100]}")
    lines.append("")

    with open(os.path.join(spec_dir_abs, "build_context.md"), "w") as f:
        f.write("\n".join(lines))


def _check_acceptance_criteria(build_info: dict) -> bool:
    """Check acceptance criteria via Claude. Returns True if all pass (or new tasks added)."""
    spec_dir_abs = build_info["spec_dir_abs"]
    domain = build_info["domain"]
    feature = build_info["feature"]
    spec_dir_rel = os.path.join("specs", domain, feature)

    config = load_config() if os.path.exists(CONFIG_FILE) else {}
    build_model = config.get("models", {}).get("build") or DEFAULT_MODELS["build"]

    criteria_prompt = f"""You are verifying acceptance criteria for a completed feature.

Read:
- `{spec_dir_rel}/implementation_plan.md` — the acceptance_criteria field
- `{spec_dir_rel}/overview.md` and `{spec_dir_rel}/requirements.md` — the spec
- The actual source files to verify each criterion is satisfied

For each acceptance criterion, check whether it is genuinely satisfied in the current code.

Output a JSON object:
{{
  "criteria": [
    {{"text": "criterion description", "pass": true, "reason": "why it passes or fails"}}
  ]
}}

If any criterion fails, also add new `todo` tasks to `{spec_dir_rel}/implementation_plan.md` to address the gap.
Append them under the existing `tasks:` list with `status: todo` and `priority: high`.

Output `[DONE]` when finished."""

    crit_objects, crit_text = run_claude_quiet(criteria_prompt, model=build_model)
    append_cost(crit_objects, spec=f"{domain}/{feature}")

    result = extract_json_block(crit_text)
    if not result:
        return True

    for criterion in result.get("criteria", []):
        text = criterion.get("text", "?")[:70]
        passed = criterion.get("pass", True)
        reason = criterion.get("reason", "")
        color = GREEN if passed else RED
        marker = "pass" if passed else "FAIL"
        print(f"    {color}[CRITERIA] {text} → {marker}{RESET}")
        if not passed and reason:
            print(f"           {DIM}{reason}{RESET}")

    return all(c.get("pass", True) for c in result.get("criteria", []))


def run_build() -> bool:
    """Execute one build task through the full phase pipeline.
    Returns True if a task was processed, False if nothing to do.
    """
    config = load_config() if os.path.exists(CONFIG_FILE) else {"projects": {}, "models": {}, "plan": {}, "build": {}}
    config_models = config.get("models", {})
    build_config = config.get("build", {})
    max_reflections = build_config.get("max_reflections", DEFAULT_BUILD_CONFIG["max_reflections"])

    build_model = config_models.get("build") or DEFAULT_MODELS["build"]
    review_model = config_models.get("build_review") or DEFAULT_MODELS["build_review"]

    fabrikets_dir = os.path.dirname(os.path.abspath(__file__))

    # === Phase 1: Context Assembly ===
    print(f"\n{BOLD}Phase 1: Task Selection{RESET} — finding next todo task")
    _mem_checkpoint("build:phase1:start")

    build_info = find_next_build_task()
    if not build_info:
        return False

    domain = build_info["domain"]
    feature = build_info["feature"]
    spec_id = build_info["spec_id"]
    tier = build_info["tier"]
    spec_dir_abs = build_info["spec_dir_abs"]
    spec_dir_rel = os.path.join("specs", domain, feature)
    plan_file = build_info["plan_file"]
    task = build_info["task"]

    print(f"  Spec: {BOLD}{domain}/{feature}{RESET}")
    print(f"  Task: {task['task'][:80]}{'...' if len(task['task']) > 80 else ''}")
    print(f"  Priority: {task['priority']}  |  Tier: {tier}")

    write_build_context(build_info)
    _mem_checkpoint("build:phase1:context_written")

    threshold = TIER_BUILD_THRESHOLDS.get(tier, 85)

    # === Phase 2: Implementation ===
    print(f"\n{BOLD}Phase 2: Implementation{RESET}\n")
    print(f"{CLAUDE_HEADER}\n")
    _mem_checkpoint("build:phase2:start")

    implement_prompt = open(os.path.join(fabrikets_dir, "prompt_build_implement.md")).read()
    implement_prompt = implement_prompt.replace("{spec_dir}", spec_dir_rel)
    objects = run_claude(implement_prompt, debug=debug, model=build_model)
    append_cost(objects, spec=f"{domain}/{feature}")
    _mem_checkpoint("build:phase2:end")
    print()

    # === Phase 3 + 4 + 5: Validate / Review / Reflect loop ===
    review = {}
    total_pct = 0

    for reflection_round in range(max_reflections + 1):
        # Phase 3: Validation
        print(f"\n{BOLD}Phase 3: Validation{RESET} (round {reflection_round + 1}/{max_reflections + 1})\n")
        print(f"{CLAUDE_HEADER}\n")
        _mem_checkpoint(f"build:phase3:round={reflection_round}:start")

        validate_prompt = open(os.path.join(fabrikets_dir, "prompt_build_validate.md")).read()
        validate_prompt = validate_prompt.replace("{spec_dir}", spec_dir_rel)
        objects = run_claude(validate_prompt, debug=debug, model=build_model)
        append_cost(objects, spec=f"{domain}/{feature}")
        _mem_checkpoint(f"build:phase3:round={reflection_round}:end")
        print()

        # Phase 4: Code Review Scoring (Haiku)
        print(f"  Scoring with {review_model}...")
        _mem_checkpoint(f"build:phase4:round={reflection_round}:start")

        review_prompt = open(os.path.join(fabrikets_dir, "prompt_build_review.md")).read()
        review_prompt = review_prompt.replace("{spec_dir}", spec_dir_rel)
        rev_objects, rev_text = run_claude_quiet(review_prompt, model=review_model)
        append_cost(rev_objects, spec=f"{domain}/{feature}")
        _mem_checkpoint(f"build:phase4:round={reflection_round}:end")

        review = extract_json_block(rev_text)
        # Fallback: try reading build_review.json directly if Claude wrote it to disk
        if not review:
            review_file = os.path.join(spec_dir_abs, "build_review.json")
            if os.path.exists(review_file):
                try:
                    with open(review_file) as f:
                        review = json.loads(f.read())
                except json.JSONDecodeError:
                    pass

        if not review:
            print(f"{YELLOW}  WARNING: Could not parse review scores. Proceeding.{RESET}")
            break

        total_pct = review.get("total_percent", 0)
        print(f"\n  {BOLD}Score: {total_pct}%{RESET} (threshold: {threshold}%)\n")

        for criterion, data in review.get("scores", {}).items():
            score = data.get("score", 0)
            max_score = data.get("max", 10)
            issues = data.get("issues", [])
            color = GREEN if score >= 8 else YELLOW if score >= 6 else RED
            label = criterion.replace("_", " ").title()
            print(f"    {color}{score}/{max_score}{RESET}  {label}")
            for issue in issues[:2]:
                print(f"          {DIM}{issue}{RESET}")

        summary = review.get("summary", "")
        if summary:
            print(f"\n  {DIM}{summary}{RESET}")

        if total_pct >= threshold:
            print(f"\n  {GREEN}Implementation passed review.{RESET}")
            break

        if reflection_round >= max_reflections:
            print(f"\n{PINK}{BOLD}  WARNING: Task did not reach quality threshold")
            print(f"  after {max_reflections} reflection(s) (scored {total_pct}%, needed {threshold}%).")
            print(f"  Review {spec_dir_rel}/implementation_plan.md before merging.{RESET}")
            break

        # Phase 5: Reflection
        print(f"\n  {BOLD}Reflecting{RESET} (round {reflection_round + 1}/{max_reflections})...\n")
        print(f"{CLAUDE_HEADER}\n")
        _mem_checkpoint(f"build:phase5:round={reflection_round}:start")

        reflect_template = open(os.path.join(fabrikets_dir, "prompt_build_reflect.md")).read()
        reflect_prompt = (reflect_template
            .replace("{spec_dir}", spec_dir_rel)
            .replace("{reflection_round}", str(reflection_round + 1))
            .replace("{max_reflections}", str(max_reflections))
            .replace("{score}", str(total_pct))
        )
        objects = run_claude(reflect_prompt, debug=debug, model=build_model)
        append_cost(objects, spec=f"{domain}/{feature}")
        _mem_checkpoint(f"build:phase5:round={reflection_round}:end")
        print()

    # === Phase 6: Finalise ===
    _mem_checkpoint("build:phase6:start")
    _update_task_status_in_plan(plan_file, task, "done")
    print(f"\n  {GREEN}Task marked done.{RESET}")

    # Check if all tasks are now done — if so, verify acceptance criteria
    plan_content_updated = read_file_safe(plan_file)
    remaining = _find_next_todo_task(plan_content_updated)
    if not remaining:
        print(f"\n  All tasks done. Verifying acceptance criteria...")
        all_passed = _check_acceptance_criteria(build_info)
        if all_passed:
            _update_plan_status(plan_file, "complete")
            specs_yaml = os.path.join(src, "specs", "specs.yaml")
            specs_content = read_file_safe(specs_yaml)
            updated = re.sub(
                rf"(- id: {re.escape(spec_id)}\n(?:    \w+:.*\n)*?    status:) \w+",
                rf"\1 done",
                specs_content,
            )
            if updated != specs_content:
                with open(specs_yaml, "w") as f:
                    f.write(updated)
            print(f"  {GREEN}Spec {domain}/{feature} complete — all acceptance criteria passed.{RESET}")

    # Commit
    score_str = f" (score: {total_pct}%)" if total_pct else ""
    subprocess.run(["git", "add", "-A"], cwd=os.path.abspath(src), capture_output=True)
    commit_msg = f"{spec_id}: {task['task'][:60]}{score_str}"
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=os.path.abspath(src), capture_output=True)

    # Clean up build artifacts
    for fname in ("build_context.md", "build_implementation.md", "build_validation.md",
                  "build_review.json", "build_reflection.log"):
        fpath = os.path.join(spec_dir_abs, fname)
        if os.path.exists(fpath):
            os.unlink(fpath)

    _mem_checkpoint("build:phase6:end")
    return True


# ─── Plan mode: full orchestrated lifecycle (assess → research → plan → validate → reflect) ──

# Plan mode: full orchestrated lifecycle (assess → research → plan → validate → reflect)
if mode == "plan":
    print(f"Running in plan mode (RPI: research → plan → validate)\n")
    plan_start = datetime.now()
    try:
        run_plan()
    except KeyboardInterrupt:
        print("\n\nSee ya!")
    finally:
        total = int((datetime.now() - plan_start).total_seconds())
        print(f"\nTotal elapsed: {total // 60}m {total % 60}s")
        _mem_summary()
        _memray_stop()
    sys.exit(0)

# Skills mode: discover project tooling and create Claude Code skills
if mode == "skills":
    os.makedirs(os.path.join(src, ".claude", "commands"), exist_ok=True)
    print("Discovering project tooling and creating skills...\n")
    print(f"\n{CLAUDE_HEADER}\n")
    objects = run_claude(prompt, debug=debug, model=claude_model)
    append_cost(objects)
    response = extract_text(objects)
    print()
    if "[DONE]" not in response:
        print(f"{YELLOW}WARNING: Skills creation may not have completed successfully.{RESET}")
    sys.exit(0)

# README mode: create or update the project README
if mode == "readme":
    print("Analysing project for README...\n")
    print(f"\n{CLAUDE_HEADER}\n")
    objects = run_claude(prompt, debug=debug, model=claude_model)
    append_cost(objects)
    response = extract_text(objects)
    print()
    if "[DONE]" not in response:
        print(f"{YELLOW}WARNING: README creation may not have completed successfully.{RESET}")
    sys.exit(0)

# Bug mode: interview to document a bug as a spec
if mode == "bug":
    import tempfile

    if message:
        bug_description = message.strip()
    else:
        editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or "nano"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", prefix="ralph_bug_", delete=False) as tmp:
            tmp.write("# Describe the bug below (lines starting with # are ignored)\n\n")
            tmp_path = tmp.name
        try:
            subprocess.run([editor, tmp_path], check=True)
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            if isinstance(e, FileNotFoundError):
                print(f"Error: editor '{editor}' not found. Set $EDITOR or use -m.", file=sys.stderr)
            os.unlink(tmp_path)
            sys.exit(1)
        with open(tmp_path) as f:
            lines = [l for l in f.readlines() if not l.startswith("#")]
        os.unlink(tmp_path)
        bug_description = "".join(lines).strip()

    if not bug_description:
        print("Aborted: empty bug description.")
        sys.exit(0)

    # Ask if Claude can run commands to investigate
    run_choice = ask_choice(
        "Allow Claude to run commands (tests, linter, etc.) to investigate the bug?",
        ["Yes — let Claude run commands to reproduce and understand the bug",
         "No — read-only, Claude should only read code and ask questions"],
    )
    can_run_commands = run_choice == 0

    # Write interview file with bug report + prompt
    bugs_dir = os.path.join(src, "specs", "bugs")
    os.makedirs(bugs_dir, exist_ok=True)
    interview_file = os.path.join(bugs_dir, "_active_interview.md")

    with open(interview_file, "w") as f:
        f.write("<!-- mode: bug -->\n\n")
        if can_run_commands:
            f.write("<!-- permissions: run_commands -->\n\n")
        f.write(f"## Bug Report\n\n{bug_description}\n\n---\n\n")
        f.write(prompt)

    print(f"Bug report captured. Starting interview...\n")

    try:
        while True:
            print(f"\n{CLAUDE_HEADER}\n")
            objects = run_claude(open(interview_file).read(), debug=debug, model=claude_model)
            append_cost(objects, spec="bugs")
            response = extract_text(objects)
            print()

            usage = extract_usage(objects)
            context_tokens = total_context_tokens(usage)
            pct = context_tokens / CONTEXT_WINDOW * 100
            if pct >= 80:
                color = RED
            elif pct >= 60:
                color = YELLOW
            else:
                color = ""
            print(f"{color}Context: {context_tokens:,} / {CONTEXT_WINDOW:,} tokens ({pct:.1f}%){RESET}\n")

            if "[DONE]" in response:
                print("Bug documented.")
                break

            user_input = ask("You: ").strip()
            if user_input.lower() in ("exit", "quit"):
                break

            with open(interview_file, "a") as f:
                f.write(f"\n\nAssistant: {response}\n\nUser: {user_input}")
    except KeyboardInterrupt:
        print("\n\nSee ya!")

    # Clean up the active interview file
    if os.path.exists(interview_file):
        os.unlink(interview_file)

    sys.exit(0)

# Spec mode: interactive interview with Claude to create/add a spec
if mode == "spec":
    specs_dir = os.path.join(src, "specs")

    mode_choice = ask_choice(
        "How would you like to start?",
        ["Create new spec from scratch", "Import an existing spec file"],
    )

    existing_spec_content = None
    if mode_choice == 1:
        while True:
            existing_path = os.path.expanduser(ask("Path to existing spec file: ").strip())
            if os.path.exists(existing_path):
                with open(existing_path) as f:
                    existing_spec_content = f.read()
                print(f"Loaded: {existing_path}")
                break
            print(f"  File not found: {existing_path} (Ctrl+C to exit)")

    # Domain and feature name
    existing_domains = sorted(
        d for d in os.listdir(specs_dir)
        if os.path.isdir(os.path.join(specs_dir, d)) and not d.startswith(".")
    ) if os.path.isdir(specs_dir) else []
    if existing_domains:
        print(f"Existing domains: {', '.join(existing_domains)}")
    domain = to_snake_case(ask("Domain (e.g. auth, billing, core): ").strip())
    if not domain:
        print("Aborted.")
        sys.exit(0)

    feature_raw = ask("Feature name: ").strip()
    if not feature_raw:
        print("Aborted.")
        sys.exit(0)
    feature = to_snake_case(feature_raw)

    description = ask("Brief description: ").strip()

    spec_dir = os.path.join(specs_dir, domain, feature)
    os.makedirs(spec_dir, exist_ok=True)
    interview_file = os.path.join(spec_dir, "_active_interview.md")

    if os.path.exists(os.path.join(spec_dir, "overview.md")):
        confirm = ask(f"Spec already exists at {domain}/{feature}. Override? (y/n): ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            sys.exit(0)
        import shutil
        shutil.rmtree(spec_dir)
        os.makedirs(spec_dir, exist_ok=True)

    # Build the initial prompt — prepend existing spec as context if importing
    if existing_spec_content:
        import_preamble = (
            "## Import Mode\n\n"
            "The user has provided an existing spec file as a starting point.\n"
            "Your goal is to review it, ask clarifying questions to fill in any gaps\n"
            "(functional requirements, non-functional requirements, edge cases, constraints),\n"
            "and then rewrite it in the Fabrikets spec format.\n\n"
            "## Existing Spec\n\n"
            f"{existing_spec_content}\n\n"
            "---\n\n"
        )
        interview_prompt = import_preamble + prompt
    else:
        interview_prompt = prompt

    spec_id = f"{domain}__{feature}"
    spec_dir_rel = os.path.join("specs", domain, feature)  # relative to src

    with open(interview_file, "w") as f:
        f.write(f"<!-- spec_id: {spec_id} -->\n")
        f.write(f"<!-- domain: {domain} -->\n")
        f.write(f"<!-- feature: {feature} -->\n")
        f.write(f"<!-- spec_dir: {spec_dir_rel} -->\n\n")
        if description:
            f.write(f"## User Description\n\n{description}\n\n---\n\n")
        f.write(interview_prompt)

    print(f"Spec: {spec_dir_rel}/")

    try:
        while True:
            print(f"\n{CLAUDE_HEADER}\n")
            spec_label = f"{domain}/{feature}"
            objects = run_claude(open(interview_file).read(), debug=debug, model=claude_model)
            append_cost(objects, spec=spec_label)
            response = extract_text(objects)
            print()

            usage = extract_usage(objects)
            context_tokens = total_context_tokens(usage)
            pct = context_tokens / CONTEXT_WINDOW * 100
            if pct >= 80:
                color = RED
            elif pct >= 60:
                color = YELLOW
            else:
                color = ""
            print(f"{color}Context: {context_tokens:,} / {CONTEXT_WINDOW:,} tokens ({pct:.1f}%){RESET}\n")

            if "[DONE]" in response:
                print(f"Interview complete. Spec saved to {spec_dir_rel}/")
                # Clean up temporary interview file
                if os.path.exists(interview_file):
                    os.unlink(interview_file)
                break

            if "[ARCHITECT]" in response:
                print(f"\n{BOLD}Calling architect subagent...{RESET}\n")
                architect_prompt = open("prompt_architect.md").read()
                architect_context = open(interview_file).read()
                architect_input = f"{architect_prompt}\n\n---\n\n## Interview so far\n\n{architect_context}"
                arch_objects = run_claude(architect_input, debug=debug, model=claude_model)
                append_cost(arch_objects, spec=spec_label)
                arch_findings = extract_text(arch_objects)
                print()
                with open(interview_file, "a") as f:
                    f.write(f"\n\nAssistant: {response}\n\nArchitect Review:\n{arch_findings}")
                continue

            user_input = ask("You: ").strip()
            if user_input.lower() in ("exit", "quit"):
                break

            with open(interview_file, "a") as f:
                f.write(f"\n\nAssistant: {response}\n\nUser: {user_input}")
    except KeyboardInterrupt:
        print("\n\nSee ya!")

    sys.exit(0)

# Build mode: multi-phase implement → validate → review → reflect loop
if mode == "build":
    print(f"Running in build mode (multi-phase: implement → validate → review)\n")
    loop_start = datetime.now()
    try:
        for iteration in range(1, max_iterations + 1):
            iter_start = datetime.now()
            print(f"\n{'='*60}")
            print(f"Build iteration {iteration}/{max_iterations} — {iter_start.strftime('%c')}")
            print(f"{'='*60}")
            _mem_checkpoint(f"build:iteration={iteration}:start")

            had_work = run_build()

            _mem_checkpoint(f"build:iteration={iteration}:end")
            elapsed = int((datetime.now() - iter_start).total_seconds())
            print(f"\nIteration {iteration} done ({elapsed // 60}m {elapsed % 60}s)")

            if not had_work:
                print("\nAll tasks complete — nothing left to build.")
                break

            if iteration >= max_iterations:
                print(f"\nMax iterations ({max_iterations}) reached.")
                break

            time.sleep(2)
    except KeyboardInterrupt:
        print("\n\nSee ya!")
    finally:
        total = int((datetime.now() - loop_start).total_seconds())
        print(f"\nTotal elapsed: {total // 60}m {total % 60}s")
        _mem_summary()
        _memray_stop()
    sys.exit(0)
