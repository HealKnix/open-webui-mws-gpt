<script lang="ts">
  import { getContext } from 'svelte';
  import { embed, showControls, showEmbeds } from '$lib/stores';

  import CitationModal from './Citations/CitationModal.svelte';

  const i18n = getContext('i18n');

  export let id = '';
  export let chatId = '';

  export let sources = [];
  export let readOnly = false;

  let citations = [];
  let showPercentage = false;
  let showRelevance = true;

  let citationModal = null;

  let showCitations = false;
  let showCitationModal = false;

  let selectedCitation: any = null;

  export const showSourceModal = (sourceId) => {
    let index;
    let suffix = null;

    if (typeof sourceId === 'string') {
      const output = sourceId.split('#');
      index = parseInt(output[0]) - 1;

      if (output.length > 1) {
        suffix = output[1];
      }
    } else {
      index = sourceId - 1;
    }

    if (citations[index]) {
      console.log('Showing citation modal for:', citations[index]);

      if (citations[index]?.source?.embed_url) {
        const embedUrl = citations[index].source.embed_url;
        if (embedUrl) {
          if (readOnly) {
            // Open in new tab if readOnly
            window.open(embedUrl, '_blank');
            return;
          } else {
            showControls.set(true);
            showEmbeds.set(true);
            embed.set({
              url: embedUrl,
              title: citations[index]?.source?.name || 'Embedded Content',
              source: citations[index],
              chatId: chatId,
              messageId: id,
              sourceId: sourceId,
            });
          }
        } else {
          selectedCitation = citations[index];
          showCitationModal = true;
        }
      } else {
        selectedCitation = citations[index];
        showCitationModal = true;
      }
    }
  };

  function calculateShowRelevance(sources: any[]) {
    const distances = sources.flatMap((citation) => citation.distances ?? []);
    const inRange = distances.filter((d) => d !== undefined && d >= -1 && d <= 1).length;
    const outOfRange = distances.filter((d) => d !== undefined && (d < -1 || d > 1)).length;

    if (distances.length === 0) {
      return false;
    }

    if (
      (inRange === distances.length - 1 && outOfRange === 1) ||
      (outOfRange === distances.length - 1 && inRange === 1)
    ) {
      return false;
    }

    return true;
  }

  function shouldShowPercentage(sources: any[]) {
    const distances = sources.flatMap((citation) => citation.distances ?? []);
    return distances.every((d) => d !== undefined && d >= -1 && d <= 1);
  }

  $: {
    citations = sources.reduce((acc, source) => {
      if (Object.keys(source).length === 0) {
        return acc;
      }

      source?.document?.forEach((document, index) => {
        const metadata = source?.metadata?.[index];
        const distance = source?.distances?.[index];

        // Within the same citation there could be multiple documents
        const id = metadata?.source ?? source?.source?.id ?? 'N/A';
        let _source = source?.source;

        if (metadata?.name) {
          _source = { ..._source, name: metadata.name };
        }

        if (id.startsWith('http://') || id.startsWith('https://')) {
          _source = { ..._source, name: id, url: id };
        }

        const existingSource = acc.find((item) => item.id === id);

        if (existingSource) {
          existingSource.document.push(document);
          existingSource.metadata.push(metadata);
          if (distance !== undefined) existingSource.distances.push(distance);
        } else {
          acc.push({
            id: id,
            source: _source,
            document: [document],
            metadata: metadata ? [metadata] : [],
            distances: distance !== undefined ? [distance] : [],
          });
        }
      });

      return acc;
    }, []);
    console.log('citations', citations);

    showRelevance = calculateShowRelevance(citations);
    showPercentage = shouldShowPercentage(citations);
  }

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

{#if citations.length > 0}
  {@const urlCitations = citations.filter((c) => c?.source?.name?.startsWith('http'))}
  <div class=" -mx-0.5 flex w-full flex-wrap items-center gap-1 py-1">
    <button
      class="dark:border-gray-850/30 flex h-8 items-center gap-1 rounded-full border border-gray-50 px-3.5 text-xs font-medium text-gray-600 transition hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
      aria-label={citations.length === 1
        ? $i18n.t('Toggle 1 source')
        : $i18n.t('Toggle {{COUNT}} sources', { COUNT: citations.length })}
      aria-expanded={showCitations}
      on:click={() => {
        showCitations = !showCitations;
      }}
    >
      {#if urlCitations.length > 0}
        <div class="flex items-center -space-x-1">
          {#each urlCitations.slice(0, 3) as citation, idx}
            <img
              src="https://www.google.com/s2/favicons?sz=32&domain={citation.source.name}"
              alt="favicon"
              class="dark:border-gray-850 size-4 shrink-0 rounded-full border border-white bg-white dark:bg-gray-900"
              on:error={(e) => {
                e.target.src = '/favicon.png';
              }}
            />
          {/each}
        </div>
      {/if}
      <div>
        {#if citations.length === 1}
          {$i18n.t('1 Source')}
        {:else}
          {$i18n.t('{{COUNT}} Sources', {
            COUNT: citations.length,
          })}
        {/if}
      </div>
    </button>
  </div>
{/if}

{#if showCitations}
  <div class="py-1.5">
    <div class="flex flex-col gap-2 text-xs">
      {#each citations as citation, idx}
        <button
          id={`source-${id}-${idx + 1}`}
          aria-label={$i18n.t('View source: {{name}}', {
            name: decodeString(citation.source.name),
          })}
          class="no-toggle flex items-center gap-1.5 rounded-xl bg-transparent text-gray-600 outline-hidden dark:text-gray-300"
          on:click={() => {
            showCitationModal = true;
            selectedCitation = citation;
          }}
        >
          <div class=" dark:bg-gray-850 rounded-md bg-gray-50 px-1 font-medium">
            {idx + 1}
          </div>
          <div
            class="flex-1 truncate text-left transition hover:text-black dark:text-white/60 dark:hover:text-white"
          >
            {decodeString(citation.source.name)}
          </div>
        </button>
      {/each}
    </div>
  </div>
{/if}
