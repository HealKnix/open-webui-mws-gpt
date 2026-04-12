<script lang="ts">
  import { getContext } from 'svelte';
  const i18n = getContext('i18n');

  import Skeleton from '$lib/components/chat/Messages/Skeleton.svelte';
  import Markdown from '$lib/components/chat/Messages/Markdown.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import CheckCircle from '$lib/components/icons/CheckCircle.svelte';

  export let message;
  export let idx;
  export let onDelete;

  // Filter out code blocks from the displayed content to keep chat clean
  $: displayContent = message.content
    .replace(/```[\s\S]*?```/g, '') // Remove full blocks
    .replace(/```[\s\S]*/g, '') // Remove partial trailing block
    .trim();
</script>

<div class="group flex flex-col gap-1.5">
  <div class="flex items-center justify-between">
    <div class="rounded-lg text-left text-[10px] font-bold tracking-widest text-gray-400 uppercase">
      {$i18n.t(message.role === 'user' ? 'You' : 'Assistant')}
    </div>

    <div class="flex items-center gap-2 opacity-0 transition-opacity group-hover:opacity-100">
      <Tooltip placement="top" content={$i18n.t('Delete')}>
        <button class="text-gray-400 transition-colors hover:text-red-500" on:click={onDelete}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="2.5"
            stroke="currentColor"
            class="size-3.5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M15 12H9m12 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
            />
          </svg>
        </button>
      </Tooltip>
    </div>
  </div>

  <div class="flex-1">
    {#if !(message?.done ?? true) && message?.content === ''}
      <Skeleton size="sm" />
    {:else}
      <div
        class="markdown-prose-sm text-sm {message.role === 'assistant'
          ? 'rounded-2xl border border-gray-100/50 bg-gray-50/50 p-3 dark:border-gray-800/50 dark:bg-gray-800/30'
          : ''}"
      >
        <Markdown id={`widget-message-${idx}`} content={displayContent} />

        {#if message.role === 'assistant'}
          {#if message.done ?? true}
            <div
              class="mt-4 flex items-center gap-2 text-[10px] font-bold tracking-widest text-green-500 uppercase dark:text-green-400"
            >
              <CheckCircle className="size-3" />
              <span>{$i18n.t('Generation Finished')}</span>
            </div>
          {:else}
            <div
              class="mt-4 flex animate-pulse items-center gap-2 text-[10px] font-bold tracking-widest text-blue-500 uppercase dark:text-blue-400"
            >
              <div class="size-1.5 rounded-full bg-blue-500"></div>
              <span>{$i18n.t('Syncing with editor...')}</span>
            </div>
          {/if}
        {/if}
      </div>
    {/if}
  </div>
</div>
