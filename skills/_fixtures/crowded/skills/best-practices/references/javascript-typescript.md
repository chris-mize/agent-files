# JavaScript / TypeScript Quality Checks

High-value defect checks only—not a style guide. These are practitioner checks grounded in common JS/TS runtime and supply-chain failure modes, not a language-specific empirical prevalence study. Prefer project ESLint/TSConfig/runtime conventions when they conflict with generic advice.

Load this for JS/TS implementation or review. Pair with the router’s compact LLM-failure check; the router alone decides when to load the full failure-mode reference.

## 1. Promises and async

- Do not leave floating promises: `void` only when intentionally fire-and-forget **and** errors are handled.
- `async` functions must await or return promises callers can observe.
- Avoid `Promise` constructor antipatterns wrapping already-async APIs.
- In event handlers / React effects, either await with try/catch or attach `.catch`; do not ignore rejections.
- Prefer `AbortSignal` for cancellable fetch/timers when lifecycle exists (components, requests, tests).

**Cheap check:** every promise either awaited, returned, or explicitly handled.

## 2. `fetch` and HTTP

- Check `response.ok` (or status allowlist) before parsing.
- Treat `response.json()` / `text()` as untrusted data; validate shape before use.
- Encode path/query params (`encodeURIComponent`) when interpolating IDs.
- Decide timeout/abort and error mapping; do not surface raw stack noise to users.
- Do not assume JSON; confirm `Content-Type` when the API is loose.

**Amateur-ish:** `return (await fetch(url)).json() as MyType`.

## 3. Types vs runtime

- Avoid `as` / `as unknown as` at trust boundaries unless a validator just proved the shape.
- Prefer narrowing, user-defined guards, schema parsers (project-standard: zod/valibot/etc.), or explicit checks.
- `any` and broad `Record<string, any>` hide bugs—narrow to what callers need.
- Generics that only assert (`getJson<T>(): Promise<T>`) are type theater without parsing.

**Cheap check:** “What runtime evidence makes this type true?”

## 4. Errors

- Do not swallow errors with empty `catch` / `.catch(() => {})` unless a comment states why and the failure is truly ignorable.
- Preserve cause (`{ cause }`) when rethrowing/wrapping.
- Map failure modes to actionable errors (status, code, retryable) at boundaries.
- Log once at the right layer; avoid duplicate noisy logs on every hop.

## 5. Resources and lifecycle

- Close handles: files, DB clients, streams, workers, servers, `AbortController`.
- In `try/finally` or `await using` (when available) for cleanup.
- Clear timers/subscriptions in React effects and tests.
- Avoid leaking listeners across hot reload / repeated calls.

## 6. Mutation and aliasing

- Know whether a helper mutates arrays/objects in place; document or avoid surprise mutation.
- Do not mutate shared config/state aliases across async gaps without coordination.
- Prefer immutable updates at React/state boundaries when the project does.
- StructuredClone / explicit copies when ownership crosses threads or caches.

## 7. Dependencies and APIs

- Verify new packages against the lockfile and registry before adding; registry existence alone is not safety (typosquat / confusion risk). Check publisher provenance, install scripts, transitive changes, and license needs.
- Do not install or recommend unverified package names. Prefer stdlib / existing deps over a new dependency for a few lines.
- Confirm import paths and named exports against installed versions (Node ESM/CJS, subpath exports).
- Do not invent APIs from similar libraries (`fs-extra` vs `node:fs`, Lodash vs native).

## 8. Runtime boundaries (browser / Node / edge)

- Do not use Node builtins (`fs`, `path`, `process`) in browser bundles without a clear bundler polyfill policy.
- Do not use browser-only APIs (`window`, `document`, `localStorage`) in Node/edge without guards.
- Edge/serverless: watch cold start, request limits, missing long-lived state, and crypto/subtle availability.
- Distinguish `node:` imports vs bare package names per project convention.

## 9. Concurrency and time

- Cache/singleton helpers need stampede / single-flight awareness when concurrent callers matter.
- Do not use `Date.now()` alone for security tokens; use crypto-strength randomness where required.
- Tests depending on real time should fake clocks or allow tolerances.

## 10. Test oracles (JS/TS)

- A green bar is not proof unless the command/output is shown and the suite actually ran.
- Mocks may isolate externals, but at least one contract/integration check should exercise the real boundary under change.
- Suites that only assert mock call graphs or mirror the implementation are weak oracles.

## 11. Security sinks (escalate when material)

- Parameterize SQL; encode HTML; avoid `child_process` with concatenated user input; sanitize paths.
- Authn ≠ authz; check authorization at the action boundary in application code—not only in prompt text.
- Secrets stay in env/secret managers—not source, logs, or client bundles.
- For substantive security work, follow `security-best-practices` / `security-threat-model` rather than expanding this list.

Published LLM bug taxonomies are mostly Python/benchmark studies; still apply these JS/TS checks from local runtime and supply-chain risk.

## Minimal review output

When issues exist, prefer:

```markdown
- P1 `file:line` Unvalidated fetch JSON typed as `User`. Parse/guard before use.
- P2 `file:line` Floating promise in `onClick`. Await and surface failure.
Residual: no integration test against real 401/500 responses.
```

Omit empty sections. Fix material issues when authoring; report-only when reviewing.
