import { mkdir, mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import type { AgentTool } from "@mariozechner/pi-agent-core";
import { type Static, Type } from "typebox";
import { lenaHome } from "../../../cwd.js";
import { MAX_OUTPUT_BYTES, runShell } from "./shell.js";

// ---------------------------------------------------------------------------
// Azure session — one authenticated, isolated CLI login shared by every call.
// ---------------------------------------------------------------------------

/** Persistent working directory for agent commands: `~/.lena/work`. */
const WORKDIR = lenaHome("work");

interface AzureSession {
  /** Environment carrying a per-session `AZURE_CONFIG_DIR` + PATH/secrets. */
  env: NodeJS.ProcessEnv;
  /** Working directory ({@link WORKDIR}): cloning repos, staging deploy artifacts. */
  cwd: string;
}

/** Cached login. `az login` runs once; every later `az` call reuses the token. */
let session: Promise<AzureSession> | undefined;

/** Seconds to allow `az login` before giving up. */
const LOGIN_TIMEOUT_SECONDS = 60;

function requireEnv(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

/**
 * Resolve the shared Azure session, logging in on first use.
 *
 * A per-session `AZURE_CONFIG_DIR` isolates this process's credential cache and
 * active subscription so concurrent sessions don't clobber a shared `~/.azure`.
 * The promise is cached, so concurrent first-callers await a single `az login`
 * and everyone after reuses the warm token cache — prepending `az login` to every
 * command would instead cost a token-endpoint round trip per call.
 */
function getAzureSession(): Promise<AzureSession> {
  return (session ??= createSession());
}

async function createSession(): Promise<AzureSession> {
  const configDir = await mkdtemp(join(tmpdir(), "lena-az-config-"));
  const cwd = WORKDIR;
  await mkdir(cwd, { recursive: true });

  const clientId = requireEnv("AZURE_CLIENT_ID");
  const clientSecret = requireEnv("AZURE_CLIENT_SECRET");
  const tenantId = requireEnv("AZURE_TENANT_ID");

  const env: NodeJS.ProcessEnv = { ...process.env, AZURE_CONFIG_DIR: configDir };

  // Pass the secret through an env var referenced as "$LENA_SP_SECRET" so the
  // literal never appears in the command string we build (and might log/stream).
  // Residual exposure: the CLI still receives it as an argv, visible in `ps`
  // inside this host. To remove even that, switch the SP to certificate auth
  // (`--password <cert.pem>`).
  const loginEnv: NodeJS.ProcessEnv = { ...env, LENA_SP_SECRET: clientSecret };
  const command =
    `az login --service-principal -u '${clientId}' -p "$LENA_SP_SECRET" ` +
    `--tenant '${tenantId}' -o none --only-show-errors`;

  const result = await runShell(command, { cwd, env: loginEnv, timeout: LOGIN_TIMEOUT_SECONDS });
  if (result.exitCode !== 0) {
    // stdout carries az's stderr (merged); the secret is not in it.
    throw new Error(`az login (service principal) failed:\n${result.stdout || "(no output)"}`);
  }

  return { env, cwd };
}

// ---------------------------------------------------------------------------
// Bash tool — Lena's single execution surface.
// ---------------------------------------------------------------------------

const schema = Type.Object({
  command: Type.String({
    description: "The bash command to run. Use `-o json` for `az` output you need to parse.",
  }),
  timeout: Type.Optional(
    Type.Number({ description: "Timeout in seconds. Omit for no timeout." }),
  ),
});

export type BashToolInput = Static<typeof schema>;

/**
 * Fast-fail deny-list for obviously destructive commands.
 *
 * IMPORTANT: this is a UX + audit speed bump, NOT the security boundary. A bash
 * string cannot be reliably parsed for intent (`eval`, `$(...)`, base64, aliases,
 * `az rest --method delete`, `curl -X DELETE https://management.azure.com/...`).
 * The load-bearing no-delete guarantee is the service principal's Azure RBAC role
 * whose NotActions exclude every delete action — the platform returns 403 regardless
 * of how the command is phrased. This regex just catches the common cases early with
 * a clear message and gives us something to log.
 */
const DELETION_PATTERN =
  /\b(rm\s+-[a-z]*[rf]|rmdir|az\b[^|;&]*\bdelete\b|--method[= ]+delete|-X[= ]*delete|\bpurge\b)/i;

/**
 * Lena's single execution surface: run a bash command with the Azure CLI
 * pre-authenticated (see {@link getAzureSession}). One tool rather than separate
 * `az` / `node` tools — both are just binaries in this same shell, and a single
 * choke point means the delete gate and (future) HITL confirmation live in
 * exactly one place. See CLAUDE.md ("Tools = the Azure surface").
 *
 * TODO(HITL): mutating commands (create/update/stop/restart/scale/deallocate)
 * should pause for human confirmation. That requires the interaction channel
 * from the not-yet-built gateway; wire it here once that lands.
 */
export const bashTool: AgentTool<typeof schema> = {
  name: "bash",
  label: "bash",
  description:
    "Run a bash command. Use this for Azure CLI (`az` is pre-authenticated against the target " +
    "subscription) and for any other shell tool (jq, grep, curl, git, node). " +
    "To run JavaScript, write a `.mjs` file with a quoted heredoc (`cat > x.mjs <<'EOF'`) and " +
    "run `node x.mjs` — that keeps the shell from touching the source, and gives real line " +
    "numbers in stack traces. Deleting Azure resources is out of scope and blocked.",
  parameters: schema,
  async execute(_toolCallId, { command, timeout }, signal) {
    if (DELETION_PATTERN.test(command)) {
      throw new Error(
        "Deletion is out of scope by design and is blocked. If the user needs a resource " +
          "deleted, explain how they can do it themselves or escalate — do not attempt it.",
      );
    }

    const { env, cwd } = await getAzureSession();
    const { stdout, exitCode, truncated } = await runShell(command, { cwd, env, signal, timeout });

    const suffix = truncated
      ? `\n\n[output truncated at ${MAX_OUTPUT_BYTES / 1000} KB — narrow the query with --query, -o tsv, or a filter]`
      : "";
    const text = (stdout || "(no output)") + suffix;

    // Contract (CLAUDE.md + pi AgentTool): throw on failure, never return an error
    // string as normal content. `null` means killed by signal — handled as abort/timeout.
    if (exitCode !== 0 && exitCode !== null) {
      throw new Error(text);
    }

    return { content: [{ type: "text", text }], details: undefined };
  },
};
