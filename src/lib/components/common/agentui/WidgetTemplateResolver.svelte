<script context="module" lang="ts">
  const templateCache = new Map<string, any>();
</script>

<script lang="ts">
  import { onMount } from 'svelte';
  import { getContext } from 'svelte';
  import { getWidgetById } from '$lib/apis/widgets';
  import WidgetMapper from './WidgetMapper.svelte';

  const i18n = getContext('i18n');

  export let widgetId: string;
  export let data: any = {};
  export let onAction: (payload: any) => void = () => {};

  let template: any = null;
  let loading = true;
  let error = false;

  onMount(async () => {
    if (templateCache.has(widgetId)) {
      template = templateCache.get(widgetId);
      loading = false;
      return;
    }

    try {
      const widget = await getWidgetById(localStorage.token, widgetId);
      if (widget?.content) {
        const parsed =
          typeof widget.content === 'string' ? JSON.parse(widget.content) : widget.content;
        templateCache.set(widgetId, parsed);
        template = parsed;
      } else {
        error = true;
      }
    } catch (e) {
      console.error(`Failed to load widget template "${widgetId}":`, e);
      error = true;
    }

    loading = false;
  });
</script>

{#if loading}
  <div
    class="flex h-32 items-center justify-center rounded-2xl border border-gray-100 bg-gray-50 dark:border-gray-800 dark:bg-gray-900"
  >
    <div class="flex items-center gap-2 text-sm text-gray-400">
      <svg class="size-4 animate-spin" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" class="opacity-25" />
        <path
          d="M4 12a8 8 0 018-8"
          stroke="currentColor"
          stroke-width="3"
          stroke-linecap="round"
          class="opacity-75"
        />
      </svg>
      {$i18n.t('Loading widget...')}
    </div>
  </div>
{:else if error}
  <div
    class="flex h-32 flex-col items-center justify-center rounded-2xl border-2 border-dashed border-red-200 dark:border-red-800/50"
  >
    <div class="text-sm text-red-400">{$i18n.t('Widget "{{id}}" not found', { id: widgetId })}</div>
  </div>
{:else}
  <WidgetMapper content={template} {data} {onAction} />
{/if}
