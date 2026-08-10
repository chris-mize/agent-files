# Compatibility and host evidence

This file records tested installation surfaces, host versions, commands, evidence, and gaps. Static validation is not host parity. A workflow is called `supported` only when discovery, invocation, isolation, and required web capabilities pass on that host.

## Release-gate vocabulary

- `supported`: all required checks passed for the named surface and version.
- `partial`: the skill is usable, but a required surface or capability is restricted and the limitation is explicit.
- `blocked`: a required capability is absent or a native control cannot be verified.
- `untested`: the package may be structurally valid, but no runtime evidence has been recorded.

`auto-review` additionally requires explicit-only native behavior and one genuinely independent reviewer. `deep-research` additionally requires fresh isolated workers with representative official, user-experience, and expert web access.

## Release-candidate identity and command ledger

- Candidate bundle: `cmize-skills` `0.1.0`.
- Source identity: canonical `src/` content fingerprint `404867decdfe3d8305206520560052f91a7f53a7e41a3ab2c40db7e53f9c16fb`; the release commit is recorded by the `v0.1.0` tag after this candidate is committed.
- Static gates: `python3 scripts/validate.py` passed; `python3 -m unittest discover -s tests -p 'test_*.py'` passed with 11 tests.
- Codex plugin catalog: `CODEX_HOME=/tmp/cmize-codex-market-replay-2/.codex codex plugin marketplace add "$PWD" --json` followed by `CODEX_HOME=/tmp/cmize-codex-market-replay-2/.codex codex plugin add cmize-skills@cmize-skills --json` passed from the repository root; installed version was `0.1.0`.
- Codex explicit skills: an isolated project `.agents/skills` install explicitly invoked `adversarial-review` and `best-practices`; both reported findings without edits.
- Codex explicit auto-review: one separate reviewer was launched and returned `insufficient evidence` for the intentionally underspecified smoke plan; no files were edited. Prompts explicitly using other skills did not invoke auto-review.
- Codex deep-research: canonical Light preflight and three research workers passed, but the required critique stage hit the platform thread limit twice; the run is recorded as terminal coverage failure.
- Cursor explicit skills: `cursor agent --print --mode ask --plugin-dir "$PWD/src"` explicitly invoked adversarial-review and best-practices without edits.
- Cursor explicit auto-review: one separate subagent was launched and returned `not ready`; no files were edited. Prompts explicitly using other skills did not invoke auto-review.
- Cursor deep-research: its Light preflight stopped with a capability gap because official access was blocked; no research workers were launched.
- Claude Code: `command -v claude` reported unavailable, so no Claude runtime command or invocation evidence exists.

### Exact replay commands

Run these from the repository root. The recorded results were bound to source fingerprint `404867decdfe3d8305206520560052f91a7f53a7e41a3ab2c40db7e53f9c16fb`; the temporary destinations were clean before each copy.

```bash
python3 scripts/validate.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/install.py --target claude --destination /tmp/cmize-skills-clean-claude --dry-run
python3 scripts/install.py --target claude --destination /tmp/cmize-skills-clean-claude
python3 scripts/install.py --target codex --destination /tmp/cmize-codex-project-replay/.agents/skills --dry-run
python3 scripts/install.py --target codex --destination /tmp/cmize-codex-project-replay/.agents/skills
python3 scripts/install.py --target cursor --destination /tmp/cmize-skills-clean-cursor --dry-run
python3 scripts/install.py --target cursor --destination /tmp/cmize-skills-clean-cursor
```

Results: validator passed; 11 unit tests passed; all three direct dry-run/copy pairs passed. The isolated Codex home used below was preconfigured for the test account outside this repository; no credentials are stored here.

```bash
python3 scripts/install.py --target codex --destination /tmp/cmize-codex-project/.agents/skills
```

Result: the canonical four-skill tree was copied into the Codex project discovery directory used by the explicit skill smoke test.

```bash
CODEX_HOME=/tmp/cmize-codex-market-replay-2/.codex \
  codex plugin marketplace add "$PWD" --json
CODEX_HOME=/tmp/cmize-codex-market-replay-2/.codex \
  codex plugin add cmize-skills@cmize-skills --json
```

Result: the marketplace was added and `cmize-skills@cmize-skills` installed as version `0.1.0` in the isolated cache.

```bash
CODEX_HOME=/tmp/cmize-codex-isolated/.codex \
  codex exec --ignore-user-config --sandbox read-only --ephemeral \
  --skip-git-repo-check -C /tmp/cmize-codex-project \
  'Use the canonical adversarial-review skill from the project .agents/skills directory explicitly on this tiny plan: "Add one validation check without adding a dependency." Do not edit files or invoke auto-review. Report the discovered skill path and one finding.'
```

Result: `/tmp/cmize-codex-project/.agents/skills/adversarial-review/SKILL.md` was discovered and the plan received an `insufficient evidence` finding; no files were edited.

