<script lang="ts">
  import { toast } from 'svelte-sonner';
  import { marked } from 'marked';

  import { onMount, getContext, tick, createEventDispatcher } from 'svelte';
  import { blur, fade } from 'svelte/transition';

  const dispatch = createEventDispatcher();

  import { getChatList } from '$lib/apis/chats';
  import { updateFolderById } from '$lib/apis/folders';

  import {
    config,
    user,
    models as _models,
    temporaryChatEnabled,
    selectedFolder,
    chats,
    currentChatPage,
  } from '$lib/stores';
  import { sanitizeResponseContent, extractCurlyBraceWords } from '$lib/utils';
  import { WEBUI_API_BASE_URL, WEBUI_BASE_URL } from '$lib/constants';

  import Suggestions from './Suggestions.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import EyeSlash from '$lib/components/icons/EyeSlash.svelte';
  import MessageInput from './MessageInput.svelte';
  import FolderPlaceholder from './Placeholder/FolderPlaceholder.svelte';
  import FolderTitle from './Placeholder/FolderTitle.svelte';

  const i18n = getContext('i18n');

  export let createMessagePair: Function;
  export let stopResponse: Function;

  export let autoScroll = false;

  export let atSelectedModel: Model | undefined;
  export let selectedModels: [''];

  export let history;

  export let prompt = '';
  export let files = [];
  export let messageInput = null;

  export let selectedToolIds = [];
  export let selectedFilterIds = [];
  export let pendingOAuthTools = [];

  export let showCommands = false;

  export let imageGenerationEnabled = false;
  export let codeInterpreterEnabled = false;
  export let webSearchEnabled = false;
  export let deepResearchEnabled = false;
  export let presentationEnabled = false;

  export let onUpload: Function = (e) => {};
  export let onSelect = (e) => {};
  export let onChange = (e) => {};

  export let toolServers = [];

  export let dragged = false;

  let models = [];
  let selectedModelIdx = 0;

  $: if (selectedModels.length > 0) {
    selectedModelIdx = models.length - 1;
  }

  $: models = selectedModels.map((id) => $_models.find((m) => m.id === id));
</script>

