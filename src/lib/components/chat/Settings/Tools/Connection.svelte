<script lang="ts">
  import { getContext, tick } from 'svelte';
  const i18n = getContext('i18n');

  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Switch from '$lib/components/common/Switch.svelte';
  import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
  import Cog6 from '$lib/components/icons/Cog6.svelte';
  import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
  import AddToolServerModal from '$lib/components/AddToolServerModal.svelte';
  import WrenchAlt from '$lib/components/icons/WrenchAlt.svelte';

  export let onDelete = () => {};
  export let onSubmit = () => {};

  export let connection = null;
  export let direct = false;

  let showConfigModal = false;
  let showDeleteConfirmDialog = false;
</script>

<AddToolServerModal
  edit
  {direct}
  bind:show={showConfigModal}
  {connection}
  onDelete={() => {
    showDeleteConfirmDialog = true;
  }}
  onSubmit={(c) => {
    connection = c;
    onSubmit(c);
  }}
/>

<ConfirmDialog
  bind:show={showDeleteConfirmDialog}
  on:confirm={() => {
    onDelete();
    showConfigModal = false;
  }}
/>

<div class="flex w-full items-center gap-2">
  <Tooltip className="w-full relative" content={''} placement="top-start">
    <div class="flex w-full">
      <div
        class="relative flex flex-1 items-center gap-1.5 {!(connection?.config?.enable ?? true)
          ? 'opacity-50'
          : ''}"
      >
        <Tooltip content={connection?.type === 'mcp' ? $i18n.t('MCP') : $i18n.t('OpenAPI')}>
          <WrenchAlt />
        </Tooltip>

        {#if connection?.info?.name}
          <div class=" w-full bg-transparent capitalize outline-hidden">
            {connection?.info?.name ?? connection?.url}
            <span class="text-gray-500">{connection?.info?.id ?? ''}</span>
          </div>
        {:else}
          <div>
            {connection?.url}
          </div>
        {/if}
      </div>
    </div>
  </Tooltip>

  <div class="flex items-center gap-1">
    <Tooltip content={$i18n.t('Configure')} className="self-start">
      <button
        class="dark:hover:bg-gray-850 self-center rounded-lg bg-transparent p-1 transition hover:bg-gray-100"
        on:click={() => {
          showConfigModal = true;
        }}
        type="button"
      >
        <Cog6 />
      </button>
    </Tooltip>

    <Tooltip
      content={(connection?.config?.enable ?? true) ? $i18n.t('Enabled') : $i18n.t('Disabled')}
    >
      <Switch
        state={connection?.config?.enable ?? true}
        on:change={() => {
          if (!connection.config) connection.config = {};
          connection.config.enable = !(connection?.config?.enable ?? true);
          onSubmit(connection);
        }}
      />
    </Tooltip>
  </div>
</div>