```bash
CODEX_HOME=/tmp/cmize-codex-isolated/.codex \
  codex exec --ignore-user-config --sandbox read-only --ephemeral \
  --skip-git-repo-check -C /tmp/cmize-codex-isolated \
  'Use the canonical best-practices skill explicitly on this small code task: "Add a validation check without a new dependency." Do not edit files. Report the skill path, the smallest recommended approach, and one verification command.'
```

Result: `/tmp/cmize-codex-isolated/.codex/skills/best-practices/SKILL.md` was used; the agent recommended an existing input-boundary guard and no new dependency; no files were edited.

```bash
CODEX_HOME=/tmp/cmize-codex-isolated/.codex \
  codex exec --ignore-user-config --sandbox read-only --ephemeral \
  --skip-git-repo-check -C /tmp/cmize-codex-isolated \
  'Use $auto-review explicitly for a single-pass, report-only review of this tiny plan: "Add one validation check without adding a dependency." Read the Codex platform adapter, launch one genuinely independent reviewer if available, and report the verdict and one finding. Do not edit files. This is an explicit invocation; do not invoke auto-review implicitly.'
```

Result: one independent reviewer launched after one host thread retry; verdict `insufficient evidence`; no files were edited.

```bash
cursor agent --print --output-format text --mode ask --trust \
  --workspace /tmp/cmize-skills-clean-cursor --plugin-dir "$PWD/src" \
  'After loading the local cmize-skills plugin, use adversarial-review explicitly on this tiny plan: "Add one validation check without adding a dependency." Do not edit files or invoke auto-review. Report the discovered skill and one finding.'
```

Result: `adversarial-review` was discovered; verdict `insufficient evidence`; no files were edited.

```bash
cursor agent --print --output-format text --mode ask --trust \
  --workspace /tmp/cmize-skills-clean-cursor --plugin-dir "$PWD/src" \
  'Use the cmize-skills best-practices skill explicitly on this small code task: "Add a validation check without a new dependency." Do not edit files. Report the skill discovered, the smallest recommended approach, and one verification command.'
```

Result: `best-practices` was discovered; the agent recommended an inline guard and existing project test command; no files were edited.

```bash
cursor agent --print --output-format text --mode ask --trust \
  --workspace /tmp/cmize-skills-clean-cursor --plugin-dir "$PWD/src" \
  '/auto-review single pass report-only: review this tiny plan: "Add one validation check without adding a dependency." Do not edit files. Use the Cursor platform adapter, launch one genuinely independent reviewer if available, and report the verdict and one finding. This is an explicit invocation; do not invoke auto-review implicitly.'
```

Result: one independent Cursor subagent launched; verdict `not ready`; no files were edited.

### Deep-research replay

```bash
CODEX_HOME=/tmp/cmize-codex-isolated/.codex \
  codex exec --ignore-user-config --model gpt-5.6-luna \
  --sandbox read-only --ephemeral --skip-git-repo-check \
  -C /tmp/cmize-codex-isolated \
  'Use only the canonical deep-research skill installed at /tmp/cmize-codex-isolated/.codex/skills/deep-research/SKILL.md. Run a Light research smoke test on: "What does the Agent Skills specification require for a portable SKILL.md?" Perform the non-interactive capability and concurrency preflight first. If fresh isolated web-capable workers with representative official, public-user, and expert access cannot be verified, stop and report that gap. Do not edit files. Keep the final report concise with worker counts, lane coverage, isolation/web evidence, and status.'
```

Result: preflight and 3/3 research workers passed across all three lanes, but the required critique stage failed after two thread-limit attempts; status `terminal coverage failure`, no files edited.

```bash
cursor agent --print --output-format text --mode ask --trust \
  --workspace /tmp/cmize-skills-clean-cursor --plugin-dir "$PWD/src" \
  'Use the cmize-skills deep-research skill explicitly for a Light research smoke test on: "What does the Agent Skills specification require for a portable SKILL.md?" Perform the non-interactive capability and concurrency preflight first. If this Cursor session cannot verify genuinely isolated, web-capable workers with representative official, public-user, and expert access, stop and report that capability gap rather than substituting same-context prompts. Do not edit files. Keep the final report concise but include attempted/completed/failed worker counts, lane coverage, isolation/web evidence, and status.'
```

Result: 3 probes ran, 2 completed and 1 failed; official access was blocked, so no research workers launched and status `blocked — capability gap`.

## Claude Code

Installation surfaces:

- marketplace: root `.claude-plugin/marketplace.json` points to `./src`;
- plugin root: `src/.claude-plugin/plugin.json`;
- direct personal skills: `~/.claude/skills`;
- direct project skills: `<project>/.claude/skills`.

Commands:

