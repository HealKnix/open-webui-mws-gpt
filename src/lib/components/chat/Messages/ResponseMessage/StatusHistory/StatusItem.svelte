<script>
  import { getContext } from 'svelte';
  const i18n = getContext('i18n');
  import WebSearchResults from '../WebSearchResults.svelte';
  import Search from '$lib/components/icons/Search.svelte';
  import Cog6 from '$lib/components/icons/Cog6.svelte';
  import Check from '$lib/components/icons/Check.svelte';
  import ChevronRight from '$lib/components/icons/ChevronRight.svelte';
  import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
  import { t } from 'i18next';

  export let status = null;
  export let done = false;

  let expanded = false;

  function toggleExpanded(e) {
    e.stopPropagation();
    expanded = !expanded;
  }

  function latestPreview(s) {
    const invs = s?.invocations ?? [];
    if (!invs.length) return '';
    const running = invs.find((x) => !x.done);
    const pick = running ?? invs[invs.length - 1];
    return pick?.preview ?? '';
  }

  function completedCount(s) {
    const invs = s?.invocations ?? [];
    return invs.filter((x) => x.done).length;
  }

  function hasAnyResult(s) {
    return (s?.invocations ?? []).some((x) => typeof x?.result === 'string' && x.result.trim());
  }

  function invocationLabel(inv, idx) {
    if (inv?.preview) return inv.preview;
    return `#${idx + 1}`;
  }
</script>

