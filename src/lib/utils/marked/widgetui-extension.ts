/**
 * Marked extension for `widgetui` code-fence blocks.
 *
 * When the LLM agent outputs a fenced code block with language `widgetui`,
 * this extension intercepts it and produces a custom `widgetUI` token
 * instead of the default `code` token.
 *
 * ```widgetui
 * {
 *   "component": "widget",
 *   "data": { "type": "card", ... }
 * }
 * ```
 */

function widgetUITokenizer(this: any, src: string) {
  // Match ```widgetui ... ```
  const match = /^```widgetui\s*\n([\s\S]*?)```\s*(?:\n|$)/.exec(src);
  if (!match) return;

  const raw = match[0];
  const jsonText = match[1].trim();

  let parsed: { component?: string; data?: unknown; widget?: string } = {};
  try {
    parsed = JSON.parse(jsonText);
  } catch {
    return;
  }

  // Widget reference format: { "widget": "widget-id", "data": { ... } }
  if (typeof parsed.widget === 'string') {
    return {
      type: 'widgetUI',
      raw,
      component: 'widget-ref',
      widget: parsed.widget,
      data: parsed.data ?? {},
    };
  }

  if (!parsed.component) {
    // If it doesn't have a component but looks like a direct widget JSON (has "type" or "children"),
    // we can wrap it automatically.
    if ((parsed as any).type || (parsed as any).children) {
      return {
        type: 'widgetUI',
        raw,
        component: 'widget',
        data: parsed,
      };
    }
    return;
  }

  return {
    type: 'widgetUI',
    raw,
    component: parsed.component as string,
    data: parsed.data ?? null,
  };
}

function widgetUIStart(src: string) {
  const idx = src.indexOf('```widgetui');
  return idx !== -1 ? idx : -1;
}

function widgetUIRenderer(token: any) {
  return `<div class="widgetui" data-component="${token.component}">${JSON.stringify(token.data)}</div>`;
}

function widgetUIExtension() {
  return {
    name: 'widgetUI',
    level: 'block' as const,
    start: widgetUIStart,
    tokenizer: widgetUITokenizer,
    renderer: widgetUIRenderer,
  };
}

export default function (options = {}) {
  return {
    extensions: [widgetUIExtension()],
  };
}
