<script>
  import { getContext } from 'svelte';

  export let title = '';
  export let content = '';
  const i18n = getContext('i18n');
</script>

<div class="px-3">
  <div class="z-50 text-center text-2xl font-medium dark:text-white" role="heading" aria-level="2">
    {#if title}
      {title}
    {:else}
      {$i18n.t('Add Files')}
    {/if}
  </div>

  <slot
    ><div class="mt-2 w-full px-2 text-center text-gray-700 dark:text-gray-200">
      {#if content}
        {content}
      {:else}
        {$i18n.t('Drop any files here to upload')}
      {/if}
    </div>
  </slot>
</div>