<div class="m-auto w-full max-w-6xl translate-y-6 px-2 py-24 text-center @2xl:px-20">
  {#if $temporaryChatEnabled}
    <Tooltip
      content={$i18n.t("This chat won't appear in history and your messages will not be saved.")}
      className="w-full flex justify-center mb-0.5"
      placement="top"
    >
      <div class="my-2 flex w-fit items-center gap-2 text-base text-gray-500">
        <EyeSlash strokeWidth="2.5" className="size-4" />{$i18n.t('Temporary Chat')}
      </div>
    </Tooltip>
  {/if}

  <div
    class="font-primary flex w-full items-center gap-4 text-center text-3xl text-gray-800 dark:text-gray-100"
  >
    <div class="flex w-full flex-col items-center justify-center">
      {#if $selectedFolder}
        <FolderTitle
          folder={$selectedFolder}
          onUpdate={async (folder) => {
            await chats.set(await getChatList(localStorage.token, $currentChatPage));
            currentChatPage.set(1);
          }}
          onDelete={async () => {
            await chats.set(await getChatList(localStorage.token, $currentChatPage));
            currentChatPage.set(1);

            selectedFolder.set(null);
          }}
        />
      {:else}
        <div class="flex w-fit max-w-xl flex-row justify-center gap-3 px-5 @sm:gap-3.5">
          <div class="flex shrink-0 justify-center">
            <div class="mb-0.5 flex -space-x-4" in:fade={{ duration: 100 }}>
              {#each models as model, modelIdx}
                <Tooltip
                  content={(models[modelIdx]?.info?.meta?.tags ?? [])
                    .map((tag) => tag.name.toUpperCase())
                    .join(', ')}
                  placement="top"
                >
                  <button
                    aria-hidden={models.length <= 1}
                    aria-label={$i18n.t('Get information on {{name}} in the UI', {
                      name: models[modelIdx]?.name,
                    })}
                    on:click={() => {
                      selectedModelIdx = modelIdx;
                    }}
                  >
                    <img
                      src={`${WEBUI_API_BASE_URL}/models/model/profile/image?id=${model?.id}&lang=${$i18n.language}`}
                      class=" size-9 rounded-full border-[1px] border-gray-100 @sm:size-10 dark:border-none"
                      aria-hidden="true"
                      draggable="false"
                      on:error={(e) => {
                        e.currentTarget.src = '/favicon.png';
                      }}
                    />
                  </button>
                </Tooltip>
              {/each}
            </div>
          </div>

          <div
            class=" line-clamp-1 flex items-center text-3xl @sm:text-3xl"
            in:fade={{ duration: 100 }}
          >
            {#if models[selectedModelIdx]?.name}
              <Tooltip
                content={models[selectedModelIdx]?.name}
                placement="top"
                className=" flex items-center "
              >
                <span class="line-clamp-1">
                  {models[selectedModelIdx]?.name}
                </span>
              </Tooltip>
            {:else}
              {$i18n.t('Hello, {{name}}', { name: $user?.name })}
            {/if}
          </div>
        </div>

        <div class="mt-1 mb-2 flex">
          <div in:fade={{ duration: 100, delay: 50 }}>
            {#if models[selectedModelIdx]?.info?.meta?.description ?? null}
              <Tooltip
                className=" w-fit"
                content={marked.parse(
                  sanitizeResponseContent(
                    models[selectedModelIdx]?.info?.meta?.description ?? '',
                  ).replaceAll('\n', '<br>'),
                )}
                placement="top"
              >
                <div
                  class="markdown mt-0.5 line-clamp-2 max-w-xl px-2 text-sm font-normal text-gray-500 dark:text-gray-400"
                >
                  {@html marked.parse(
                    sanitizeResponseContent(
                      models[selectedModelIdx]?.info?.meta?.description ?? '',
                    ).replaceAll('\n', '<br>'),
                  )}
                </div>
              </Tooltip>

              {#if models[selectedModelIdx]?.info?.meta?.user}
                <div class="mt-0.5 text-sm font-normal text-gray-400 dark:text-gray-500">
                  By
                  {#if models[selectedModelIdx]?.info?.meta?.user.community}
                    <a
                      href="https://openwebui.com/m/{models[selectedModelIdx]?.info?.meta?.user
                        .username}"
                      >{models[selectedModelIdx]?.info?.meta?.user.name
                        ? models[selectedModelIdx]?.info?.meta?.user.name
                        : `@${models[selectedModelIdx]?.info?.meta?.user.username}`}</a
                    >
                  {:else}
                    {models[selectedModelIdx]?.info?.meta?.user.name}
                  {/if}
                </div>
              {/if}
            {/if}
          </div>
        </div>
      {/if}

      <div class="w-full py-3 text-base font-normal @md:max-w-3xl {atSelectedModel ? 'mt-2' : ''}">
        <MessageInput
          bind:this={messageInput}
          {history}
          {selectedModels}
          bind:files
          bind:prompt
          bind:autoScroll
          bind:selectedToolIds
          bind:selectedFilterIds
          bind:imageGenerationEnabled
          bind:codeInterpreterEnabled
          bind:webSearchEnabled
          bind:deepResearchEnabled
          bind:presentationEnabled
          bind:atSelectedModel
          bind:showCommands
          bind:dragged
          {pendingOAuthTools}
          {toolServers}
          {stopResponse}
          {createMessagePair}
          placeholder={$i18n.t('How can I help you today?')}
          {onChange}
          {onUpload}
          on:submit={(e) => {
            dispatch('submit', e.detail);
          }}
        />
      </div>
    </div>
  </div>

  {#if $selectedFolder}
    <div
      class="font-primary mx-auto min-h-62 px-4 md:max-w-3xl md:px-6"
      in:fade={{ duration: 200, delay: 200 }}
    >
      <FolderPlaceholder folder={$selectedFolder} />
    </div>
  {:else}
    <div class="font-primary mx-auto mt-2 max-w-2xl" in:fade={{ duration: 200, delay: 200 }}>
      <div class="mx-5">
        <Suggestions
          suggestionPrompts={atSelectedModel?.info?.meta?.suggestion_prompts ??
            models[selectedModelIdx]?.info?.meta?.suggestion_prompts ??
            $config?.default_prompt_suggestions ??
            []}
          inputValue={prompt}
          {onSelect}
        />
      </div>
    </div>
  {/if}
</div>
