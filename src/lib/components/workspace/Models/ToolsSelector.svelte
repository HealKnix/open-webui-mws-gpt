<script lang="ts">
  import Checkbox from '$lib/components/common/Checkbox.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import { getContext, onMount } from 'svelte';

  export let tools = [];

  let _tools = {};

  export let selectedToolIds = [];

  const i18n = getContext('i18n');

  onMount(() => {
    _tools = tools.reduce((acc, tool) => {
      acc[tool.id] = {
        ...tool,
        selected: selectedToolIds.includes(tool.id),
      };

      return acc;
    }, {});
  });
</script>

<div>
  <div class="mb-1 flex w-full justify-between">
    <div class="mb-1 text-xs font-medium">{$i18n.t('Tools')}</div>
  </div>

  <div class="mb-1 flex flex-col">
    {#if tools.length > 0}
      <div class=" flex flex-wrap items-center">
        {#each Object.keys(_tools) as tool, toolIdx}
          <div class=" mr-3 flex items-center gap-2">
            <div class="flex items-center self-center">
              <Checkbox
                state={_tools[tool].selected ? 'checked' : 'unchecked'}
                on:change={(e) => {
                  _tools[tool].selected = e.detail === 'checked';
                  selectedToolIds = Object.keys(_tools).filter((t) => _tools[t].selected);
                }}
              />
            </div>

            <Tooltip content={_tools[tool]?.meta?.description ?? _tools[tool].id}>
              <div class=" w-full py-0.5 text-sm font-medium capitalize">
                {_tools[tool].name}
              </div>
            </Tooltip>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <div class=" text-xs dark:text-gray-700">
    {$i18n.t('To select toolkits here, add them to the "Tools" workspace first.')}
  </div>
</div>
