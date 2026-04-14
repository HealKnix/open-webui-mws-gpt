<script lang="ts">
  import { getContext, createEventDispatcher } from 'svelte';

  const i18n = getContext('i18n');
  const dispatch = createEventDispatcher();

  import Dropdown from '$lib/components/common/Dropdown.svelte';

  export let onClose: Function = () => {};
  export let devices: any;

  let show = false;
</script>

<Dropdown
  bind:show
  side="top"
  sideOffset={6}
  onOpenChange={(state) => {
    if (state === false) {
      onClose();
    }
  }}
>
  <slot />

  <div slot="content">
    <div
      class="z-[9999] min-w-[180px] rounded-lg border border-gray-100 bg-white p-1 shadow-xs dark:border-gray-800 dark:bg-gray-900 dark:text-white"
    >
      {#each devices as device}
        <button
          class="flex w-full cursor-pointer items-center gap-2 rounded-md px-3 py-1.5 text-sm hover:bg-gray-50 dark:hover:bg-gray-800"
          on:click={() => {
            dispatch('change', device.deviceId);
          }}
        >
          <div class="flex items-center">
            <div class=" line-clamp-1">
              {device?.label ?? 'Camera'}
            </div>
          </div>
        </button>
      {/each}
    </div>
  </div>
</Dropdown>
