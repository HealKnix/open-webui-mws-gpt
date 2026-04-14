<script lang="ts">
  import { getContext } from 'svelte';
  import { toast } from 'svelte-sonner';

  import { mobile, showArchivedChats, showSidebar, user } from '$lib/stores';

  import { slide } from 'svelte/transition';
  import { page } from '$app/stores';

  import { WEBUI_API_BASE_URL } from '$lib/constants';

  import UserMenu from '$lib/components/layout/Sidebar/UserMenu.svelte';
  import PencilSquare from '../icons/PencilSquare.svelte';
  import Tooltip from '../common/Tooltip.svelte';
  import Sidebar from '../icons/Sidebar.svelte';
  import Hashtag from '../icons/Hashtag.svelte';
  import Lock from '../icons/Lock.svelte';
  import UserAlt from '../icons/UserAlt.svelte';
  import ChannelInfoModal from './ChannelInfoModal.svelte';
  import Users from '../icons/Users.svelte';
  import Pin from '../icons/Pin.svelte';
  import PinnedMessagesModal from './PinnedMessagesModal.svelte';

  const i18n = getContext('i18n');

  let showChannelPinnedMessagesModal = false;
  let showChannelInfoModal = false;

  const hasPublicReadGrant = (grants: any) =>
    Array.isArray(grants) &&
    grants.some(
      (grant) =>
        grant?.principal_type === 'user' &&
        grant?.principal_id === '*' &&
        grant?.permission === 'read',
    );

  const isPublicChannel = (channel: any): boolean => {
    if (channel?.type === 'group') {
      if (typeof channel?.is_private === 'boolean') {
        return !channel.is_private;
      }
      return hasPublicReadGrant(channel?.access_grants);
    }
    return hasPublicReadGrant(channel?.access_grants);
  };

  export let channel;

  export let onPin = (messageId, pinned) => {};
  export let onUpdate = () => {};
</script>

