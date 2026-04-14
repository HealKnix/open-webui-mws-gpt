<script lang="ts">
  import { getContext, onMount } from 'svelte';
  import Checkbox from '$lib/components/common/Checkbox.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';

  const i18n = getContext('i18n');

  export let filters = [];
  export let selectedFilterIds = [];

  let _filters = {};

  onMount(() => {
    _filters = filters.reduce((acc, filter) => {
      acc[filter.id] = {
        ...filter,
        selected: selectedFilterIds.includes(filter.id),
      };

      return acc;
    }, {});
  });
</script>

<div>
  <div class="mb-1 flex w-full justify-between">
    <div class="mb-1 text-xs font-medium">{$i18n.t('Default Filters')}</div>
  </div>

  <div class="flex flex-col">
    {#if filters.length > 0}
      <div class=" flex flex-wrap items-center">
        {#each Object.keys(_filters) as filter, filterIdx}
          <div class=" mr-3 flex items-center gap-2">
            <div class="flex items-center self-center">
              <Checkbox
                state={_filters[filter].selected ? 'checked' : 'unchecked'}
                on:change={(e) => {
                  _filters[filter].selected = e.detail === 'checked';
                  selectedFilterIds = Object.keys(_filters).filter((t) => _filters[t].selected);
                }}
              />
            </div>

            <div class=" w-full py-0.5 text-sm font-medium capitalize">
              <Tooltip content={_filters[filter].meta.description}>
                {_filters[filter].name}
              </Tooltip>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>
