<script lang="ts">
  import Checkbox from '$lib/components/common/Checkbox.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import { getContext } from 'svelte';

  export let tools = [];
  export let selectedToolIds = [];
  export let title = 'Tools';
  export let helperText = 'To select toolkits here, add them to the "Tools" workspace first.';

  let _tools: Record<string, any> = {};

  const i18n = getContext('i18n');

  $: _tools = tools.reduce((acc, tool) => {
    acc[tool.id] = {
      ...tool,
      selected: selectedToolIds.includes(tool.id),
    };

    return acc;
  }, {});
</script>

<div>
  <div class="mb-1 flex w-full justify-between">
    <div class="mb-1 text-xs font-medium">{$i18n.t(title)}</div>
  </div>

  <div class="mb-1 flex flex-col">
    {#if tools.length > 0}
      <div class="flex flex-wrap items-center gap-2">
        {#each Object.keys(_tools) as tool}
          <Checkbox
            state={_tools[tool].selected ? 'checked' : 'unchecked'}
            on:change={(e) => {
              _tools[tool].selected = e.detail === 'checked';
              selectedToolIds = Object.keys(_tools).filter((t) => _tools[t].selected);
            }}
            tooltip={{
              label: _tools[tool].name,
              description: _tools[tool]?.meta?.description ?? _tools[tool].id,
            }}
          />
        {/each}
      </div>
    {/if}
  </div>

  <div class=" text-xs dark:text-gray-700">
    {$i18n.t(helperText)}
  </div>
</div>
