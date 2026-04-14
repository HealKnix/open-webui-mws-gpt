<script lang="ts">
  import { toast } from 'svelte-sonner';
  import { onMount, getContext } from 'svelte';

  const i18n = getContext('i18n');

  import { WEBUI_NAME, user, mcpApps as _mcpApps } from '$lib/stores';
  import { goto } from '$app/navigation';
  import { getMcpApps, deleteMcpAppById, toggleMcpAppById } from '$lib/apis/mcp_apps';
  import { capitalizeFirstLetter } from '$lib/utils';

  import Tooltip from '../common/Tooltip.svelte';
  import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
  import EllipsisHorizontal from '../icons/EllipsisHorizontal.svelte';
  import GarbageBin from '../icons/GarbageBin.svelte';
  import Search from '../icons/Search.svelte';
  import Plus from '../icons/Plus.svelte';
  import XMark from '../icons/XMark.svelte';
  import Spinner from '../common/Spinner.svelte';
  import Badge from '$lib/components/common/Badge.svelte';
  import Switch from '../common/Switch.svelte';
  import McpAppMenu from './McpApps/McpAppMenu.svelte';

  let shiftKey = false;
  let loaded = false;

  let query = '';
  let apps = [];
  let loading = false;

  let selectedApp = null;
  let showDeleteConfirm = false;

  const loadApps = async () => {
    loading = true;
    try {
      const res = await getMcpApps(localStorage.token);
      if (res) {
        apps = res;
      }
    } catch (error) {
      toast.error(`${error}`);
    } finally {
      loading = false;
    }
  };

  $: filteredApps = apps.filter((app) => {
    if (!query) return true;
    const q = query.toLowerCase();
    return app.name?.toLowerCase().includes(q) || app.description?.toLowerCase().includes(q);
  });

  const deleteHandler = async (app) => {
    const res = await deleteMcpAppById(localStorage.token, app.id).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    if (res) {
      toast.success($i18n.t('MCP App deleted successfully'));
    }

    await loadApps();
    _mcpApps.set(apps);
  };

  const transportLabel = (transport) => {
    switch (transport) {
      case 'http_streamable':
        return 'HTTP';
      case 'sse':
        return 'SSE';
      case 'stdio':
        return 'stdio';
      default:
        return transport;
    }
  };

  onMount(async () => {
    loaded = true;
    await loadApps();

    const onKeyDown = (event) => {
      if (event.key === 'Shift') shiftKey = true;
    };
    const onKeyUp = (event) => {
      if (event.key === 'Shift') shiftKey = false;
    };
    const onBlur = () => {
      shiftKey = false;
    };

    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('keyup', onKeyUp);
    window.addEventListener('blur-sm', onBlur);

    return () => {
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('keyup', onKeyUp);
      window.removeEventListener('blur-sm', onBlur);
    };
  });
</script>

<svelte:head>
  <title>
    {$i18n.t('MCP Apps')} • {$WEBUI_NAME}
  </title>
</svelte:head>

