# Supervise the reviewer

The owner remains responsible until each child finishes or is deliberately stopped. Use native process tools; do not detach a call and hope to collect it later.

```text
launch → retain handle → read live events → inspect progress → wait again
                              │                    │
                         blocked/failed        completed + exited
                              ↓                    ↓
                       diagnose or cancel     validate findings
```

## Keep control

Before launch, choose a managed tool that can start, poll/read, and stop the process. A short tool wait must return a handle, not kill the child. Give each child its own private temporary directory. Save its handle, model, artifact version, event/stderr paths, and provider session/thread ID there. They identify different things: a provider ID does not control the local process.

- **Codex owner:** use `exec_command` with `tty: true` and a short `yield_time_ms`; poll the returned `session_id` with `write_stdin`. The PTY keeps Ctrl-C cancellation available. Keep the outer orchestration alive until it has returned the process handle.
- **Cursor owner:** inspect the available Shell tools. The installed CLI supports background Shell jobs, a returned shell ID and terminal output file, and `AwaitShell(shell_id, block_until_ms, pattern)`. Read its startup output immediately, then poll the same job. A shell-start success is not its eventual exit status. App tool names can differ; use their actual schema.

Read complete JSON lines incrementally; retain an unfinished line for the next read. Keep a log offset and last received event/meaningful activity. If native output is truncated, recover from the raw event log, not a guessed summary. The startup `REVIEW_DIR` line and Cursor terminal headers/footers are process metadata, not JSON events; parse the raw event file. Keep logs per child; avoid dumping tool payloads or token streams into chat.

## Judge progress

| Observation | Owner action |
|---|---|
| New public progress or tool transitions matching the brief | Continue; summarize the current phase and coverage. |
| Streaming text/model activity without a new checkpoint | Active, but useful progress is unproven. Reassess scope and repetition; do not equate token output with advancing the review. |
| Process alive, no new events | Quiet/unknown. Inspect pending tools, stderr, retries, and elapsed time against the task and model effort. Liveness does not prove remote progress. |
| Permission/auth/quota error, disconnected stream, repeated failing step | Diagnose the specific blocker. Do not start a duplicate or count it as success. |
| Terminal event | Read the result and confirm process exit; one can arrive before the other. |

Poll in short slices that let the owner inspect and update Chris within a minute. Wait intervals are observation windows, not total-runtime limits. Silent reasoning can be legitimate; checkpoints in the brief help but are not guaranteed heartbeats.

Do not impose a default lifetime timeout. Honor an explicit user deadline/budget and disclose unavoidable host limits. For prolonged quiet or activity without advancing coverage, report the last observed checkpoint and uncertainty, then choose continued observation, diagnosis, or cancellation based on evidence. Repeated loops, out-of-scope work, or a known blocker justify intervention even while output continues. Do not silently kill at a fixed age or poll forever without reassessment.

## Stop or follow up

In Codex, cancel with `write_stdin(session_id, chars: "\u0003")` on the retained PTY, then poll that session until it reports exit. Check that the launch's descendants are gone; stopping the shell alone is insufficient.

In Cursor, use the PID from the job metadata: inspect `ps -p "$review_pid" -o pid,ppid,pgid,lstart,command` and list its process-group members. Only if the group belongs exclusively to this job, use `kill -TERM -- "-$review_pgid"`. If it is shared, stop verified job descendants and parent individually; never kill an unrelated/shared group or by process name. Use this verified-PID fallback for surviving descendants in either harness. Poll the native handle to confirm termination, verify child cleanup, preserve logs, and mark cancelled/incomplete. A signal can prevent the exit file being written; use native termination status. An expired tool wait does not imply cancellation.

These one-shot CLIs support monitoring and cancellation, not live chat through stdin. Send a clarification as a separate reviewer follow-up after completion/cancellation, with explicit prior findings and scope. Never mix in the author's conversation. Richer live control needs a client for [Codex app-server](https://developers.openai.com/codex/app-server) (`turn/steer`, `turn/interrupt`) or [Cursor ACP](https://cursor.com/docs/cli/acp) (`session/update`, `session/cancel`); do not invent those controls on `exec`/print mode.
