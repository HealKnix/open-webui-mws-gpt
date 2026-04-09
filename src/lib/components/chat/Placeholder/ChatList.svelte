<script lang="ts">
  import { getContext, onMount } from 'svelte';
  const i18n = getContext('i18n');

  import dayjs from 'dayjs';
  import localizedFormat from 'dayjs/plugin/localizedFormat';
  import { getTimeRange } from '$lib/utils';
  import ChevronUp from '$lib/components/icons/ChevronUp.svelte';
  import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
  import Loader from '$lib/components/common/Loader.svelte';
  import Spinner from '$lib/components/common/Spinner.svelte';

  dayjs.extend(localizedFormat);

  export let chats = [];

  export let chatListLoading = false;
  export let allChatsLoaded = false;

  export let loadHandler: Function = null;

  let chatList = null;

  const init = async () => {
    if (chats.length === 0) {
      chatList = [];
    } else {
      chatList = chats.map((chat) => ({
        ...chat,
        time_range: getTimeRange(chat.updated_at),
      }));

      chatList.sort((a, b) => {
        if (direction === 'asc') {
          return a[orderBy] > b[orderBy] ? 1 : -1;
        } else {
          return a[orderBy] < b[orderBy] ? 1 : -1;
        }
      });
    }
  };

  const setSortKey = (key) => {
    if (orderBy === key) {
      direction = direction === 'asc' ? 'desc' : 'asc';
    } else {
      orderBy = key;
      direction = 'asc';
    }

    init();
  };

  let orderBy = 'updated_at';
  let direction = 'desc'; // 'asc' or 'desc'

  $: if (chats) {
    init();
  }
</script>

{#if chatList}
  {#if chatList.length > 0}
    <div class="-mr-0.5 mb-1 flex items-center text-xs font-medium">
      <button
        class="basis-3/5 cursor-pointer px-1.5 py-1 select-none"
        on:click={() => setSortKey('title')}
      >
        <div class="flex items-center gap-1.5">
          {$i18n.t('Title')}

          {#if orderBy === 'title'}
            <span class="font-normal"
              >{#if direction === 'asc'}
                <ChevronUp className="size-2" />
              {:else}
                <ChevronDown className="size-2" />
              {/if}
            </span>
          {:else}
            <span class="invisible">
              <ChevronUp className="size-2" />
            </span>
          {/if}
        </div>
      </button>
      <button
        class="hidden cursor-pointer justify-end px-1.5 py-1 select-none sm:flex sm:basis-2/5"
        on:click={() => setSortKey('updated_at')}
      >
        <div class="flex items-center gap-1.5">
          {$i18n.t('Updated at')}

          {#if orderBy === 'updated_at'}
            <span class="font-normal"
              >{#if direction === 'asc'}
                <ChevronUp className="size-2" />
              {:else}
                <ChevronDown className="size-2" />
              {/if}
            </span>
          {:else}
            <span class="invisible">
              <ChevronUp className="size-2" />
            </span>
          {/if}
        </div>
      </button>
    </div>
  {/if}

  <div class="mb-3 w-full text-left text-sm">
    {#if chatList.length === 0}
      <div
        class="flex h-full min-h-20 w-full items-center justify-center px-5 text-center text-xs text-gray-500 dark:text-gray-400"
      >
        {$i18n.t('No chats found')}
      </div>
    {/if}

    {#each chatList as chat, idx (chat.id)}
      {#if (idx === 0 || (idx > 0 && chat.time_range !== chatList[idx - 1].time_range)) && chat?.time_range}
        <div
          class="w-full text-xs font-medium text-gray-500 dark:text-gray-500 {idx === 0
            ? ''
            : 'pt-5'} px-2 pb-2"
        >
          {$i18n.t(chat.time_range)}
          <!-- localisation keys for time_range to be recognized from the i18next parser (so they don't get automatically removed):
							{$i18n.t('Today')}
							{$i18n.t('Yesterday')}
							{$i18n.t('Previous 7 days')}
							{$i18n.t('Previous 30 days')}
							{$i18n.t('January')}
							{$i18n.t('February')}
							{$i18n.t('March')}
							{$i18n.t('April')}
							{$i18n.t('May')}
							{$i18n.t('June')}
							{$i18n.t('July')}
							{$i18n.t('August')}
							{$i18n.t('September')}
							{$i18n.t('October')}
							{$i18n.t('November')}
							{$i18n.t('December')}
							-->
        </div>
      {/if}

      <a
        class=" dark:hover:bg-gray-850 flex w-full items-center justify-between rounded-lg px-3 py-2 text-sm hover:bg-gray-50"
        draggable="false"
        href={`/c/${chat.id}`}
        on:click={() => (show = false)}
      >
        <div class="line-clamp-1 w-full text-ellipsis sm:basis-3/5">
          {chat?.title}
        </div>

        <div class="hidden items-center justify-end sm:flex sm:basis-2/5">
          <div class=" text-xs text-gray-500 dark:text-gray-400">
            {dayjs(chat?.updated_at * 1000).calendar()}
          </div>
        </div>
      </a>
    {/each}

    {#if !allChatsLoaded && loadHandler}
      <Loader
        on:visible={(e) => {
          if (!chatListLoading) {
            loadHandler();
          }
        }}
      >
        <div class="flex w-full animate-pulse items-center justify-center gap-2 py-1 text-xs">
          <Spinner className=" size-4" />
          <div class=" ">Loading...</div>
        </div>
      </Loader>
    {/if}
  </div>
{/if}
