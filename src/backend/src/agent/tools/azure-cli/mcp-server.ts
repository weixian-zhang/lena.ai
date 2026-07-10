import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

// A single local stdio Azure MCP server (`@azure/mcp`), shared across calls.
// Lena only uses its "extension cli generate" tool, so we start it scoped to the
// `extension` namespace with `--mode all` (exposes each command as its own tool
// rather than collapsing the namespace behind a router tool).

/** `npx` fetches `@azure/mcp` on first run. */
const SERVER_COMMAND = "npx";

const SERVER_ARGS = [
  "-y",
  "@azure/mcp@latest",
  "server",
  "start",
  "--namespace",
  "extension",
  "--mode",
  "all",
];

/** Expected generate-tool name; resolved against the live list as a safety net. */
const CLI_GENERATE_TOOL = "extension_cli_generate";

/** Startup + handshake budget; generous because the first `npx` run downloads. */
const STARTUP_TIMEOUT_MS = 120_000;

export interface McpSession {
  /** Connected MCP client, ready for `callTool`. */
  client: Client;
  /** Resolved name of the cli-generate tool to route calls to. */
  toolName: string;
}

// Cached promise: concurrent callers share one spawn; cleared on failure so a
// dead child process doesn't poison later calls.
let session: Promise<McpSession> | undefined;

/** Our full environment as a `Record<string, string>`, dropping unset keys. */
function inheritedEnv(): Record<string, string> {
  const env: Record<string, string> = {};
  for (const [key, value] of Object.entries(process.env)) {
    if (value !== undefined) env[key] = value;
  }
  return env;
}

/** Resolve the shared Azure MCP session, starting the server on first use. */
export function getCliGenerateSession(): Promise<McpSession> {
  if (!session) {
    session = createSession().catch((err) => {
      session = undefined;
      throw err;
    });
  }
  return session;
}

async function createSession(): Promise<McpSession> {
  const transport = new StdioClientTransport({
    command: SERVER_COMMAND,
    args: SERVER_ARGS,
    // Forward our env so the server's DefaultAzureCredential finds the SP creds
    // (AZURE_CLIENT_ID/SECRET/TENANT_ID) — the transport otherwise inherits only
    // a safe subset (HOME/PATH/...) and the credential chain stalls without them.
    env: inheritedEnv(),
    stderr: "pipe", // keep the child's logs off our stdio

  });

  const client = new Client({ name: "lena", version: "0.0.0" }, { capabilities: {} });
  await client.connect(transport, { timeout: STARTUP_TIMEOUT_MS });

  const toolName = await resolveAzCliCommandTool(client);
  return { client, toolName };
}

// Resolve the generate tool by exact name.
async function resolveAzCliCommandTool(client: Client): Promise<string> {
  const { tools } = await client.listTools();
  const exact = tools.find((t) => t.name === CLI_GENERATE_TOOL);
  if (exact) return exact.name;

  const seen = tools.map((t) => t.name).join(", ") || "(none)";
  throw new Error(
    `Azure MCP server exposed no cli-generate tool (expected "${CLI_GENERATE_TOOL}"). Saw: ${seen}`,
  );
}
