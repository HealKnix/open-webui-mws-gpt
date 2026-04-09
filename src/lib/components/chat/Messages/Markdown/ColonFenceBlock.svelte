<script lang="ts">
  import { getContext } from 'svelte';
  const i18n = getContext('i18n');

  import { copyToClipboard } from '$lib/utils';
  import { settings } from '$lib/stores';
  import MarkdownTokens from './MarkdownTokens.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import DocumentDuplicate from '$lib/components/icons/DocumentDuplicate.svelte';

  export let id: string = '';
  export let token: any;
  export let tokenIdx: number = 0;

  export let done: boolean = true;
  export let editCodeBlock: boolean = true;
  export let sourceIds: string[] = [];
  export let onTaskClick: Function = () => {};
  export let onSourceClick: Function = () => {};

  const fenceType: string = token.fenceType ?? 'default';

  const label = fenceType.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  let copied = false;

  const copyText = async () => {
    copied = true;
    await copyToClipboard(token.text, null, $settings?.copyFormatted ?? false);
    setTimeout(() => {
      copied = false;
    }, 1000);
  };
</script>

<div class="group relative my-2 rounded-2xl border border-gray-100 px-4 py-3 dark:border-gray-800">
  <!-- Header row: type badge + copy button -->
  <div class="mb-2 flex items-center justify-between">
    <span class="text-xs font-medium text-gray-500 dark:text-gray-400">
      {label}
    </span>

    <div class="invisible flex gap-0.5 group-hover:visible">
      <Tooltip content={copied ? $i18n.t('Copied') : $i18n.t('Copy')}>
        <button
          class="rounded-lg bg-transparent p-1 transition hover:bg-black/5 dark:hover:bg-white/5"
          on:click={(e) => {
            e.stopPropagation();
            copyText();
          }}
        >
          {#if copied}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="1.5"
              stroke="currentColor"
              class="size-3.5 text-green-500"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
            </svg>
          {:else}
            <DocumentDuplicate className="size-3.5" strokeWidth="1.5" />
          {/if}
        </button>
      </Tooltip>
    </div>
  </div>

  <!-- Content -->
  <div class="prose-sm" dir="auto">
    <MarkdownTokens
      id={`${id}-${tokenIdx}-cf`}
      tokens={token.tokens}
      {done}
      {editCodeBlock}
      {sourceIds}
      {onTaskClick}
      {onSourceClick}
    />
  </div>
</div>
