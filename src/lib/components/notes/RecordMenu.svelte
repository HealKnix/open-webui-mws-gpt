<script lang="ts">
  import { createEventDispatcher, getContext } from 'svelte';

  import Dropdown from '$lib/components/common/Dropdown.svelte';
  import Mic from '../icons/Mic.svelte';
  import CursorArrowRays from '../icons/CursorArrowRays.svelte';
  import CloudArrowUp from '../icons/CloudArrowUp.svelte';

  const i18n = getContext('i18n');

  export let show = false;
  export let className = 'max-w-[170px]';

  export let onRecord = () => {};
  export let onCaptureAudio = () => {};
  export let onUpload = () => {};

  const dispatch = createEventDispatcher();
</script>

<Dropdown
  bind:show
  sideOffset={8}
  onOpenChange={(state) => {
    dispatch('change', state);
  }}
>
  <slot />

  <div slot="content">
    <div
      class="dark:bg-gray-850 font-primary z-50 min-w-[170px] rounded-xl bg-white p-1 text-sm shadow-lg dark:text-white"
    >
      <button
        class="flex w-full rounded-md px-3 py-1.5 transition hover:bg-gray-50 dark:hover:bg-gray-800"
        on:click={async () => {
          onRecord();
          show = false;
        }}
      >
        <div class=" mr-2 self-center">
          <Mic className="size-4" strokeWidth="2" />
        </div>
        <div class=" self-center truncate">{$i18n.t('Record')}</div>
      </button>

      <button
        class="flex w-full rounded-md px-3 py-1.5 transition hover:bg-gray-50 dark:hover:bg-gray-800"
        on:click={() => {
          onCaptureAudio();
          show = false;
        }}
      >
        <div class=" mr-2 self-center">
          <CursorArrowRays className="size-4" strokeWidth="2" />
        </div>
        <div class=" self-center truncate">{$i18n.t('Capture Audio')}</div>
      </button>

      <button
        class="flex w-full rounded-md px-3 py-1.5 transition hover:bg-gray-50 dark:hover:bg-gray-800"
        on:click={() => {
          onUpload();
          show = false;
        }}
      >
        <div class=" mr-2 self-center">
          <CloudArrowUp className="size-4" strokeWidth="2" />
        </div>
        <div class=" self-center truncate">{$i18n.t('Upload Audio')}</div>
      </button>
    </div>
  </div>
</Dropdown>
