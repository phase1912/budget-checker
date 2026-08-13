<!-- meridian:start -->
# Meridian — Code Intelligence

This project is indexed by Meridian as **budget-checker** (866 symbols, 1173 relationships, 16 execution flows). Use the Meridian MCP tools to understand code, assess impact, and navigate safely.

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

## SDLC Process Rules

- **Meridian SDLC overrides built-in planning:** When using Meridian SDLC, it is the MANDATORY single source of truth. DO NOT use your built-in planning mode or create `implementation_plan.md` artifacts.
- **No premature coding:** Do NOT edit any source code files until the Meridian SDLC engine explicitly advances to the `implementation` stage. Your first tool call should be to start the process.
- **MUST NOT automatically answer inquiries:** When executing the SDLC process, DO NOT automatically call `sdlc_answer` using assumptions from the initial prompt. You must show the user exactly what is being asked.
- **MUST pause and confirm:** NEVER batch multiple `sdlc_submit` calls in a single turn. After a stage is closed by the engine, you MUST stop execution, present the generated artifact link to the user, and wait for explicit confirmation ("Proceed to next stage?") before continuing. Do not silently power through stages.
- **For Antigravity:** You MUST use your native `ask_question` tool to present the SDLC questions as an interactive form. You may recommend an answer by prefixing the option with "(Recommended)", but the user must submit the form.
- **Create Artifacts Per Stage:** You MUST write the physical Markdown artifact files to disk (e.g., in `docs/sdlc/{slug}/`) at each corresponding stage and register them via `sdlc_add_artifact` BEFORE calling `sdlc_submit`. Do NOT skip creating documents or attach unrelated files just to bypass the gate.
- **No String-Only Bypasses:** Answers to SDLC questions must reference the physical files you created in `docs/sdlc/`.
- **Strict Git Hygiene:** When committing or pushing, you MUST only stage the exact files you created or modified for the current step (e.g., `git add path/to/specific_file`). NEVER use `git commit -a`, `git add .`, or push files that you did not change.

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

## SDLC human decisions — no terminal commands

`sdlc_decide` resolves an SDLC escalation and is human-facing: the agent must not decide it unilaterally. That does **not** mean handing the user a CLI command to run themselves.

- Ask the person directly in the conversation — plain text or a short yes/no — and wait for a genuine answer.
- Once they've answered, call `sdlc_decide` yourself, with their answer as `rationale`.
- Never tell the user to open a terminal or run `meridian sdlc decide ...` (or `node .meridian/run.cjs sdlc decide ...`) themselves. The audit trail is the `rationale` you pass, not who typed the call.
