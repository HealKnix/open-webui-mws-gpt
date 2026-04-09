<script lang="ts">
  import { getContext, createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher();
  const i18n = getContext('i18n');

  import { WEBUI_VERSION } from '$lib/constants';
  import XMark from '../icons/XMark.svelte';

  export let version = {
    current: WEBUI_VERSION,
    latest: WEBUI_VERSION,
  };
</script>

<div
  class="flex w-full max-w-80 items-start rounded-lg border border-[3371D5] bg-[#F1F8FE] px-3.5 py-3 pr-2 text-xs text-[#2B6CD4] shadow-lg dark:border-[#03113B] dark:bg-[#020C1D] dark:text-[#6795EC]"
>
  <div class="flex-1 font-medium">
    {$i18n.t(`A new version (v{{LATEST_VERSION}}) is now available.`, {
      LATEST_VERSION: version.latest,
    })}

    <a href="https://github.com/open-webui/open-webui/releases" target="_blank" class="underline">
      {$i18n.t('Update for the latest features and improvements.')}</a
    >
  </div>

  <div class=" shrink-0 pr-1">
    <button
      class=" transition hover:text-blue-900 dark:hover:text-blue-300"
      on:click={() => {
        dispatch('close');
      }}
    >
      <XMark />
    </button>
  </div>
</div>
