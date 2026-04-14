<script lang="ts">
  import fileSaver from 'file-saver';
  const { saveAs } = fileSaver;

  import { toast } from 'svelte-sonner';

  import { goto } from '$app/navigation';
  import { onMount, tick, getContext } from 'svelte';

  import {
    OLLAMA_API_BASE_URL,
    OPENAI_API_BASE_URL,
    WEBUI_API_BASE_URL,
    WEBUI_BASE_URL,
  } from '$lib/constants';
  import { WEBUI_NAME, config, user, models, settings } from '$lib/stores';

  import { chatCompletion } from '$lib/apis/openai';

  import { splitStream } from '$lib/utils';
  import Collapsible from '../common/Collapsible.svelte';
  import Dropdown from '../common/Dropdown.svelte';
  import DropdownSub from '../common/DropdownSub.svelte';

  import Messages from '$lib/components/playground/Chat/Messages.svelte';
  import ChevronUp from '../icons/ChevronUp.svelte';
  import ChevronDown from '../icons/ChevronDown.svelte';
  import Pencil from '../icons/Pencil.svelte';
  import Cog6 from '../icons/Cog6.svelte';
  import Sidebar from '../common/Sidebar.svelte';
  import ArrowRight from '../icons/ArrowRight.svelte';
  import Download from '../icons/Download.svelte';
  import EllipsisHorizontal from '../icons/EllipsisHorizontal.svelte';

  const i18n = getContext('i18n');

  let loaded = false;

  let selectedModelId = '';
  let loading = false;
  let stopResponseFlag = false;

  let systemTextareaElement: HTMLTextAreaElement;
  let messagesContainerElement: HTMLDivElement;

  let showSystem = false;
  let showSettings = false;

  let system = '';

  let role = 'user';
  let message = '';

  let messages = [];

  const scrollToBottom = () => {
    const element = messagesContainerElement;

    if (element) {
      element.scrollTop = element?.scrollHeight;
    }
  };

  const stopResponse = () => {
    stopResponseFlag = true;
    console.log('stopResponse');
  };

  const resizeSystemTextarea = async () => {
    await tick();
    if (systemTextareaElement) {
      systemTextareaElement.style.height = '';
      systemTextareaElement.style.height = Math.min(systemTextareaElement.scrollHeight, 555) + 'px';
    }
  };

  $: if (showSystem) {
    resizeSystemTextarea();
  }

  const chatCompletionHandler = async () => {
    if (selectedModelId === '') {
      toast.error($i18n.t('Please select a model.'));
      return;
    }

    const model = $models.find((model) => model.id === selectedModelId);
    if (!model) {
      selectedModelId = '';
      return;
    }

    const [res, controller] = await chatCompletion(
      localStorage.token,
      {
        model: model.id,
        stream: true,
        messages: [
          system
            ? {
                role: 'system',
                content: system,
              }
            : undefined,
          ...messages,
        ].filter((message) => message),
      },
      `${WEBUI_BASE_URL}/api`,
    );

    let responseMessage;
    if (messages.at(-1)?.role === 'assistant') {
      responseMessage = messages.at(-1);
    } else {
      responseMessage = {
        role: 'assistant',
        content: '',
      };
      messages.push(responseMessage);
      messages = messages;
    }

    await tick();
    const textareaElement = document.getElementById(`assistant-${messages.length - 1}-textarea`);

    if (res && res.ok) {
      const reader = res.body
        .pipeThrough(new TextDecoderStream())
        .pipeThrough(splitStream('\n'))
        .getReader();

      while (true) {
        const { value, done } = await reader.read();
        if (done || stopResponseFlag) {
          if (stopResponseFlag) {
            controller.abort('User: Stop Response');
          }
          break;
        }

        try {
          let lines = value.split('\n');

          for (const line of lines) {
            if (line !== '') {
              console.log(line);
              if (line === 'data: [DONE]') {
                // responseMessage.done = true;
                messages = messages;
              } else {
                let data = JSON.parse(line.replace(/^data: /, ''));
                console.log(data);

                if (responseMessage.content == '' && data.choices[0].delta.content == '\n') {
                  continue;
                } else {
                  textareaElement.style.height = textareaElement.scrollHeight + 'px';

                  responseMessage.content += data.choices[0].delta.content ?? '';
                  messages = messages;

                  textareaElement.style.height = textareaElement.scrollHeight + 'px';

                  await tick();
                }
              }
            }
          }
        } catch (error) {
          console.log(error);
        }

        scrollToBottom();
      }
    }
  };

  const addHandler = async () => {
    if (message) {
      messages.push({
        role: role,
        content: message,
      });
      messages = messages;
      message = '';
      await tick();
      scrollToBottom();
    }
  };

  const submitHandler = async () => {
    if (selectedModelId) {
      await addHandler();

      loading = true;
      await chatCompletionHandler();

      loading = false;
      stopResponseFlag = false;
    }
  };

  const exportToJson = () => {
    const now = Math.floor(Date.now() / 1000);

    // Convert flat messages array to history map format
    const messagesMap: Record<string, any> = {};
    let currentId: string | null = null;
    let parentId: string | null = null;

    // Add system message if present
    if (system) {
      const systemId = crypto.randomUUID();
      messagesMap[systemId] = {
        id: systemId,
        parentId: null,
        childrenIds: [],
        role: 'system',
        content: system,
        timestamp: now,
      };
      parentId = systemId;
    }

    // Add conversation messages
    for (const msg of messages) {
      const msgId = crypto.randomUUID();

      // Link parent to child
      if (parentId && messagesMap[parentId]) {
        messagesMap[parentId].childrenIds.push(msgId);
      }

      messagesMap[msgId] = {
        id: msgId,
        parentId: parentId,
        childrenIds: [],
        role: msg.role,
        content: msg.content,
        timestamp: now,
        ...(msg.role === 'assistant' && selectedModelId ? { model: selectedModelId } : {}),
      };

      currentId = msgId;
      parentId = msgId;
    }

    const exportData = {
      chat: {
        title: 'Playground Chat',
        models: [selectedModelId],
        params: system ? { system } : {},
        history: {
          messages: messagesMap,
          currentId,
        },
      },
      meta: {},
      pinned: false,
      created_at: now,
      updated_at: now,
    };

    const blob = new Blob([JSON.stringify([exportData], null, 2)], {
      type: 'application/json',
    });
    saveAs(blob, `playground-chat-${Date.now()}.json`);
    toast.success($i18n.t('Chat exported successfully'));
  };

  const downloadTxt = () => {
    let chatText = '';

    // Add system message if present
    if (system) {
      chatText += `### SYSTEM\n${system}\n\n`;
    }

    // Add conversation messages
    for (const msg of messages) {
      chatText += `### ${msg.role.toUpperCase()}\n${msg.content}\n\n`;
    }

    const blob = new Blob([chatText.trim()], {
      type: 'text/plain',
    });
    saveAs(blob, `playground-chat-${Date.now()}.txt`);
    toast.success($i18n.t('Chat exported successfully'));
  };

  onMount(async () => {
    if ($user?.role !== 'admin') {
      await goto('/');
    }

    if ($settings?.models) {
      selectedModelId = $settings?.models[0];
    } else if ($config?.default_models) {
      selectedModelId = $config?.default_models.split(',')[0];
    } else {
      selectedModelId = '';
    }
    loaded = true;
  });
