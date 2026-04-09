<script lang="ts">
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import { onMount, tick, getContext } from 'svelte';

  const i18n = getContext('i18n');

  export let followUps: string[] = [];
  export let onClick: (followUp: string) => void = () => {};
</script>

<div class="mt-4">
  <div class="text-sm font-medium">
    {$i18n.t('Follow up')}
  </div>

  <div class="mt-1.5 flex flex-col gap-1 text-left">
    {#each followUps as followUp, idx (idx)}
      <Tooltip content={followUp} placement="top-start" className="line-clamp-1">
        <button
          class=" flex w-full cursor-pointer items-center gap-2 bg-transparent py-1.5 text-left text-sm text-gray-500 transition hover:text-black dark:text-gray-400 dark:hover:text-white"
          on:click={() => onClick(followUp)}
          aria-label={$i18n.t('Follow up: {{question}}', { question: followUp })}
        >
          <div class="line-clamp-1">
            {followUp}
          </div>
        </button>
      </Tooltip>

      {#if idx < followUps.length - 1}
        <hr class="dark:border-gray-850/30 border-gray-50" />
      {/if}
    {/each}
  </div>
</div>
