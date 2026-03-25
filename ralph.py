#!/usr/bin/env python3
"""Ralph - AI-driven development loop"""

import sys
import os
import re
import json
import subprocess
import threading
import time
from datetime import datetime

CYAN = "\033[36m"
YELLOW = "\033[33m"
RED = "\033[31m"
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

# Parse arguments
mode = "spec"
max_iterations = 1
debug = False
project_name = None
message = None
bugs_only = False

def print_help():
    print("""
Usage: ralph.py <command> [options]

Commands:
  spec        Interview Claude to define a new feature spec (default)
  plan        Generate implementation plans from existing specs
  build       Implement tasks from implementation plans
  bug         Document a bug as a spec (opens $EDITOR, or use -m for inline)
  bootstrap   Register a new project in config.yaml

Options:
  -p, --project NAME      Project to work on (as registered in config.yaml)
  -m, --message TEXT      Inline bug description (used with 'bug' to skip editor)
  --bugs                  Only process bug specs (used with 'build' or 'plan')
  --max-iterations N      Max number of specs/tasks to process per run (default: 1)
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
    elif args[i] in ("spec", "plan", "build", "bug", "bootstrap"):
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
    else:
        print(f"Error: unknown argument '{args[i]}'", file=sys.stderr)
        print("Run './ralph.py --help' for usage.", file=sys.stderr)
        sys.exit(1)
    i += 1

prompt_files = {"spec": "prompt_spec.md", "plan": "prompt_plan.md", "build": "prompt_build.md", "bug": "prompt_bug.md"}
prompt_file = prompt_files.get(mode)

os.makedirs(".ralph", exist_ok=True)
print("\033[2J\033[H", end="", flush=True)  # clear screen, cursor to top
print_logo()


def load_config() -> dict:
    """Returns {"projects": {"name": "expanded_path", ...}}"""
    config = {"projects": {}}
    in_projects = False
    with open(CONFIG_FILE) as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped == "projects:":
                in_projects = True
                continue
            if in_projects and line.startswith("  "):
                key, _, value = stripped.partition(":")
                config["projects"][key.strip()] = os.path.expanduser(value.strip())
            else:
                in_projects = False
    return config


def save_config(config: dict) -> None:
    with open(CONFIG_FILE, "w") as f:
        f.write("projects:\n")
        for name, path in config["projects"].items():
            f.write(f"  {name}: {path}\n")


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
    print("\nWelcome to Fabrikets! Let's register a new project.\n")
    name = ask("Project name (e.g. my-app): ").strip()
    src = ask("Source directory: ").strip()
    domain = to_snake_case(ask("Initial domain group name (e.g. auth, billing, core): ").strip())

    config = load_config() if os.path.exists(CONFIG_FILE) else {"projects": {}}
    config["projects"][name] = src
    save_config(config)
    print(f"\nProject '{name}' registered → {src}\n")

    src_expanded = os.path.expanduser(src)
    os.makedirs(os.path.join(src_expanded, domain), exist_ok=True)
    return src_expanded


def resolve_project() -> str:
    """Resolve the src directory for the active project. Exits on error."""
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
        print(f"Project: {name}  ({path})")
        return os.path.expanduser(path)

    print("Multiple projects registered. Select one with -p:\n", file=sys.stderr)
    for n, p in projects.items():
        print(f"  -p {n:<20} {p}", file=sys.stderr)
    sys.exit(1)


src = resolve_project()
os.makedirs(src, exist_ok=True)

TRACKED_FILES = [src]

if not prompt_file or not os.path.exists(prompt_file):
    print(f"Error: prompt file for '{mode}' not found", file=sys.stderr)
    sys.exit(1)

print(f"Running in {mode} mode using {prompt_file}")
prompt = open(prompt_file).read()

if bugs_only:
    prompt = "**IMPORTANT: Only process specs where `domain: bugs`. Skip all other specs.**\n\n" + prompt


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


def run_claude(prompt: str, debug: bool = False) -> list:
    src_abs = os.path.abspath(src)
    context = f"<!-- fabrikets_src: {src_abs} -->\n<!-- Your working directory is the project src directory. All file paths are relative to here. -->\n\n"
    proc = subprocess.Popen(
        ["claude", "--dangerously-skip-permissions", "--output-format", "stream-json", "--print", "--verbose"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=src_abs,
    )
    proc.stdin.write(context + prompt)
    proc.stdin.close()

    spinner = Spinner()
    spinner.start()

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

    spinner.stop()
    proc.wait()
    return objects


def append_cost(objects: list) -> None:
    for obj in objects:
        if obj.get("type") == "result":
            cost = str(obj.get("total_cost_usd", ""))[:6]
            usage = obj.get("usage", {})
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            line = f"cost: ${cost}  in: {usage.get('input_tokens', 0)}  out: {usage.get('output_tokens', 0)}  [{ts}]\n"
            with open(".ralph/cost.md", "a") as f:
                f.write(line)


def extract_usage(objects: list) -> dict:
    for obj in objects:
        if obj.get("type") == "result":
            return obj.get("usage", {})
    return {}


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

    # Write interview file with bug report + prompt
    bugs_dir = os.path.join(src, "specs", "bugs")
    os.makedirs(bugs_dir, exist_ok=True)
    interview_file = os.path.join(bugs_dir, "_active_interview.md")

    with open(interview_file, "w") as f:
        f.write("<!-- mode: bug -->\n\n")
        f.write(f"## Bug Report\n\n{bug_description}\n\n---\n\n")
        f.write(prompt)

    print(f"Bug report captured. Starting interview...\n")

    try:
        while True:
            print(f"\n{CLAUDE_HEADER}\n")
            objects = run_claude(open(interview_file).read(), debug=debug)
            append_cost(objects)
            response = extract_text(objects)
            print()

            usage = extract_usage(objects)
            input_tokens = usage.get("input_tokens", 0)
            pct = input_tokens / CONTEXT_WINDOW * 100
            if pct >= 80:
                color = RED
            elif pct >= 60:
                color = YELLOW
            else:
                color = ""
            print(f"{color}Context: {input_tokens:,} / {CONTEXT_WINDOW:,} tokens ({pct:.1f}%){RESET}\n")

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
    domain = to_snake_case(ask("Domain group name: ").strip())
    if not domain:
        print("Aborted.")
        sys.exit(0)

    feature_raw = ask("Feature name: ").strip()
    if not feature_raw:
        print("Aborted.")
        sys.exit(0)
    feature = to_snake_case(feature_raw)

    spec_dir = os.path.join(specs_dir, domain, feature)
    os.makedirs(spec_dir, exist_ok=True)
    interview_file = os.path.join(spec_dir, "_interview.md")

    if os.path.exists(interview_file):
        print(f"Spec already exists: {interview_file}")
        sys.exit(1)

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
        f.write(interview_prompt)

    print(f"Spec: {spec_dir_rel}/")

    try:
        while True:
            print(f"\n{CLAUDE_HEADER}\n")
            objects = run_claude(open(interview_file).read(), debug=debug)
            append_cost(objects)
            response = extract_text(objects)
            print()

            usage = extract_usage(objects)
            input_tokens = usage.get("input_tokens", 0)
            pct = input_tokens / CONTEXT_WINDOW * 100
            if pct >= 80:
                color = RED
            elif pct >= 60:
                color = YELLOW
            else:
                color = ""
            print(f"{color}Context: {input_tokens:,} / {CONTEXT_WINDOW:,} tokens ({pct:.1f}%){RESET}\n")

            if "[DONE]" in response:
                print(f"Interview complete. Spec saved to {interview_file}")
                break

            if "[ARCHITECT]" in response:
                print(f"\n{BOLD}Calling architect subagent...{RESET}\n")
                architect_prompt = open("prompt_architect.md").read()
                architect_context = open(interview_file).read()
                architect_input = f"{architect_prompt}\n\n---\n\n## Interview so far\n\n{architect_context}"
                arch_objects = run_claude(architect_input, debug=debug)
                append_cost(arch_objects)
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

# Main loop
loop_start = datetime.now()
try:
    for iteration in range(1, max_iterations + 1):
        iter_start = datetime.now()
        print(f"\n=== Iteration {iteration}/{max_iterations} starting at {iter_start.strftime('%c')} ===")
        before_hash = get_files_hash()

        print("Sending prompt to Claude...")
        print("\n--- Claude's response ---")
        objects = run_claude(prompt, debug=debug)
        elapsed = (datetime.now() - iter_start).seconds
        print(f"\n--- End response --- ({elapsed // 60}m {elapsed % 60}s)\n")

        append_cost(objects)

        # Check for API errors
        has_result = any(obj.get("type") == "result" for obj in objects)
        if not has_result:
            print(f"{RED}ERROR: No result from API. Possible causes:{RESET}")
            print("  - Rate limit exceeded")
            print("  - Quota/tokens exhausted")
            print("  - Network error")
            print("Loop ended: API error")
            sys.exit(1)

        after_hash = get_files_hash()
        show_file_diff(before_hash, after_hash)

        result = extract_text(objects)

        if "[STOP]" in result:
            print("\nLoop ended: all work complete")
            break
        elif "[PROGRESS]" in result:
            print("\nProgress made, continuing to next iteration...")
        else:
            print(f"\n{YELLOW}WARNING: No [PROGRESS] or [STOP] marker in response.{RESET}")
            print("The LLM may not have been able to do any work.")
            print("Loop ended: no progress")
            break

        if iteration >= max_iterations:
            print(f"\nLoop ended: max iterations ({max_iterations}) reached")
            break

        time.sleep(2)
except KeyboardInterrupt:
    print("\n\nSee ya!")
finally:
    total = (datetime.now() - loop_start).seconds
    print(f"\nTotal elapsed: {total // 60}m {total % 60}s")
