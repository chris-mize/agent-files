# Instruction density

Always-on prompts should be the smallest high-signal set (Anthropic, effective context engineering, 2025). Filling the window is quality loss, not thoroughness.

Always-on size: Claude docs target under 200 lines per memory file. HumanLayer published root files under 60 lines. Personal `AGENTS.md` is voice plus landmines, not a repository manual.

ETH Zurich arXiv:2602.11988: developer-written AGENTS.md was about +4% issue-resolve versus omit; LLM-generated context can hurt; cost rose more than 20%. Prefer delete or move to `references/` over generated paragraphs.

Addy Osmani: `/init` architecture tours hurt. Do not generate overviews.

More instructions produce more omissions (IFScale arXiv:2507.11538, AGENTIF arXiv:2505.16944, Lost in the Middle arXiv:2307.03172).

Skills are optional. Vercel (January 2026): skills were never invoked in 56% of one eval; an always-on index beat skills on a narrow docs task. Do not assume a skill fires. When-to-use lives in YAML `description` only.

`AGENTS.md` points at skills by **name**. Do not paste their procedures.

Progressive disclosure: metadata always; `SKILL.md` on trigger; references only when the body says to read them. Default `SKILL.md` body soft cap is 80 lines.

Must-happen belongs in hooks and CI, not more prose.

Add a line only after a repeated miss on the frozen suite. Delete it when the miss is gone.
