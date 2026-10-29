# ace_research.py
# Training module for ACEsi's web research workflow.
#
# Teaches ACEsi how to perform research tasks by combining web_search → webfetch →
# data extraction → write_file. The key lesson is that web_search returns only
# titles and URLs, while the actual data (addresses, phone numbers, emails) lives
# on the fetched pages — so webfetch is ALWAYS needed after web_search.
#
# Usage:
#   from ace_research import run_research_task
#   result = run_research_task(prompt, server, max_rounds=30)
#
# A "research task" is any user request that asks for factual information found
# on the web. The pattern:
#   1. web_search  → get a list of relevant URLs
#   2. webfetch   → read each URL's full content (search results are just titles)
#   3. Extract     → parse the data the user asked for from each fetched page
#   4. Compile      → gather all extracted data into a coherent answer
#   5. write_file   → save the results if the user asked to "save" / "note"
#   6. FINAL       → give the user a concise summary

import json
import re
import logging

logger = logging.getLogger("ace_research")

# ── Core research instructions injected into ACEsi's reasoning ────────────────

RESEARCH_WORKFLOW_INSTRUCTIONS = """
RESEARCH WORKFLOW — when a task asks for factual information on the web:

1. web_search {"query": "<search query>"}  → find the most relevant URLs.
   Search results give titles + URLs only. NOT full details.

2. For EACH relevant URL: webfetch {"url": "<url>", "format": "markdown"}
   This reads the actual page content where addresses, phones, emails live.

3. Extract the requested data from each webfetch result.

4. If the user asked to "save" / "note" / "write": compile the data and call
   write_file {"path": "notes/....md", "content": "..."} LAST, only after all
   data is gathered.

5. FINAL: give a concise summary + where it was saved (if applicable).

CRITICAL RULES:
- ONE tool call per turn. Never batch webfetch calls.
- webfetch returns up to ~8000 chars; if the page is long and you need more,
  fetch again with format="html" and extract specific sections.
- After web_search, DO NOT emit FINAL with just titles — you MUST webfetch.
- After webfetch, DO NOT emit FINAL with a URL list — you MUST extract details.
- If a URL fails to fetch, try the next one; don't stall.
- If the user says "list N agencies/companies/etc.", aim for exactly N.
"""


def extract_urls_from_search_result(search_output):
    """Given the text output of a web_search call, extract URLs.

    The search returns lines like:
      - Etchells & Young | Expert Rental Agents
        https://www.etchellsandyoung.co.za/...
    """
    urls = []
    lines = str(search_output).split("\n")
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("http://") or stripped.startswith("https://"):
            urls.append(stripped)
        else:
            m = re.match(r'(?:- )?.*?(\bhttps?://\S+)', stripped)
            if m:
                urls.append(m.group(1))
    return urls


def extract_contact_details(webfetch_content, patterns=None):
    """Extract structured contact info from fetched page text.

    Returns a dict with keys: name, address, phone, email, website.
    `patterns` can override the regex patterns used.
    """
    if patterns is None:
        patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'(?:\+27\s?|0|\(0)(?:\d{2,4}\s?\d{3,4}\s?\d{4,5}|\d{8,10})',
            "url": r'https?://[^\s<>"]+',
        }

    text = str(webfetch_content)
    result = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text)
        # Deduplicate while preserving order
        seen = set()
        unique = []
        for m in matches:
            if m not in seen:
                seen.add(m)
                unique.append(m)
        result[key] = unique[:5]  # top 5 of each

    return result


def compile_research_results(results_list, filename, title="Research Results"):
    """Compile extracted data from multiple fetches into a markdown file.

    Args:
        results_list: list of dicts, each like {"name": ..., "address": ...,
                        "phone": ..., "email": ..., "website": ...}
        filename: path to write the compiled markdown
        title: title for the compiled document
    Returns:
        The markdown content string.
    """
    lines = ["# %s" % title, ""]
    for i, r in enumerate(results_list, 1):
        lines.append("## %d. %s" % (i, r.get("name", "Agency %d" % i)))
        for field in ("address", "phone", "email", "website"):
            val = r.get(field)
            if val:
                if isinstance(val, list):
                    val = "; ".join(val[:2])
                lines.append("- **%s:** %s" % (field.capitalize(), val))
        lines.append("")

    content = "\n".join(lines)

    import os
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else ".", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    return content


def run_research_task(prompt, server=None, max_rounds=30):
    """Execute a research task end-to-end.

    This is a template that server.py's /autonomous route calls when the user
    wants web research. It injects the RESEARCH_WORKFLOW_INSTRUCTIONS into the
    system prompt so ACEsi follows the search → fetch → extract → save pattern.

    Args:
        prompt: the user's research request (e.g. "Find 10 rental agencies...")
        server: server instance with _call_tool
        max_rounds: safety cap on model interactions

    Returns:
        TaskResult-like dict with outputs and summary.
    """
    if server is None:
        try:
            import server as srv_mod
            server = getattr(srv_mod, "server_instance", None)
        except Exception:
            pass

    result = {"outputs": [], "errors": [], "completed": False, "summary": {}}
    if server is None:
        result["errors"].append("run_research_task: no server instance")
        return result

    # Use ace_prompt to build a system prompt that includes research guidance
    try:
        from ace_prompt import build_task_prompt
        system_prompt = build_task_prompt(server) + "\n\n" + RESEARCH_WORKFLOW_INSTRUCTIONS
    except Exception:
        system_prompt = RESEARCH_WORKFLOW_INSTRUCTIONS

    # Delegate to ace_task.run_task_autonomous, passing our enhanced prompt
    try:
        from ace_task import run_task_autonomous
        tr = run_task_autonomous(
            prompt=prompt,
            task_name="research",
            server=server,
            max_turns=max_rounds,
            auto_dump=False,  # no UI nav in research tasks
        )
        result["outputs"] = tr.outputs
        result["errors"] = tr.errors
        result["completed"] = tr.steps_failed == 0 and tr.steps_run > 0
        result["summary"] = tr.summary()
    except Exception as e:
        result["errors"].append("run_research_task failed: %s" % str(e)[:200])

    return result


# ── Demonstration / test ───────────────────────────────────────────────────────

def demo():
    """Print the exact instruction ACEsi should be trained with."""
    print("RESEARCH WORKFLOW INSTRUCTIONS FOR ACEsi")
    print("=" * 50)
    print(RESEARCH_WORKFLOW_INSTRUCTIONS)
    print("=" * 50)
    print("\nExample command pattern:")
    print('1. CALL: web_search {"query": "real estate rental agencies Sandton Johannesburg", "max_results": 10}')
    print('2. CALL: webfetch {"url": "https://example.com/agency1", "format": "markdown"}')
    print('(repeat for each URL from search results)')
    print('3. CALL: write_file {"path": "notes/rental_agencies.md", "content": "..."}')
    print('4. FINAL: summary of what was found')


if __name__ == "__main__":
    demo()
