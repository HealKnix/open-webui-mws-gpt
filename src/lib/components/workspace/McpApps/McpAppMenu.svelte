<script lang="ts">
  import { getContext } from 'svelte';

  import Dropdown from '$lib/components/common/Dropdown.svelte';
  import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';

  const i18n = getContext('i18n');

  export let editHandler: Function;
  export let deleteHandler: Function;
  export let onClose: Function;

  let show = false;
</script>

<Dropdown
  bind:show
  onOpenChange={(state) => {
    if (state === false) {
      onClose();
    }
  }}
>
  <Tooltip content={$i18n.t('More')}>
    <slot />
  </Tooltip>

  <div slot="content">
    <div
      class="dark:bg-gray-850 z-50 min-w-[170px] rounded-2xl border border-gray-100 bg-white px-1 py-1 shadow-lg dark:border-gray-800 dark:text-white"
    >
      <button
        class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
        on:click={() => {
          editHandler();
        }}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
          class="h-4 w-4"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L6.832 19.82a4.5 4.5 0 01-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 011.13-1.897L16.863 4.487zm0 0L19.5 7.125"
          />
        </svg>

        <div class="flex items-center">{$i18n.t('Edit')}</div>
      </button>

      <hr class="dark:border-gray-850/30 my-1 border-gray-50" />

      <button
        class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
        on:click={() => {
          deleteHandler();
        }}
      >
        <GarbageBin />
        <div class="flex items-center">{$i18n.t('Delete')}</div>
      </button>
    </div>
  </div>
</Dropdown>
