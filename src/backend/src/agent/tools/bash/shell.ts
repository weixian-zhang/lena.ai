import { spawn } from "node:child_process";

/**
 * Maximum number of output bytes returned to the model. Azure listings (e.g.
 * `az resource list`) can be enormous; we cap what goes into the context window
 * and flag truncation so the model knows to narrow its query (filters, `--query`,
 * `-o tsv`) rather than assume it saw everything.
 */
export const MAX_OUTPUT_BYTES = 100_000;

/** Shell used to run commands. `/bin/bash` is present on Lena's Linux/macOS hosts. */
const SHELL = "/bin/bash";

export interface RunShellOptions {
  /** Working directory for the command. */
  cwd: string;
  /** Environment for the child process (carries `AZURE_CONFIG_DIR`, secrets, PATH). */
  env: NodeJS.ProcessEnv;
  /** Aborts the command and kills its process tree when signalled. */
  signal?: AbortSignal;
  /** Timeout in seconds. Omit or `0` for no timeout. */
  timeout?: number;
}

export interface RunShellResult {
  /** Merged stdout + stderr in arrival order, capped at {@link MAX_OUTPUT_BYTES}. */
  stdout: string;
  /** Process exit code. `null` if the process was terminated by a signal. */
  exitCode: number | null;
  /** True when output was cut at the byte cap. */
  truncated: boolean;
}

/**
 * Run a single shell command, streaming stdout+stderr into a capped buffer.
 *
 * Reimplemented from Pi's `createLocalBashOperations` core (packages/coding-agent/
 * src/core/tools/bash.ts) minus its TUI coupling. On non-Windows the child is spawned
 * in its own process group (`detached`) so a timeout or abort can kill the whole tree
 * — a bare `child.kill()` would orphan grandchildren (e.g. `az` sub-processes).
 *
 * Rejects with `"aborted"`, a timeout message, or a spawn error. A non-zero exit is
 * NOT a rejection here — the caller decides how to surface it (the bash tool throws,
 * per the tool contract in CLAUDE.md).
 */
export function runShell(command: string, options: RunShellOptions): Promise<RunShellResult> {
  const { cwd, env, signal, timeout } = options;
  if (signal?.aborted) return Promise.reject(new Error("aborted"));

  return new Promise<RunShellResult>((resolve, reject) => {
    const child = spawn(SHELL, ["-c", command], {
      cwd,
      env,
      detached: process.platform !== "win32",
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    });

    const chunks: Buffer[] = [];
    let bytes = 0;
    let truncated = false;
    let timedOut = false;
    let timer: NodeJS.Timeout | undefined;

    const kill = () => {
      if (!child.pid) return;
      try {
        // Negative pid targets the whole process group on POSIX.
        if (process.platform !== "win32") process.kill(-child.pid, "SIGKILL");
        else child.kill("SIGKILL");
      } catch {
        // Process already exited — nothing to kill.
      }
    };

    const onData = (buf: Buffer) => {
      if (truncated) return;
      const remaining = MAX_OUTPUT_BYTES - bytes;
      if (buf.length >= remaining) {
        chunks.push(buf.subarray(0, remaining));
        bytes = MAX_OUTPUT_BYTES;
        truncated = true;
      } else {
        chunks.push(buf);
        bytes += buf.length;
      }
    };

    const onAbort = () => kill();

    const cleanup = () => {
      if (timer) clearTimeout(timer);
      signal?.removeEventListener("abort", onAbort);
    };

    child.stdout.on("data", onData);
    child.stderr.on("data", onData);

    if (timeout && timeout > 0) {
      timer = setTimeout(() => {
        timedOut = true;
        kill();
      }, timeout * 1000);
    }
    if (signal) signal.addEventListener("abort", onAbort, { once: true });

    child.on("error", (err) => {
      cleanup();
      reject(err);
    });

    child.on("close", (code) => {
      cleanup();
      if (signal?.aborted) return reject(new Error("aborted"));
      if (timedOut) return reject(new Error(`Command timed out after ${timeout} seconds`));
      // Decode once at the end so multi-byte UTF-8 is never split across chunks.
      resolve({ stdout: Buffer.concat(chunks).toString("utf8"), exitCode: code, truncated });
    });
  });
}
