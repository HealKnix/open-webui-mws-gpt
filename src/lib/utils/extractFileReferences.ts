export type FileReferenceType = 'pdf' | 'md' | 'docx' | 'pptx';

export interface FileReference {
  name: string;
  url: string;
  ext: FileReferenceType;
}

const SUPPORTED_EXTS: FileReferenceType[] = ['pdf', 'md', 'docx', 'pptx'];

const getExt = (url: string): FileReferenceType | null => {
  try {
    const clean = url.split('#')[0].split('?')[0];
    const lower = clean.toLowerCase();
    for (const ext of SUPPORTED_EXTS) {
      if (lower.endsWith('.' + ext)) return ext;
    }
  } catch {
    // ignore
  }
  return null;
};

const decodeName = (raw: string): string => {
  try {
    return decodeURIComponent(raw);
  } catch {
    return raw;
  }
};

export const extractFileReferences = (content: string): FileReference[] => {
  if (!content) return [];

  const results: FileReference[] = [];
  const seen = new Set<string>();

  const push = (name: string, url: string) => {
    const ext = getExt(url);
    if (!ext) return;
    const key = url;
    if (seen.has(key)) return;
    seen.add(key);
    results.push({ name: name || url.split('/').pop() || url, url, ext });
  };

  const mdLinkRe = /\[([^\]\n]+)\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g;
  let m: RegExpExecArray | null;
  while ((m = mdLinkRe.exec(content)) !== null) {
    push(decodeName(m[1]).trim(), m[2].trim());
  }

  const bareRe =
    /(?<![\("])((?:https?:\/\/|\/)[^\s<>"'`)]+\.(?:pdf|md|docx|pptx))(?![^\s<>"'`)]*\))/gi;
  while ((m = bareRe.exec(content)) !== null) {
    const url = m[1];
    const name = decodeName(url.split('/').pop() ?? url);
    push(name, url);
  }

  return results;
};
