<script lang="ts">
  import { onMount, tick, getContext } from 'svelte';
  import { toast } from 'svelte-sonner';
  import { PaneGroup, Pane, PaneResizer } from 'paneforge';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import LockClosed from '$lib/components/icons/LockClosed.svelte';
  import ChevronLeft from '$lib/components/icons/ChevronLeft.svelte';
  import AccessControlModal from '../common/AccessControlModal.svelte';
  import { user } from '$lib/stores';
  import { slugify } from '$lib/utils';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import { updateWidgetAccessGrants } from '$lib/apis/widgets';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';

  import CodeEditor from '$lib/components/common/CodeEditor.svelte';
  import WidgetMapper from '$lib/components/common/agentui/WidgetMapper.svelte';
  import WidgetChatSidebar from './WidgetChatSidebar.svelte';
  import Sparkles from '$lib/components/icons/Sparkles.svelte';

  export let onSubmit: Function;
  export let edit = false;
  export let widget = null;
  export let clone = false;
  export let disabled = false;

  const i18n = getContext('i18n');

  let loading = false;
  let showAccessControlModal = false;
  let showAiSidebar = false;

  let name = '';
  let id = '';
  let description = '';
  let content = '{}';
  let _content = '{}'; // Internal for CodeEditor

  let accessGrants = [];
  let hasManualEdit = false;
  let hasManualName = false;
  let hasManualDescription = false;

  let jsonError = '';
  let codeEditor;

  // Auto-generate ID from name
  $: if (!edit && !clone && !hasManualEdit) {
    id = name !== '' ? slugify(name) : '';
  }

  // Validate JSON content for error reporting
  $: {
    try {
      if (_content.trim()) {
        JSON.parse(_content);
        jsonError = '';
      }
    } catch (e) {
      jsonError = e.message;
    }
  }

  const submitHandler = async () => {
    if (disabled) {
      toast.error($i18n.t('You do not have permission to edit this widget.'));
      return;
    }

    if (jsonError) {
      toast.error($i18n.t('Invalid JSON: ') + jsonError);
      return;
    }

    loading = true;
    content = _content; // Sync back to exported variable
    await onSubmit({
      id,
      name,
      description,
      content,
      is_active: true,
      meta: { tags: [] },
      access_grants: accessGrants,
    });

    loading = false;
  };

  onMount(async () => {
    if (widget) {
      name = widget.name || '';
      await tick();
      id = widget.id || '';
      description = widget.description || '';
      content = widget.content || '{}';
      _content = content;
      accessGrants = widget?.access_grants === undefined ? [] : widget?.access_grants;

      if (name) hasManualName = true;
      if (description) hasManualDescription = true;
      if (id) hasManualEdit = true;
    }
  });

  let showSyncBadge = false;
  let syncTimeout = null;

  const handleAiApply = (newJson: string) => {
    _content = newJson;
    content = newJson;

    showSyncBadge = true;
    if (syncTimeout) clearTimeout(syncTimeout);
    syncTimeout = setTimeout(() => {
      showSyncBadge = false;
      syncTimeout = null;
    }, 2000);
  };
</script>

<AccessControlModal
  bind:show={showAccessControlModal}
  bind:accessGrants
  accessRoles={['read', 'write']}
  share={$user?.permissions?.sharing?.widgets || $user?.role === 'admin'}
  sharePublic={$user?.permissions?.sharing?.public_widgets || $user?.role === 'admin'}
  shareUsers={($user?.permissions?.access_grants?.allow_users ?? true) || $user?.role === 'admin'}
  onChange={async () => {
    if (edit && widget?.id) {
      try {
        await updateWidgetAccessGrants(localStorage.token, widget.id, accessGrants);
        toast.success($i18n.t('Saved'));
      } catch (error) {
        toast.error(`${error}`);
      }
    }
  }}
/>

