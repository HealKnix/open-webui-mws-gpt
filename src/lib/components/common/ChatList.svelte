<script lang="ts">
  import { getContext } from 'svelte';
  import dayjs from 'dayjs';
  import calendar from 'dayjs/plugin/calendar';
  import { WEBUI_API_BASE_URL } from '$lib/constants';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import Loader from '$lib/components/common/Loader.svelte';

  dayjs.extend(calendar);

  const i18n = getContext('i18n');

  export let chatList: Array<{
    id: string;
    title: string;
    updated_at: number;
    user_id?: string;
    user_name?: string;
    time_range?: string;
  }> | null = null;
  export let loading = false;
  export let allLoaded = false;
  export let showUserInfo = false;
  export let shareUrl = false;
  export let emptyMessage = 'No chats found';
  export let onLoadMore: (() => void) | null = null;
  export let onChatClick: ((chatId: string) => void) | null = null;
</script>

<div>
  {#if chatList && chatList.length > 0}
    <div class="mb-1.5 flex text-xs font-medium">
      {#if showUserInfo}
        <div class="w-32 px-1.5 py-1">
          {$i18n.t('User')}
        </div>
      {/if}
      <div class="px-1.5 py-1 {showUserInfo ? 'flex-1' : 'basis-3/5'}">
        {$i18n.t('Title')}
      </div>
      <div class="hidden px-1.5 py-1 sm:flex {showUserInfo ? 'w-28' : 'basis-2/5'} justify-end">
        {$i18n.t('Updated at')}
      </div>
    </div>
  {/if}
  <div class="max-h-[22rem] overflow-y-scroll">
    {#if loading && (!chatList || chatList.length === 0)}
      <div class="flex justify-center py-8">
        <Spinner />
      </div>
    {:else if !chatList || chatList.length === 0}
      <div class="py-8 text-center text-sm text-gray-500">
        {$i18n.t(emptyMessage)}
      </div>
    {:else}
      {#each chatList as chat, idx (chat.id)}
        {#if chat.time_range && (idx === 0 || chat.time_range !== chatList[idx - 1]?.time_range)}
          <div
            class="w-full text-xs font-medium text-gray-500 dark:text-gray-500 {idx === 0
              ? ''
              : 'pt-5'} px-2 pb-2"
          >
            {$i18n.t(chat.time_range)}
          </div>
        {/if}

        <div
          class="dark:hover:bg-gray-850 flex w-full items-center rounded-lg px-3 py-2 text-sm hover:bg-gray-50"
        >
          {#if showUserInfo && chat.user_id}
            <div class="flex w-32 shrink-0 items-center gap-2">
              <img
                src="{WEBUI_API_BASE_URL}/users/{chat.user_id}/profile/image"
                alt={chat.user_name || 'User'}
                class="size-5 shrink-0 rounded-full object-cover"
              />
              <span class="truncate text-xs text-gray-600 dark:text-gray-400"
                >{chat.user_name || 'Unknown'}</span
              >
            </div>
          {/if}
          <a
            class={showUserInfo ? 'flex-1' : 'basis-3/5'}
            href={shareUrl ? `/s/${chat.id}` : `/c/${chat.id}`}
            on:click={() => onChatClick?.(chat.id)}
          >
            <div class="line-clamp-1 w-full text-ellipsis">
              {chat.title}
            </div>
          </a>

          <div class="{showUserInfo ? 'w-28' : 'basis-2/5'} flex items-center justify-end">
            <div class="hidden text-xs text-gray-500 sm:flex dark:text-gray-400">
              {dayjs(chat.updated_at * 1000).calendar(null, {
                sameDay: '[Today] h:mm A',
                lastDay: '[Yesterday] h:mm A',
                lastWeek: 'MMM D',
                sameElse: 'MMM D, YYYY',
              })}
            </div>
          </div>
        </div>
      {/each}

      {#if !allLoaded && onLoadMore}
        <Loader
          on:visible={() => {
            if (!loading) {
              onLoadMore();
            }
          }}
        >
          <div class="flex w-full animate-pulse items-center justify-center gap-2 py-1 text-xs">
            <Spinner className="size-4" />
            <div>{$i18n.t('Loading...')}</div>
          </div>
        </Loader>
      {/if}
    {/if}
  </div>
</div>
