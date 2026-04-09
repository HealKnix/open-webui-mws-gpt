<script lang="ts">
  import { onMount, getContext } from 'svelte';
  import { models } from '$lib/stores';
  import { getLeaderboard } from '$lib/apis/evaluations';
  import ModelModal from './LeaderboardModal.svelte';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Search from '$lib/components/icons/Search.svelte';
  import ChevronUp from '$lib/components/icons/ChevronUp.svelte';
  import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
  import { WEBUI_API_BASE_URL } from '$lib/constants';

  const i18n = getContext('i18n');

  let rankedModels = [];
  let query = '';
  let loading = true;
  let debounceTimer: ReturnType<typeof setTimeout>;
  let orderBy = 'rating';
  let direction: 'asc' | 'desc' = 'desc';

  let showModal = false;
  let selectedModel = null;

  const toggleSort = (key: string) => {
    if (orderBy === key) {
      direction = direction === 'asc' ? 'desc' : 'asc';
    } else {
      orderBy = key;
      direction = key === 'name' ? 'asc' : 'desc';
    }
  };

  const openModal = (model) => {
    selectedModel = model;
    showModal = true;
  };

  const closeModal = () => {
    selectedModel = null;
    showModal = false;
  };

  const loadLeaderboard = async (searchQuery = '') => {
    loading = true;
    try {
      const result = await getLeaderboard(localStorage.token, searchQuery);
      const statsMap = new Map((result?.entries ?? []).map((e) => [e.model_id, e]));

      rankedModels = $models
        .filter((m) => m?.owned_by !== 'arena' && !m?.info?.meta?.hidden)
        .map((model) => {
          const s = statsMap.get(model.id);
          return {
            ...model,
            rating: s?.rating ?? '-',
            stats: {
              count: s ? s.won + s.lost : 0,
              won: s?.won?.toString() ?? '-',
              lost: s?.lost?.toString() ?? '-',
            },
            top_tags: s?.top_tags ?? [],
          };
        })
        .sort((a, b) => {
          if (a.rating === '-') return 1;
          if (b.rating === '-') return -1;
          return b.rating - a.rating;
        });
    } catch (err) {
      console.error('Leaderboard load failed:', err);
    }
    loading = false;
  };

  const debouncedLoad = () => {
    loading = true;
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => loadLeaderboard(query), 500);
  };

  $: if (query !== null) {
    debouncedLoad();
  }

  $: sortedModels = [...rankedModels].sort((a, b) => {
    const getValue = (m, key) => {
      if (key === 'name') return m.name ?? m.id ?? '';
      if (key === 'rating') return m.rating === '-' ? -Infinity : m.rating;
      if (key === 'won' || key === 'lost') {
        const v = m.stats[key];
        return v === '-' ? -Infinity : Number(v);
      }
      return 0;
    };
    const aVal = getValue(a, orderBy);
    const bVal = getValue(b, orderBy);
    if (orderBy === 'name') {
      return direction === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }
    return direction === 'asc' ? aVal - bVal : bVal - aVal;
  });
</script>

<ModelModal bind:show={showModal} model={selectedModel} onClose={closeModal} />

<div
  class="sticky top-0 z-10 flex flex-col justify-between gap-1 bg-white pt-0.5 pb-1 md:flex-row dark:bg-gray-900"
>
  <div class="flex shrink-0 items-center gap-2 px-0.5 text-xl font-medium">
    {$i18n.t('Leaderboard')}
    <span class="text-lg text-gray-500">{rankedModels.length}</span>
  </div>
  <Tooltip content={$i18n.t('Re-rank models by topic similarity')}>
    <div class="flex flex-1">
      <Search className="size-3 ml-1 mr-3 self-center" />
      <input
        class="w-full rounded-r-xl bg-transparent py-1 pr-4 text-sm outline-hidden"
        bind:value={query}
        placeholder={$i18n.t('Search')}
      />
    </div>
  </Tooltip>
</div>

<div
  class="scrollbar-hidden relative min-h-[100px] max-w-full overflow-x-auto rounded-sm whitespace-nowrap"
