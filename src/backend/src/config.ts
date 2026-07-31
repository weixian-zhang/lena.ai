// Central home for token limits and the estimation ratios behind them. Kept in one
// file so the context budget can be reasoned about — and retuned for a new model
// deployment — without hunting through call sites.

/** Character-to-token ratio for prose. */
export const CHARS_PER_TOKEN = 4;

/** Ratio for JSON payloads (tool call arguments) — punctuation-dense, so denser in tokens. */
export const JSON_CHARS_PER_TOKEN = 3;

/** Per-message allowance for the role/delimiter framing the provider adds. */
export const MESSAGE_OVERHEAD_TOKENS = 4;

/** Flat estimate per image, covering up to ~4K resolution. */
export const IMAGE_TOKENS = 3_000;

/** Flat estimate per PDF (~100 pages at 258 tokens/page). */
export const PDF_TOKENS = 25_800;

/** Max chars kept from a single tool result before it is truncated. */
export const TOOL_RESULT_TRUNCATE_CHARS = 2_000;

/** Total context window of the model deployment. */
export const CONTEXT_WINDOW_TOKENS = 200_000;

/** Max output tokens per turn — sized for a compaction summary, the longest generation. */
export const MAX_OUTPUT_TOKENS = 32_768;
