# Codex workspace chats and logs backup

Snapshot time: 2026-08-26T10:54:30Z

Workspace: `/home/lutein/Projects/class-gedf-test-04`

## Contents

- `chats/`: 14 original Codex rollout JSONL files whose recorded working directory is this workspace or a child directory.
- `metadata/threads.jsonl`: one JSON object per exported conversation with identifying and indexing metadata.
- `logs/codex-app/logs.jsonl`: 3,735 Codex application-log records linked to the exported conversation IDs.
- `logs/workspace/`: seven `.log`/`.out` files found inside the workspace, preserving their relative paths.
- `SHA256SUMS`: SHA-256 checksums for every other file in this backup.

This is a non-destructive point-in-time export. It intentionally excludes Codex credentials, configuration, caches, databases, attachments not embedded in rollouts, and records associated with other workspaces. The JSONL files may contain prompts, responses, tool calls, command output, paths, and other potentially sensitive workspace data; store the archive accordingly.

Verify after extracting:

```bash
sha256sum -c SHA256SUMS
```