>
  {#if loading}
    <div
      class="absolute inset-0 z-10 flex items-center justify-center bg-white/50 dark:bg-gray-900/50"
    >
      <Spinner className="size-5" />
    </div>
  {/if}

  {#if !rankedModels.length && !loading}
    <div class="py-1 text-center text-xs text-gray-500">{$i18n.t('No models found')}</div>
  {:else if rankedModels.length}
    <table
      class="w-full text-left text-sm text-gray-500 dark:text-gray-400 {loading
        ? 'opacity-20'
        : ''}"
    >
      <thead class="bg-transparent text-xs text-gray-800 uppercase dark:text-gray-200">
        <tr class="dark:border-gray-850/30 border-b-[1.5px] border-gray-50">
          {#each [{ key: 'rating', label: 'RK', class: 'w-3' }, { key: 'name', label: 'Model', class: '' }, { key: 'rating', label: 'Rating', class: 'text-right w-fit' }, { key: 'won', label: 'Won', class: 'text-right w-5' }, { key: 'lost', label: 'Lost', class: 'text-right w-5' }] as col}
            <th
              scope="col"
              class="cursor-pointer px-2.5 py-2 select-none {col.class}"
              on:click={() => toggleSort(col.key)}
            >
              <div
                class="flex items-center gap-1.5 {col.class.includes('right') ? 'justify-end' : ''}"
              >
                {$i18n.t(col.label)}
                {#if orderBy === col.key}
                  {#if direction === 'asc'}<ChevronUp className="size-2" />{:else}<ChevronDown
                      className="size-2"
                    />{/if}
                {:else}
                  <span class="invisible"><ChevronUp className="size-2" /></span>
                {/if}
              </div>
            </th>
          {/each}
        </tr>
      </thead>
      <tbody>
        {#each sortedModels as model, idx (model.id)}
          <tr
            class="group dark:hover:bg-gray-850/50 cursor-pointer bg-white text-xs transition hover:bg-gray-50 dark:bg-gray-900"
            on:click={() => openModal(model)}
          >
            <td class="px-3 py-1.5 font-medium text-gray-900 dark:text-white">
              {model.rating !== '-' ? idx + 1 : '-'}
            </td>
            <td class="px-3 py-1.5">
              <div class="flex items-center gap-2">
                <img
                  src="{WEBUI_API_BASE_URL}/models/model/profile/image?id={model.id}"
                  alt={model.name}
                  class="size-5 shrink-0 rounded-full object-cover"
                  on:error={(e) => {
                    e.target.src = '/favicon.png';
                  }}
                />
                <Tooltip content={`${model.name} (${model.id})`} placement="top-start">
                  <span class="line-clamp-1 font-medium text-gray-800 dark:text-gray-200"
                    >{model.name}</span
                  >
                </Tooltip>
              </div>
            </td>
            <td class="px-3 py-1.5 text-right font-medium text-gray-900 dark:text-white">
              {model.rating}
            </td>
            <td class="w-10 px-3 py-1.5 text-right font-medium text-green-500">
              {#if model.stats.won === '-'}-{:else}
                <span class="hidden group-hover:inline"
                  >{((Number(model.stats.won) / model.stats.count) * 100).toFixed(1)}%</span
                >
                <span class="group-hover:hidden">{model.stats.won}</span>
              {/if}
            </td>
            <td class="w-10 px-3 py-1.5 text-right font-medium text-red-500">
              {#if model.stats.lost === '-'}-{:else}
                <span class="hidden group-hover:inline"
                  >{((Number(model.stats.lost) / model.stats.count) * 100).toFixed(1)}%</span
                >
                <span class="group-hover:hidden">{model.stats.lost}</span>
              {/if}
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  {/if}
</div>

<div class="mt-1.5 flex w-full justify-end text-xs text-gray-500">
  <div class="text-right">
    <div class="line-clamp-1">
      ⓘ {$i18n.t(
        'The evaluation leaderboard is based on the Elo rating system and is updated in real-time.',
      )}
    </div>
    {$i18n.t(
      'The leaderboard is currently in beta, and we may adjust the rating calculations as we refine the algorithm.',
    )}
  </div>
</div>
