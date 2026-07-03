# Note 2 — Model & provider (`pi-ai`, DEPENDENCY, stay agnostic)

Provider-agnostic `Model` abstraction that `pi-agent-core` builds on. Lena takes
a `Model`; **the provider is always config/env, never hardcoded** (no Foundry/
OpenAI/Anthropic assumption anywhere in Lena).

Reference files (read-only):
- `packages/ai/README.md` — full API (~1391 lines). Key sections below.
- `packages/ai/src/index.ts` — exports
- `packages/ai/src/models.ts`, `models.generated.ts` — model catalog
- `packages/ai/src/types.ts` — `Model`, `Message`, `Context`, `Usage`, `StreamOptions`
- `packages/ai/src/env-api-keys.ts` — reading provider creds from env
- `packages/ai/src/providers/` — per-provider API implementations

## Core idea

A **provider** offers **models** through an **API** implementation. The registry
maps provider → API (e.g. Anthropic → `anthropic-messages`, OpenAI →
`openai-responses`, xAI/Groq/Cerebras/… → `openai-completions`).

```ts
import { getModel, getModels, getProviders } from "@earendil-works/pi-ai";

const providers = getProviders();          // ['openai','anthropic','google',...]
const model = getModel(provider, modelId); // BOTH come from Lena config/env
```

Built-in APIs (README "APIs, Models, and Providers"): `anthropic-messages`,
`google-generative-ai`, `google-vertex`, `mistral-conversations`,
`openai-completions`, `openai-responses`, `openai-codex-responses`,
`azure-openai-responses`, `bedrock-converse-stream`.

## Streaming primitives

- `streamSimple` / `completeSimple` — unified provider-agnostic interface (README
  "Unified Interface"). Prefer these; thinking/reasoning is normalized.
- `stream` / `complete` — provider-specific options when needed.
- `StopReason`: `stop | length | toolUse | error | aborted` (README "Stop Reasons").

## Credentials

- `findEnvKeys(provider)` / `getEnvApiKey(provider)` read known env vars
  (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, Vertex ADC, Bedrock, `github-copilot`, …).
- For expiring/OAuth tokens use `Agent`'s `getApiKey: async (provider) => ...`
  (dynamic resolution) rather than a static key.
- OAuth providers + Vertex AI covered in README "OAuth Providers".

## Testing without a real provider

`registerFauxProvider()` (README "Faux provider for tests") — in-memory scripted
provider. Use `fauxAssistantMessage`, `fauxText`, `fauxThinking`, `fauxToolCall`
to script deterministic flows. Good for Lena's `src/evaluation/*.yaml` replays
and unit tests — no network, no keys.

## Lena mapping

- Config selects `{ provider, modelId }`; Lena calls `getModel(provider, modelId)`.
- Backend resolves creds via env/OAuth (`getApiKey`), never ships keys to browser.
- Tests + evals use the faux provider for determinism.
- Do **not** wrap `Model` in a Lena-specific provider enum — keep it open.
