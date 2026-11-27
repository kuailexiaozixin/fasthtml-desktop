import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { BUNDLED_SKILL_RANK } from "@deepseek-ai/dsh-skill";

// Distributable `fasthtml-desktop` skill provider for DeepSeek Harness.
// The published npm package keeps the skill under skills/fasthtml-desktop/,
// while the local skill checkout keeps it at the repository root.

const PROVIDER_NAME = "fasthtml-desktop";
const NESTED_SKILL = new URL("./skills/fasthtml-desktop/SKILL.md", import.meta.url);
const LOCAL_SKILL = new URL("./SKILL.md", import.meta.url);
const SKILL_BODY_URL = existsSync(NESTED_SKILL) ? NESTED_SKILL : LOCAL_SKILL;
const SKILL_ROOT = existsSync(NESTED_SKILL)
  ? new URL("./skills/fasthtml-desktop/", import.meta.url)
  : new URL("./", import.meta.url);
const RESOURCE_BASE = {
  kind: "directory",
  path: fileURLToPath(SKILL_ROOT),
};

const CANDIDATE = {
  name: "fasthtml-desktop",
  description:
    "FastHTML + pywebview desktop application development skill: full lifecycle from need discovery, FastHTML web development, pywebview desktop shell wrapping to PyInstaller packaging into a native-window desktop EXE (WebView2 rendering, local HTTP service). Use when the user mentions FastHTML, pywebview, web desktop, HTMX interface, local HTTP service, or a web app delivered with a native window.",
  invocation: { modelInvocable: true, userInvocable: true },
  provider: PROVIDER_NAME,
  source: "bundled",
  resourceBase: RESOURCE_BASE,
  rank: BUNDLED_SKILL_RANK,
  locator: SKILL_BODY_URL,
};

const provider = {
  name: PROVIDER_NAME,
  list: () => Promise.resolve([CANDIDATE]),
  async get(_candidate) {
    return {
      name: CANDIDATE.name,
      description: CANDIDATE.description,
      invocation: CANDIDATE.invocation,
      provider: CANDIDATE.provider,
      source: CANDIDATE.source,
      resourceBase: RESOURCE_BASE,
      content: await readFile(SKILL_BODY_URL, "utf8"),
    };
  },
};

/** Cordis plugin name. */
export const name = "fasthtml-desktop";
/** Service required by the bundled provider. */
export const inject = ["skills"];

/** Register the bundled `fasthtml-desktop` provider on ctx.skills. */
export function apply(ctx) {
  ctx.skills.registerProvider(() => provider);
}