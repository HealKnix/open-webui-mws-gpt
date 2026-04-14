<script lang="ts">
  import { cn } from '$lib/utils';
  import { getContext } from 'svelte';
  import Button from '../Button.svelte';
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
  <!-- Container -->
  {#if parsedContent.type === 'container' || (!parsedContent.type && parsedContent.children)}
    <div class="space-y-4">
      {#each parsedContent.children || [] as child}
        <svelte:self content={child} {data} {onAction} />
      {/each}
    </div>
    <!-- Flex -->
  {:else if parsedContent.type === 'flex'}
    <div class="flex flex-wrap gap-4">
      {#each parsedContent.children || [] as child}
        <svelte:self content={child} {data} {onAction} />
      {/each}
    </div>
    <!-- Card -->
  {:else if parsedContent.type === 'card'}
    <div
      class="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-xs transition hover:shadow-sm dark:border-gray-800 dark:bg-gray-900"
    >
      {#if parsedContent.props?.image}
        <div class="relative h-48 w-full overflow-hidden bg-gray-100 dark:bg-gray-800">
          <img src={parsedContent.props.image} alt="Cover" class="h-full w-full object-cover" />
          {#if parsedContent.props?.badge}
            <div
              class="absolute top-3 left-3 inline-flex items-center rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-bold tracking-wider text-blue-700 uppercase ring-1 ring-blue-700/10 ring-inset dark:bg-blue-400/10 dark:text-blue-400 dark:ring-blue-400/20"
            >
              {template(parsedContent.props.badge, data)}
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
              {template(parsedContent.props.rating, data)}
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
    <!-- Card Grid -->
  {:else if parsedContent.type === 'card-grid'}
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {#if parsedContent.children}
        {#each parsedContent.children as child}
          <div class="h-full">
            <svelte:self content={child} {data} {onAction} />
          </div>
        {/each}
      {/if}
    </div>
    <!-- Button -->
  {:else if parsedContent.type === 'button'}
    <Button
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
      color={parsedContent.props?.color || 'primary'}
      variant={parsedContent.props?.variant || 'solid'}
    >
      {template(parsedContent.props?.label || parsedContent.props?.value || 'Button', data)}
    </Button>
    <!-- Text -->
  {:else if parsedContent.type === 'text'}
    <div class="text-sm text-gray-600 dark:text-gray-300">
      {template(parsedContent.props?.value || parsedContent.props?.text || '', data)}
    </div>
    <!-- Badge -->
  {:else if parsedContent.type === 'badge'}
    <span
      class="inline-flex items-center rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-bold tracking-wider text-blue-700 uppercase ring-1 ring-blue-700/10 ring-inset dark:bg-blue-400/10 dark:text-blue-400 dark:ring-blue-400/20"
    >
      {template(
        parsedContent.props?.value || parsedContent.props?.label || parsedContent.props?.text || '',
        data,
      )}
    </span>
    <!-- Divider -->
  {:else if parsedContent.type === 'divider'}
    <hr class="border-gray-100 dark:border-gray-800" />
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
