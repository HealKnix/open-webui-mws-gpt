<script lang="ts">
  import Modal from '$lib/components/common/Modal.svelte';
  import { getContext } from 'svelte';
  import { getModelHistory } from '$lib/apis/evaluations';
  import ModelActivityChart from './ModelActivityChart.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';

  export let show = false;
  export let model = null;
  export let onClose: () => void = () => {};

  const i18n = getContext('i18n');

  type TimeRange = '30d' | '1y' | 'all';
  const TIME_RANGES: { key: TimeRange; label: string; days: number }[] = [
    { key: '30d', label: '30D', days: 30 },
    { key: '1y', label: '1Y', days: 365 },
    { key: 'all', label: 'All', days: 0 }, // 0 = all time, starts from first feedback
  ];

  let selectedRange: TimeRange = '30d';
  let history: Array<{ date: string; won: number; lost: number }> = [];
  let loadingHistory = false;

  const close = () => {
    show = false;
    onClose();
  };

  const loadHistory = async (days: number) => {
    if (!model?.id) return;
    loadingHistory = true;
    try {
      const result = await getModelHistory(localStorage.token, model.id, days);
      history = result?.history ?? [];
    } catch (err) {
      console.error('Failed to load model history:', err);
      history = [];
    }
    loadingHistory = false;
  };

  const selectRange = (range: TimeRange) => {
    selectedRange = range;
    const config = TIME_RANGES.find((r) => r.key === range);
    if (config) {
      loadHistory(config.days);
    }
  };

  // Load history when model changes and modal is shown
  $: if (show && model?.id) {
    selectRange(selectedRange);
  }

  // Use top_tags from backend response (already computed)
  $: topTags = model?.top_tags ?? [];
</script>

<Modal size="md" bind:show>
  {#if model}
    <div class="flex justify-between px-5 pt-4 pb-2 dark:text-gray-300">
      <Tooltip content={`${model.name} (${model.id})`} placement="top-start">
        <div class="line-clamp-1 self-center text-lg font-medium">
          {model.name}
        </div>
      </Tooltip>
      <button class="self-center" on:click={close} aria-label="Close">
        <XMark className={'size-5'} />
      </button>
    </div>
    <div class="px-5 pb-4 dark:text-gray-200">
      <!-- Activity Chart -->
      <div class="mb-4">
        <div class="mb-2 flex items-center justify-between">
          <div class="text-xs font-medium tracking-wide text-gray-500 uppercase">
            {$i18n.t('Activity')}
          </div>
          <div
            class="inline-flex rounded-full bg-gray-100/80 p-0.5 backdrop-blur-sm dark:bg-gray-800/80"
          >
            {#each TIME_RANGES as range}
              <button
                type="button"
                class="rounded-full px-2.5 py-0.5 text-xs font-medium transition-all duration-200 {selectedRange ===
                range.key
                  ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-white'
                  : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}"
                on:click={() => selectRange(range.key)}
              >
                {range.label}
              </button>
            {/each}
          </div>
        </div>
        <ModelActivityChart
          {history}
          loading={loadingHistory}
          aggregateWeekly={selectedRange === '1y' || selectedRange === 'all'}
        />
      </div>

      <div class="mb-4">
        <div class="mb-2 text-xs font-medium tracking-wide text-gray-500 uppercase">
          {$i18n.t('Tags')}
        </div>
        {#if topTags.length}
          <div class="-mx-1 flex flex-wrap gap-1">
            {#each topTags as tagInfo}
              <span class="dark:bg-gray-850 rounded-full bg-gray-100 px-2 py-0.5 text-xs">
                {tagInfo.tag} <span class="font-medium text-gray-500">{tagInfo.count}</span>
              </span>
            {/each}
          </div>
        {:else}
          <span class="text-sm text-gray-500">-</span>
        {/if}
      </div>

      <div class="flex justify-end pt-2">
        <button
          class="rounded-full bg-black px-3.5 py-1.5 text-sm font-medium text-white transition hover:bg-gray-900 dark:bg-white dark:text-black dark:hover:bg-gray-100"
          type="button"
          on:click={close}
        >
          {$i18n.t('Close')}
        </button>
      </div>
    </div>
  {/if}
</Modal>
