<script lang="ts">
  import { onMount, tick, getContext } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';

  import dayjs from 'dayjs';

  import { settings, chatId, WEBUI_NAME, models, config } from '$lib/stores';
  import { convertMessagesToHistory, createMessagesList } from '$lib/utils';

  import { getChatByShareId, cloneSharedChatById } from '$lib/apis/chats';

  import Messages from '$lib/components/chat/Messages.svelte';

  import { getUserInfoById, getUserSettings } from '$lib/apis/users';
  import { getModels } from '$lib/apis';
  import { toast } from 'svelte-sonner';
  import localizedFormat from 'dayjs/plugin/localizedFormat';

  const i18n = getContext('i18n');
  dayjs.extend(localizedFormat);

  let loaded = false;

  let autoScroll = true;
  let processing = '';
  let messagesContainerElement: HTMLDivElement;

  // let chatId = $page.params.id;
  let showModelSelector = false;
  let selectedModels = [''];

  let chat = null;
  let user = null;

  let title = '';
  let files = [];

  let messages = [];
  let history = {
    messages: {},
    currentId: null,
  };

  $: messages = createMessagesList(history, history.currentId);

  $: if ($page.params.id) {
    (async () => {
      if (await loadSharedChat()) {
        await tick();
        loaded = true;
      } else {
        await goto('/');
      }
    })();
  }

  //////////////////////////
  // Web functions
  //////////////////////////

  const loadSharedChat = async () => {
    const userSettings = await getUserSettings(localStorage.token).catch((error) => {
      console.error(error);
      return null;
    });

    if (userSettings) {
      settings.set(userSettings.ui);
    } else {
      let localStorageSettings = {} as Parameters<(typeof settings)['set']>[0];

      try {
        localStorageSettings = JSON.parse(localStorage.getItem('settings') ?? '{}');
      } catch (e: unknown) {
        console.error('Failed to parse settings from localStorage', e);
      }

      settings.set(localStorageSettings);
    }

    await models.set(
      await getModels(
        localStorage.token,
        $config?.features?.enable_direct_connections && ($settings?.directConnections ?? null),
      ),
    );
    await chatId.set($page.params.id);
    chat = await getChatByShareId(localStorage.token, $chatId).catch(async (error) => {
      await goto('/');
      return null;
    });

    if (chat) {
      user = await getUserInfoById(localStorage.token, chat.user_id).catch((error) => {
        console.error(error);
        return null;
      });

      const chatContent = chat.chat;

      if (chatContent) {
        console.log(chatContent);

        selectedModels =
          (chatContent?.models ?? undefined) !== undefined
            ? chatContent.models
            : [chatContent.models ?? ''];
        history =
          (chatContent?.history ?? undefined) !== undefined
            ? chatContent.history
            : convertMessagesToHistory(chatContent.messages);
        title = chatContent.title;

        autoScroll = true;
        await tick();

        if (messages.length > 0 && messages.at(-1)?.id && messages.at(-1)?.id in history.messages) {
          history.messages[messages.at(-1)?.id].done = true;
        }
        await tick();

        return true;
      } else {
        return null;
      }
    }
  };

  const cloneSharedChat = async () => {
    if (!chat) return;

    const res = await cloneSharedChatById(localStorage.token, chat.id).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    if (res) {
      goto(`/c/${res.id}`);
    }
  };
</script>

<svelte:head>
  <title>
    {title
      ? `${title.length > 30 ? `${title.slice(0, 30)}...` : title} • ${$WEBUI_NAME}`
      : `${$WEBUI_NAME}`}
  </title>
</svelte:head>

{#if loaded}
  <div
    class="flex h-screen max-h-[100dvh] w-full flex-col bg-white text-gray-700 dark:bg-gray-900 dark:text-gray-100"
  >
    <div class="relative flex flex-auto flex-col justify-center">
      <div class=" flex h-0 w-full flex-auto flex-col overflow-auto" id="messages-container">
        <div
          class="w-full px-2 pt-5 {($settings?.widescreenMode ?? null)
            ? 'max-w-full'
            : 'max-w-5xl'} mx-auto"
        >
          <div class="px-3">
            <h1 class=" m-0 line-clamp-1 text-2xl font-medium">
              {title}
            </h1>

            <div class="mt-1 flex items-center justify-between text-sm">
              <time
                class="text-gray-400"
                datetime={new Date(chat?.chat?.timestamp || Date.now()).toISOString()}
              >
                {dayjs(chat.chat.timestamp).format('LLL')}
              </time>
            </div>
          </div>
        </div>

        <div class=" flex h-full w-full flex-col py-2" role="main">
          <div class="w-full">
            <Messages
              className="h-full flex pt-4 pb-8 "
              {user}
              chatId={$chatId}
              readOnly={true}
              {selectedModels}
              {processing}
              bind:history
              bind:messages
              bind:autoScroll
              bottomPadding={files.length > 0}
              sendMessage={() => {}}
              continueResponse={() => {}}
              regenerateResponse={() => {}}
            />
          </div>
        </div>
      </div>

      <div
        class="absolute right-0 bottom-0 left-0 flex w-full justify-center bg-linear-to-b from-transparent to-white dark:to-gray-900"
      >
        <div class="pb-5">
          <button
            class="rounded-full bg-black px-3.5 py-1.5 text-sm font-medium text-white transition hover:bg-gray-900 dark:bg-white dark:text-black dark:hover:bg-gray-100"
            on:click={cloneSharedChat}
          >
            {$i18n.t('Clone Chat')}
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}
