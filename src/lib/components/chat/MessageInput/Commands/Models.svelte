<script lang="ts">
  import Fuse from 'fuse.js';

  import { createEventDispatcher, onDestroy, onMount } from 'svelte';
  import { tick, getContext } from 'svelte';

  import { models } from '$lib/stores';
  import { WEBUI_API_BASE_URL, WEBUI_BASE_URL } from '$lib/constants';
  import Tooltip from '$lib/components/common/Tooltip.svelte';

  const i18n = getContext('i18n');

  export let query = '';
  export let onSelect = (e) => {};

  let selectedIdx = 0;
  export let filteredItems = [];

  let fuse = new Fuse(
    $models
      .filter((model) => !model?.info?.meta?.hidden)
      .map((model) => {
        const _item = {
          ...model,
          modelName: model?.name,
          tags: model?.info?.meta?.tags?.map((tag) => tag.name).join(' '),
          desc: model?.info?.meta?.description,
        };
        return _item;
      }),
    {
      keys: ['value', 'tags', 'modelName'],
      threshold: 0.5,
    },
  );

  $: filteredItems = query
    ? fuse.search(query).map((e) => {
        return e.item;
      })
    : $models.filter((model) => !model?.info?.meta?.hidden);

  $: if (query) {
    selectedIdx = 0;
  }

  export const selectUp = () => {
    selectedIdx = Math.max(0, selectedIdx - 1);
  };

  export const selectDown = () => {
    selectedIdx = Math.min(selectedIdx + 1, filteredItems.length - 1);
  };

  export const select = async () => {
    const model = filteredItems[selectedIdx];
    if (model) {
      onSelect({ type: 'model', data: model });
    }
  };
</script>

<div class="px-2 py-1 text-xs text-gray-500">
  {$i18n.t('Models')}
</div>

{#if filteredItems.length > 0}
  {#each filteredItems as model, modelIdx}
    <Tooltip content={model.id} placement="top-start">
      <button
        class="w-full rounded-xl px-2.5 py-1.5 text-left {modelIdx === selectedIdx
          ? 'selected-command-option-button bg-gray-50 dark:bg-gray-800'
          : ''}"
        type="button"
        on:click={() => {
          onSelect({ type: 'model', data: model });
        }}
        on:mousemove={() => {
          selectedIdx = modelIdx;
        }}
        on:focus={() => {}}
        data-selected={modelIdx === selectedIdx}
      >
        <div class="line-clamp-1 flex text-black dark:text-gray-100">
          <img
            src={`${WEBUI_API_BASE_URL}/models/model/profile/image?id=${model.id}&lang=${$i18n.language}`}
            alt={model?.name ?? model.id}
            class="mr-2 size-5 items-center rounded-full"
            on:error={(e) => {
              e.currentTarget.src = '/favicon.png';
            }}
          />
          <div class="truncate">
            {model.name}
          </div>
        </div>
      </button>
    </Tooltip>
  {/each}
{/if}
