<script lang="ts">
  import { Pagination } from 'bits-ui';
  import { createEventDispatcher } from 'svelte';

  import ChevronLeft from '../icons/ChevronLeft.svelte';
  import ChevronRight from '../icons/ChevronRight.svelte';

  export let page = 0;
  export let count = 0;
  export let perPage = 20;
</script>

<div class="flex justify-center">
  <Pagination.Root bind:page {count} {perPage}>
    {#snippet children({ pages })}
      <div class="my-2 flex items-center">
        <Pagination.PrevButton
          class="dark:hover:bg-gray-850 mr-[25px] inline-flex size-8 items-center justify-center rounded-[9px] bg-transparent hover:bg-gray-50 active:scale-98 disabled:cursor-not-allowed disabled:text-gray-400 hover:disabled:bg-transparent dark:disabled:text-gray-700 dark:hover:disabled:bg-transparent"
        >
          <ChevronLeft className="size-4" strokeWidth="2" />
        </Pagination.PrevButton>
        <div class="flex items-center gap-2.5">
          {#each pages as page (page.key)}
            {#if page.type === 'ellipsis'}
              <div class="text-foreground-alt text-sm font-medium">...</div>
            {:else}
              <Pagination.Page
                {page}
                class="dark:hover:bg-gray-850 hover:bg-dark-10 dark:data-selected:bg-gray-850 inline-flex size-8 items-center justify-center rounded-[9px] bg-transparent text-sm font-medium transition hover:bg-gray-50 active:scale-98 disabled:cursor-not-allowed disabled:opacity-50 hover:disabled:bg-transparent data-selected:bg-gray-50 data-selected:text-gray-700 data-selected:hover:bg-gray-100 dark:data-selected:text-gray-50 dark:data-selected:hover:bg-gray-800"
              >
                {page.value}
              </Pagination.Page>
            {/if}
          {/each}
        </div>
        <Pagination.NextButton
          class="dark:hover:bg-gray-850  ml-[25px] inline-flex size-8 items-center justify-center rounded-[9px] bg-transparent hover:bg-gray-50 active:scale-98 disabled:cursor-not-allowed disabled:text-gray-400 hover:disabled:bg-transparent dark:disabled:text-gray-700 dark:hover:disabled:bg-transparent"
        >
          <ChevronRight className="size-4" strokeWidth="2" />
        </Pagination.NextButton>
      </div>
    {/snippet}
  </Pagination.Root>
</div>
