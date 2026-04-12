import { describe, expect, it } from 'vitest';

import {
  TOOL_APPROVAL_EVENT_NAME,
  formatToolApprovalArgs,
  formatToolApprovalMessage,
  isToolApprovalRequestEvent,
  toToolApprovalResponse,
} from './agui';

describe('agui utils', () => {
  it('detects tool approval request events', () => {
    expect(
      isToolApprovalRequestEvent({
        type: 'CUSTOM',
        name: TOOL_APPROVAL_EVENT_NAME,
        value: { toolId: 'tool:echo' },
      }),
    ).toBe(true);

    expect(
      isToolApprovalRequestEvent({
        type: 'RUN_STARTED',
        name: TOOL_APPROVAL_EVENT_NAME,
      }),
    ).toBe(false);
  });

  it('formats args preview as json when given an object', () => {
    expect(formatToolApprovalArgs({ value: 7 })).toBe('{\n  "value": 7\n}');
  });

  it('builds a read-only approval message with tool name and args preview', () => {
    expect(
      formatToolApprovalMessage({
        toolName: 'echo',
        args: { value: 7 },
      }),
    ).toContain('```json');

    expect(
      formatToolApprovalMessage({
        toolName: 'echo',
        args: { value: 7 },
      }),
    ).toContain('"value": 7');
  });

  it('normalizes confirm and cancel results into approval responses', () => {
    expect(toToolApprovalResponse(true)).toEqual({ approved: true });
    expect(toToolApprovalResponse(false)).toEqual({ approved: false });
    expect(toToolApprovalResponse({ approved: true })).toEqual({ approved: true });
  });
});
