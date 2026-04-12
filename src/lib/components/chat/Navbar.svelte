<script lang="ts">
  import { getContext } from 'svelte';
  import { toast } from 'svelte-sonner';

  import {
    WEBUI_NAME,
    banners,
    chatId,
    config,
    mobile,
    settings,
    showArchivedChats,
    showControls,
    showSidebar,
    temporaryChatEnabled,
    user,
  } from '$lib/stores';

  import { slide } from 'svelte/transition';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';

  import ShareChatModal from '../chat/ShareChatModal.svelte';
  import ModelSelector from '../chat/ModelSelector.svelte';
  import Tooltip from '../common/Tooltip.svelte';
  import Menu from '$lib/components/layout/Navbar/Menu.svelte';
  import UserMenu from '$lib/components/layout/Sidebar/UserMenu.svelte';
  import AdjustmentsHorizontal from '../icons/AdjustmentsHorizontal.svelte';

  import PencilSquare from '../icons/PencilSquare.svelte';
  import Banner from '../common/Banner.svelte';
  import Sidebar from '../icons/Sidebar.svelte';

  import ChatBubbleDotted from '../icons/ChatBubbleDotted.svelte';
  import ChatBubbleDottedChecked from '../icons/ChatBubbleDottedChecked.svelte';

  import EllipsisHorizontal from '../icons/EllipsisHorizontal.svelte';
  import ChatPlus from '../icons/ChatPlus.svelte';
  import ChatCheck from '../icons/ChatCheck.svelte';
  import Knobs from '../icons/Knobs.svelte';
  import { WEBUI_API_BASE_URL } from '$lib/constants';

  const i18n = getContext('i18n');

  export let initNewChat: Function;
  export let shareEnabled: boolean = false;
  export let scrollTop = 0;

  export let chat;
  export let history;
  export let selectedModels;
  export let showModelSelector = true;

  export let onSaveTempChat: () => {};
  export let archiveChatHandler: (id: string) => void;
  export let moveChatHandler: (id: string, folderId: string) => void;

  let closedBannerIds = [];

  let showShareChatModal = false;
  let showDownloadChatModal = false;
</script>

<ShareChatModal bind:show={showShareChatModal} chatId={$chatId} />

<button
  id="new-chat-button"
  class="hidden"
  on:click={() => {
    initNewChat();
  }}
  aria-label="New Chat"
/>

<nav
  class="sticky top-0 z-30 w-full {chat?.id
    ? 'pt-0.5 pb-1'
    : 'pt-1 pb-1'} drag-region -mb-12 flex flex-col items-center"
