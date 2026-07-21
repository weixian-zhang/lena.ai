import { homedir } from "node:os";
import { join } from "node:path";

/** Lena's private root under the user's home directory: `~/.lena`. */
export const LENA_HOME = join(homedir(), ".lena");

/**
 * Resolve a path inside Lena's home directory (`~/.lena`).
 */
export function lenaHome(...segments: string[]): string {
  return join(LENA_HOME, ...segments);
}
