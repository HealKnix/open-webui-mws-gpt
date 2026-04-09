<script>
  import { getContext, onMount } from 'svelte';
  const i18n = getContext('i18n');

  import ManageOllama from './ManageOllama.svelte';

  export let ollamaConfig = null;

  let selectedUrlIdx = 0;
</script>

{#if ollamaConfig}
  <div class="dark:bg-gray-850 mb-2.5 flex-1 rounded-lg bg-gray-50 pr-1.5 dark:text-gray-300">
    <select
      class="w-full bg-transparent px-4 py-2 text-sm outline-hidden"
      bind:value={selectedUrlIdx}
      placeholder={$i18n.t('Select an Ollama instance')}
    >
      {#each ollamaConfig.OLLAMA_BASE_URLS as url, idx}
        <option value={idx}>{url}</option>
      {/each}
    </select>
  </div>

  <div>
    <ManageOllama urlIdx={selectedUrlIdx} />
  </div>
{/if}
