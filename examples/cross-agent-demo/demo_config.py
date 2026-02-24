"""
Shared configuration and utilities for the Gaugid Cross-Agent Demo.

Provides terminal formatting, configuration loading, and common helpers
used by all three agents and the demo runner.
"""

import os
import sys
import time
import textwrap
from dataclasses import dataclass

# ── Terminal Colors & Formatting ──────────────────────────────────────────────


class C:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Agent colors
    TRAVEL = "\033[38;5;33m"  # Blue
    FOOD = "\033[38;5;208m"  # Orange
    ASSISTANT = "\033[38;5;135m"  # Purple

    # UI colors
    GREEN = "\033[38;5;34m"
    RED = "\033[38;5;196m"
    YELLOW = "\033[38;5;220m"
    CYAN = "\033[38;5;45m"
    WHITE = "\033[38;5;255m"
    GRAY = "\033[38;5;245m"

    # Backgrounds
    BG_BLUE = "\033[48;5;17m"
    BG_ORANGE = "\033[48;5;52m"
    BG_PURPLE = "\033[48;5;53m"
    BG_GREEN = "\033[48;5;22m"
    BG_DARK = "\033[48;5;236m"


# ── Agent Identifiers ────────────────────────────────────────────────────────

AGENT_TRAVEL = "travel"
AGENT_FOOD = "food"
AGENT_ASSISTANT = "assistant"

AGENT_COLORS = {
    AGENT_TRAVEL: C.TRAVEL,
    AGENT_FOOD: C.FOOD,
    AGENT_ASSISTANT: C.ASSISTANT,
}

AGENT_NAMES = {
    AGENT_TRAVEL: "Travel Agent (Google ADK)",
    AGENT_FOOD: "Food Agent (LangGraph)",
    AGENT_ASSISTANT: "Personal Assistant (Anthropic)",
}

AGENT_ICONS = {
    AGENT_TRAVEL: "plane",
    AGENT_FOOD: "fork_and_knife",
    AGENT_ASSISTANT: "robot",
}


# ── Configuration ─────────────────────────────────────────────────────────────


@dataclass
class DemoConfig:
    """Demo configuration loaded from environment variables."""

    gaugid_connection_token: str = ""
    gaugid_api_url: str = ""
    google_api_key: str = ""
    anthropic_api_key: str = ""
    demo_mode: bool = False  # If True, simulate API calls

    @classmethod
    def from_env(cls) -> "DemoConfig":
        """Load configuration from environment variables."""
        return cls(
            gaugid_connection_token=os.getenv("GAUGID_CONNECTION_TOKEN", ""),
            gaugid_api_url=os.getenv("GAUGID_API_URL", ""),
            google_api_key=os.getenv("GOOGLE_API_KEY", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            demo_mode=os.getenv("DEMO_MODE", "").lower() in ("1", "true", "yes"),
        )

    def validate(self) -> list[str]:
        """Validate configuration, return list of missing items."""
        missing = []
        if not self.gaugid_connection_token:
            missing.append("GAUGID_CONNECTION_TOKEN")
        if not self.google_api_key:
            missing.append("GOOGLE_API_KEY (needed for Travel Agent)")
        if not self.anthropic_api_key:
            missing.append("ANTHROPIC_API_KEY (needed for Assistant Agent)")
        return missing


# ── Pretty Printing ───────────────────────────────────────────────────────────

LINE_WIDTH = 72


def banner(text: str, color: str = C.CYAN) -> None:
    """Print a large banner."""
    border = "=" * LINE_WIDTH
    print(f"\n{color}{C.BOLD}{border}")
    print(f"  {text}")
    print(f"{border}{C.RESET}\n")


def section(text: str, color: str = C.WHITE) -> None:
    """Print a section header."""
    print(f"\n{color}{C.BOLD}--- {text} ---{C.RESET}\n")


def step(number: int, text: str) -> None:
    """Print a numbered step."""
    print(f"  {C.CYAN}{C.BOLD}[{number}]{C.RESET} {text}")


def agent_header(agent_id: str) -> None:
    """Print an agent header bar."""
    color = AGENT_COLORS.get(agent_id, C.WHITE)
    name = AGENT_NAMES.get(agent_id, agent_id)
    border = "-" * LINE_WIDTH
    print(f"\n{color}{C.BOLD}{border}")
    print(f"  {name}")
    print(f"{border}{C.RESET}")


def agent_says(agent_id: str, text: str) -> None:
    """Print what an agent says."""
    color = AGENT_COLORS.get(agent_id, C.WHITE)
    name = AGENT_NAMES.get(agent_id, agent_id)
    # Word-wrap long lines
    wrapped = textwrap.fill(text, width=LINE_WIDTH - 6)
    indented = textwrap.indent(wrapped, "    ")
    print(f"  {color}{C.BOLD}{name}:{C.RESET}")
    print(f"{C.WHITE}{indented}{C.RESET}")


def memory_proposed(agent_id: str, content: str, category: str) -> None:
    """Print a memory proposal notification."""
    color = AGENT_COLORS.get(agent_id, C.WHITE)
    print(f"  {color}>> Memory proposed:{C.RESET} {C.DIM}{content}{C.RESET}")
    print(f"     {C.GRAY}Category: {category}{C.RESET}")


def memory_loaded(memories: list[dict], label: str = "Profile memories loaded") -> None:
    """Print loaded memories."""
    print(f"  {C.GREEN}{label} ({len(memories)} found):{C.RESET}")
    for m in memories:
        cat = m.get("category", "unknown")
        content = m.get("content", "")
        # Truncate long content
        if len(content) > 80:
            content = content[:77] + "..."
        print(f"    {C.DIM}[{cat}]{C.RESET} {content}")


def success(text: str) -> None:
    """Print a success message."""
    print(f"  {C.GREEN}{C.BOLD}OK{C.RESET} {text}")


def error(text: str) -> None:
    """Print an error message."""
    print(f"  {C.RED}{C.BOLD}ERROR{C.RESET} {text}")


def info(text: str) -> None:
    """Print an info message."""
    print(f"  {C.GRAY}{text}{C.RESET}")


def pause_for_dashboard() -> None:
    """Pause and prompt user to check the Gaugid dashboard."""
    border = "-" * LINE_WIDTH
    print(f"\n{C.YELLOW}{C.BOLD}{border}")
    print("  DASHBOARD CHECK")
    print(f"{border}{C.RESET}")
    print(f"  {C.YELLOW}Open the Gaugid dashboard to see the memory proposals.")
    print(f"  Approve or reject them, then come back here.{C.RESET}")
    print()
    input(f"  {C.BOLD}Press Enter when ready to continue...{C.RESET}")
    print()


def typewrite(text: str, delay: float = 0.02) -> None:
    """Print text character by character for dramatic effect."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def format_profile_summary(profile: dict) -> str:
    """Format a profile dict into a readable summary."""
    lines = []
    memories = profile.get("memories", {})
    for mem_type in ("episodic", "semantic", "procedural"):
        mems = memories.get(mem_type, [])
        if mems:
            lines.append(f"  {C.BOLD}{mem_type.title()} memories ({len(mems)}):{C.RESET}")
            for m in mems:
                cat = m.get("category", "")
                content = m.get("content", "")
                confidence = m.get("confidence", 0)
                status = m.get("status", "unknown")
                lines.append(
                    f"    [{cat}] {content}"
                    f" {C.DIM}(confidence: {confidence}, status: {status}){C.RESET}"
                )
    if not lines:
        lines.append(f"  {C.DIM}(no memories yet){C.RESET}")
    return "\n".join(lines)
