#!/usr/bin/env python3
"""Ralph - AI-driven development loop"""

import sys
import os
import re
import json
import subprocess
import threading
import time
import uuid
import atexit
import blessed
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


_term = blessed.Terminal()
_status_cfg: dict = {}


class StatusBar:
    def start(self, config: dict) -> None:
        global _status_cfg
        _status_cfg = config
        # Reserve the last terminal row by restricting the scroll region
        sys.stdout.write(f"\033[1;{_term.height - 1}r")
        sys.stdout.flush()
        self.refresh()
        atexit.register(self._teardown)
        threading.Thread(target=self._loop, daemon=True).start()

    def refresh(self) -> None:
        try:
            total = 0.0
            if os.path.exists(".ralph/cost.md"):
                with open(".ralph/cost.md") as f:
                    for line in f:
                        m = re.search(r"\$(\d+\.\d+)", line)
                        if m:
                            total += float(m.group(1))
            src = _status_cfg.get("src", "??")
            content = f"  cost: ${total:.4f}  │  src: {src}  "
            padded = content.ljust(_term.width)[: _term.width]
            bar = _term.on_color(235) + _term.color(216) + padded + _term.normal
            sys.stdout.write(_term.save + _term.move(_term.height - 1, 0) + bar + _term.restore)
            sys.stdout.flush()
        except Exception:
            pass

    def _loop(self) -> None:
        while True:
            self.refresh()
            time.sleep(2)

    def _teardown(self) -> None:
        try:
            sys.stdout.write("\033[r")  # restore full scroll region
            sys.stdout.write(_term.move(_term.height - 1, 0) + _term.clear_eol)
            sys.stdout.flush()
        except Exception:
            pass


status_bar = StatusBar()


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


def run_bootstrap() -> dict:
    print("\nWelcome to Fabrikets! No config found — let's set up your project.\n")
    src = input("Source directory [src]: ").strip() or "src"
    if not os.path.exists(src):
        ans = input(f"'{src}' doesn't exist. Create it? [y/N] ").strip().lower()
        if ans in ("y", "yes"):
            os.makedirs(src, exist_ok=True)
        else:
            print("Aborted.")
            sys.exit(0)
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

status_bar.start(config)

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
    proc = subprocess.Popen(
        ["claude", "--dangerously-skip-permissions", "--output-format", "stream-json", "--print", "--verbose"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    proc.stdin.write(prompt)
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
    status_bar.refresh()


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
    if os.path.exists("specs/specs.yaml"):
        question = "Start an interview with Claude to add a new specification? [y/N] "
    else:
        question = "No specs found. Start an interview with Claude to create a new specification? [y/N] "
    answer = input(question).strip().lower()
    if answer not in ("y", "yes"):
        print("Aborted.")
        sys.exit(0)

    spec_id = uuid.uuid4().hex[:6]
    spec_dir = f"specs/{spec_id}"
    os.makedirs(spec_dir, exist_ok=True)

    interview_file = f"{spec_dir}/interview.md"
    with open(interview_file, "w") as f:
        f.write(f"<!-- spec_id: {spec_id} -->\n")
        f.write(f"<!-- spec_dir: {spec_dir} -->\n\n")
        f.write(prompt)

    print(f"Spec ID: {spec_id}  (saved to {spec_dir}/)")

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
                print(f"Interview complete. Spec saved to {spec_dir}/")
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

            user_input = input("You: ").strip()
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
