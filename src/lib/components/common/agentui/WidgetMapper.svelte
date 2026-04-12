<script lang="ts">
  import { getContext } from 'svelte';
  const i18n = getContext('i18n');

  export let content: any = {};
  export let data: any = {};
  export let onAction: (payload: any) => void = () => {};

  // Simple template engine for strings like "Hello {{user}}"
  const template = (str: string, context: any) => {
    if (typeof str !== 'string') return str;
    return str.replace(/\{\{(.*?)\}\}/g, (match, key) => {
      const parts = key.trim().split('.');
      let value = context;
      for (const part of parts) {
        value = value?.[part];
      }
      return value !== undefined ? value : match;
    });
  };

  let parsedContent = {};
  $: {
    try {
      if (typeof content === 'string') {
        parsedContent = JSON.parse(content || '{}');
      } else {
        parsedContent = content || {};
      }
    } catch (e) {
      parsedContent = {};
    }
  }
</script>

{#if parsedContent && typeof parsedContent === 'object' && Object.keys(parsedContent).length > 0}
  {#if parsedContent.type === 'container' || (!parsedContent.type && parsedContent.children)}
    <div class="bg-background space-y-4 {parsedContent.props?.class || ''}">
      {#each parsedContent.children || [] as child}
        <svelte:self content={child} {data} {onAction} />
      {/each}
    </div>
  {:else if parsedContent.type === 'flex'}
    <div class="flex flex-wrap gap-4 {parsedContent.props?.class || ''}">
      {#each parsedContent.children || [] as child}
        <svelte:self content={child} {data} {onAction} />
      {/each}
    </div>
  {:else if parsedContent.type === 'card'}
    <div
      class="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-xs transition hover:shadow-sm dark:border-gray-800 dark:bg-gray-900 {parsedContent
        .props?.class || ''}"
    >
      {#if parsedContent.props?.image}
        <div class="relative h-48 w-full overflow-hidden bg-gray-100 dark:bg-gray-800">
          <img src={parsedContent.props.image} alt="Cover" class="h-full w-full object-cover" />
          {#if parsedContent.props?.badge}
            <div class="absolute top-3 left-3">
              <svelte:self
                content={{ type: 'badge', props: parsedContent.props.badge }}
                {data}
                {onAction}
              />
            </div>
          {/if}
          {#if parsedContent.props?.price}
            <div
              class="absolute right-3 bottom-3 rounded-lg bg-black/70 px-3 py-1.5 text-sm font-bold text-white backdrop-blur-md"
            >
              {template(parsedContent.props.price, data)}
            </div>
          {/if}
        </div>
      {/if}

      <div class="p-5">
        <div class="flex items-start justify-between gap-4">
          <div class="flex-1">
            {#if parsedContent.props?.title}
              <h3 class="text-lg font-bold text-gray-900 dark:text-gray-100">
                {template(parsedContent.props.title, data)}
              </h3>
            {/if}
            {#if parsedContent.props?.subtitle}
              <p class="mt-0.5 text-sm text-gray-500 dark:text-gray-400">
                {template(parsedContent.props.subtitle, data)}
              </p>
            {/if}
          </div>
          {#if parsedContent.props?.rating}
            <div
              class="flex items-center gap-1 rounded-full bg-yellow-50 px-2 py-0.5 text-xs font-bold text-yellow-700 dark:bg-yellow-400/10 dark:text-yellow-500"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                class="size-3"
              >
                <path
                  fill-rule="evenodd"
                  d="M10.868 2.884c-.321-.772-1.415-.772-1.736 0l-1.83 4.401-4.753.381c-.833.067-1.171 1.107-.536 1.651l3.62 3.102-1.106 4.637c-.194.813.691 1.456 1.405 1.02L10 15.591l4.069 2.485c.713.436 1.598-.207 1.404-1.02l-1.106-4.637 3.62-3.102c.635-.544.297-1.584-.536-1.65l-4.752-.382-1.831-4.401Z"
                  clip-rule="evenodd"
                />
              </svg>
              {parsedContent.props.rating}
            </div>
          {/if}
        </div>

        {#if parsedContent.props?.description}
          <p class="mt-3 text-sm text-gray-600 dark:text-gray-300">
            {template(parsedContent.props.description, data)}
          </p>
        {/if}

        {#if parsedContent.children && parsedContent.children.length > 0}
          <div class="mt-4 space-y-3">
            {#each parsedContent.children as child}
              <svelte:self content={child} {data} {onAction} />
            {/each}
          </div>
        {/if}
      </div>
    </div>
  {:else if parsedContent.type === 'card-grid'}
    <div
      class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 {parsedContent.props?.class ||
        ''}"
    >
      {#if parsedContent.children}
        {#each parsedContent.children as child}
          <div class="h-full">
            <svelte:self content={child} {data} {onAction} />
          </div>
        {/each}
      {/if}
    </div>
  {:else if parsedContent.type === 'button'}
    <button
      on:click={(e) => {
        e.stopPropagation();
        onAction({
          type: 'button',
          action_text: template(
            parsedContent.props?.action_text || parsedContent.props?.label || 'Button clicked',
            data,
          ),
          props: parsedContent.props,
        });
      }}
      class="inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-bold transition active:scale-[0.98] {parsedContent
        .props?.class || ''} 
      {(parsedContent.props?.variant || 'primary') === 'primary'
        ? 'bg-blue-600 text-white shadow-xs hover:bg-blue-700'
        : (parsedContent.props?.variant || 'primary') === 'secondary'
          ? 'bg-gray-100 text-gray-900 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-100 dark:hover:bg-gray-700'
          : 'border border-gray-200 bg-transparent text-gray-600 hover:bg-gray-50'}"
    >
      {#if parsedContent.props?.icon}
        <div class="size-4 opacity-80">
          {#if parsedContent.props.icon === 'calendar-check'}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="2"
              stroke="currentColor"
              ><path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5m-9-6h.008v.008H12v-.008ZM12 15h.008v.008H12V15Zm0 2.25h.008v.008H12v-.008ZM9.75 15h.008v.008H9.75V15Zm0 2.25h.008v.008H9.75v-.008ZM7.5 15h.008v.008H7.5V15Zm0 2.25h.008v.008H7.5v-.008Zm6.75-4.5h.008v.008h-.008v-.008Zm0 2.25h.008v.008h-.008V15Zm0 2.25h.008v.008h-.008v-.008Zm2.25-4.5h.008v.008H16.5v-.008Zm0 2.25h.008v.008H16.5V15Z"
              /></svg
            >
          {:else if parsedContent.props.icon === 'info'}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="2"
              stroke="currentColor"
              ><path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z"
              /></svg
            >
          {:else}
            <span class="text-[10px]">{parsedContent.props.icon}</span>
          {/if}
        </div>
      {/if}
      {template(parsedContent.props?.label || parsedContent.props?.value || 'Button', data)}
    </button>
  {:else if parsedContent.type === 'text'}
    <div class="text-sm text-gray-600 dark:text-gray-300 {parsedContent.props?.class || ''}">
      {template(parsedContent.props?.value || parsedContent.props?.text || '', data)}
    </div>
  {:else if parsedContent.type === 'badge'}
    <span
      class="inline-flex items-center rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-bold tracking-wider text-blue-700 uppercase ring-1 ring-blue-700/10 ring-inset dark:bg-blue-400/10 dark:text-blue-400 dark:ring-blue-400/20 {parsedContent
        .props?.class || ''}"
    >
      {template(
        parsedContent.props?.value || parsedContent.props?.label || parsedContent.props?.text || '',
        data,
      )}
    </span>
  {:else if parsedContent.type === 'divider'}
    <hr class="border-gray-100 dark:border-gray-800 {parsedContent.props?.class || ''}" />
  {/if}
{:else}
  <div
    class="flex h-64 flex-col items-center justify-center rounded-2xl border-2 border-dashed border-gray-100 dark:border-gray-800"
  >
    <div class="text-sm text-gray-400 italic">{$i18n.t('Invalid or Empty JSON')}</div>
    <div class="mt-2 text-[10px] text-gray-300">
      {$i18n.t('Start typing code to see the preview')}
    </div>
  </div>
{/if}
