<script lang="ts">
  import { getContext } from 'svelte';

  import Dropdown from '$lib/components/common/Dropdown.svelte';
  import DropdownSub from '$lib/components/common/DropdownSub.svelte';
  import Download from '$lib/components/icons/Download.svelte';
  import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
  import DocumentDuplicate from '$lib/components/icons/DocumentDuplicate.svelte';
  import Share from '$lib/components/icons/Share.svelte';
  import Link from '$lib/components/icons/Link.svelte';

  const i18n = getContext('i18n');

  export let show = false;
  export let className = 'max-w-[180px]';

  export let onDownload = (type) => {};
  export let onDelete = () => {};

  export let onCopyLink = null;
  export let onCopyToClipboard = null;

  export let onChange = () => {};
</script>

<Dropdown
  bind:show
  align="end"
  sideOffset={6}
  onOpenChange={(state) => {
    onChange(state);
  }}
>
  <slot />

  <div slot="content">
    <div
      class="dark:bg-gray-850 z-50 min-w-[180px] rounded-2xl border border-gray-100 bg-white px-1 py-1 text-sm shadow-lg dark:border-gray-800 dark:text-white"
    >
      <DropdownSub>
        <button
          slot="trigger"
          class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm hover:bg-gray-50 dark:hover:bg-gray-800"
        >
          <Download strokeWidth="2" />
          <div class="flex items-center">{$i18n.t('Download')}</div>
        </button>

        <button
          class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
          on:click={() => {
            onDownload('txt');
          }}
        >
          <div class="line-clamp-1 flex items-center">{$i18n.t('Plain text (.txt)')}</div>
        </button>

        <button
          class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
          on:click={() => {
            onDownload('md');
          }}
        >
          <div class="line-clamp-1 flex items-center">{$i18n.t('Plain text (.md)')}</div>
        </button>

        <button
          class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
          on:click={() => {
            onDownload('pdf');
          }}
        >
          <div class="line-clamp-1 flex items-center">{$i18n.t('PDF document (.pdf)')}</div>
        </button>
      </DropdownSub>

      {#if onCopyLink || onCopyToClipboard}
        <DropdownSub>
          <button
            slot="trigger"
            class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm hover:bg-gray-50 dark:hover:bg-gray-800"
          >
            <Share strokeWidth="2" />
            <div class="flex items-center">{$i18n.t('Share')}</div>
          </button>

          {#if onCopyLink}
            <button
              class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
              on:click={() => {
                onCopyLink();
              }}
            >
              <Link />
              <div class="flex items-center">{$i18n.t('Copy link')}</div>
            </button>
          {/if}

          {#if onCopyToClipboard}
            <button
              class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
              on:click={() => {
                onCopyToClipboard();
              }}
            >
              <DocumentDuplicate strokeWidth="2" />
              <div class="flex items-center">{$i18n.t('Copy to clipboard')}</div>
            </button>
          {/if}
        </DropdownSub>
      {/if}

      <button
        class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
        on:click={() => {
          onDelete();
        }}
      >
        <GarbageBin />
        <div class="flex items-center">{$i18n.t('Delete')}</div>
      </button>
    </div>
  </div>
</Dropdown>
