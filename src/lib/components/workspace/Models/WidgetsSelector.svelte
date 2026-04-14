<script lang="ts">
  import Checkbox from '$lib/components/common/Checkbox.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import { getContext, onMount } from 'svelte';

  import { getWidgetItems } from '$lib/apis/widgets';

  export let selectedWidgetIds: string[] = [];

  let _widgets: Record<string, any> = {};

  const i18n = getContext('i18n');

  onMount(async () => {
    const res = await getWidgetItems(localStorage.token).catch(() => null);
    const widgets = res?.items ?? [];
    _widgets = widgets.reduce((acc: Record<string, any>, widget: any) => {
      acc[widget.id] = {
        ...widget,
        selected: selectedWidgetIds.includes(widget.id),
      };

      return acc;
    }, {});
  });
</script>

<div>
  <div class="mb-1 flex w-full justify-between">
    <div class="mb-1 text-xs font-medium">{$i18n.t('Widgets')}</div>
  </div>

  <div class="mb-1 flex flex-col">
    {#if Object.keys(_widgets).length > 0}
      <div class="flex flex-wrap items-center gap-2">
        {#each Object.keys(_widgets) as widget, widgetIdx}
          <Checkbox
            state={_widgets[widget].selected ? 'checked' : 'unchecked'}
            on:change={(e) => {
              _widgets[widget].selected = e.detail === 'checked';
              selectedWidgetIds = Object.keys(_widgets).filter((w) => _widgets[w].selected);
            }}
            tooltip={{
              label: _widgets[widget].name,
              description: _widgets[widget].description,
            }}
          />
        {/each}
      </div>
    {/if}
  </div>

  <div class=" text-xs dark:text-gray-700">
    {$i18n.t('To select widgets here, add them to the "Widgets" workspace first.')}
  </div>
</div>
