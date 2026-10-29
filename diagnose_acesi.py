#!/usr/bin/env python3
"""Static diagnostic for server.py — parses with ast, executes nothing.

Checks three failure modes that can silently break the /chat loop:

1. NESTED helpers: the five _final_answer family functions must be at
   module level. If any landed inside _chat_dispatch (or another function),
   they're defined but unreachable — a NameError at the call site.

2. Tuple-unpack arity: `text, tcs, finish = got` must unpack 3 values to
   match _chat_one's 3-tuple return. A mismatch raises ValueError every round.

3. _chat_one return arity: confirms _chat_one returns a 3-tuple.
"""

import ast
import sys


HELPERS = [
    "_collect_tool_evidence",
    "_last_user_question",
    "_evidence_fallback",
    "_build_grounded_prompt",
    "_final_answer",
]


def _module_level_functions(tree):
    """Return {name: lineno} for every FunctionDef at module level."""
    return {
        node.name: node.lineno
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }


def _all_function_defs(tree):
    """Return {name: (lineno, enclosing)} for every FunctionDef, including nested."""
    result = {}

    def walk(node, enclosing=None):
        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                result[child.name] = (child.lineno, enclosing)
                walk(child, child.name)

    walk(tree)
    return result


def check_nested(tree):
    """Flag helpers that are defined inside another function."""
    all_defs = _all_function_defs(tree)
    module_defs = set(_module_level_functions(tree))
    problems = []
    for helper in HELPERS:
        if helper in all_defs:
            lineno, enclosing = all_defs[helper]
            if enclosing:
                problems.append(
                    f"  NESTED  {helper}    defined at line {lineno} "
                    f"inside {enclosing} -- NOT reachable at module level"
                )
        else:
            problems.append(
                f"  MISSING {helper}    not found in file"
            )
    return problems


def _count_assignment_targets(node):
    """Count names in the LHS of an assignment like `a, b, c = ...`."""
    if isinstance(node.targets[0], ast.Tuple):
        return len(node.targets[0].elts)
    return 1


def check_unpack(tree):
    """Find `text, tcs, finish = got` (or similar) and report arity."""
    problems = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not node.targets:
            continue
        value = node.value
        if not (isinstance(value, ast.Name) and value.id == "got"):
            continue
        arity = _count_assignment_targets(node)
        names = []
        if isinstance(node.targets[0], ast.Tuple):
            names = [e.id for e in node.targets[0].elts
                     if isinstance(e, ast.Name)]
        status = "OK" if arity == 3 else f"BROKEN - expected 3, got {arity} -> {('ValueError' if arity != 3 else '')}"
        problems.append(
            f"  line {node.lineno}  {', '.join(names)} = got  ->  unpacks {arity}  {status}"
        )
    return problems


def check_chat_one_return(tree):
    """Confirm _chat_one returns exactly 3 values."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name != "_chat_one":
            continue
        returns = []
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and child.value is not None:
                if isinstance(child.value, ast.Tuple):
                    returns.append(len(child.value.elts))
                elif isinstance(child.value, ast.Call):
                    returns.append("call")
                else:
                    returns.append("other")
        return returns
    return None


def main(path):
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source, filename=path)

    print("=== CHECK 1: helper placement (module-level?) ===")
    nested = check_nested(tree)
    if not nested:
        print("  all 5 helpers at module level -- OK")
    else:
        for line in nested:
            print(line)

    print("\n=== CHECK 2: tuple-unpack arity from 'got' ===")
    unpack = check_unpack(tree)
    if not unpack:
        print("  no '... = got' assignment found in dispatch loop")
    else:
        for line in unpack:
            print(line)

    print("\n=== CHECK 3: _chat_one return arity ===")
    ret = check_chat_one_return(tree)
    if ret is None:
        print("  _chat_one not found")
    else:
        print(f"  _chat_one return statements: {ret}")

    print("\n=== VERDICT ===")
    fail = any(n.startswith("  NESTED") or n.startswith("  MISSING") for n in nested)
    fail = fail or any("BROKEN" in u for u in unpack)
    print("  ALL CHECKS PASSED" if not fail else "  ISSUES DETECTED (see above)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python diagnose_acesi.py <server.py>")
        sys.exit(1)
    main(sys.argv[1])