<PinnedMessagesModal bind:show={showChannelPinnedMessagesModal} {channel} {onPin} />
<ChannelInfoModal bind:show={showChannelInfoModal} {channel} {onUpdate} />
<nav class="drag-region sticky top-0 z-30 -mb-8 flex w-full flex-col items-center px-1.5 py-1">
  <div
    id="navbar-bg-gradient-to-b"
    class=" pointer-events-none absolute inset-0 -bottom-7 z-[-1] bg-linear-to-b from-white via-white via-50% to-transparent dark:from-gray-900 dark:via-gray-900 dark:to-transparent"
  ></div>

  <div class=" mx-auto flex w-full max-w-full bg-transparent px-1 pt-0.5">
    <div class="flex w-full max-w-full items-center">
      {#if $mobile}
        <div
          class="{$showSidebar
            ? 'md:hidden'
            : ''} mt-0.5 mr-1.5 flex flex-none items-center self-start text-gray-600 dark:text-gray-400"
        >
          <Tooltip
            content={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}
            interactive={true}
          >
            <button
              id="sidebar-toggle-button"
              class=" dark:hover:bg-gray-850 cursor- flex cursor-pointer rounded-lg transition hover:bg-gray-100"
              on:click={() => {
                showSidebar.set(!$showSidebar);
              }}
            >
              <div class=" self-center p-1.5">
                <Sidebar />
              </div>
            </button>
          </Tooltip>
        </div>
      {/if}

      <div
        class="flex max-w-full flex-1 items-center overflow-hidden py-0.5
			{$showSidebar ? 'ml-1' : ''}
			"
      >
        {#if channel}
          <div class="flex shrink-0 items-center gap-0.5">
            {#if channel?.type === 'dm'}
              {#if channel?.users}
                {@const channelMembers = channel.users.filter((u) => u.id !== $user?.id)}
                <div class="relative mr-1.5 flex">
                  {#each channelMembers.slice(0, 2) as u, index}
                    <img
                      src={`${WEBUI_API_BASE_URL}/users/${u.id}/profile/image`}
                      alt={u.name}
                      class=" size-6.5 rounded-full border-2 border-white dark:border-gray-900 {index ===
                      1
                        ? '-ml-3'
                        : ''}"
                    />
                  {/each}

                  {#if channelMembers.length === 1}
                    <div class="absolute right-0 bottom-0">
                      <span class="relative flex size-2">
                        {#if channelMembers[0]?.is_active}
                          <span
                            class="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75"
                          ></span>
                        {/if}
                        <span
                          class="relative inline-flex size-2 rounded-full {channelMembers[0]
                            ?.is_active
                            ? 'bg-green-500'
                            : 'bg-gray-300 dark:bg-gray-700'} border-[1.5px] border-white dark:border-gray-900"
                        ></span>
                      </span>
                    </div>
                  {/if}
                </div>
              {:else}
                <Users className="size-4 ml-1 mr-0.5" strokeWidth="2" />
              {/if}
            {:else}
              <div class=" flex size-4.5 items-center justify-center">
                {#if isPublicChannel(channel)}
                  <Hashtag className="size-3.5" strokeWidth="2.5" />
                {:else}
                  <Lock className="size-5" strokeWidth="2" />
                {/if}
              </div>
            {/if}

            <div class=" line-clamp-1 w-full flex-1 self-center overflow-hidden text-left">
              {#if channel?.name}
                {channel.name}
              {:else}
                {channel?.users
                  ?.filter((u) => u.id !== $user?.id)
                  .map((u) => u.name)
                  .join(', ')}
              {/if}
            </div>
          </div>
        {/if}
      </div>

      <div class="flex flex-none items-center gap-1 self-start text-gray-600 dark:text-gray-400">
        {#if channel}
          <Tooltip content={$i18n.t('Pinned Messages')}>
            <button
              class=" dark:border-gray-850 dark:hover:bg-gray-850 flex cursor-pointer rounded-xl border border-gray-50 px-1.5 py-1.5 text-gray-600 transition hover:bg-gray-50 dark:text-gray-400"
              aria-label="Pinned Messages"
              type="button"
              on:click={() => {
                showChannelPinnedMessagesModal = true;
              }}
            >
              <div class=" m-auto flex items-center gap-0.5 self-center">
                <Pin className=" size-4" strokeWidth="1.5" />
              </div>
            </button>
          </Tooltip>

          {#if channel?.user_count !== undefined}
            <Tooltip content={$i18n.t('Users')}>
              <button
                class=" dark:border-gray-850 dark:hover:bg-gray-850 flex cursor-pointer rounded-xl border border-gray-50 px-1.5 py-1 text-gray-600 transition hover:bg-gray-50 dark:text-gray-400"
                aria-label="User Count"
                type="button"
                on:click={() => {
                  showChannelInfoModal = true;
                }}
              >
                <div class=" m-auto flex items-center gap-0.5 self-center">
                  <UserAlt className=" size-4" strokeWidth="1.5" />

                  <div class="text-sm">
                    {channel.user_count}
                  </div>
                </div>
              </button>
            </Tooltip>
          {/if}
        {/if}

        {#if $user !== undefined}
          <UserMenu
            className="w-[240px]"
            role={$user?.role}
            help={true}
            on:show={(e) => {
              if (e.detail === 'archived-chat') {
                showArchivedChats.set(true);
              }
            }}
          >
            <button
              class="dark:hover:bg-gray-850 flex w-full rounded-xl p-1.5 transition select-none hover:bg-gray-50"
              aria-label="User Menu"
            >
              <div class=" self-center">
                <img
                  src={`${WEBUI_API_BASE_URL}/users/${$user?.id}/profile/image`}
                  class="size-6 rounded-full object-cover"
                  alt="User profile"
                  draggable="false"
                />
              </div>
            </button>
          </UserMenu>
        {/if}
      </div>
    </div>
  </div>
</nav>
