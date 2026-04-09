<script lang="ts">
  import { getContext } from 'svelte';

  import Dropdown from '$lib/components/common/Dropdown.svelte';
  import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
  import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import EllipsisHorizontal from '$lib/components/icons/EllipsisHorizontal.svelte';

  const i18n = getContext('i18n');

  export let isProduction = false;
  export let onDelete: Function;
  export let onClose: Function;

  let show = false;
  let showDeleteConfirmDialog = false;
</script>

<ConfirmDialog
  bind:show={showDeleteConfirmDialog}
  title={$i18n.t('Delete Version')}
  message={$i18n.t(
    "Are you sure you want to delete this version? Child versions will be relinked to this version's parent.",
  )}
  confirmLabel={$i18n.t('Delete')}
  onConfirm={() => {
    onDelete();
  }}
/>

<Dropdown
  bind:show
  onOpenChange={(state) => {
    if (state === false) {
      onClose();
    }
  }}
>
  <Tooltip content={$i18n.t('More')}>
    <slot>
      <button
        class="dark:hover:bg-gray-850 rounded-lg p-1 text-gray-500 transition hover:bg-gray-50"
        aria-label={$i18n.t('More Options')}
      >
        <EllipsisHorizontal className="size-5" />
      </button>
    </slot>
  </Tooltip>

  <div slot="content">
    <div
      class="dark:bg-gray-850 z-50 min-w-[170px] rounded-2xl border border-gray-100 bg-white p-1 shadow-lg dark:border-gray-800 dark:text-white"
    >
      {#if isProduction}
        <Tooltip content={$i18n.t('Cannot delete the production version')} placement="top">
          <div
            class="flex cursor-not-allowed items-center gap-2 rounded-xl px-3 py-1.5 text-sm opacity-40"
          >
            <GarbageBin />
            <div class="flex items-center">{$i18n.t('Delete')}</div>
          </div>
        </Tooltip>
      {:else}
        <button
          class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
          on:click={() => {
            show = false;
            showDeleteConfirmDialog = true;
          }}
        >
          <GarbageBin />
          <div class="flex items-center">{$i18n.t('Delete')}</div>
        </button>
      {/if}
    </div>
  </div>
</Dropdown>
