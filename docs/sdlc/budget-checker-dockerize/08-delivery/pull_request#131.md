pull_request — NOT CREATED: forge unidentified, no URL to report

## What blocked this stage

The pull request could not be opened, so there is no pull_request artifact with a URL to register. The reason is stated plainly rather than papered over:

- The previous stage's answer to `pr-create-command` (settled_question#123) was that the forge cannot be identified — `git remote -v` is not available in this process's frames, and no remote URL appears in any object in the chain.
- This frame (assemble-pr-v1) has repository read/write tools only. No shell, no forge CLI (`gh`, `glab`, `tea`), no git state. Opening the pull request through a forge API or MCP server is explicitly disallowed, and a pull request opened any other way cannot be confirmed by the `pr-verify-command` gate — so an unconfirmed claim would fail the gate as surely as a missing pull request does.
- No URL means no valid artifact: the engine confirms a pull request by reading the URL out of the artifact's content and running it through `pr-verify-command`. An artifact that describes a pull request without naming it cannot be confirmed.

## What IS done and ready

- **The PR body is written** to `docs/sdlc/budget-checker-dockerize/pr-body.md` (3,110 bytes), with all four required sections: Summary (dockerize the FastAPI backend and React/Vite frontend behind `docker compose up` — six new packaging files, zero application source changes), Requirements covered (the change brief's three acceptance criteria, criterion IDs inline), Testing (verification_report#76's inspection record: all env-var touchpoints cross-checked; existing pytest and vitest suites discovered but unrun; Docker acceptance criteria unexecuted), and Risk and blast radius (review_report#106's two low-severity findings and the dominant residual risk — no acceptance criterion has ever been executed against a real Docker daemon).
- **The diff is verified in the tree**: `docker-compose.yml`, `backend/Dockerfile`, `backend/.dockerignore`, `frontend/Dockerfile`, `frontend/nginx.conf`, `frontend/.dockerignore` all exist; `search_text` confirms `docker-compose.yml` is present at the root and no other Docker-related files exist outside `docs/sdlc/`.
- **The review gate passed** (settled_question#108, Bohdan: yes) on review_report#106, verdict READY.

## What a person must do to finish

1. Run `git remote -v` to identify the forge and confirm the branch that carries the six files.
2. Confirm the forge CLI is installed and authenticated, and verify its flags against `--help` (the prior stage declined to invent them — the same discipline this stage applies).
3. Run the create command with `--body-file docs/sdlc/budget-checker-dockerize/pr-body.md` and the base branch resolved to the repository default.
4. Re-run this stage so the pull_request artifact can be registered with the real URL on its first line, parented to review_report#106.

## Base branch

Unknown. No default branch is determinable from this frame; the branch strategy answer was "stay" (settled_question#128), so the PR should target whatever the repository's default is, resolved at create time.
