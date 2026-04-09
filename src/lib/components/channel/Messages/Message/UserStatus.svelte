<script lang="ts">
  import { getContext, onMount } from 'svelte';

  const i18n = getContext('i18n');

  import { user as _user, channels, socket } from '$lib/stores';
  import { WEBUI_API_BASE_URL, WEBUI_BASE_URL } from '$lib/constants';
  import { getChannels, getDMChannelByUserId } from '$lib/apis/channels';

  import ChatBubbles from '$lib/components/icons/ChatBubbles.svelte';
  import ChatBubble from '$lib/components/icons/ChatBubble.svelte';
  import ChatBubbleOval from '$lib/components/icons/ChatBubbleOval.svelte';
  import { goto } from '$app/navigation';
  import Emoji from '$lib/components/common/Emoji.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';

  export let user = null;

  const directMessageHandler = async () => {
    if (!user) {
      return;
    }

    const res = await getDMChannelByUserId(localStorage.token, user.id).catch((error) => {
      console.error('Error fetching DM channel:', error);
      return null;
    });

    if (res) {
      goto(`/channels/${res.id}`);
    }
  };
</script>

{#if user}
  <div class="py-3">
    <div class=" flex w-full items-center gap-3.5 px-3">
      <div class=" flex shrink-0 items-center">
        <img
          src={`${WEBUI_API_BASE_URL}/users/${user?.id}/profile/image`}
          class=" size-14 rounded-xl object-cover"
          alt="profile"
        />
      </div>

      <div class=" flex w-full flex-1 flex-col">
        <div class="mb-0.5 line-clamp-1 pr-2 font-medium">
          {user.name}
        </div>

        <div class=" flex items-center gap-2">
          {#if user?.is_active}
            <div>
              <span class="relative flex size-2">
                <span
                  class="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75"
                />
                <span class="relative inline-flex size-2 rounded-full bg-green-500" />
              </span>
            </div>

            <span class="text-xs"> {$i18n.t('Active')} </span>
          {:else}
            <div>
              <span class="relative flex size-2">
                <span class="relative inline-flex size-2 rounded-full bg-gray-500" />
              </span>
            </div>

            <span class="text-xs"> {$i18n.t('Away')} </span>
          {/if}
        </div>
      </div>
    </div>

    {#if user?.status_emoji || user?.status_message}
      <div class="mx-2 mt-2">
        <Tooltip content={user?.status_message}>
          <div
            class="flex w-full items-center gap-2 rounded-xl bg-gray-50 px-2.5 py-1.5 text-xs text-black transition dark:bg-gray-900/50 dark:text-white"
          >
            {#if user?.status_emoji}
              <div class=" shrink-0 self-center">
                <Emoji className="size-4" shortCode={user?.status_emoji} />
              </div>
            {/if}
            <div class=" line-clamp-2 flex-1 self-center text-left">
              {user?.status_message}
            </div>
          </div>
        </Tooltip>
      </div>
    {/if}

    {#if user?.bio}
      <div class="mx-3.5 mt-2">
        <Tooltip content={user?.bio}>
          <div class=" line-clamp-3 flex-1 self-center text-left text-xs">
            {user?.bio}
          </div>
        </Tooltip>
      </div>
    {/if}

    {#if (user?.groups ?? []).length > 0}
      <div class="mx-3.5 mt-2 flex max-h-20 flex-wrap gap-0.5 overflow-y-auto">
        {#each user.groups as group}
          <div
            class="rounded-lg bg-gray-50 px-1.5 py-0.5 text-xs text-black transition dark:bg-gray-900/50 dark:text-white"
          >
            {group.name}
          </div>
        {/each}
      </div>
    {/if}

    {#if $_user?.id !== user.id}
      <hr class="my-2.5 border-gray-100/50 dark:border-gray-800/50" />

      <div class=" flex w-full flex-col items-center px-2.5">
        <button
          class="dark:hover:bg-gray-850 flex w-full items-center gap-2 rounded-xl border border-gray-100/50 px-3 py-1.5 text-left text-sm transition hover:bg-gray-50 dark:border-gray-800/50"
          type="button"
          on:click={() => {
            directMessageHandler();
          }}
        >
          <div>
            <ChatBubbleOval className="size-4" />
          </div>

          <div class="font-medium">
            {$i18n.t('Message')}
          </div>
        </button>
      </div>
    {/if}
  </div>
{/if}