{#if !status?.hidden}
  <div class="status-description flex w-full items-center gap-2 py-0.5 text-left">
    {#if status?.action === 'web_search' && (status?.urls || status?.items)}
      <WebSearchResults {status}>
        <div class="flex flex-col justify-center -space-y-0.5">
          <div
            class="{(done || status?.done) === false
              ? 'shimmer'
              : ''} line-clamp-1 text-base text-wrap"
          >
            <!-- $i18n.t("Generating search query") -->
            <!-- $i18n.t("No search query generated") -->
            <!-- $i18n.t('Searched {{count}} sites') -->
            {#if status?.description?.includes('{{count}}')}
              {$i18n.t(status?.description, {
                count: (status?.urls || status?.items).length,
              })}
            {:else if status?.description === 'No search query generated'}
              {$i18n.t('No search query generated')}
            {:else if status?.description === 'Generating search query'}
              {$i18n.t('Generating search query')}
            {:else}
              {status?.description}
            {/if}
          </div>
        </div>
      </WebSearchResults>
    {:else if status?.action === 'knowledge_search'}
      <div class="flex flex-col justify-center -space-y-0.5">
        <div
          class="{(done || status?.done) === false
            ? 'shimmer'
            : ''} line-clamp-1 text-base text-wrap text-gray-500 dark:text-gray-500"
        >
          {$i18n.t(`Searching Knowledge for "{{searchQuery}}"`, {
            searchQuery: status.query,
          })}
        </div>
      </div>
    {:else if status?.action === 'web_search_queries_generated' && status?.queries}
      <div class="flex flex-col justify-center -space-y-0.5">
        <div
          class="{(done || status?.done) === false
            ? 'shimmer'
            : ''} line-clamp-1 text-base text-wrap text-gray-500 dark:text-gray-500"
        >
          {$i18n.t(`Searching`)}
        </div>

        <div class=" mt-2 flex flex-wrap gap-1">
          {#each status.queries as query, idx (query)}
            <div
              class="dark:bg-gray-850 flex items-center gap-1 rounded-lg bg-gray-50 px-2 py-1 text-xs"
            >
              <div>
                <Search className="size-3" />
              </div>

              <span class="line-clamp-1">
                {query}
              </span>
            </div>
          {/each}
        </div>
      </div>
    {:else if status?.action === 'queries_generated' && status?.queries}
      <div class="flex flex-col justify-center -space-y-0.5">
        <div
          class="{(done || status?.done) === false
            ? 'shimmer'
            : ''} line-clamp-1 text-base text-wrap text-gray-500 dark:text-gray-500"
        >
          {$i18n.t(`Querying`)}
        </div>

        <div class=" mt-2 flex flex-wrap gap-1">
          {#each status.queries as query, idx (query)}
            <div
              class="dark:bg-gray-850 flex items-center gap-1 rounded-lg bg-gray-50 px-2 py-1 text-xs"
            >
              <div>
                <Search className="size-3" />
              </div>

              <span class="line-clamp-1">
                {query}
              </span>
            </div>
          {/each}
        </div>
      </div>
    {:else if status?.action === 'tool_call'}
      {@const preview = latestPreview(status)}
      {@const count = status?.invocations?.length ?? 0}
      {@const doneCount = completedCount(status)}
      {@const isDone = done || status?.done}
      {@const canExpand = hasAnyResult(status)}
      <div class="flex min-w-0 flex-1 flex-col gap-0.5">
        <div class="flex min-w-0 items-center gap-2">
          <Cog6 className="size-3.5 shrink-0 text-gray-500" />

          <div
            class="{isDone === false
              ? 'shimmer'
              : ''} flex min-w-0 flex-1 items-center gap-1.5 text-base text-gray-500 dark:text-gray-500"
          >
            {#if status?.appName}
              <span class="truncate">{status.appName}</span>
              <span class="text-gray-400 dark:text-gray-600">›</span>
            {/if}
            <span class="font-medium text-gray-700 dark:text-gray-300">
              {status?.displayName ?? status?.description ?? 'tool'}
            </span>

            {#if count > 1}
              <span
                class="dark:bg-gray-850 shrink-0 rounded-md bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-600 tabular-nums dark:text-gray-400"
              >
                ×{count}
              </span>
            {/if}

            {#if preview}
              <span class="truncate" title={preview}>
                — {preview}
              </span>
            {/if}
          </div>

          <div class="ml-auto flex shrink-0 items-center gap-1 text-xs text-gray-500 tabular-nums">
            {#if count > 1 && !isDone}
              <span>{doneCount}/{count}</span>
            {:else if isDone}
              <Check className="size-3.5 text-green-600 dark:text-green-500" />
            {/if}
            {#if canExpand}
              <button
                type="button"
                class="dark:hover:bg-gray-850 -mr-1 flex size-5 items-center justify-center rounded hover:bg-gray-100"
                aria-label={expanded ? $i18n.t('Hide tool results') : $i18n.t('Show tool results')}
                aria-expanded={expanded}
                on:click={toggleExpanded}
              >
                {#if expanded}
                  <ChevronDown className="size-3.5" />
                {:else}
                  <ChevronRight className="size-3.5" />
                {/if}
              </button>
            {/if}
          </div>
        </div>

        {#if expanded && canExpand}
          <div class="mt-1 ml-[22px] flex flex-col gap-1.5">
            {#each status.invocations ?? [] as inv, idx (inv.tool_call_id)}
              {#if typeof inv?.result === 'string' && inv.result.trim()}
                <div class="dark:bg-gray-850/60 rounded-md bg-gray-50 p-2">
                  <div class="mb-1 truncate font-mono text-[11px] text-gray-500 dark:text-gray-400">
                    {invocationLabel(inv, idx)}
                  </div>
                  <pre
                    class="max-h-64 overflow-auto font-mono text-xs break-words whitespace-pre-wrap text-gray-700 dark:text-gray-300">{inv.result}</pre>
                </div>
              {/if}
            {/each}
          </div>
        {/if}
      </div>
    {:else if status?.action === 'sources_retrieved' && status?.count !== undefined}
      <div class="flex flex-col justify-center -space-y-0.5">
        <div
          class="{(done || status?.done) === false
            ? 'shimmer'
            : ''} line-clamp-1 text-base text-wrap text-gray-500 dark:text-gray-500"
        >
          {#if status.count === 0}
            {$i18n.t('No sources found')}
          {:else if status.count === 1}
            {$i18n.t('Retrieved 1 source')}
          {:else}
            <!-- {$i18n.t('Source')} -->
            <!-- {$i18n.t('No source available')} -->
            <!-- {$i18n.t('No distance available')} -->
            <!-- {$i18n.t('Retrieved {{count}} sources')} -->
            {$i18n.t('Retrieved {{count}} sources', {
              count: status.count,
            })}
          {/if}
        </div>
      </div>
    {:else}
      <div class="flex flex-col justify-center -space-y-0.5">
        <div
          class="{(done || status?.done) === false
            ? 'shimmer'
            : ''} line-clamp-1 text-base text-wrap text-gray-500 dark:text-gray-500"
        >
          <!-- $i18n.t(`Searching "{{searchQuery}}"`) -->
          {#if status?.description?.includes('{{searchQuery}}')}
            {$i18n.t(status?.description, {
              searchQuery: status?.query,
            })}
          {:else if status?.description === 'No search query generated'}
            {$i18n.t('No search query generated')}
          {:else if status?.description === 'Generating search query'}
            {$i18n.t('Generating search query')}
          {:else if status?.description === 'Searching the web'}
            {$i18n.t('Searching the web')}
          {:else}
            {status?.description}
          {/if}
        </div>
      </div>
    {/if}
  </div>
{/if}
