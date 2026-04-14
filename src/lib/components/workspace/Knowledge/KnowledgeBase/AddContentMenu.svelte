<script lang="ts">
  import { getContext, createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  import Dropdown from '$lib/components/common/Dropdown.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import ArrowUpCircle from '$lib/components/icons/ArrowUpCircle.svelte';
  import BarsArrowUp from '$lib/components/icons/BarsArrowUp.svelte';
  import FolderOpen from '$lib/components/icons/FolderOpen.svelte';
  import ArrowPath from '$lib/components/icons/ArrowPath.svelte';
  import GlobeAlt from '$lib/components/icons/GlobeAlt.svelte';

  const i18n = getContext('i18n');

  export let onClose: Function = () => {};

  export let onSync: Function = () => {};
  export let onUpload: Function = (data) => {};

  let show = false;
</script>

<Dropdown
  bind:show
  onOpenChange={(state) => {
    if (state === false) {
      onClose();
    }
  }}
  align="end"
>
  <Tooltip content={$i18n.t('Add Content')}>
    <button
      class=" dark:bg-gray-850 flex items-center space-x-1 rounded-xl p-1.5 text-sm font-medium transition hover:bg-gray-100 dark:hover:bg-gray-800"
      on:click={(e) => {
        e.stopPropagation();
        show = true;
      }}
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 16 16"
        fill="currentColor"
        class="h-4 w-4"
      >
        <path
          d="M8.75 3.75a.75.75 0 0 0-1.5 0v3.5h-3.5a.75.75 0 0 0 0 1.5h3.5v3.5a.75.75 0 0 0 1.5 0v-3.5h3.5a.75.75 0 0 0 0-1.5h-3.5v-3.5Z"
        />
      </svg>
    </button>
  </Tooltip>

  <div slot="content">
    <div
      class="dark:bg-gray-850 z-50 min-w-[200px] rounded-2xl border border-gray-100 bg-white px-1 py-1 shadow-lg transition dark:border-gray-800 dark:text-white"
    >
      <button
        class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
        on:click={() => {
          onUpload({ type: 'files' });
        }}
      >
        <ArrowUpCircle strokeWidth="2" />
        <div class="flex items-center">{$i18n.t('Upload files')}</div>
      </button>

      <button
        class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
        on:click={() => {
          onUpload({ type: 'directory' });
        }}
      >
        <FolderOpen strokeWidth="2" />
        <div class="flex items-center">{$i18n.t('Upload directory')}</div>
      </button>

      <Tooltip
        content={$i18n.t(
          'This option will delete all existing files in the collection and replace them with newly uploaded files.',
        )}
        className="w-full"
      >
        <button
          class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
          on:click={() => {
            onSync();
          }}
        >
          <ArrowPath strokeWidth="2" />
          <div class="flex items-center">{$i18n.t('Sync directory')}</div>
        </button>
      </Tooltip>

      <button
        class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
        on:click={() => {
          onUpload({ type: 'web' });
        }}
      >
        <GlobeAlt strokeWidth="2" />
        <div class="flex items-center">{$i18n.t('Add webpage')}</div>
      </button>

      <button
        class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
        on:click={() => {
          onUpload({ type: 'text' });
        }}
      >
        <BarsArrowUp strokeWidth="2" />
        <div class="flex items-center">{$i18n.t('Add text content')}</div>
      </button>
    </div>
  </div>
</Dropdown>
