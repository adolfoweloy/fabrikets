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
    ORG  = "\033[38;5;208m"   # orange (door accent)
    WIN  = "\033[38;5;220m"   # amber (windows)
    SMK  = "\033[38;5;244m"   # gray (smoke)

    # Center 21-wide factory over the ~79-wide text block
    pad = " " * 29

    factory = [
        f"    {SMK}░{RESET}     {SMK}░{RESET}     {SMK}░{RESET}    ",
        f"    {PALE}█{RESET}     {PALE}█{RESET}     {PALE}█{RESET}    ",
        f"    {PALE}█{RESET}     {PALE}█{RESET}     {PALE}█{RESET}    ",
        f"{PALE}█████████████████████{RESET}",
        f"{PALE}█{RESET}   {WIN}▒▒{RESET}    {WIN}▒▒{RESET}    {WIN}▒▒{RESET}  {PALE}█{RESET}",
        f"{PALE}█{RESET}   {WIN}▒▒{RESET}    {WIN}▒▒{RESET}    {WIN}▒▒{RESET}  {PALE}█{RESET}",
        f"{PALE}█                   █{RESET}",
        f"{PALE}█{RESET}      {ORG}████████{RESET}     {PALE}█{RESET}",
        f"{PALE}█████████████████████{RESET}",
    ]
    for line in factory:
        print(pad + line)
    print()

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

CONTEXT_WINDOW = 200_000
CONFIG_FILE = "config.yaml"

# Parse arguments
mode = "spec"
max_iterations = 1
debug = False

args = sys.argv[1:]
i = 0
while i < len(args):
    if args[i] == "--max-iterations":
        i += 1
        max_iterations = int(args[i])
    elif args[i] in ("spec", "plan", "build"):
        mode = args[i]
    elif args[i] in ("-d", "--debug"):
        debug = True
    else:
        print(f"Error: unknown argument '{args[i]}'", file=sys.stderr)
        print("Usage: ./ralph.py [spec|plan|build] [-d] [--max-iterations N]", file=sys.stderr)
        sys.exit(1)
    i += 1

prompt_files = {"spec": "prompt_spec.md", "plan": "prompt_plan.md", "build": "prompt_build.md"}
prompt_file = prompt_files[mode]

os.makedirs(".ralph", exist_ok=True)
print_logo()


def load_config() -> dict:
    config = {}
    with open(CONFIG_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, _, value = line.partition(":")
                config[key.strip()] = value.strip()
    return config


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


def run_bootstrap() -> dict:
    print("\nWelcome to Fabrikets! No config found — let's set up your project.\n")
    src = ask("Source directory [src]: ").strip() or "src"
    domain = to_snake_case(ask("Initial domain group name (e.g. auth, billing, core): ").strip())
    os.makedirs(os.path.join(src, domain), exist_ok=True)
    config = {"src": src}
    with open(CONFIG_FILE, "w") as f:
        for k, v in config.items():
            f.write(f"{k}: {v}\n")
    print(f"\nConfig saved to {CONFIG_FILE}\n")
    return config


if not os.path.exists(CONFIG_FILE):
    config = run_bootstrap()
else:
    config = load_config()

os.makedirs(config["src"], exist_ok=True)

TRACKED_FILES = ["implementation_plan.md", "specs/", config["src"]]

if not os.path.exists(prompt_file):
    print(f"Error: {prompt_file} not found", file=sys.stderr)
    sys.exit(1)

print(f"Running in {mode} mode using {prompt_file}")
prompt = open(prompt_file).read()


def get_files_hash() -> str:
    try:
        result = subprocess.run(
            f"find {' '.join(TRACKED_FILES)} -type f 2>/dev/null | xargs md5sum 2>/dev/null | sort",
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
    src_abs = os.path.abspath(config["src"])
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
        if obj_type == "assistant":
            for block in obj.get("message", {}).get("content", []):
                if block.get("type") == "text":
                    text = block.get("text", "")
                    if text:
                        spinner.stop()
                        print(render_markdown(text), end="", flush=True)
                elif block.get("type") == "tool_use":
                    if debug:
                        spinner.stop()
                        name = block.get("name", "")
                        summary = format_tool_input(name, block.get("input", {}))
                        print(f"{CYAN}[{name}] {summary}{RESET}")
        elif obj_type == "user":
            for block in obj.get("message", {}).get("content", []):
                if block.get("type") == "tool_result" and block.get("is_error"):
                    spinner.stop()
                    content = block.get("content", "")
                    if isinstance(content, list):
                        content = " ".join(b.get("text", "") for b in content)
                    print(f"{RED}  ERROR: {str(content)[:150]}{RESET}")

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


# Spec mode: interactive interview with Claude to create/add a spec
if mode == "spec":
    src = config["src"]

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
        d for d in os.listdir(src)
        if os.path.isdir(os.path.join(src, d)) and not d.startswith(".")
    ) if os.path.isdir(src) else []
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

    domain_dir = os.path.join(src, domain)
    os.makedirs(domain_dir, exist_ok=True)
    interview_file = os.path.join(domain_dir, f"{feature}.md")

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

    with open(interview_file, "w") as f:
        f.write(f"<!-- spec_id: {spec_id} -->\n")
        f.write(f"<!-- domain: {domain} -->\n")
        f.write(f"<!-- feature: {feature} -->\n")
        f.write(f"<!-- spec_file: {interview_file} -->\n\n")
        f.write(interview_prompt)

    print(f"Spec: {interview_file}")

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
try:
    for iteration in range(1, max_iterations + 1):
        print(f"\n=== Iteration {iteration}/{max_iterations} starting at {datetime.now().strftime('%c')} ===")
        before_hash = get_files_hash()

        print("Sending prompt to Claude...")
        print("\n--- Claude's response ---")
        objects = run_claude(prompt, debug=debug)
        print("\n--- End response ---\n")

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
