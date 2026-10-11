# Research ledger

Verification date: 2026-08-10. A row marked `verified` has a canonical source and a claim bounded by that source. A `provisional` row is context only and must not authorize a pilot or implementation decision.

## PairCoder — verified

- **Source:** Huan Zhang, Wei Cheng, Yuhan Wu, and Wei Hu, “A Pair Programming Framework for Code Generation via Multi-Plan Exploration and Feedback-Driven Refinement,” ASE 2024; canonical source: https://arxiv.org/html/2409.05001
- **Supported claim:** PairCoder separates high-level navigation/planning from implementation and uses execution feedback, iterative refinement, and multiple plans.
- **Limitation:** This is a code-generation framework evaluated on its own benchmarks; it does not establish that a portable prompt skill will reproduce its gains or reduce cost.
- **Use here:** Supports separating planning from implementation when ambiguity justifies the added role.

## S2R — verified

- **Source:** Ruotian Ma et al., “S2R: Teaching LLMs to Self-verify and Self-correct via Reinforcement Learning,” ACL 2025, pp. 22632–22654; canonical source: https://aclanthology.org/2025.acl-long.1104/
- **Supported claim:** Training a model to self-verify and self-correct can improve reasoning performance and adaptive test-time behavior.
- **Limitation:** The strongest results use supervised fine-tuning and reinforcement learning. This skill borrows the inference pattern and makes no training-equivalence claim.
- **Use here:** Justifies explicit verification and correction as a hypothesis to test, not as a guaranteed prompt-only improvement.

## Minimal generator–critic MAS — verified

- **Source:** Yuru Wang et al., “Scalability of LLM-Based Multi-Agent Systems for Scientific Code Generation: A Preliminary Study,” MathNLP 2025, pp. 50–61; canonical source: https://aclanthology.org/2025.mathnlp-main.4/
- **Supported claim:** A simple iterative critic-in-the-loop framework performed strongly under matched compute, while more complex multi-agent structures added little.
- **Limitation:** It is a preliminary study in scientific code generation with its own models and budget; it does not prove the selected profiles will win.
- **Use here:** Supports a generator–critic fast path and a bounded, evidence-driven planner.

## COPE — verified

- **Source:** Byeongchan Lee et al., “Efficient LLM Collaboration via Planning,” arXiv:2506.11578 (2025); canonical source: https://arxiv.org/abs/2506.11578
- **Supported claim:** COPE uses planning as a lightweight intermediate for test-time collaboration between smaller and larger models and reports cost/performance improvements on its benchmarks.
- **Limitation:** Results depend on its trained/evaluated models, benchmarks, and pricing assumptions; they are not a Cursor/Codex cost guarantee.
- **Use here:** Supports compact contracts and conditional strategic-model involvement.

## Three Roles, One Model — verified

- **Source:** S. Aaron McClendon, Jorge Gallego-Feliciano, Stavros Zervoudakis, and Antonios Saravanos, “Three Roles, One Model: Role Orchestration at Inference Time to Close the Performance Gap Between Small and Large Agents,” arXiv:2604.11465 (2026); canonical source: https://arxiv.org/abs/2604.11465
- **Supported claim:** Structured summarization, main-agent, and isolated correction roles can improve a frozen small model on an agent benchmark without additional training.
- **Limitation:** The study uses Qwen3-8B and AppWorld; role prompting and benchmark transfer remain open questions.
- **Use here:** Supports bounded trajectory digests and a fresh, context-isolated critic.

## Agentic Systems as Boosting Weak Reasoning Models — verified

- **Source:** Varun Sunkaraneni, Pierfrancesco Beneventano, Riccardo Neumarker, Tomaso Poggio, and Tomer Galanti, “Agentic Systems as Boosting Weak Reasoning Models,” arXiv:2605.14163 (2026); canonical source: https://arxiv.org/html/2605.14163
- **Supported claim:** Verifier-backed proposal/critic systems can recover more correct solutions from weak-model proposal pools, while proposal coverage and critic soundness remain distinct bottlenecks.
- **Limitation:** Results are on verifier-backed SWE-bench tasks and use a proposal committee; a single generator–critic loop may retain shared blind spots.
- **Use here:** Requires tracking proposal coverage and critic soundness separately and prevents overclaiming that critique fixes generation gaps.

## RecursiveMAS — verified, not a v1 mechanism

- **Source:** Jiaru Zou et al., “Recursive Multi-Agent Systems,” arXiv:2604.25917 (2026); canonical source: https://arxiv.org/html/2604.25917
- **Supported claim:** RecursiveMAS transfers latent states between trained agent components and reports efficiency/performance gains in its evaluated setting.
- **Limitation:** It requires model-internal latent-state access and training. A Cursor/Codex Skill cannot implement this through ordinary text handoffs.
- **Use here:** Future research direction only; the v1 package uses portable textual/structured handoffs.

## Two Minute Papers video — provisional context

- **Source:** Two Minute Papers, “Scientists Found A Better Language For AI Agents,” https://www.youtube.com/watch?v=dUmT0OIGoqE; oEmbed verifies the title and channel, and the watch transcript matches the RecursiveMAS topic.
- **Supported claim:** The video presents latent-state cross-agent communication, reported efficiency gains, and limitations around model scale and optimal latent thought length.
- **Limitation/status:** The canonical watch/oEmbed retrieval used during implementation did not expose the upload date. Keep this row provisional and do not use it as a gate-supporting citation until the date is independently verified.

## Host documentation — verified

- **Cursor Skills:** https://cursor.com/docs/skills documents user-level skill discovery, explicit `/skill-name` invocation, `disable-model-invocation: true`, references, scripts, and user-level `$CURSOR_HOME/skills/`.
- **Cursor Subagents:** https://cursor.com/docs/subagents.md documents custom user-level agents under `$CURSOR_HOME/agents/`.
- **Codex skill metadata:** host-local skill-creator documentation at `$CODEX_HOME/skills/.system/skill-creator/references/openai_yaml.md` documents `agents/openai.yaml` and `policy.allow_implicit_invocation: false`.
- **Host capability observations:** local catalogs and role dispatch are runtime inputs. They may expose only a subset of requested profiles and do not prove observed identity, effort, speed tier, usage, cost, or fallback state. The runtime capability probe must verify exact availability before any named arm.
- **Use here:** These are host-format facts; live role dispatch, complete model catalog, controller identity, and usage receipts still require runtime capability checks.
