export const TOOL_APPROVAL_EVENT_NAME = 'tool_approval_requested';

export type ToolApprovalRequestValue = {
  requestId?: string;
  runId?: string;
  toolId?: string;
  toolName?: string;
  args?: unknown;
  parentMessageId?: string | null;
};

export const isToolApprovalRequestEvent = (event: {
  type?: string;
  name?: string;
  value?: ToolApprovalRequestValue;
}) => {
  if (!event) return false;

  const type = event.type ?? '';
  return (type === 'CUSTOM' || type === 'CustomEvent') && event.name === TOOL_APPROVAL_EVENT_NAME;
};

export const formatToolApprovalArgs = (args: unknown) => {
  if (typeof args === 'string') {
    return args.trim() === '' ? '{}' : args;
  }

  if (args === undefined) {
    return '{}';
  }

  try {
    return JSON.stringify(args ?? {}, null, 2);
  } catch {
    return '{}';
  }
};

export const formatToolApprovalMessage = (value: ToolApprovalRequestValue = {}) => {
  const toolName = value.toolName ?? value.toolId ?? 'tool';
  const argsPreview = formatToolApprovalArgs(value.args);

  return [`Approve running \`${toolName}\`?`, '', 'Arguments:', '```json', argsPreview, '```'].join(
    '\n',
  );
};

export const toToolApprovalResponse = (result: unknown) => {
  if (result && typeof result === 'object' && 'approved' in result) {
    return result as { approved: boolean };
  }

  return { approved: result === true };
};