```text
/plugin marketplace add https://github.com/chris-mize/portable-skills.git
/plugin install cmize-skills@cmize-skills
/cmize-skills:adversarial-review
/cmize-skills:auto-review
/cmize-skills:deep-research
/cmize-skills:best-practices
```

Evidence record:

- Version: `claude` was not installed on the test machine (`command -v claude` returned unavailable).
- Discovery: not testable without Claude Code.
- Direct-copy installer: dry run and copy passed into `/private/tmp/cmize-skills-clean-claude`.
- `auto-review` manual-only control: `disable-model-invocation: true` is present; native runtime behavior remains a release-gate check.
- Independent reviewer: not testable.
- `deep-research` web/isolation: not testable.
- Result: `blocked` for host support; package-shape support is covered by static validation only.

## Codex

Installation surfaces:

- marketplace: root `.agents/plugins/marketplace.json` points to `./src`;
- plugin root: `src/.codex-plugin/plugin.json`;
- direct personal skills: `~/.agents/skills`;
- legacy personal skills: `~/.codex/skills`;
- direct project skills: `<project>/.agents/skills` (or the legacy `.codex/skills`).

Commands:

```bash
codex plugin marketplace add https://github.com/chris-mize/portable-skills.git
codex plugin add cmize-skills@cmize-skills
```

Evidence record:

- Version: `codex-cli 0.145.0`.
- Discovery: passed from an isolated Codex home after direct copy; the agent found all four canonical skills.
- Direct-copy installer: dry run and copy passed into `/private/tmp/cmize-codex-project/.agents/skills`; a second legacy-surface copy into `.codex/skills` also passed.
- Marketplace: local Codex marketplace add and `codex plugin add cmize-skills@cmize-skills --json` passed; installed version `0.1.0`.
- `auto-review` manual-only control: `src/skills/auto-review/agents/openai.yaml` declares `allow_implicit_invocation: false`; native runtime behavior remains a release-gate check.
- Negative smoke path: explicit adversarial-review and best-practices prompts reported that auto-review was not invoked; this is behavioral evidence, not a security guarantee.
- Independent reviewer: explicit single-pass smoke test launched one separate worker and returned `not ready`; no files were edited.
- `deep-research` web/isolation: canonical Light run preflight passed with 3/3 distinct workers and all three lanes; 3/3 research workers completed, but the required critique failed after two thread-limit launch attempts. The run is `terminal coverage failure`, so deep-research is not claimed fully supported.
- Residual host issue: Codex emitted a model-cache schema warning in one run and later a model-refresh timeout; the successful skill and marketplace gates were unaffected.
- Result: `partial`; adversarial-review, auto-review, and best-practices passed explicit smoke tests, while deep-research remains blocked by its required critique-stage capability.

## Cursor

Installation surfaces:

- marketplace: root `.cursor-plugin/marketplace.json` points to `./src`;
- plugin root: `src/.cursor-plugin/plugin.json`;
- direct personal skills: `~/.cursor/skills`;
- direct project skills: `<project>/.cursor/skills`.

Commands and UI:

```bash
cursor agent plugin marketplace add https://github.com/chris-mize/portable-skills.git
```

Then install `cmize-skills` from Cursor's Plugins/marketplaces UI:

```text
/adversarial-review
/auto-review
/deep-research
/best-practices
```

Evidence record:

- Version: Cursor `3.15.6`, build `a1f686545fd0ce8917bbd2449f733551a9bce420`, `arm64`.
- Discovery: passed with `cursor agent --plugin-dir .../src`; the agent found `cmize-skills` and the requested skills.
- Direct-copy installer: dry run and copy passed into `/private/tmp/cmize-skills-clean-cursor`.
- `auto-review` manual-only control: `disable-model-invocation: true` is present; native runtime behavior remains a release-gate check.
- Negative smoke path: explicit adversarial-review and best-practices prompts reported that auto-review was not invoked; this is behavioral evidence, not a security guarantee.
- Independent reviewer: explicit single-pass smoke test launched a separate Cursor subagent and returned `insufficient evidence`; no files were edited.
- `deep-research` web/isolation: Light preflight launched 3 probes, 2 completed and 1 failed; no research workers launched because official access was blocked and public-user access was restricted. The skill correctly returned `blocked — capability gap`.
- Result: `partial`; adversarial-review, auto-review, and best-practices passed explicit smoke tests, while deep-research is correctly blocked for this environment.

## Direct-install evidence

The repository validator and installer unit tests are host-independent. They prove package shape, link integrity, refusal to overwrite by default, selected-skill behavior, dry-run behavior, replacement, and symlink handling. They do not prove that a host discovers or invokes a copied skill.

The clean-install gate must record:

- exact host version and installation surface;
- source revision and destination;
- discovery output;
- one explicit invocation of each skill;
- manual-only behavior for `auto-review`;
- independent-worker and web evidence where required;
- blocked services, missing capabilities, and residual risk.