<div class="flex h-full w-full flex-col">
  <PaneGroup direction="horizontal">
    <!-- Main Content -->
    <Pane defaultSize={70} maxSize={70} minSize={50}>
      <div class="flex h-full w-full flex-col overflow-hidden bg-white dark:bg-gray-900">
        <!-- Header -->
        <div class="border-b border-gray-50 bg-white p-4 dark:border-gray-800 dark:bg-gray-900">
          <div class="flex items-center justify-between gap-4">
            <div class="flex items-center gap-2 overflow-hidden">
              <Tooltip content={$i18n.t('Back')}>
                <button
                  class="rounded-lg p-1.5 hover:bg-gray-50 dark:hover:bg-gray-800"
                  on:click={() => {
                    const returnTo = $page.url.searchParams.get('returnTo');
                    goto(returnTo || '/workspace/widgets');
                  }}
                >
                  <ChevronLeft strokeWidth="2.5" className="size-5" />
                </button>
              </Tooltip>

              <div class="flex flex-col gap-0.5 overflow-hidden">
                <input
                  class="w-full bg-transparent text-lg font-semibold outline-hidden"
                  placeholder={$i18n.t('Widget Name')}
                  bind:value={name}
                  on:input={() => (hasManualName = true)}
                  {disabled}
                />
                <div class="flex items-center gap-2 text-xs text-gray-400">
                  <span class="shrink-0">{id || 'widget-id'}</span>
                  <span class="text-gray-200 dark:text-gray-700">|</span>
                  <input
                    class="w-full bg-transparent outline-hidden"
                    placeholder={$i18n.t('Brief description...')}
                    bind:value={description}
                    on:input={() => (hasManualDescription = true)}
                    {disabled}
                  />
                </div>
              </div>
            </div>

            <div class="flex shrink-0 items-center gap-2">
              <button
                class="dark:bg-gray-850 flex items-center gap-1.5 rounded-full border border-gray-100 bg-gray-50 px-3 py-1.5 text-sm font-medium transition hover:bg-gray-100 dark:border-gray-800 dark:hover:bg-gray-800"
                on:click={() => (showAiSidebar = !showAiSidebar)}
              >
                <Sparkles className="size-3.5 text-blue-500" />
                <span>{$i18n.t('AI Generator')}</span>
              </button>

              <button
                class="dark:bg-gray-850 flex items-center gap-1.5 rounded-full border border-gray-100 bg-gray-50 px-3 py-1.5 text-sm font-medium transition hover:bg-gray-100 dark:border-gray-800 dark:hover:bg-gray-800"
                on:click={() => (showAccessControlModal = true)}
              >
                <LockClosed strokeWidth="2.5" className="size-3.5" />
                <span>{$i18n.t('Access')}</span>
              </button>

              {#if !disabled}
                <button
                  class="rounded-full bg-black px-4 py-1.5 text-sm font-medium text-white transition hover:bg-gray-900 dark:bg-white dark:text-black dark:hover:bg-gray-100"
                  on:click={submitHandler}
                  disabled={loading}
                >
                  {#if loading}
                    <Spinner className="size-4" />
                  {:else}
                    {$i18n.t('Save')}
                  {/if}
                </button>
              {/if}
            </div>
          </div>
        </div>

        <!-- Editor & Preview Body -->
        <div class="flex flex-1 overflow-hidden">
          <PaneGroup direction="horizontal">
            <!-- Editor Section -->
            <Pane defaultSize={50} minSize={20}>
              <div class="flex h-full flex-col border-r border-gray-50 dark:border-gray-800">
                <div
                  class="flex items-center justify-between border-b border-gray-50 bg-gray-50/50 px-4 py-2 dark:border-gray-800 dark:bg-gray-900/50"
                >
                  <div class="flex items-center gap-2">
                    <span class="text-xs font-medium tracking-wider text-gray-500 uppercase"
                      >{$i18n.t('JSON Schema')}</span
                    >
                    {#if showSyncBadge}
                      <span
                        class="flex animate-pulse items-center gap-1.5 rounded-full bg-blue-500/10 px-2 py-0.5 text-[9px] font-bold text-blue-500 transition"
                      >
                        <div class="size-1 rounded-full bg-blue-500"></div>
                        {$i18n.t('Live Sync')}
                      </span>
                    {/if}
                  </div>
                  {#if jsonError}
                    <span class="max-w-[200px] truncate font-mono text-[10px] text-red-500"
                      >{jsonError}</span
                    >
                  {/if}
                </div>
                <div class="flex-1 overflow-hidden">
                  <CodeEditor
                    bind:this={codeEditor}
                    bind:value={_content}
                    lang="json"
                    id="widget-editor"
                    onChange={(v) => (_content = v)}
                    onSave={submitHandler}
                  />
                </div>
              </div>
            </Pane>

            <PaneResizer
              class="w-1 bg-transparent transition hover:bg-gray-100 dark:hover:bg-gray-800"
            />

            <!-- Preview Section -->
            <Pane defaultSize={50} minSize={20}>
              <div class="flex h-full flex-col bg-gray-50 dark:bg-gray-950/50">
                <div
                  class="flex items-center justify-between border-b border-gray-50 bg-gray-50/50 px-4 py-2 dark:border-gray-800 dark:bg-gray-900/50"
                >
                  <span class="text-xs font-medium tracking-wider text-gray-500 uppercase"
                    >{$i18n.t('Live Preview')}</span
                  >
                </div>
                <div
                  class="flex-1 overflow-auto bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] [background-size:16px_16px] p-8 dark:bg-[radial-gradient(#1f2937_1px,transparent_1px)]"
                >
                  <WidgetMapper content={_content} />
                </div>
              </div>
            </Pane>
          </PaneGroup>
        </div>
      </div>
    </Pane>

    {#if showAiSidebar}
      <PaneResizer class="w-0.5 bg-gray-100 dark:bg-gray-800" />
      <Pane defaultSize={30} minSize={20}>
        <WidgetChatSidebar
          onClose={() => (showAiSidebar = false)}
          onApply={handleAiApply}
          currentJson={_content}
        />
      </Pane>
    {/if}
  </PaneGroup>
</div>

<style>
  :global(.paneforge-group) {
    height: 100%;
  }

  /* Optional: any specific styles if needed */
</style>
