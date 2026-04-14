<script lang="ts">
  import { getContext, createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher();
  const i18n = getContext('i18n');

  import Dropdown from '$lib/components/common/Dropdown.svelte';
  import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';

  let show = false;
</script>

<Dropdown bind:show>
  <Tooltip content={$i18n.t('More')}>
    <slot />
  </Tooltip>

  <div slot="content">
    <div
      class="dark:bg-gray-850 z-50 min-w-[150px] rounded-xl bg-white p-1 shadow-lg dark:text-white"
    >
      <button
        class="flex w-full cursor-pointer items-center gap-2 rounded-md px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
        on:click={() => {
          dispatch('delete');
          show = false;
        }}
      >
        <GarbageBin strokeWidth="2" />
        <div class="flex items-center">{$i18n.t('Delete')}</div>
      </button>
    </div>
  </div>
</Dropdown>
