<script lang="ts">
  import { getContext, createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  import Dropdown from '$lib/components/common/Dropdown.svelte';
  import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Download from '$lib/components/icons/Download.svelte';
  import EllipsisHorizontal from '$lib/components/icons/EllipsisHorizontal.svelte';

  const i18n = getContext('i18n');

  export let onExport: null | Function = null;
  export let onClose: Function = () => {};

  let show = false;
</script>

<Dropdown
  bind:show
  align="end"
  onOpenChange={(state) => {
    if (state === false) {
      onClose();
    }
  }}
>
  <Tooltip content={$i18n.t('More')}>
    <slot
      ><button
        class="w-fit self-center rounded-xl p-1.5 text-sm hover:bg-black/5 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white"
        type="button"
        aria-label={$i18n.t('More Options')}
        on:click={(e) => {
          e.stopPropagation();
          show = true;
        }}
      >
        <EllipsisHorizontal className="size-5" />
      </button>
    </slot>
  </Tooltip>

  <div slot="content">
    <div
      class="dark:bg-gray-850 z-50 min-w-[170px] rounded-2xl border border-gray-100 bg-white px-1 py-1 shadow-lg dark:border-gray-800 dark:text-white"
    >
      {#if onExport}
        <button
          class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
          on:click={() => {
            onExport();
          }}
        >
          <Download />
          <div class="flex items-center">{$i18n.t('Export')}</div>
        </button>
      {/if}

      <button
        class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
        on:click={() => {
          dispatch('delete');
        }}
      >
        <GarbageBin />
        <div class="flex items-center">{$i18n.t('Delete')}</div>
      </button>
    </div>
  </div>
</Dropdown>
