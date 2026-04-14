<script lang="ts">
  import { getContext, createEventDispatcher, tick } from 'svelte';
  import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
  import Check from '$lib/components/icons/Check.svelte';
  import Search from '$lib/components/icons/Search.svelte';
  import Select from '$lib/components/common/Select.svelte';
  import { cn } from '$lib/utils';
  import Input from './Input.svelte';

  const i18n = getContext('i18n');
  const dispatch = createEventDispatcher();

  export let value = '';
  export let align: 'start' | 'end' = 'start';
  export let items: {
    value: string;
    label: string;
    description?: string;
    icon?: any;
  }[] = [];
  export let placeholder = $i18n.t('Select');
  export let onChange: (value: string) => void = (val) => {
    dispatch('change', val);
  };

  export let search = false;
  export let searchPlaceholder = $i18n.t('Search');

  export let triggerClass = '';

  let query = '';
  let open = false;
  let inputEl;

  $: filteredItems = query
    ? items.filter(
        (i) =>
          i.label.toLowerCase().includes(query.toLowerCase()) ||
          i.value.toLowerCase().includes(query.toLowerCase()),
      )
    : items;

  $: selectedItem = items.find((i) => i.value === value);

  $: if (open && search) {
    tick().then(() => {
      inputEl?.focus();
    });
  }
</script>

<Select
  bind:value
  bind:open
  {items}
  {placeholder}
  {align}
  triggerClass={cn(
    'relative w-full not-sm:max-w-52 flex items-center justify-between gap-2 px-3 py-1.5 transition-all rounded-xl border border-border bg-background outline-none ring-primary focus-visible:ring-2 ring-offset-0 focus-visible:ring-offset-2 ring-offset-background text-wrap',
    triggerClass,
  )}
  contentClassName={cn(search && 'max-h-80 flex flex-col')}
  onChange={() => onChange(value)}
>
  <svelte:fragment slot="trigger" let:selectedLabel let:open>
    <div class="flex flex-1 items-center gap-2 overflow-hidden">
      {#if selectedItem?.icon && typeof selectedItem?.icon !== 'string'}
        <div class="flex shrink-0 items-center justify-center">
          <svelte:component
            this={selectedItem.icon}
            className="size-3.5 {selectedItem ? 'text-primary' : 'text-gray-500'}"
          />
        </div>
      {:else if selectedItem?.icon}
        <div
          class={cn(
            'flex shrink-0 items-center justify-center',
            selectedItem ? 'text-primary' : 'text-gray-500',
          )}
        >
          {selectedItem.icon}
        </div>
      {/if}
      <span
        class="truncate text-sm {selectedItem
          ? 'text-gray-900 dark:text-gray-100'
          : 'text-gray-400'}"
      >
        {selectedLabel}
      </span>
    </div>
    <ChevronDown
      className="size-3.5 text-gray-400 transition-transform duration-300 {open
        ? 'rotate-180'
        : ''}"
      strokeWidth="2.5"
    />
  </svelte:fragment>

  <svelte:fragment let:selectItem>
    {#if search}
      <div class="flex w-full space-x-2 px-2 pb-0.5">
        <div class="flex flex-1">
          <div class=" mr-2 self-center">
            <Search className="size-3.5" />
          </div>
          <input
            class="w-full rounded-r-xl bg-transparent py-1 pr-4 text-sm outline-hidden"
            bind:value={query}
            placeholder={$i18n.t('Search')}
          />
        </div>
      </div>
    {/if}

    <div class="scrollbar-none flex flex-col gap-0.5 overflow-y-auto">
      {#if filteredItems.length === 0}
        <div class="text-muted-foreground pt-4 pb-6 text-center text-xs">
          {$i18n.t('No results found')}
        </div>
      {:else}
        {#each filteredItems as item}
          <button
            class="hover:bg-card/50 group flex w-full cursor-pointer items-center gap-3 rounded-xl px-3 py-2 text-sm transition-all duration-150 active:scale-[0.99]"
            type="button"
            on:click={() => {
              selectItem(item);
              query = '';
            }}
          >
            {#if item.icon && typeof item.icon !== 'string'}
              <div
                class="flex size-8 shrink-0 items-center justify-center rounded-lg transition-colors
            {value === item.value ? 'bg-primary/10 text-primary' : 'bg-card'}"
              >
                <svelte:component this={item.icon} className="size-4" />
              </div>
            {:else if item.icon}
              <div
                class={cn(
                  'flex shrink-0 items-center justify-center',
                  value === item.value ? 'text-primary' : 'text-gray-500',
                )}
              >
                {item.icon}
              </div>
            {/if}

            <div class="flex flex-1 flex-col items-start overflow-hidden text-left">
              <span
                class="text-sm font-medium {value === item.value
                  ? 'text-primary'
                  : 'text-gray-700 dark:text-gray-200'}"
              >
                {item.label}
              </span>
              {#if item.description}
                <span
                  class="line-clamp-1 text-[11px] leading-tight text-gray-500 dark:text-gray-400"
                >
                  {item.description}
                </span>
              {/if}
            </div>

            <div
              class="flex shrink-0 items-center justify-center {value === item.value
                ? 'text-primary'
                : 'invisible opacity-0'} transition-all"
            >
              <Check className="size-4" strokeWidth="3" />
            </div>
          </button>
        {/each}
      {/if}
    </div>
  </svelte:fragment>
</Select>
