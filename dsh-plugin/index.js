import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { BUNDLED_SKILL_RANK } from "@deepseek-ai/dsh-skill";

// Bundled `fasthtml-desktop` skill provider for DeepSeek Harness.
//
// This is the embedded-provider pattern used by the official
// `@deepseek-ai/dsh-skill-badge` plugin: the SKILL.md body lives in assets/,
// and the skill is registered on ctx.skills via registerProvider().
// resourceBase points at the skill repository root so the model can resolve
// the references/, scripts/, examples/ paths the SKILL.md body cites.
//
// NOTE: this is a LOCAL / in-repo plugin, NOT a distributable self-contained
// npm package. resourceBase resolves to the parent skill repo via a relative
// path; after `npm publish` the package installs under a profile's
// node_modules and that path no longer points at the skill repo, so resource
// resolution breaks. Do not publish to npm in its current form.

const PROVIDER_NAME = "fasthtml-desktop";

// assets/SKILL.md holds a copy of the skill body (kept in sync with SKILL.md).
const SKILL_BODY_URL = new URL("../assets/SKILL.md", import.meta.url);

// The skill root is the parent of this dsh-plugin/ directory, so the body's
// relative references (references/..., scripts/..., examples/...) resolve.
const RESOURCE_BASE = {
  kind: "directory",
  path: fileURLToPath(new URL("../../", import.meta.url)),
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
