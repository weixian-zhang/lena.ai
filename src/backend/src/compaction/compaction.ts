// Tool-result truncation. Keeps a small head and a large tail: the head shows
// what the command was doing, the tail holds the result and any error, which is
// where the answer usually is.

/** Fallback when `DEFAULT_TRUNCATE_TOOL_RESULT_THRESHOLD` is unset or unparseable. */
export const DEFAULT_TRUNCATE_TOOL_RESULT_THRESHOLD = 40_000;

/** Fraction of the budget spent on the head; the rest goes to the tail. */
const HEAD_RATIO = 0.2;

/**
 * Max chars to keep from one tool result, from the environment.
 *
 * Read lazily rather than at module load so it reflects whoever called
 * `process.loadEnvFile` first, instead of letting import order decide.
 * Underscores are stripped so `40_000` in `.env` parses like the TS literal.
 */
export function maxToolResultChars(): number {
  const raw = process.env.DEFAULT_TRUNCATE_TOOL_RESULT_THRESHOLD?.replace(/_/g, "");
  const parsed = Number(raw);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_TRUNCATE_TOOL_RESULT_THRESHOLD;
}

/**
 * Truncate a tool result to `maxChars`, keeping the first 20% and last 80% with
 * a marker in between. Returns the input unchanged when it already fits.
 *
 * The marker states the omitted count and how to narrow the query, so the model
 * can recover rather than assume it saw everything.
 */
export function truncateToolResult(content: string, maxChars = maxToolResultChars()): string {
  if (content.length <= maxChars) return content;

  const headChars = Math.floor(maxChars * HEAD_RATIO);
  const tailChars = maxChars - headChars;
  const omitted = content.length - headChars - tailChars;

  return (
    `${content.slice(0, headChars)}\n\n` +
    `... [${omitted.toLocaleString()} of ${content.length.toLocaleString()} characters omitted — ` +
    `narrow the query with --query, -o tsv, or a filter] ...\n\n` +
    `${content.slice(-tailChars)}`
  );
}
