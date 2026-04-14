<script lang="ts">
  import { getContext } from 'svelte';
  import { config, user } from '$lib/stores';

  import Dropdown from '$lib/components/common/Dropdown.svelte';
  import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Share from '$lib/components/icons/Share.svelte';
  import DocumentDuplicate from '$lib/components/icons/DocumentDuplicate.svelte';
  import Download from '$lib/components/icons/Download.svelte';

  const i18n = getContext('i18n');

  export let shareHandler: Function;
  export let cloneHandler: Function;
  export let exportHandler: Function;
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
      class="dark:bg-gray-850 z-50 min-w-[170px] rounded-2xl border border-gray-100 bg-white p-1 shadow-lg dark:border-gray-800 dark:text-white"
    >
      {#if $config.features.enable_community_sharing}
        <button
          class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
          on:click={() => {
            shareHandler();
          }}
        >
          <Share />
          <div class="flex items-center">{$i18n.t('Share')}</div>
        </button>
      {/if}

      <button
        class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
        on:click={() => {
          cloneHandler();
        }}
      >
        <DocumentDuplicate />
        <div class="flex items-center">{$i18n.t('Clone')}</div>
      </button>

      {#if $user?.role === 'admin' || $user?.permissions?.workspace?.prompts_export}
        <button
          class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
          on:click={() => {
            exportHandler();
          }}
        >
          <Download />
          <div class="flex items-center">{$i18n.t('Export')}</div>
        </button>
      {/if}

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
