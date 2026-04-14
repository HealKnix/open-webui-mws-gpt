<script lang="ts">
  import { getContext, tick } from 'svelte';

  import { activeMcpApp } from '$lib/stores';
  import { getMcpApps } from '$lib/apis/mcp_apps';

  import Dropdown from '$lib/components/common/Dropdown.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Bolt from '$lib/components/icons/Bolt.svelte';
  import Check from '$lib/components/icons/Check.svelte';

  const i18n = getContext('i18n');

  export let onClose: Function = () => {};

  let show = false;
  let apps = [];
  let loading = false;

  $: if (show) {
    loadApps();
  }

  const loadApps = async () => {
    loading = true;
    try {
      const result = await getMcpApps(localStorage.token);
      if (result) {
        apps = result.filter((app) => app.is_active);
      }
    } catch (e) {
      console.error('Failed to load MCP apps:', e);
    } finally {
      loading = false;
    }
  };

  const selectApp = async (app) => {
    if ($activeMcpApp?.id === app.id) {
      $activeMcpApp = null;
    } else {
      $activeMcpApp = app;
    }
    show = false;
    await tick();
    onClose();
  };
</script>

<Dropdown
  bind:show
  onOpenChange={(state) => {
    if (state === false) {
      onClose();
    }
  }}
>
  <Tooltip content={$i18n.t('MCP Apps')} placement="top">
    <slot />
  </Tooltip>
  <div slot="content">
    <div
      class="dark:bg-gray-850 scrollbar-thin z-50 max-h-72 max-w-70 min-w-70 overflow-x-hidden overflow-y-auto rounded-2xl border border-gray-100 bg-white px-1 py-1 shadow-lg dark:border-gray-800 dark:text-white"
    >
      {#if loading}
        <div class="flex items-center justify-center py-4">
          <div
            class="size-4 animate-spin rounded-full border-2 border-gray-300 border-t-gray-600"
          ></div>
        </div>
      {:else if apps.length === 0}
        <div class="px-3 py-3 text-center text-xs text-gray-500">
          {$i18n.t('No MCP Apps available')}
        </div>
      {:else}
        {#each apps as app (app.id)}
          <button
            class="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-left text-sm transition-colors hover:bg-gray-50 dark:hover:bg-gray-800"
            on:click={() => selectApp(app)}
          >
            <div
              class="flex size-7 shrink-0 items-center justify-center rounded-lg bg-gray-100 text-base dark:bg-gray-700"
            >
              {#if app.icon}
                {app.icon}
              {:else}
                <Bolt className="size-3.5" strokeWidth="1.75" />
              {/if}
            </div>
            <div class="min-w-0 flex-1">
              <div class="truncate font-medium">{app.name}</div>
              {#if app.description}
                <div class="truncate text-xs text-gray-500 dark:text-gray-400">
                  {app.description}
                </div>
              {/if}
            </div>
            {#if $activeMcpApp?.id === app.id}
              <Check className="size-4 shrink-0 text-emerald-500" />
            {/if}
          </button>
        {/each}
      {/if}
    </div>
  </div>
</Dropdown>
