// Helpers for AG UI tool-call status rendering.
//
// MCP tools are bound under a namespaced name in backend middleware:
//   `mcp_app:{uuid}_{short_tool_name}`
// We strip the namespace on the frontend so the user sees "Local Shell › run_command"
// instead of the raw UUID.

export const MCP_NAME_RE = /^mcp_app:([0-9a-fA-F-]{36})_(.+)$/;

export type ResolvedToolName = {
  displayName: string;
  appName?: string;
  mcpAppId?: string;
};

export function resolveToolName(
  raw: string | undefined,
  apps: { id: string; name: string }[] | null | undefined,
): ResolvedToolName {
  const name = raw ?? 'tool';
  const m = name.match(MCP_NAME_RE);
  if (!m) return { displayName: name };
  const uuid = m[1];
  const shortName = m[2];
  const app = apps?.find((a) => a?.id === uuid);
  return {
    displayName: shortName,
    appName: app?.name,
    mcpAppId: uuid,
  };
}

// Best-effort parse of a (possibly still-streaming) JSON args string.
function safeParsePartialJson(s: string): any | null {
  if (!s) return null;
  try {
    return JSON.parse(s);
  } catch {}
  // try to close common unterminated shapes
  const candidates = [s + '"}', s + '}', s + '"', s + '"}]}', s + ']}'];
  for (const c of candidates) {
    try {
      return JSON.parse(c);
    } catch {}
  }
  return null;
}

function probeRegex(s: string): string {
  const path = s.match(/"(?:file_path|filepath|path|filename|file)"\s*:\s*"([^"]+)/);
  if (path) return basename(path[1]);
  const cmd = s.match(/"(?:command|cmd|shell_command)"\s*:\s*"([^"\n]+)/);
  if (cmd) return truncate(cmd[1], 80);
  const q = s.match(/"(?:query|q|search)"\s*:\s*"([^"]+)/);
  if (q) return `"${truncate(q[1], 60)}"`;
  const url = s.match(/"(?:url|uri)"\s*:\s*"([^"]+)/);
  if (url) return truncate(url[1], 80);
  return '';
}

function basename(p: string): string {
  if (!p) return '';
  const idx = Math.max(p.lastIndexOf('/'), p.lastIndexOf('\\'));
  return idx >= 0 ? p.slice(idx + 1) : p;
}

function firstLine(s: string): string {
  return s.split(/\r?\n/)[0] ?? s;
}

function truncate(s: string, n: number): string {
  return s.length > n ? s.slice(0, n - 1) + '…' : s;
}

// Returns a short preview string like `README.md` or `ls -la` derived from
// the tool's JSON arguments. Tolerant of still-streaming partial JSON.
export function extractArgPreview(_tool: string, argsStr: string | undefined): string {
  if (!argsStr) return '';
  const obj = safeParsePartialJson(argsStr);
  if (!obj || typeof obj !== 'object') return probeRegex(argsStr);

  const pathish =
    obj.path ?? obj.file_path ?? obj.filepath ?? obj.filename ?? obj.file ?? obj.target;
  if (typeof pathish === 'string' && pathish) return basename(pathish);

  const cmd = obj.command ?? obj.cmd ?? obj.shell_command;
  if (typeof cmd === 'string' && cmd) return truncate(firstLine(cmd), 80);

  const q = obj.query ?? obj.q ?? obj.search;
  if (typeof q === 'string' && q) return `"${truncate(q, 60)}"`;

  const url = obj.url ?? obj.uri;
  if (typeof url === 'string' && url) return truncate(url, 80);

  for (const v of Object.values(obj)) {
    if (typeof v === 'string' && v) return truncate(v, 80);
  }
  return '';
}
