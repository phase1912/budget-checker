<!-- meridian:start -->
# Meridian — Code Intelligence

This project is indexed by Meridian as **budget-checker** (1082 symbols, 1389 relationships, 16 execution flows). Use the Meridian MCP tools to understand code, assess impact, and navigate safely.

> Index stale? Run `node .meridian/run.cjs analyze` from the project root — it auto-selects an available runner. No `.meridian/run.cjs` yet? `npx meridian analyze` (npm 11 crash → `npm i -g meridian`; #1939).

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows. For regression review, compare against the default branch: `detect_changes({scope: "compare", base_ref: "master"})`.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `query({search_query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `context({name: "symbolName"})`.
- For security review, `explain({target: "fileOrSymbol"})` lists taint findings (source→sink flows; needs `analyze --pdg`).

## Never Do

- NEVER edit a function, class, or method without first running `impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit changes without running `detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `meridian://repo/budget-checker/context` | Codebase overview, check index freshness |
| `meridian://repo/budget-checker/clusters` | All functional areas |
| `meridian://repo/budget-checker/processes` | All execution flows |
| `meridian://repo/budget-checker/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/meridian-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/meridian-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/meridian-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/meridian-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/meridian-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/meridian-cli/SKILL.md` |

<!-- meridian:end -->

## Which engine runs the work — read this before starting anything

Two different products are connected here and both are called Meridian. They are
not alternatives; only one of them runs work.

**`meridian-engine` is the engine. Use it.** Its tools are `list_repositories`,
`start_process`, `advance_process`, `process_status`, `list_questions`,
`relay_answer`, `list_artifacts`, `read_artifact`.

**Never use the `sdlc_*` tools** — `sdlc_start`, `sdlc_submit`, `sdlc_answer`,
`sdlc_check`, `sdlc_status`, `sdlc_decide`, `sdlc_add_artifact` and the rest.
They belong to the previous system, they write into `docs/sdlc/proc-N-…/`, and a
process started through them is invisible to the engine. If you find yourself
about to call one, stop and use `meridian-engine` instead.

The `meridian` tools that are **not** `sdlc_*` — `impact`, `query`, `context`,
`detect_changes`, `rename`, `explain` — are code intelligence, not a process
engine. They stay useful and the rules above the marker still apply to them.

### What your role is, and it is different from before

The previous system made *you* the maker: it tracked a process while you wrote
the code. The engine does not work that way. The work happens **inside** it — its
own maker writes the artifacts and edits the tree — and you are an operator:

- start a process, grant it bounded execution, poll where it got to, read what
  it produced;
- **do not write source files yourself** while a process is running. If you are
  creating files, something has gone wrong: check which tools you are calling.
- questions for a person arrive through the client as a form, or wait at the
  engine's desk. Answer them there; do not answer them on somebody's behalf.

If the engine cannot be reached, say so and stop. Falling back to `sdlc_*`, or to
doing the work by hand, is not a fallback — it is a different process with a
different audit trail, and it leaves the engine holding nothing.
