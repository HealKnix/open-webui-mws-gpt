/**
 * Marked extension for `agentui` code-fence blocks.
 *
 * When the LLM agent outputs a fenced code block with language `agentui`,
 * this extension intercepts it and produces a custom `agentUI` token
 * instead of the default `code` token.  The body of the fence is expected
 * to be a JSON object with at least a `component` field:
 *
 * ```agentui
 * {
 *   "component": "hotel-cards",
 *   "data": [ ... ]
 * }
 * ```
 *
 * The resulting token carries the parsed `component` string and the raw
 * `data` payload so the Svelte renderer can pick the matching component.
 */

function agentUITokenizer(this: any, src: string) {
  // Match ```agentui ... ``` (with optional trailing whitespace on the closing fence)
  const match = /^```agentui\s*\n([\s\S]*?)```\s*(?:\n|$)/.exec(src);
  if (!match) return;

  const raw = match[0];
  const jsonText = match[1].trim();

  let parsed: { component?: string; data?: unknown } = {};
  try {
    parsed = JSON.parse(jsonText);
  } catch {
    // If the JSON is malformed, fall through to the default code renderer
    return;
  }

  if (!parsed.component) return;

  return {
    type: 'agentUI',
    raw,
    component: parsed.component as string,
    data: parsed.data ?? null,
  };
}

function agentUIStart(src: string) {
  const idx = src.indexOf('```agentui');
  return idx !== -1 ? idx : -1;
}

function agentUIRenderer(token: any) {
  // Fallback HTML (never actually used because MarkdownTokens handles it)
  return `<div class="agentui" data-component="${token.component}">${JSON.stringify(token.data)}</div>`;
}

function agentUIExtension() {
  return {
    name: 'agentUI',
    level: 'block' as const,
    start: agentUIStart,
    tokenizer: agentUITokenizer,
    renderer: agentUIRenderer,
  };
}

export default function (options = {}) {
  return {
    extensions: [agentUIExtension()],
  };
}