</script>

<div class=" flex h-full w-full flex-col justify-between overflow-y-auto">
  <div class="relative mx-auto h-full w-full md:px-0">
    <div class=" flex h-full flex-col px-3.5">
      <div class="flex w-full items-center gap-1.5">
        <Collapsible
          className="w-full flex-1"
          bind:open={showSystem}
          buttonClassName="w-full rounded-lg text-sm border border-gray-100/30 dark:border-gray-850/30 w-full py-1 px-1.5"
          grow={true}
        >
          <div class="flex items-center justify-between gap-2">
            <div class=" ml-1.5 shrink-0 font-medium">
              {$i18n.t('System Instructions')}
            </div>

            {#if !showSystem && system.trim()}
              <div class=" line-clamp-1 flex-1 text-gray-500">
                {system}
              </div>
            {/if}

            <div class="shrink-0">
              <button class="rounded-lg bg-transparent p-1.5 transition hover:bg-white/5">
                {#if showSystem}
                  <ChevronUp className="size-3.5" />
                {:else}
                  <Pencil className="size-3.5" />
                {/if}
              </button>
            </div>
          </div>

          <div slot="content">
            <div class="px-1.5 pt-1">
              <textarea
                bind:this={systemTextareaElement}
                class="h-full w-full resize-none bg-transparent text-sm outline-hidden"
                bind:value={system}
                placeholder={$i18n.t("You're a helpful assistant.")}
                on:input={() => {
                  resizeSystemTextarea();
                }}
                rows="4"
              />
            </div>
          </div>
        </Collapsible>

        <Dropdown>
          <button
            class="rounded-lg bg-transparent p-1.5 text-sm font-medium text-gray-500 transition hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
            aria-label={$i18n.t('More options')}
          >
            <EllipsisHorizontal className="size-4" />
          </button>

          <div slot="content">
            <div
              class="dark:bg-gray-850 z-50 min-w-[200px] rounded-2xl border border-gray-100 bg-white px-1 py-1 shadow-lg dark:border-gray-800 dark:text-white"
            >
              <DropdownSub>
                <button
                  slot="trigger"
                  class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
                >
                  <Download strokeWidth="1.5" />
                  <div class="flex items-center">{$i18n.t('Download')}</div>
                </button>
                <button
                  class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
                  disabled={messages.length === 0}
                  on:click={() => {
                    exportToJson();
                  }}
                >
                  <div class="line-clamp-1 flex items-center">
                    {$i18n.t('Export chat (.json)')}
                  </div>
                </button>
                <button
                  class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
                  disabled={messages.length === 0}
                  on:click={() => {
                    downloadTxt();
                  }}
                >
                  <div class="line-clamp-1 flex items-center">{$i18n.t('Plain text (.txt)')}</div>
                </button>
              </DropdownSub>
            </div>
          </div>
        </Dropdown>
      </div>

      <div
        class=" flex h-0 w-full flex-auto flex-col justify-between overflow-auto pb-2.5"
        id="messages-container"
        bind:this={messagesContainerElement}
      >
        <div class=" flex h-full w-full flex-col">
          <div class="flex-1 p-1">
            <Messages bind:messages />
          </div>
        </div>
      </div>

      <div class="pb-3">
        <div
          class="dark:border-gray-850/30 w-full rounded-xl border border-gray-100/30 px-3 py-2.5"
        >
          <div class="py-0.5">
            <!-- $i18n.t('a user') -->
            <!-- $i18n.t('an assistant') -->
            <textarea
              bind:value={message}
              class=" h-full w-full resize-none bg-transparent text-sm outline-hidden"
              placeholder={$i18n.t(`Enter {{role}} message here`, {
                role: role === 'user' ? $i18n.t('a user') : $i18n.t('an assistant'),
              })}
              on:input={(e) => {
                e.target.style.height = '';
                e.target.style.height = Math.min(e.target.scrollHeight, 150) + 'px';
              }}
              on:focus={(e) => {
                e.target.style.height = '';
                e.target.style.height = Math.min(e.target.scrollHeight, 150) + 'px';
              }}
              rows="2"
            />
          </div>

          <div
            class="mt-2 flex flex-col items-start justify-between gap-2 sm:flex-row sm:items-center"
          >
            <div class="shrink-0">
              <button
                type="button"
                class="dark:bg-gray-850 shrink-0 rounded-lg bg-gray-50 px-3.5 py-1.5 text-sm font-medium text-gray-900 transition hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-800 {($settings?.highContrastMode ??
                false)
                  ? ''
                  : 'outline-hidden'}"
                aria-pressed={role === 'assistant'}
                aria-label={$i18n.t(
                  role === 'user' ? 'Switch to Assistant role' : 'Switch to User role',
                )}
                on:click={() => {
                  role = role === 'user' ? 'assistant' : 'user';
                }}
              >
                {#if role === 'user'}
                  {$i18n.t('User')}
                {:else}
                  {$i18n.t('Assistant')}
                {/if}
              </button>
            </div>

            <div class="flex w-full items-center justify-between gap-2 sm:w-auto">
              <div class="flex-1">
                <select
                  class=" dark:border-gray-850/30 -mx-0.5 w-full rounded-lg border border-gray-100/30 bg-transparent px-2 py-1 text-sm outline-hidden"
                  bind:value={selectedModelId}
                >
                  {#each $models as model}
                    <option value={model.id} class="bg-gray-50 dark:bg-gray-700"
                      >{model.name}</option
                    >
                  {/each}
                </select>
              </div>

              <div class="flex shrink-0 gap-2">
                {#if !loading}
                  <button
                    disabled={message === ''}
                    class="dark:disabled:hover:bg-gray-850 dark:bg-gray-850 rounded-lg bg-gray-50 px-3.5 py-1.5 text-sm font-medium text-gray-900 transition hover:bg-gray-100 disabled:cursor-not-allowed disabled:bg-gray-50 dark:text-gray-200 dark:hover:bg-gray-800"
                    on:click={() => {
                      addHandler();
                      role = role === 'user' ? 'assistant' : 'user';
                    }}
                  >
                    {$i18n.t('Add')}
                  </button>

                  <button
                    class="rounded-lg bg-black px-3.5 py-1.5 text-sm font-medium text-white transition hover:bg-gray-900 dark:bg-white dark:text-black dark:hover:bg-gray-100"
                    on:click={() => {
                      submitHandler();
                    }}
                  >
                    {$i18n.t('Run')}
                  </button>
                {:else}
                  <button
                    class="rounded-lg bg-gray-300 px-3 py-1.5 text-sm font-medium text-black transition"
                    on:click={() => {
                      stopResponse();
                    }}
                  >
                    {$i18n.t('Cancel')}
                  </button>
                {/if}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
