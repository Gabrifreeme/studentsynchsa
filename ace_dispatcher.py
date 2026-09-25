"""ace_dispatcher.py - self-contained multi-subtask agent dispatcher.

Single-file build of the ace_ref reference implementation. Drop this next to
server.py and import from it; no dependencies beyond the standard library.

    from ace_dispatcher import TaskRunner, TaskLedger, ToolRegistry, Subtask, RunConfig

Four invariants this enforces:
  1. A tool can never raise into the loop - ToolRegistry.call() returns a ToolOutcome.
  2. A failed subtask is recorded, then execution continues.
  3. Every state change is persisted before the next step starts.
  4. The report states what succeeded before what failed.

See ace_ref/README.md for the porting map into server.py, and ace_ref/tests/ for the
47-test suite this file is generated from.
"""

from __future__ import annotations

import json
import os
import queue
import re
import threading
import time
import uuid
import inspect
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Iterable

# ----------------------------------------------------------------------------
# TOOLS - registry, timeouts, bounded retries
# ----------------------------------------------------------------------------


# Tool registry with hard per-tool timeouts and bounded retries.
# The rule this module enforces: **a tool can never raise into the caller's loop.**
# `call()` always returns a `ToolOutcome`. That single property is what stops one bad
# tool (your hanging `weather`) from taking down the other four subtasks.




class ToolError(Exception):
    """Retryable tool failure (network blip, 5xx, transient parse error)."""


class NonRetryableToolError(ToolError):
    """Bad input, missing credential, 404. Retrying is pointless."""


class ToolTimeout(ToolError):
    """The tool exceeded its deadline. Always retryable, at most `retries` times."""


class ToolNotFound(LookupError):
    """No tool registered under that name."""


@dataclass
class ToolOutcome:
    ok: bool
    value: Any = None
    error: str | None = None
    error_type: str | None = None
    attempts: int = 0
    elapsed: float = 0.0
    timed_out: bool = False

    def __bool__(self) -> bool:
        return self.ok


@dataclass
class ToolSpec:
    name: str
    fn: Callable[..., Any]
    timeout: float = 10.0
    retries: int = 2  # 2 retries == 3 total attempts
    backoff: float = 0.4  # seconds, doubled per retry
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def max_attempts(self) -> int:
        return self.retries + 1


def _run_guarded(
    fn: Callable[..., Any], args: tuple, kwargs: dict, timeout: float, label: str
) -> Any:
    """Call `fn` with a hard deadline.

    Implemented with a daemon thread rather than an executor pool: daemon threads
    are abandoned at process exit, so a genuinely hung tool cannot wedge shutdown.

    Caveat worth knowing: the thread is *abandoned, not killed*. Python has no safe
    way to terminate a thread mid-syscall. So this wrapper is the backstop that
    keeps your loop alive -- the real fix belongs in the tool itself (set a timeout
    on the HTTP client). Both layers matter; this one is non-negotiable.
    """
    box: queue.Queue[tuple[str, Any]] = queue.Queue(maxsize=1)

    def target() -> None:
        try:
            box.put(("ok", fn(*args, **kwargs)))
        except BaseException as exc:  # noqa: BLE001 - boundary: nothing may escape a tool
            box.put(("err", exc))

    worker = threading.Thread(target=target, daemon=True, name=f"tool-{label}")
    worker.start()
    try:
        kind, payload = box.get(timeout=timeout)
    except queue.Empty:
        raise ToolTimeout(f"tool '{label}' exceeded {timeout}s deadline") from None

    if kind == "err":
        raise payload
    return payload


