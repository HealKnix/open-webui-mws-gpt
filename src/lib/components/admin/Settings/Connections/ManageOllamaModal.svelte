<script lang="ts">
  import { toast } from 'svelte-sonner';
  import { getContext, onMount } from 'svelte';
  const i18n = getContext('i18n');

  import Modal from '$lib/components/common/Modal.svelte';
  import ManageOllama from '../Models/Manage/ManageOllama.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';

  export let show = false;
  export let urlIdx: number | null = null;
</script>

<Modal size="sm" bind:show>
  <div>
    <div class=" flex justify-between px-5 pt-4 pb-2 dark:text-gray-100">
      <div
        class="font-primary flex w-full items-center justify-between self-center text-lg font-medium"
      >
        <div class=" shrink-0">
          {$i18n.t('Manage Ollama')}
        </div>
      </div>
      <button
        class="self-center"
        on:click={() => {
          show = false;
        }}
      >
        <XMark className={'size-5'} />
      </button>
    </div>

    <div class="flex w-full flex-col px-5 pb-4 md:flex-row md:space-x-4 dark:text-gray-200">
      <ManageOllama {urlIdx} />
    </div>
  </div>
</Modal>
