<script lang="ts">
  import VirtualList from '@sveltejs/svelte-virtual-list';

  import { getContext } from 'svelte';

  import { WEBUI_BASE_URL } from '$lib/constants';

  import Dropdown from '$lib/components/common/Dropdown.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';

  import emojiGroups from '$lib/emoji-groups.json';
  import emojiShortCodes from '$lib/emoji-shortcodes.json';

  const i18n = getContext('i18n');

  export let onClose = () => {};
  export let onSubmit = (name) => {};
  export let side = 'top';
  export let align = 'start';
  export let user = null;
  export let selected = null;

  let show = false;
  let emojis = emojiShortCodes;
  let search = '';
  let flattenedEmojis = [];
  let emojiRows = [];

  // Reactive statement to filter the emojis based on search query
  $: {
    if (search) {
      emojis = Object.keys(emojiShortCodes).reduce((acc, key) => {
        if (key.includes(search.toLowerCase())) {
          acc[key] = emojiShortCodes[key];
        } else {
          if (Array.isArray(emojiShortCodes[key])) {
            const filtered = emojiShortCodes[key].filter((emoji) =>
              emoji.includes(search.toLowerCase()),
            );
            if (filtered.length) {
              acc[key] = filtered;
            }
          } else {
            if (emojiShortCodes[key].includes(search.toLowerCase())) {
              acc[key] = emojiShortCodes[key];
            }
          }
        }
        return acc;
      }, {});
    } else {
      emojis = emojiShortCodes;
    }
  }
  // Flatten emoji groups and group them into rows of 8 for virtual scrolling
  $: {
    flattenedEmojis = [];
    Object.keys(emojiGroups).forEach((group) => {
      const groupEmojis = emojiGroups[group].filter((emoji) => emojis[emoji]);
      if (groupEmojis.length > 0) {
        flattenedEmojis.push({ type: 'group', label: group });
        flattenedEmojis.push(
          ...groupEmojis.map((emoji) => ({
            type: 'emoji',
            name: emoji,
            shortCodes:
              typeof emojiShortCodes[emoji] === 'string'
                ? [emojiShortCodes[emoji]]
                : emojiShortCodes[emoji],
          })),
        );
      }
    });
    // Group emojis into rows of 8
    emojiRows = [];
    let currentRow = [];
    flattenedEmojis.forEach((item) => {
      if (item.type === 'emoji') {
        currentRow.push(item);
        if (currentRow.length === 8) {
          emojiRows.push(currentRow);
          currentRow = [];
        }
      } else if (item.type === 'group') {
        if (currentRow.length > 0) {
          emojiRows.push(currentRow); // Push the remaining row
          currentRow = [];
        }
        emojiRows.push([item]); // Add the group label as a separate row
      }
    });
    if (currentRow.length > 0) {
      emojiRows.push(currentRow); // Push the final row
    }
  }
  const ROW_HEIGHT = 48; // Approximate height for a row with multiple emojis
  // Handle emoji selection
  function selectEmoji(emoji) {
    const selectedCode = emoji.shortCodes[0];
    if (selected === selectedCode) {
      onSubmit(null);
    } else {
      onSubmit(selectedCode);
    }
    show = false;
  }
</script>

<Dropdown
  bind:show
  {align}
  onOpenChange={(state) => {
    if (state === false) {
      search = '';
      onClose();
    }
  }}
>
  <slot />

  <div slot="content">
    <div
      class="dark:bg-gray-850 z-9999 w-80 max-w-full rounded-3xl border border-gray-100 bg-white shadow-lg dark:border-gray-800 dark:text-white"
    >
      <div class="mb-1 px-4 pt-2.5 pb-2">
        <input
          type="text"
          class="w-full bg-transparent text-sm outline-hidden"
          placeholder={$i18n.t('Search all emojis')}
          bind:value={search}
        />
      </div>

      <!-- Virtualized Emoji List -->
      <div class="flex h-96 w-full justify-start overflow-y-auto px-3 pb-3 text-sm">
        {#if emojiRows.length === 0}
          <div class="text-center text-xs text-gray-500 dark:text-gray-400">
            {$i18n.t('No results')}
          </div>
        {:else}
          <div class="ml-0.5 flex w-full">
            <VirtualList rowHeight={ROW_HEIGHT} items={emojiRows} height={384} let:item>
              <div class="w-full">
                {#if item.length === 1 && item[0].type === 'group'}
                  <!-- Render group header -->
                  <div class="mb-2 text-xs font-medium text-gray-500 dark:text-gray-400">
                    {item[0].label}
                  </div>
                {:else}
                  <!-- Render emojis in a row -->
                  <div class="flex w-full items-center gap-1.5">
                    {#each item as emojiItem}
                      <Tooltip
                        content={emojiItem.shortCodes.map((code) => `:${code}:`).join(', ')}
                        placement="top"
                      >
                        <button
                          class="cursor-pointer rounded-lg p-1.5 transition hover:bg-gray-200 dark:hover:bg-gray-700 {selected ===
                          emojiItem.shortCodes[0]
                            ? 'bg-gray-200 dark:bg-gray-700'
                            : ''}"
                          on:click={() => selectEmoji(emojiItem)}
                        >
                          <img
                            src="/assets/emojis/{emojiItem.name.toLowerCase()}.svg"
                            alt={emojiItem.name}
                            class="size-5"
                            loading="lazy"
                          />
                        </button>
                      </Tooltip>
                    {/each}
                  </div>
                {/if}
              </div>
            </VirtualList>
          </div>
        {/if}
      </div>
    </div>
  </div>
</Dropdown>
