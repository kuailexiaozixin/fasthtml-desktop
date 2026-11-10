import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { BUNDLED_SKILL_RANK } from "@deepseek-ai/dsh-skill";

// Distributable `fasthtml-desktop` skill provider for DeepSeek Harness.
//
// This is the embedded-provider pattern used by the official
// `@deepseek-ai/dsh-skill-badge` plugin, made SELF-CONTAINED so it can be
// published to npm and installed by anyone. The npm package IS the full skill
// repository (references/, scripts/, examples/, docs/, templates/, ...),
// so resourceBase points at the package root: every relative path the SKILL.md
// body cites resolves inside the installed package, with no dependency on the
// publisher's machine or repo location.

const PROVIDER_NAME = "fasthtml-desktop";

// SKILL.md lives at the package root (same as the skill repo root).
const SKILL_BODY_URL = new URL("./SKILL.md", import.meta.url);

// resourceBase = package root, so references/..., scripts/..., examples/...
// resolve inside the installed npm package.
const RESOURCE_BASE = {
  kind: "directory",
  path: fileURLToPath(new URL("./", import.meta.url)),
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
