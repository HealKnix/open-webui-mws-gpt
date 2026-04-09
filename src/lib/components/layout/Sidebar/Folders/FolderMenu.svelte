<script lang="ts">
  import { getContext, createEventDispatcher } from 'svelte';

  const i18n = getContext('i18n');
  const dispatch = createEventDispatcher();

  import Dropdown from '$lib/components/common/Dropdown.svelte';
  import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
  import Pencil from '$lib/components/icons/Pencil.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Download from '$lib/components/icons/Download.svelte';
  import Folder from '$lib/components/icons/Folder.svelte';

  export let align: 'start' | 'end' = 'start';
  export let onEdit = () => {};
  export let onExport = () => {};
  export let onDelete = () => {};
  export let onCreateSub = () => {};

  let show = false;
</script>

<Dropdown
  bind:show
  {align}
  onOpenChange={(state) => {
    if (state === false) {
      dispatch('close');
    }
  }}
>
  <Tooltip content={$i18n.t('More')}>
    <button
      on:click={(e) => {
        e.stopPropagation();
        show = !show;
      }}
    >
      <slot />
    </button>
  </Tooltip>

  <div slot="content">
    <div
      class="dark:bg-gray-850 z-50 min-w-[170px] rounded-2xl border border-gray-100 bg-white px-1 py-1 shadow-lg dark:border-gray-800 dark:text-white"
    >
      <button
        class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
        on:click={() => {
          onCreateSub();
        }}
      >
        <Folder />
        <div class="flex items-center">{$i18n.t('Create Folder')}</div>
      </button>

      <hr class="my-1 border-gray-50/30 dark:border-gray-800/30" />

      <button
        class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
        on:click={() => {
          onEdit();
        }}
      >
        <Pencil />
        <div class="flex items-center">{$i18n.t('Edit')}</div>
      </button>

      <button
        class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
        on:click={() => {
          onExport();
        }}
      >
        <Download />
        <div class="flex items-center">{$i18n.t('Export')}</div>
      </button>

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
