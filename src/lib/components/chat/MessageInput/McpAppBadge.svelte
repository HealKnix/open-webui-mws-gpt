<script lang="ts">
  import { getContext } from 'svelte';

  import { activeMcpApp } from '$lib/stores';

  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Bolt from '$lib/components/icons/Bolt.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';

  const i18n = getContext('i18n');
</script>

{#if $activeMcpApp}
  <Tooltip content={$activeMcpApp.description ?? $activeMcpApp.name} placement="top">
    <button
      on:click|preventDefault={() => {
        $activeMcpApp = null;
      }}
      type="button"
      class="group flex max-w-full items-center gap-1.5 overflow-hidden rounded-full border border-emerald-200/40 bg-emerald-50 px-2 py-[5px] text-sm text-emerald-600 transition-colors duration-300 hover:bg-emerald-100 focus:outline-hidden dark:border-emerald-500/20 dark:bg-emerald-400/10 dark:text-emerald-400 dark:hover:bg-emerald-600/10"
    >
      {#if $activeMcpApp.icon}
        <span class="text-sm leading-none">{$activeMcpApp.icon}</span>
      {:else}
        <Bolt className="size-3.5" strokeWidth="1.75" />
      {/if}

      <span class="max-w-24 truncate text-xs font-medium">{$activeMcpApp.name}</span>

      <div class="hidden group-hover:block">
        <XMark className="size-3.5" strokeWidth="1.75" />
      </div>
    </button>
  </Tooltip>
{/if}
