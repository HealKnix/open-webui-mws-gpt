<script lang="ts">
  import { onDestroy, onMount, createEventDispatcher } from 'svelte';
  import { toast } from 'svelte-sonner';

  export let resource: {
    uri?: string;
    mimeType?: string;
    text?: string;
    blob?: string;
  };
  export let appId: string = '';
  export let toolCallId: string = '';
  export let toolName: string = '';
  export let toolInput: Record<string, any> | undefined = undefined;
  export let toolOutput: { content?: any; structuredContent?: any } | undefined = undefined;

  const dispatch = createEventDispatcher<{
    action: { type: string; payload: any };
  }>();

  let iframeEl: HTMLIFrameElement;
  let iframeHeight = 320;
  let iframeReady = false;
  let displayMode: 'inline' | 'fullscreen' = 'inline';

  function exitFullscreen() {
    if (displayMode !== 'fullscreen') return;
    displayMode = 'inline';
    sendHostContext();
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Escape' && displayMode === 'fullscreen') {
      e.preventDefault();
      exitFullscreen();
    }
  }

  function isHtmlMime(mime?: string): boolean {
    if (!mime) return false;
    return mime.startsWith('text/html');
  }

  function isUriListMime(mime?: string): boolean {
    if (!mime) return false;
    return mime.startsWith('text/uri-list');
  }

  function decodeBlob(blob: string): string {
    try {
      return atob(blob);
    } catch {
      return '';
    }
  }

  $: htmlContent = (() => {
    if (!resource) return '';
    if (isHtmlMime(resource.mimeType)) {
      if (resource.text != null) return resource.text;
      if (resource.blob) return decodeBlob(resource.blob);
    }
    return '';
  })();

  $: externalUrl = (() => {
    if (!resource) return '';
    if (isUriListMime(resource.mimeType)) {
      const raw = resource.text ?? (resource.blob ? decodeBlob(resource.blob) : '');
      return (
        (raw || '')
          .split('\n')
          .map((l) => l.trim())
          .find((l) => l && !l.startsWith('#')) || ''
      );
    }
    return '';
  })();

  function postNotification(method: string, params: Record<string, any> = {}) {
    try {
      console.log('[MCP-UI host → iframe]', method, params);
      iframeEl?.contentWindow?.postMessage({ jsonrpc: '2.0', method, params }, '*');
    } catch {
      // iframe may not be ready yet — retried on load/initialize
    }
  }

  function postRpcResult(id: any, result: Record<string, any> = {}) {
    try {
      iframeEl?.contentWindow?.postMessage({ jsonrpc: '2.0', id, result }, '*');
    } catch {
      // ignore
    }
  }

  function postRpcError(id: any, code: number, message: string) {
    try {
      iframeEl?.contentWindow?.postMessage({ jsonrpc: '2.0', id, error: { code, message } }, '*');
    } catch {
      // ignore
    }
  }

  function sendToolNotifications() {
    // MCP Apps spec (`ext-apps`): params carry the tool arguments directly
    // under `arguments`, and the result notification carries the raw
    // CallToolResult (`content` + `structuredContent` + optional `isError`).
    // See excalidraw-mcp `mcp-app.tsx` ontoolinput/ontoolresult handlers.
    if (toolInput !== undefined) {
      postNotification('ui/notifications/tool-input', {
        arguments: toolInput,
      });
    }
    if (toolOutput !== undefined && toolOutput !== null) {
      postNotification('ui/notifications/tool-result', {
        content: toolOutput?.content,
        structuredContent: toolOutput?.structuredContent,
      });
    }
  }

  function sendHostContext() {
    postNotification('ui/notifications/host-context-changed', {
      displayMode,
    });
  }

  function handleMessage(e: MessageEvent) {
    if (!iframeEl || e.source !== iframeEl.contentWindow) return;
    const data = e.data;
    if (!data || typeof data !== 'object') return;

    const method = data.method;
    const params = data.params || {};
    const id = data.id;

    console.log('[MCP-UI iframe → host]', method, { id, params });

    if (!method) return;

    switch (method) {
      case 'ui/initialize': {
        // Reply to the RPC request if it expects one, and push the
        // tool input/result the widget is waiting for.
        if (id !== undefined) {
          postRpcResult(id, {
            protocolVersion: params.protocolVersion || '2026-01-26',
            hostInfo: {
              name: 'open-webui',
              version: '1.0.0',
            },
            hostCapabilities: {},
            hostContext: {},
          });
        }
        iframeReady = true;
        sendToolNotifications();
        return;
      }
      case 'ui/notifications/initialized': {
        iframeReady = true;
        sendToolNotifications();
        return;
      }
      case 'ui/notifications/size-changed': {
        const h = params?.height;
        if (typeof h === 'number' && Number.isFinite(h) && h > 0) {
          iframeHeight = Math.max(120, Math.min(2000, Math.round(h)));
        }
        return;
      }
      case 'ui/open-link': {
        const url = params?.url;
        if (typeof url === 'string' && url) {
          window.open(url, '_blank', 'noopener,noreferrer');
        }
        return;
      }
      case 'ui/message': {
        // Widget asked the host to do something (e.g. run a tool).
        const payloadType = params?.type;
        if (payloadType === 'tool-call') {
          dispatch('action', {
            type: 'tool',
            payload: {
              toolName: params.name,
              params: params.arguments ?? {},
            },
          });
        } else if (payloadType === 'notify') {
          const m = params?.message;
          if (typeof m === 'string' && m) toast.info(m);
        } else {
          dispatch('action', { type: 'intent', payload: params });
        }
        return;
      }
      case 'ui/update-model-context': {
        dispatch('action', { type: 'prompt', payload: params });
        return;
      }
      case 'tools/call': {
        // Widget asks host to run an MCP tool (e.g. read_checkpoint).
        // Not yet proxied through the MCP client — reply with an error
        // so the widget can surface it instead of hanging.
        if (id !== undefined) {
          postRpcError(id, -32601, 'tools/call proxying not implemented in host');
        }
        return;
      }
      case 'ui/request-display-mode': {
        const requested = params?.mode === 'fullscreen' ? 'fullscreen' : 'inline';
        displayMode = requested;
        if (id !== undefined) {
          postRpcResult(id, { mode: requested });
        }
        sendHostContext();
        return;
      }
      default:
        // Some widgets also use legacy `type` field — fall through quietly.
        return;
    }
  }

  function onIframeLoad() {
    // Some widgets render eagerly without initialize. Push notifications
    // on iframe load as a safety net.
    sendToolNotifications();
  }

  // Re-deliver notifications if tool result arrives after init (streaming).
  $: if (iframeReady && (toolInput !== undefined || toolOutput !== undefined)) {
    sendToolNotifications();
  }

  onMount(() => {
    window.addEventListener('message', handleMessage);
    window.addEventListener('keydown', handleKeyDown);
  });

  onDestroy(() => {
    window.removeEventListener('message', handleMessage);
    window.removeEventListener('keydown', handleKeyDown);
  });
