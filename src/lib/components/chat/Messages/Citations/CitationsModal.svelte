<script lang="ts">
  import { getContext, onMount, tick } from 'svelte';

  const i18n = getContext('i18n');

  import Modal from '$lib/components/common/Modal.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';
  import CitationModal from './CitationModal.svelte';

  export let id = '';
  export let show = false;
  export let citations = [];
  export let showPercentage = false;
  export let showRelevance = true;

  let showCitationModal = false;
  let selectedCitation: any = null;

  export const showCitation = (citation) => {
    selectedCitation = citation;
    showCitationModal = true;
  };

  const decodeString = (str: string) => {
    try {
      return decodeURIComponent(str);
    } catch (e) {
      return str;
    }
  };
</script>

<CitationModal
  bind:show={showCitationModal}
  citation={selectedCitation}
  {showPercentage}
  {showRelevance}
/>

<Modal size="lg" bind:show>
  <div>
    <div class=" flex justify-between px-5 pt-4 pb-2 dark:text-gray-300">
      <div class=" self-center text-lg font-medium capitalize">
        {$i18n.t('Citations')}
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

    <div class="flex w-full flex-col px-6 pb-5 md:flex-row md:space-x-4">
      <div
        class="scrollbar-hidden flex max-h-[22rem] w-full flex-col gap-2 overflow-y-scroll text-left text-sm dark:text-gray-200"
      >
        {#each citations as citation, idx}
          <button
            id={`source-${id}-${idx + 1}`}
            class="no-toggle flex items-center gap-1.5 rounded-xl bg-white outline-hidden dark:bg-gray-900 dark:text-gray-300"
            on:click={() => {
              showCitationModal = true;
              selectedCitation = citation;
            }}
          >
            <div class=" font-medium">
              {idx + 1}.
            </div>
            <div
              class="flex-1 truncate text-left text-black/60 transition hover:text-black dark:text-white/60 dark:hover:text-white"
            >
              {decodeString(citation.source.name)}
            </div>
          </button>
        {/each}
      </div>
    </div>
  </div>
</Modal>