>
  <div class="flex w-full items-center pr-1 pl-1.5">
    <!-- <div
      id="navbar-bg-gradient-to-b"
      class="{chat?.id
        ? 'visible'
        : 'invisible'} pointer-events-none absolute inset-0 -bottom-10 z-[-1] bg-linear-to-b from-white/90 via-white/50 via-40% to-transparent to-97% backdrop-blur dark:from-gray-900/90 dark:via-gray-900/50 dark:to-transparent"
    ></div> -->
    {#each new Array(50) as _, i}
      <div
        class="{chat?.id
          ? 'visible'
          : 'invisible'} bg-background/5 pointer-events-none absolute top-0 right-0 left-0 z-[-1]"
        style="height: {i}px; backdrop-filter: blur({(i * Math.E) / 180}px); filter: blur({(i *
          Math.E) /
          180}px);"
      ></div>
    {/each}

    <div class=" mx-auto flex w-full max-w-full bg-transparent px-1.5 pt-0.5 md:px-2">
      <div class="flex w-full max-w-full items-center">
        {#if $mobile && !$showSidebar}
          <div
            class="mt-1 mr-1 flex flex-none -translate-x-0.5 items-center self-start text-gray-600 dark:text-gray-400"
          >
            <Tooltip content={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}>
              <button
                class=" dark:hover:bg-gray-850 flex cursor-pointer rounded-lg transition hover:bg-gray-100"
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
          class="mt-0.5 max-w-full flex-1 overflow-hidden py-0.5
			{$showSidebar ? 'ml-1' : ''}
			"
        >
          {#if showModelSelector}
            <ModelSelector bind:selectedModels showSetDefault={!shareEnabled} />
          {/if}
        </div>

        <div class="flex flex-none items-center self-start text-gray-600 dark:text-gray-400">
          <!-- <div class="md:hidden flex self-center w-[1px] h-5 mx-2 bg-gray-300 dark:bg-stone-700" /> -->

          {#if $user?.role === 'user' ? ($user?.permissions?.chat?.temporary ?? true) && !($user?.permissions?.chat?.temporary_enforced ?? false) : true}
            {#if !chat?.id}
              <Tooltip content={$i18n.t(`Temporary Chat`)}>
                <button
                  class="dark:hover:bg-gray-850 flex cursor-pointer rounded-xl px-2 py-2 transition hover:bg-gray-50"
                  id="temporary-chat-button"
                  on:click={async () => {
                    if (($settings?.temporaryChatByDefault ?? false) && $temporaryChatEnabled) {
                      // for proper initNewChat handling
                      await temporaryChatEnabled.set(null);
                    } else {
                      await temporaryChatEnabled.set(!$temporaryChatEnabled);
                    }

                    if ($page.url.pathname !== '/') {
                      await goto('/');
                    }

                    // add 'temporary-chat=true' to the URL
                    if ($temporaryChatEnabled) {
                      window.history.replaceState(null, '', '?temporary-chat=true');
                    } else {
                      window.history.replaceState(null, '', location.pathname);
                    }
                  }}
                >
                  <div class=" m-auto self-center">
                    {#if $temporaryChatEnabled}
                      <ChatBubbleDottedChecked className=" size-4.5" strokeWidth="1.5" />
                    {:else}
                      <ChatBubbleDotted className=" size-4.5" strokeWidth="1.5" />
                    {/if}
                  </div>
                </button>
              </Tooltip>
            {:else if $temporaryChatEnabled}
              <Tooltip content={$i18n.t(`Save Chat`)}>
                <button
                  class="dark:hover:bg-gray-850 flex cursor-pointer rounded-xl px-2 py-2 transition hover:bg-gray-50"
                  id="save-temporary-chat-button"
                  on:click={async () => {
                    onSaveTempChat();
                  }}
                >
                  <div class=" m-auto self-center">
                    <ChatCheck className=" size-4.5" strokeWidth="1.5" />
                  </div>
                </button>
              </Tooltip>
            {/if}
          {/if}

          {#if $mobile && !$temporaryChatEnabled && chat && chat.id}
            <Tooltip content={$i18n.t('New Chat')}>
              <button
                class=" flex {$showSidebar
                  ? 'md:hidden'
                  : ''} dark:hover:bg-gray-850 cursor-pointer rounded-xl px-2 py-2 text-gray-600 transition hover:bg-gray-50 dark:text-gray-400"
                on:click={() => {
                  initNewChat();
                }}
                aria-label="New Chat"
              >
                <div class=" m-auto self-center">
                  <ChatPlus className=" size-4.5" strokeWidth="1.5" />
                </div>
              </button>
            </Tooltip>
          {/if}

          {#if shareEnabled && chat && (chat.id || $temporaryChatEnabled)}
            <Menu
              {chat}
              {shareEnabled}
              shareHandler={() => {
                showShareChatModal = !showShareChatModal;
              }}
              archiveChatHandler={() => {
                archiveChatHandler(chat.id);
              }}
              {moveChatHandler}
            >
              <button
                class="dark:hover:bg-gray-850 flex cursor-pointer rounded-xl px-2 py-2 transition hover:bg-gray-50"
                id="chat-context-menu-button"
              >
                <div class=" m-auto self-center">
                  <EllipsisHorizontal className=" size-5" strokeWidth="1.5" />
                </div>
              </button>
            </Menu>
          {/if}

          {#if $user?.role === 'admin' || ($user?.permissions.chat?.controls ?? true)}
            <Tooltip content={$i18n.t('Controls')}>
              <button
                class=" dark:hover:bg-gray-850 flex cursor-pointer rounded-xl px-2 py-2 transition hover:bg-gray-50"
                on:click={async () => {
                  await showControls.set(!$showControls);
                }}
                aria-label="Controls"
              >
                <div class=" m-auto self-center">
                  <Knobs className=" size-5" strokeWidth="1" />
                </div>
              </button>
            </Tooltip>
          {/if}

          {#if $user !== undefined && $user !== null}
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
              <div
                class="dark:hover:bg-gray-850 flex w-full rounded-xl p-1.5 transition select-none hover:bg-gray-50"
              >
                <div class=" self-center">
                  <span class="sr-only">{$i18n.t('User menu')}</span>
                  <img
                    src={`${WEBUI_API_BASE_URL}/users/${$user?.id}/profile/image`}
                    class="size-6 rounded-full object-cover"
                    alt=""
                    draggable="false"
                  />
                </div>
              </div>
            </UserMenu>
          {/if}
        </div>
      </div>
    </div>
  </div>

  {#if $temporaryChatEnabled && ($chatId ?? '').startsWith('local:')}
    <div class=" z-30 w-full text-center">
      <div class="text-xs text-gray-500">{$i18n.t('Temporary Chat')}</div>
    </div>
  {/if}

  <div class="absolute top-[100%] right-0 left-0 h-fit">
    {#if !history.currentId && !$chatId && ($banners.length > 0 || ($config?.license_metadata?.type ?? null) === 'trial' || (($config?.license_metadata?.seats ?? null) !== null && $config?.user_count > $config?.license_metadata?.seats))}
      <div class=" z-30 w-full">
        <div class=" flex w-full flex-col gap-1">
          {#if ($config?.license_metadata?.type ?? null) === 'trial'}
            <Banner
              banner={{
                type: 'info',
                title: 'Trial License',
                content: $i18n.t(
                  'You are currently using a trial license. Please contact support to upgrade your license.',
                ),
              }}
            />
          {/if}

          {#if ($config?.license_metadata?.seats ?? null) !== null && $config?.user_count > $config?.license_metadata?.seats}
            <Banner
              banner={{
                type: 'error',
                title: 'License Error',
                content: $i18n.t(
                  'Exceeded the number of seats in your license. Please contact support to increase the number of seats.',
                ),
              }}
            />
          {/if}

          {#each $banners.filter((b) => ![...JSON.parse(localStorage.getItem('dismissedBannerIds') ?? '[]'), ...closedBannerIds].includes(b.id)) as banner (banner.id)}
            <Banner
              {banner}
              on:dismiss={(e) => {
                const bannerId = e.detail;

                if (banner.dismissible) {
                  localStorage.setItem(
                    'dismissedBannerIds',
                    JSON.stringify(
                      [
                        bannerId,
                        ...JSON.parse(localStorage.getItem('dismissedBannerIds') ?? '[]'),
                      ].filter((id) => $banners.find((b) => b.id === id)),
                    ),
                  );
                } else {
                  closedBannerIds = [...closedBannerIds, bannerId];
                }
              }}
            />
          {/each}
        </div>
      </div>
    {/if}
  </div>
</nav>