</script>

<div
  class="mcp-ui-wrapper my-2 overflow-hidden rounded-lg border border-gray-200 dark:border-gray-800"
  class:is-fullscreen={displayMode === 'fullscreen'}
>
  {#if displayMode === 'fullscreen'}
    <button
      type="button"
      class="mcp-ui-exit-fs"
      on:click={exitFullscreen}
      aria-label="Exit fullscreen">Esc · Exit fullscreen</button
    >
  {/if}
  {#if htmlContent}
    <iframe
      bind:this={iframeEl}
      title="MCP UI ({toolName || toolCallId || appId || 'resource'})"
      sandbox="allow-scripts allow-forms allow-popups"
      referrerpolicy="no-referrer"
      srcdoc={htmlContent}
      on:load={onIframeLoad}
      style="width:100%;height:{displayMode === 'fullscreen'
        ? '100%'
        : iframeHeight + 'px'};border:0;display:block;background:white;"
    ></iframe>
  {:else if externalUrl}
    <iframe
      bind:this={iframeEl}
      title="MCP UI ({toolName || toolCallId || appId || 'resource'})"
      sandbox="allow-scripts allow-forms allow-popups"
      referrerpolicy="no-referrer"
      src={externalUrl}
      on:load={onIframeLoad}
      style="width:100%;height:{displayMode === 'fullscreen'
        ? '100%'
        : iframeHeight + 'px'};border:0;display:block;background:white;"
    ></iframe>
  {:else}
    <div class="p-3 text-xs text-gray-500">
      Unsupported MCP UI resource ({resource?.mimeType ?? 'unknown'})
    </div>
  {/if}
</div>

<style>
  .mcp-ui-wrapper.is-fullscreen {
    position: fixed;
    inset: 0;
    z-index: 9999;
    margin: 0;
    border-radius: 0;
    border: 0;
    background: white;
  }
  .mcp-ui-exit-fs {
    position: absolute;
    top: 12px;
    right: 12px;
    z-index: 10000;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 500;
    background: rgba(0, 0, 0, 0.7);
    color: white;
    border: 0;
    border-radius: 6px;
    cursor: pointer;
  }
  .mcp-ui-exit-fs:hover {
    background: rgba(0, 0, 0, 0.85);
  }
</style>
