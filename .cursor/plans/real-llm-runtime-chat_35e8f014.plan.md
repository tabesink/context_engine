---
name: real-llm-runtime-chat
overview: Replace placeholder echo chat with real LLM-backed runtime execution via AgentSession, enforcing explicit key config and keeping the provider interface Bedrock-ready.
todos:
  - id: replace-echo-provider
    content: Implement LiteLLM-backed LLMProvider with explicit api_key_env enforcement and tool-call parsing
    status: completed
  - id: build-runtime-run-executor
    content: Add backend runtime execution path that uses AgentSession for run completion and persistence
    status: completed
  - id: refactor-stream-events
    content: Replace placeholder stream delta generation with real runtime output streaming
    status: completed
  - id: add-hardfail-and-regression-tests
    content: Add tests for missing-key hard-fail and real chat/stream persistence behavior
    status: completed
  - id: update-config-and-docs
    content: Document explicit llm.api_key_env requirements and first-provider setup in workspace/deploy docs
    status: completed
isProject: false
---

# Wire Real LLM Through Runtime Worker

## Confirmed decisions
- Provider-first path: LiteLLM + OpenAI now, with interface kept Bedrock-ready.
- Runtime architecture path: implement proper run execution through runtime session flow, not a direct endpoint-only patch.
- Key policy: hard-fail in non-test runtime when key config is missing/invalid.
- Key contract: require explicit `llm.api_key_env` in workspace config (no implicit default env var).

## Current gap
- Backend send/stream path does not call runtime LLM execution; it streams placeholder assistant content from persisted rows in [`d:\Projects\clawagent\src\backend\app.py`](d:\Projects\clawagent\src\backend\app.py) and [`d:\Projects\clawagent\src\backend\persistence\repositories.py`](d:\Projects\clawagent\src\backend\persistence\repositories.py).
- `LLMProvider` is a pure echo placeholder in [`d:\Projects\clawagent\src\agent\provider\llm.py`](d:\Projects\clawagent\src\agent\provider\llm.py).

## Implementation plan
- Implement real provider adapter in [`d:\Projects\clawagent\src\agent\provider\llm.py`](d:\Projects\clawagent\src\agent\provider\llm.py):
  - Replace echo behavior with LiteLLM chat-completion calls.
  - Parse assistant content + tool calls into existing `LLMToolCall` format.
  - Enforce explicit `llm.api_key_env` lookup and raise typed config/provider errors when missing.
  - Keep provider/model mapping abstraction generic enough for future Bedrock model routing.
- Add runtime run executor in backend service layer (new module under [`d:\Projects\clawagent\src\backend\`](d:\Projects\clawagent\src\backend\)):
  - Load agent definition for run’s `agent_id`.
  - Rehydrate conversation history into runtime message format.
  - Execute `AgentSession.chat()` and persist assistant terminal output back to canonical messages/runs.
  - Preserve ownership, lock, idempotency, and run status semantics.
- Refactor stream flow in [`d:\Projects\clawagent\src\backend\app.py`](d:\Projects\clawagent\src\backend\app.py):
  - Stream actual generated deltas/events from runtime execution instead of splitting pre-filled placeholder text.
  - Keep existing typed event contract (`run.started`, `message.delta`, `message.completed`, `run.completed`, failure/cancel paths).
- Add strict config validation:
  - Extend checks in [`d:\Projects\clawagent\src\agent\utils\config.py`](d:\Projects\clawagent\src\agent\utils\config.py) so non-test startup fails if `llm.api_key_env` is unset/empty for real-provider mode.
  - Update workspace example docs in [`d:\Projects\clawagent\default_workspace\config.example.yaml`](d:\Projects\clawagent\default_workspace\config.example.yaml) and CLI/deploy docs in [`d:\Projects\clawagent\scripts\README.md`](d:\Projects\clawagent\scripts\README.md).

## Tests and verification
- Add/adjust provider and runtime integration tests in [`d:\Projects\clawagent\tests\`](d:\Projects\clawagent\tests\):
  - Missing `llm.api_key_env` causes typed hard failure in non-test runtime.
  - Chat flow produces non-echo assistant output when provider is stubbed/mocked.
  - Streaming emits expected event sequence while preserving run/message persistence invariants.
- Manual CLI verification:
  - `login -> chat` path returns model-generated responses.
  - Conversation history and run statuses remain consistent.
  - Failure mode for missing key/config is explicit and actionable (not generic 500).

## Risks to control
- Do not regress tool safety/approval flow while replacing placeholder stream generation.
- Keep run state transitions and cancellation semantics unchanged from current API contract.
- Keep Bedrock future path in interface only (no Bedrock execution in this phase).