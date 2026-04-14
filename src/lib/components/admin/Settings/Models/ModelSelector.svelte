<script lang="ts">
  import { getContext } from 'svelte';
  const i18n = getContext('i18n');

  import Minus from '$lib/components/icons/Minus.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';

  export let title = '';
  export let tooltip = '';
  export let models = [];
  export let modelIds = [];

  let selectedModelId = '';
</script>

<div>
  <div class="flex w-full flex-col">
    <div class="mb-1 flex justify-between">
      <div class="flex items-center gap-1 text-xs text-gray-500">
        {title}
        {#if tooltip}
          <Tooltip content={tooltip} className="cursor-help">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="1.5"
              stroke="currentColor"
              class="size-3"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z"
              />
            </svg>
          </Tooltip>
        {/if}
      </div>
    </div>

    <div class="-mr-1 flex items-center">
      <select
        class="w-full rounded-lg bg-transparent py-1 text-sm {selectedModelId
          ? ''
          : 'text-gray-500'} outline-hidden placeholder:text-gray-300 dark:placeholder:text-gray-700"
        bind:value={selectedModelId}
        on:change={() => {
          if (selectedModelId && !modelIds.includes(selectedModelId)) {
            modelIds = [...modelIds, selectedModelId];
          }
          selectedModelId = '';
        }}
      >
        <option value="">{$i18n.t('Select a model')}</option>
        {#each models as model}
          {#if !modelIds.includes(model.id)}
            <option value={model.id} class="bg-gray-50 dark:bg-gray-700">{model.name}</option>
          {/if}
        {/each}
      </select>
    </div>

    <!-- <hr class=" border-gray-100 dark:border-gray-700/10 my-2.5 w-full" /> -->

    {#if modelIds.length > 0}
      <div class="flex flex-col">
        {#each modelIds as modelId, modelIdx}
          <div class=" flex w-full items-center justify-between gap-2">
            <div class=" flex-1 rounded-lg py-1 text-sm">
              {models.find((model) => model.id === modelId)?.name}
            </div>
            <div class="shrink-0">
              <button
                type="button"
                on:click={() => {
                  modelIds = modelIds.filter((_, idx) => idx !== modelIdx);
                }}
              >
                <Minus strokeWidth="2" className="size-3.5" />
              </button>
            </div>
          </div>
        {/each}
      </div>
    {:else}
      <div class="py-2 text-center text-xs text-gray-500">
        {$i18n.t('No models selected')}
      </div>
    {/if}
  </div>
</div>