class ToolRegistry:
    def __init__(self) -> None:
        self._specs: dict[str, ToolSpec] = {}

    def register(
        self,
        name: str,
        fn: Callable[..., Any] | None = None,
        *,
        timeout: float = 10.0,
        retries: int = 2,
        backoff: float = 0.4,
        description: str = "",
        **metadata: Any,
    ) -> Any:
        """Register directly, or use as a decorator: @registry.tool("name", timeout=5)."""

        def attach(func: Callable[..., Any]) -> Callable[..., Any]:
            self._specs[name] = ToolSpec(
                name=name,
                fn=func,
                timeout=timeout,
                retries=retries,
                backoff=backoff,
                description=description or (func.__doc__ or "").strip().split("\n")[0],
                metadata=dict(metadata),
            )
            return func

        if fn is None:
            return attach
        return attach(fn)

    def tool(self, name: str, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return lambda func: self.register(name, func, **kwargs)  # type: ignore[arg-type,return-value]

    def __contains__(self, name: object) -> bool:
        return name in self._specs

    def spec(self, name: str) -> ToolSpec:
        try:
            return self._specs[name]
        except KeyError:
            raise ToolNotFound(
                f"no tool named {name!r}; registered: {sorted(self._specs)}"
            ) from None

    def names(self) -> list[str]:
        return sorted(self._specs)

    def signature(self, name: str) -> str:
        spec = self.spec(name)
        fn = spec.metadata.get("original_fn") or spec.fn
        try:
            sig = inspect.signature(fn)
        except (ValueError, TypeError):
            arg_keys = spec.metadata.get("arg_keys")
            if arg_keys:
                return f"{name}({', '.join(f'{k}: any' for k in arg_keys)})"
            return f"{name}()"
        parts = []
        for param in sig.parameters.values():
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue
            if param.annotation is param.empty:
                ann = "any"
            else:
                ann = getattr(param.annotation, "__name__", str(param.annotation))
            if param.default is param.empty:
                parts.append(f"{param.name}: {ann}")
            else:
                default = param.default
                if isinstance(default, bool):
                    default = "true" if default else "false"
                else:
                    default = repr(default)
                parts.append(f"{param.name}: {ann} = {default}")
        return f"{name}({', '.join(parts)})"

    def describe_for_prompt(self) -> str:
        lines = ["## Available tools"]
        for name in self.names():
            spec = self.spec(name)
            desc = spec.description or spec.metadata.get("description") or ""
            lines.append(f"- `{self.signature(name)}` - {desc}")
        return "\n".join(lines)

    def audit_prompt(self, prompt_text: str) -> list[str]:
        issues: list[str] = []
        registered = set(self.names())
        mentioned = set()
        for name in registered:
            if re.search(r'\b' + re.escape(name) + r'\b', prompt_text):
                mentioned.add(name)
        missing = registered - mentioned
        for name in sorted(missing):
            issues.append(f"registered tool '{name}' missing from prompt")
        unregistered = mentioned - registered
        for name in sorted(unregistered):
            issues.append(f"prompt mentions unregistered tool '{name}'")
        return issues

    def assert_prompt_matches(self, prompt_text: str, source: str = "") -> None:
        issues = self.audit_prompt(prompt_text)
        if issues:
            prefix = f"[{source}] " if source else ""
            raise RuntimeError(prefix + "; ".join(issues))

    # ---- execution -------------------------------------------------------
    def call_once(self, name: str, **args: Any) -> Any:
        """One attempt, no retry. Raises ToolError subclasses."""
        spec = self.spec(name)
        return _run_guarded(spec.fn, (), args, spec.timeout, spec.name)

    def call(self, name: str, on_attempt: Callable[[int, ToolOutcome], None] | None = None,
             **args: Any) -> ToolOutcome:
        """Run with bounded retries. Never raises."""
        try:
            spec = self.spec(name)
        except ToolNotFound as exc:
            return ToolOutcome(ok=False, error=str(exc), error_type="ToolNotFound", attempts=0)

        started = time.time()
        last: ToolOutcome | None = None

        for attempt in range(1, spec.max_attempts + 1):
            try:
                value = _run_guarded(spec.fn, (), args, spec.timeout, spec.name)
                outcome = ToolOutcome(
                    ok=True,
                    value=value,
                    attempts=attempt,
                    elapsed=time.time() - started,
                )
                if on_attempt:
                    on_attempt(attempt, outcome)
                return outcome  # success exits here -- falling through would re-invoke the tool
            except NonRetryableToolError as exc:
                outcome = ToolOutcome(
                    ok=False,
                    error=f"{type(exc).__name__}: {exc}",
                    error_type=type(exc).__name__,
                    attempts=attempt,
                    elapsed=time.time() - started,
                )
                if on_attempt:
                    on_attempt(attempt, outcome)
                return outcome  # retrying a 404 three times just wastes your budget
            except ToolTimeout as exc:
                outcome = ToolOutcome(
                    ok=False,
                    error=str(exc),
                    error_type="ToolTimeout",
                    attempts=attempt,
                    timed_out=True,
                    elapsed=time.time() - started,
                )
            except ToolError as exc:
                outcome = ToolOutcome(
                    ok=False,
                    error=f"{type(exc).__name__}: {exc}",
                    error_type=type(exc).__name__,
                    attempts=attempt,
                    elapsed=time.time() - started,
                )
            except Exception as exc:  # noqa: BLE001 - unknown tools blow up; treat as retryable
                outcome = ToolOutcome(
                    ok=False,
                    error=f"{type(exc).__name__}: {exc}",
                    error_type=type(exc).__name__,
                    attempts=attempt,
                    elapsed=time.time() - started,
                )
            except BaseException as exc:  # noqa: BLE001 - KeyboardInterrupt/SystemExit from a tool
                # A tool must not be able to inject a control-flow signal into the
                # agent loop. Box it, report it, do not retry, do not re-raise.
                outcome = ToolOutcome(
                    ok=False,
                    error=f"{type(exc).__name__}: {exc}",
                    error_type=type(exc).__name__,
                    attempts=attempt,
                    elapsed=time.time() - started,
                )
                if on_attempt:
                    on_attempt(attempt, outcome)
                return outcome

            last = outcome
            if on_attempt:
                on_attempt(attempt, outcome)

            if attempt < spec.max_attempts:
                time.sleep(spec.backoff * (2 ** (attempt - 1)))

        assert last is not None
        return last


# ----------------------------------------------------------------------------
# LEDGER - the durable subtask checklist
# ----------------------------------------------------------------------------


# Subtask ledger: the durable checklist that keeps a multi-part task from collapsing.
# The whole point of this module is that the *plan* lives on disk, not in the model's
# context. If subtask 4 of 6 explodes, subtasks 1-3 keep their results and 5-6 still run.




class Status(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


TERMINAL = {Status.DONE, Status.FAILED, Status.SKIPPED}


def _json_default(obj: Any) -> Any:
    """Best-effort coercion so an odd tool result never breaks persistence."""
    if isinstance(obj, Status):
        return obj.value
    if hasattr(obj, "__dict__"):
        return vars(obj)
    return str(obj)


@dataclass
class Subtask:
    """One unit of work. `tool` is a hint; the runner executes it via the registry."""

    id: str
    title: str
    tool: str | None = None
    args: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    # Soft deps: wait for them if they can, but proceed even if they fail.
    soft_depends_on: list[str] = field(default_factory=list)
    status: Status = Status.PENDING
    attempts: int = 0  # how many times this *subtask* was executed (resets on rerun)
    tool_attempts: int = 0  # tool invocations inside the last execution (incl. retries)
    result: Any = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    ended_at: float | None = None

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL

    def clone(self) -> "Subtask":
        """A detached copy, so a plan list stays reusable across runs."""
        return Subtask.from_dict(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "tool": self.tool,
            "args": self.args,
            "depends_on": list(self.depends_on),
            "soft_depends_on": list(self.soft_depends_on),
            "status": self.status.value,
            "attempts": self.attempts,
            "tool_attempts": self.tool_attempts,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Subtask":
        return cls(
            id=data["id"],
            title=data["title"],
            tool=data.get("tool"),
            args=data.get("args") or {},
            depends_on=list(data.get("depends_on") or []),
            soft_depends_on=list(data.get("soft_depends_on") or []),
            status=Status(data.get("status", "pending")),
            attempts=int(data.get("attempts", 0)),
            tool_attempts=int(data.get("tool_attempts", 0)),
            result=data.get("result"),
            error=data.get("error"),
            created_at=float(data.get("created_at") or time.time()),
            started_at=data.get("started_at"),
            ended_at=data.get("ended_at"),
        )


_REF = re.compile(r"\{\{\s*ref:([A-Za-z0-9_]+)((?:\.[A-Za-z0-9_]+)*)\s*\}\}")


def _dig(value: Any, path: str) -> Any:
    """Walk a dotted path ('results.0.url') through dicts, lists and objects.

    Numeric segments index into lists/tuples -- without that, the common
    search-then-fetch pattern (`{{ref:search.results.0.url}}`) resolves to None.
    Missing segments resolve to None rather than raising.
    """
    cur = value
    for part in path.lstrip(".").split("."):
        if not part:
            continue
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, (list, tuple)):
            if not part.lstrip("-").isdigit():
                return None
            index = int(part)
            if -len(cur) <= index < len(cur):
                cur = cur[index]
            else:
                return None
        else:
            cur = getattr(cur, part, None)
        if cur is None:
            return None
    return cur


class TaskLedger:
    """An ordered, dependency-aware, persistable set of subtasks.

    Every mutation writes to disk. That is what makes completed work survive a
    later failure, a crash, or a restart.
    """

    def __init__(self, tasks: Iterable[Subtask] | None = None, path: str | None = None) -> None:
        self.tasks: list[Subtask] = []
        self.path = path
        self._lock = threading.RLock()
        for task in tasks or []:
            self.add(task)

    # ---- construction -------------------------------------------------
    def add(self, task: Subtask) -> Subtask:
        """Store a *copy* of `task`.

        A plan is a template. If the ledger mutated the caller's Subtask objects,
        running the same plan twice would silently no-op the second time, because
        every task would already be terminal. Callers get back the stored copy.
        """
        with self._lock:
            if any(t.id == task.id for t in self.tasks):
                raise ValueError(f"duplicate subtask id: {task.id}")
            unknown = set(task.depends_on) - {t.id for t in self.tasks}
            if unknown:
                raise ValueError(
                    f"subtask {task.id!r} depends on unknown id(s): {sorted(unknown)}"
                )
            stored = task.clone()
            self.tasks.append(stored)
            self._persist()
            return stored

    def get(self, task_id: str) -> Subtask:
        for task in self.tasks:
            if task.id == task_id:
                return task
        raise KeyError(task_id)

    def __len__(self) -> int:
        return len(self.tasks)

    def __iter__(self):
        return iter(self.tasks)

    # ---- state transitions --------------------------------------------
    def mark_running(self, task_id: str) -> Subtask:
        return self._transition(task_id, Status.RUNNING)

    def mark_done(self, task_id: str, result: Any = None) -> Subtask:
        task = self._transition(task_id, Status.DONE)
        task.result = result
        task.error = None
        self._persist()
        return task

    def mark_failed(self, task_id: str, error: str) -> Subtask:
        task = self._transition(task_id, Status.FAILED)
        task.error = error
        self._persist()
        return task

    def mark_skipped(self, task_id: str, reason: str) -> Subtask:
        task = self._transition(task_id, Status.SKIPPED)
        task.error = reason
        self._persist()
        return task

    def _transition(self, task_id: str, status: Status) -> Subtask:
        with self._lock:
            task = self.get(task_id)
            task.status = status
            now = time.time()
            if status is Status.RUNNING:
                task.started_at = now
                task.attempts += 1
            elif status in TERMINAL:
                task.ended_at = now
            self._persist()
            return task

    def reset_for_rerun(self, only_ids: set[str] | None = None) -> list[Subtask]:
        """Clear terminal state so a subtask can run again (used by resume)."""
        cleared: list[Subtask] = []
        with self._lock:
            for task in self.tasks:
                if only_ids is not None and task.id not in only_ids:
                    continue
                task.status = Status.PENDING
                task.attempts = 0
                task.tool_attempts = 0
                task.error = None
                task.started_at = None
                task.ended_at = None
                cleared.append(task)
            self._persist()
        return cleared

    # ---- scheduling ----------------------------------------------------
    def next_runnable(self) -> Subtask | None:
        """First PENDING task whose hard deps are all DONE.

        A task blocked by a FAILED hard dep is cascaded to SKIPPED immediately,
        so it never sits in the queue pretending it might run. Soft deps are
        only waited on while they are still PENDING/RUNNING.
        """
        with self._lock:
            by_id = {t.id: t for t in self.tasks}

            for task in self.tasks:
                if task.status is not Status.PENDING:
                    continue

                blocked_hard = [
                    d for d in task.depends_on if by_id[d].status in (Status.FAILED, Status.SKIPPED)
                ]
                if blocked_hard:
                    self.mark_skipped(
                        task.id,
                        f"dependency failed: {', '.join(blocked_hard)}",
                    )
                    continue

                waiting = [
                    d
                    for d in (*task.depends_on, *task.soft_depends_on)
                    if by_id[d].status in (Status.PENDING, Status.RUNNING)
                ]
                if waiting:
                    continue

                return task

            return None

    def pending_ids(self) -> list[str]:
        return [t.id for t in self.tasks if t.status is Status.PENDING]

    def counts(self) -> dict[str, int]:
        out = {s.value: 0 for s in Status}
        for task in self.tasks:
            out[task.status.value] += 1
        return out

    @property
    def is_complete(self) -> bool:
        return all(t.is_terminal for t in self.tasks)

    # ---- result passing -------------------------------------------------
    def results(self) -> dict[str, Any]:
        """Successful results keyed by subtask id, for downstream reference."""
        return {t.id: t.result for t in self.tasks if t.status is Status.DONE}

    def resolve(self, value: Any) -> Any:
        """Substitute {{ref:task_id}} / {{ref:task_id.path}} placeholders.

        A placeholder that is the *entire* string is replaced with the raw object
        (preserving type); one embedded in longer text is interpolated as a string.
        """
        if isinstance(value, str):
            exact = _REF.fullmatch(value.strip())
            if exact:
                return _dig(self.results(), exact.group(1) + exact.group(2))

            def sub(match: re.Match[str]) -> str:
                found = _dig(self.results(), match.group(1) + match.group(2))
                return "" if found is None else str(found)

            return _REF.sub(sub, value)

        if isinstance(value, dict):
            return {k: self.resolve(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.resolve(v) for v in value]
        return value

    # ---- persistence ----------------------------------------------------
    def _persist(self) -> None:
        if not self.path:
            return
        tmp = f"{self.path}.tmp"
        directory = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(directory, exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(
                {"version": 1, "tasks": [t.to_dict() for t in self.tasks]},
                handle,
                indent=2,
                default=_json_default,
            )
        os.replace(tmp, self.path)  # atomic: a crash mid-write can't corrupt the ledger

    @classmethod
    def load(cls, path: str) -> "TaskLedger":
        ledger = cls(path=None)
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        ledger.tasks = [Subtask.from_dict(d) for d in data["tasks"]]
        # Re-running a subtask that was RUNNING when we died: it never finished.
        for task in ledger.tasks:
            if task.status is Status.RUNNING:
                task.status = Status.PENDING
                task.started_at = None
        ledger.path = path
        ledger._persist()
        return ledger

    @staticmethod
    def new_id(prefix: str = "t") -> str:
        return f"{prefix}_{uuid.uuid4().hex[:6]}"


# ----------------------------------------------------------------------------
# RUNNER - the dispatcher loop
# ----------------------------------------------------------------------------


# The dispatcher loop: walk the ledger, execute subtasks, never lose work.
# This is the piece to port into `_chat_dispatch` / `run_agent`. The two invariants:
# 1. The loop never exits because a tool failed. `registry.call()` returns an outcome;
# a failed subtask is *recorded*, not raised.
# 2. Every state change is persisted before the next step starts, so a crash, a step
# cap, or a hung tool leaves the finished subtasks intact on disk.




@dataclass
class RunConfig:
    max_steps: int = 50
    on_event: Callable[[str, dict[str, Any]], None] | None = None
    # When True, a failed subtask stops the whole run. Off by default -- that is
    # exactly the behaviour that made your agent abandon a 5-part request.
    fail_fast: bool = False


@dataclass
class RunResult:
    ledger: TaskLedger
    steps: int = 0
    stopped_early: str | None = None
    outcomes: dict[str, ToolOutcome] = field(default_factory=dict)

    @property
    def done(self) -> list[Subtask]:
        return [t for t in self.ledger if t.status is Status.DONE]

    @property
    def failed(self) -> list[Subtask]:
        return [t for t in self.ledger if t.status is Status.FAILED]

    @property
    def skipped(self) -> list[Subtask]:
        return [t for t in self.ledger if t.status is Status.SKIPPED]

    @property
    def ok(self) -> bool:
        return not self.failed and not self.skipped

    def counts(self) -> dict[str, int]:
        return self.ledger.counts()


class TaskRunner:
    def __init__(
        self,
        registry: ToolRegistry,
        config: RunConfig | None = None,
        ledger_path: str | None = None,
    ) -> None:
        self.registry = registry
        self.config = config or RunConfig()
        self.ledger_path = ledger_path

    def _emit(self, event: str, **payload: Any) -> None:
        if self.config.on_event:
            self.config.on_event(event, payload)

    def run(self, tasks: list[Subtask] | TaskLedger | None = None) -> RunResult:
        """Execute pending subtasks. Safe to call again on the same ledger to resume."""
        if isinstance(tasks, TaskLedger):
            ledger = tasks
        else:
            ledger = TaskLedger(tasks or [], path=self.ledger_path)

        result = RunResult(ledger=ledger)

        while True:
            task = ledger.next_runnable()
            if task is None:
                break

            if result.steps >= self.config.max_steps:
                # Cap hit: park what is left instead of throwing away what finished.
                result.stopped_early = f"max_steps={self.config.max_steps} reached"
                for task_id in ledger.pending_ids():
                    ledger.mark_skipped(task_id, result.stopped_early)
                self._emit("step_cap", reason=result.stopped_early)
                break

            result.steps += 1
            self._execute(ledger, task, result)

            if self.config.fail_fast and task.status is Status.FAILED:
                result.stopped_early = f"fail_fast after {task.id!r}"
                for task_id in ledger.pending_ids():
                    ledger.mark_skipped(task_id, result.stopped_early)
                self._emit("fail_fast", task_id=task.id)
                break

        return result

    def _execute(self, ledger: TaskLedger, task: Subtask, result: RunResult) -> None:
        self._emit("subtask_start", id=task.id, title=task.title, tool=task.tool)
        ledger.mark_running(task.id)

        if task.tool is None:
            ledger.mark_failed(task.id, "subtask has no tool assigned")
            self._emit("subtask_failed", id=task.id, error="no tool assigned")
            return

        if task.tool not in self.registry:
            # Recorded as a failure, not raised. This is the line that keeps the
            # remaining subtasks alive when one step references a missing tool.
            error = f"unknown tool {task.tool!r}; available: {self.registry.names()}"
            ledger.mark_failed(task.id, error)
            self._emit("subtask_failed", id=task.id, error=error)
            return

        resolved_args = ledger.resolve(task.args)

        def on_attempt(attempt: int, outcome: ToolOutcome) -> None:
            self._emit(
                "attempt",
                id=task.id,
                tool=task.tool,
                attempt=attempt,
                ok=outcome.ok,
                error=outcome.error,
                timed_out=outcome.timed_out,
            )

        outcome = self.registry.call(task.tool, on_attempt=on_attempt, **resolved_args)
        result.outcomes[task.id] = outcome
        task.tool_attempts = outcome.attempts

        if outcome.ok:
            ledger.mark_done(task.id, outcome.value)
            self._emit(
                "subtask_done",
                id=task.id,
                attempts=outcome.attempts,
                elapsed=round(outcome.elapsed, 3),
            )
        else:
            # Name the error class, not just its message: "ToolTimeout" tells you
            # to add a client-side timeout, "404" tells you to fix the URL.
            detail = f"{outcome.error_type}: {outcome.error} (after {outcome.attempts} attempt(s))"
            ledger.mark_failed(task.id, detail)
            self._emit("subtask_failed", id=task.id, error=detail, error_type=outcome.error_type)


def decompose(
    request: str,
    planner: Callable[[str], list[Subtask]] | None = None,
) -> list[Subtask]:
    """Turn one compound request into a subtask list.

    Pass your LLM-backed planner in; the signature is the only contract. Keeping it
    injectable means the runner stays testable and you can swap the decomposer
    without touching the loop.

    A planner is worth its weight in gold only if it also emits `depends_on`.
    That field is why the note file gets written: the write step can name the three
    fetch steps it needs, and the runner will not start it until they are DONE.
    """
    if planner is None:
        raise ValueError("decompose() needs a planner callable (e.g. your LLM call)")
    tasks = planner(request)
    if not tasks:
        raise ValueError(f"planner returned no subtasks for: {request!r}")
    seen: set[str] = set()
    for task in tasks:
        if task.id in seen:
            raise ValueError(f"planner emitted duplicate id {task.id!r}")
        seen.add(task)
    return tasks


# ----------------------------------------------------------------------------
# REPORT - partial-completion reporting
# ----------------------------------------------------------------------------


# Partial-completion reporting.
# Your agent's failure message -- "I attempted the task multiple times but couldn't find
# a reliable answer" -- is a whole-task verdict on a partially-succeeded run. This module
# exists so that verdict can never be produced when four of five subtasks actually worked.




_ICONS = {
    Status.DONE: "[done]",
    Status.FAILED: "[FAILED]",
    Status.SKIPPED: "[skipped]",
    Status.PENDING: "[pending]",
    Status.RUNNING: "[running]",
}


def summarize(result: RunResult, show_results: bool = True, max_chars: int = 500) -> str:
    """Markdown report. Leads with what succeeded, then states exactly what didn't."""
    counts = result.counts()
    total = sum(counts.values())
    lines: list[str] = []

    if result.ok:
        lines.append(f"All {total} subtasks completed.")
    else:
        lines.append(
            f"**{counts['done']} of {total} subtasks completed.** "
            f"{counts['failed']} failed, {counts['skipped']} skipped. "
            "Results from the successful steps are preserved below."
        )

    if result.stopped_early:
        lines.append(f"\nRun stopped early: {result.stopped_early}")

    for task in result.ledger:
        lines.append(f"\n### {_ICONS[task.status]} {task.title}  (`{task.id}`)")
        if task.tool:
            invocations = task.tool_attempts or task.attempts
            lines.append(f"- tool: `{task.tool}` - {invocations} tool call(s)")

        if task.status is Status.DONE and show_results:
            rendered = _render(task.result, max_chars)
            lines.append(f"- result: {rendered}")
        elif task.error:
            lines.append(f"- why: {task.error}")

    if result.failed:
        lines.append("\n## What to check next")
        for task in result.failed:
            lines.append(f"- `{task.id}` ({task.tool}): {task.error}")

    return "\n".join(lines)


def _render(value: Any, max_chars: int) -> str:
    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, indent=2, default=str)
        except (TypeError, ValueError):
            text = str(value)
    text = text.strip()
    if len(text) > max_chars:
        text = text[:max_chars] + f"... [+{len(text) - max_chars} chars]"
    return text


def to_json(result: RunResult) -> str:
    """Machine-readable handoff, for feeding the partial state back to the model."""
    return json.dumps(
        {
            "counts": result.counts(),
            "steps": result.steps,
            "stopped_early": result.stopped_early,
            "ok": result.ok,
            "tasks": [t.to_dict() for t in result.ledger],
        },
        indent=2,
        default=str,
    )


_SUBTASK_PROBES = [
    ("web search",   ("web_search",),            r"\bsearch\b|\bfind out\b|\bagenc"),
    ("fetch pages",  ("webfetch", "curl"),       r"\bfetch\b|\btop \d+\b"),
    ("save file",    ("write_file", "open_in_vscode"), r"\bsave\b|\bwrite .*file\b"),
    ("weather",      ("weather",),               r"\bweather\b"),
    ("current time", ("get_time",),              r"\bcurrent time\b|\bwhat time\b"),
]


class GapReport:
    def __init__(self, has_gaps: bool, missing: list[str]):
        self.has_gaps = has_gaps
        self.missing = missing

    def __str__(self):
        return f"missing tools for: {', '.join(self.missing)}"

    def __repr__(self):
        return self.__str__()


def find_gaps(user_message: str, allowed_names: set[str]) -> GapReport:
    """Report which subtasks mentioned in the request have no matching tool."""
    text = (user_message or "").lower()
    done = set(allowed_names)
    missing = [label for label, tools, pattern in _SUBTASK_PROBES
               if re.search(pattern, text) and not (done & set(tools))]
    return GapReport(has_gaps=bool(missing), missing=missing)


def widen_to_cover(user_message: str, allowed_names: set[str], registered: set[str]) -> set[str]:
    """Add tools needed by the request but not yet in allowed_names."""
    gaps = find_gaps(user_message, allowed_names)
    if not gaps.has_gaps:
        return allowed_names
    needed = set()
    for label, tools, pattern in _SUBTASK_PROBES:
        if label in gaps.missing:
            needed.update(tools)
    return allowed_names | (needed & registered)
