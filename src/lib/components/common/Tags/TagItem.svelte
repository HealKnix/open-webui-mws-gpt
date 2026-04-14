<script>
  import { getContext } from 'svelte';

  const i18n = getContext('i18n');

  import XMark from '$lib/components/icons/XMark.svelte';

  export let tag;
  export let disabled = false;
  export let onDelete = () => {};
</script>

{#if tag}
  {#if disabled}
    <span
      class="flex items-center gap-1 rounded-full border border-gray-100 bg-gray-100/50 px-1.5 py-[1px] text-xs font-medium text-gray-600 dark:border-gray-800 dark:bg-gray-800/50 dark:text-gray-300"
    >
      <span class="line-clamp-1">{tag.name}</span>
    </span>
  {:else}
    <button
      type="button"
      class="flex items-center gap-1 rounded-full border border-gray-100 bg-gray-100/50 px-1.5 py-[1px] text-xs font-medium text-gray-600 transition-colors hover:bg-gray-100 dark:border-gray-800 dark:bg-gray-800/50 dark:text-gray-300 dark:hover:bg-gray-800"
      on:click={() => {
        onDelete();
      }}
    >
      <span class="line-clamp-1">{tag.name}</span>
      <XMark className="size-3" strokeWidth="2.5" />
    </button>
  {/if}
{/if}