{#if loaded}
  <div class="mt-1.5 mb-3 flex flex-col gap-1 px-1">
    <div class="flex items-center justify-between">
      <div class="flex shrink-0 items-center gap-2 px-0.5 text-xl font-medium md:self-center">
        <div>
          {$i18n.t('MCP Apps')}
        </div>

        <div class="text-lg font-medium text-gray-500 dark:text-gray-500">
          {apps.length || ''}
        </div>
      </div>

      <div class="flex w-full justify-end gap-1.5">
        {#if $user?.role === 'admin'}
          <a
            class="flex items-center rounded-xl bg-black px-2 py-1.5 text-sm font-medium text-white transition dark:bg-white dark:text-black"
            href="/workspace/mcpapps/create"
          >
            <Plus className="size-3" strokeWidth="2.5" />
            <div class="hidden text-xs md:ml-1 md:block">{$i18n.t('New MCP App')}</div>
          </a>
        {/if}
      </div>
    </div>
  </div>

  <div
    class="dark:border-gray-850/30 rounded-3xl border border-gray-100/30 bg-white py-2 dark:bg-gray-900"
  >
    <div class="flex w-full space-x-2 px-3.5 py-0.5 pb-2">
      <div class="flex flex-1">
        <div class="mr-3 ml-1 self-center">
          <Search className="size-3.5" />
        </div>
        <input
          class="w-full rounded-r-xl bg-transparent py-1 pr-4 text-sm outline-hidden"
          bind:value={query}
          aria-label={$i18n.t('Search MCP Apps')}
          placeholder={$i18n.t('Search MCP Apps')}
        />
        {#if query}
          <div class="translate-y-[0.5px] self-center rounded-l-xl bg-transparent pl-1.5">
            <button
              class="hover:bg-card-hover rounded-full p-0.5 transition"
              aria-label={$i18n.t('Clear search')}
              on:click={() => {
                query = '';
              }}
            >
              <XMark className="size-3" strokeWidth="2" />
            </button>
          </div>
        {/if}
      </div>
    </div>

    {#if loading}
      <div class="my-16 mb-24 flex h-full w-full items-center justify-center">
        <Spinner className="size-5" />
      </div>
    {:else if filteredApps.length !== 0}
      <div class="my-2 grid gap-2 px-3 lg:grid-cols-2">
        {#each filteredApps as app (app.id)}
          <Tooltip content={app.description ?? app.id}>
            <div
              class="dark:hover:bg-gray-850/50 flex w-full cursor-pointer space-x-4 rounded-2xl px-3 py-2.5 text-left transition hover:bg-gray-50"
            >
              <a
                class="flex w-full flex-1 cursor-pointer space-x-3.5"
                href={`/workspace/mcpapps/edit?id=${encodeURIComponent(app.id)}`}
              >
                <div
                  class="flex size-9 shrink-0 items-center justify-center rounded-lg bg-gray-100 text-lg dark:bg-gray-800"
                >
                  {app.icon || '⚡'}
                </div>
                <div class="flex items-center text-left">
                  <div class="flex-1 self-center">
                    <div class="flex items-center gap-2">
                      <div class="line-clamp-1 text-sm font-medium">
                        {app.name}
                      </div>
                      <Badge type="info" content={transportLabel(app.transport)} />
                      {#if !app.is_active}
                        <Badge type="muted" content={$i18n.t('Inactive')} />
                      {/if}
                    </div>
                    <div class="px-0.5">
                      <div class="line-clamp-1 shrink-0 text-xs text-gray-500">
                        {app.description || app.url || app.command || ''}
                      </div>
                    </div>
                  </div>
                </div>
              </a>

              <div class="flex flex-row gap-0.5 self-center">
                {#if shiftKey}
                  <Tooltip content={$i18n.t('Delete')}>
                    <button
                      class="w-fit self-center rounded-xl px-2 py-2 text-sm hover:bg-black/5 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white"
                      type="button"
                      aria-label={$i18n.t('Delete')}
                      on:click|preventDefault|stopPropagation={() => {
                        deleteHandler(app);
                      }}
                    >
                      <GarbageBin />
                    </button>
                  </Tooltip>
                {:else}
                  <McpAppMenu
                    editHandler={() => {
                      goto(`/workspace/mcpapps/edit?id=${encodeURIComponent(app.id)}`);
                    }}
                    deleteHandler={async () => {
                      selectedApp = app;
                      showDeleteConfirm = true;
                    }}
                    onClose={() => {}}
                  >
                    <button
                      class="w-fit self-center rounded-xl p-1.5 text-sm hover:bg-black/5 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white"
                      type="button"
                      on:click|preventDefault|stopPropagation
                    >
                      <EllipsisHorizontal className="size-5" />
                    </button>
                  </McpAppMenu>
                {/if}

                <button on:click|stopPropagation|preventDefault>
                  <Tooltip content={app.is_active ? $i18n.t('Enabled') : $i18n.t('Disabled')}>
                    <Switch
                      bind:state={app.is_active}
                      on:change={async () => {
                        toggleMcpAppById(localStorage.token, app.id);
                      }}
                    />
                  </Tooltip>
                </button>
              </div>
            </div>
          </Tooltip>
        {/each}
      </div>
    {:else}
      <div class="my-16 mb-24 flex h-full w-full flex-col items-center justify-center">
        <div class="max-w-md text-center">
          <div class="mb-3 text-3xl">⚡</div>
          <div class="mb-1 text-lg font-medium">{$i18n.t('No MCP Apps found')}</div>
          <div class="text-center text-xs text-gray-500">
            {#if query}
              {$i18n.t('Try adjusting your search or filter to find what you are looking for.')}
            {:else}
              {$i18n.t('Create your first MCP App to get started.')}
            {/if}
          </div>
        </div>
      </div>
    {/if}
  </div>

  <ConfirmDialog
    bind:show={showDeleteConfirm}
    title={$i18n.t('Delete MCP App?')}
    on:confirm={() => {
      deleteHandler(selectedApp);
    }}
  >
    <div class="truncate text-sm text-gray-500">
      {$i18n.t('This will delete')} <span class="font-medium">{selectedApp?.name}</span>.
    </div>
  </ConfirmDialog>
{:else}
  <div class="flex h-full w-full items-center justify-center">
    <Spinner className="size-5" />
  </div>
{/if}
