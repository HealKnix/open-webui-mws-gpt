<script lang="ts">
  import { getContext, onMount, tick } from 'svelte';
  import { toast } from 'svelte-sonner';
  import { chatCompletion } from '$lib/apis/openai';
  import { user, models, settings, config } from '$lib/stores';
  import { WEBUI_BASE_URL } from '$lib/constants';
  import { splitStream } from '$lib/utils';

  import Spinner from '$lib/components/common/Spinner.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Messages from './WidgetChatSidebar/Messages.svelte';
  import MessageInput from '$lib/components/channel/MessageInput.svelte';

  const i18n = getContext('i18n');

  export let onApply: (json: string) => void;
  export let onClose: () => void;
  export let currentJson: string = '';

  let loading = false;
  let stopResponseFlag = false;
  let chatInputElement;
  let messagesContainerElement: HTMLDivElement;
  let scrolledToBottom = true;

  let selectedModelId = '';
  let messages: { role: string; content: string; done?: boolean }[] = [];

  $: if ($models.length > 0 && selectedModelId === '') {
    selectedModelId = $settings.models?.[0] || $models[0].id;
  }

  const systemPrompt = `You are an elite UI Designer. Return ONLY a REUSABLE WIDGET TEMPLATE in JSON format.
NO TEXT, NO EXPLANATIONS, NO MARKDOWN BLOCKS. JUST RAW JSON.

## TEMPLATIZATION RULES
- USE {{data.key}} for all dynamic data (e.g. {{data.title}}, {{data.price}}).
- NEVER hardcode final text values.

## SCHEMA
{
  "type": "card" | "container" | "flex" | "button" | "text" | "badge" | "divider",
  "props": { ... },
  "actions": [ ... optional array of buttons ... ],
  "children": [ ... recursively ... ]
}

## EXAMPLE
{
  "type": "card",
  "props": { "title": "{{data.title}}", "image": "{{data.image}}" },
  "children": [{ "type": "text", "props": { "value": "{{data.desc}}" } }]
}

Current JSON in editor: ${currentJson}`;

  const scrollToBottom = () => {
    if (messagesContainerElement && scrolledToBottom) {
      messagesContainerElement.scrollTop = messagesContainerElement.scrollHeight;
    }
  };

  const onScroll = () => {
    if (messagesContainerElement) {
      scrolledToBottom =
        messagesContainerElement.scrollHeight - messagesContainerElement.scrollTop <=
        messagesContainerElement.clientHeight + 10;
    }
  };

  const chatCompletionHandler = async () => {
    if (selectedModelId === '') {
      toast.error($i18n.t('Please select a model.'));
      return;
    }

    let responseMessage;
    if (messages.at(-1)?.role === 'assistant') {
      responseMessage = messages.at(-1);
    } else {
      responseMessage = { role: 'assistant', content: '', done: false };
      messages = [...messages, responseMessage];
    }

    await tick();
    scrollToBottom();

    stopResponseFlag = false;
    const [res, controller] = await chatCompletion(
      localStorage.token,
      {
        model: selectedModelId,
        messages: [
          { role: 'system', content: systemPrompt },
          ...messages.slice(0, -1).map((m) => ({ role: m.role, content: m.content })),
        ],
        stream: true,
      },
      `${WEBUI_BASE_URL}/api`,
    );

    if (res && res.ok) {
      const reader = res.body
        .pipeThrough(new TextDecoderStream())
        .pipeThrough(splitStream('\n'))
        .getReader();

      let messageContent = '';
      while (true) {
        const { value, done } = await reader.read();
        if (done || stopResponseFlag) {
          if (stopResponseFlag) controller.abort('User: Stop Response');
          responseMessage.done = true;
          messages = messages;
          break;
        }

        try {
          const lines = value.split('\n');
          for (const line of lines) {
            if (line === 'data: [DONE]') {
              responseMessage.done = true;
            } else if (line.startsWith('data: ')) {
              const data = JSON.parse(line.replace(/^data: /, ''));
              const deltaContent = data.choices[0]?.delta?.content ?? '';
              messageContent += deltaContent;
              responseMessage.content = messageContent;

              // Real-time synchronization:
              // Try to extract JSON and apply it to the editor immediately
              const jsonMatch = messageContent.match(/\{[\s\S]*\}/);
              if (jsonMatch) {
                // We send the partial JSON to the editor.
                // CodeMirror and JSON parser in Editor will handle the partial status (e.g. showing error until finished)
                onApply(jsonMatch[0]);
              }

              messages = messages;
            }
          }
        } catch (e) {
          // Ignore partial JSON parse errors for stream extraction
        }
        await tick();
        scrollToBottom();
      }
    }
  };

  const submitHandler = async (e) => {
    const { content } = e;
    if (!content.trim() || loading || !selectedModelId) return;

    messages = [...messages, { role: 'user', content }];
    loading = true;

    await tick();
    scrollToBottom();

    await chatCompletionHandler();
    loading = false;
  };

  const handleApply = (content: string) => {
    const jsonMatch = content.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      onApply(jsonMatch[0]);
      toast.success($i18n.t('Applied to editor'));
    } else {
      toast.error($i18n.t('No valid JSON found'));
    }
  };
</script>

<div
  class="flex h-full w-full flex-col border-l border-gray-100 bg-white dark:border-gray-800 dark:bg-gray-950"
>
  <!-- Header -->
  <div
    class="flex items-center justify-between border-b border-gray-50 p-4 dark:border-gray-800 dark:bg-gray-900"
  >
    <div class="flex items-center gap-2">
      <h3 class="text-sm font-semibold">{$i18n.t('Chat')}</h3>
      <Tooltip content={$i18n.t('Experimental features')}>
        <span class="text-[10px] font-bold tracking-widest text-gray-400 uppercase"
          >({$i18n.t('Experimental')})</span
        >
      </Tooltip>
    </div>
    <button
      class="rounded-lg p-1.5 transition hover:bg-gray-50 dark:hover:bg-gray-800"
      on:click={onClose}
    >
      <XMark className="size-4" />
    </button>
  </div>

  <!-- Messages List -->
  <div
    class="flex-1 overflow-y-auto scroll-smooth p-4"
    bind:this={messagesContainerElement}
    on:scroll={onScroll}
  >
    {#if messages.length === 0}
      <div class="flex h-full flex-col items-center justify-center px-10 text-center">
        <div class="mb-4 rounded-full bg-blue-50 p-3 dark:bg-blue-400/10">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="2"
            stroke="currentColor"
            class="size-6 text-blue-500"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M12 18L12 20M12 20L10 18M12 20L14 18M12 18L12 6M12 6L10 8M12 6L14 8M6 12L4 12M4 12L6 10M4 12L6 14M18 12L20 12M20 12L18 10M20 12L18 14"
            />
          </svg>
        </div>
        <h4 class="mb-1 text-sm font-medium">{$i18n.t('Design with AI')}</h4>
        <p class="line-clamp-2 text-xs text-gray-500">
          {$i18n.t(
            'Describe your widget in plain language and let the assistant generate the schema for you.',
          )}
        </p>
      </div>
    {:else}
      <Messages bind:messages onApply={handleApply} />
    {/if}
  </div>

  <!-- Input Area -->
  <div class="border-t border-gray-50 bg-white/50 p-4 dark:border-gray-800 dark:bg-gray-900/50">
    <MessageInput
      bind:chatInputElement
      placeholder={$i18n.t('Ask assistant...')}
      inputLoading={loading}
      onSubmit={submitHandler}
      onStop={() => (stopResponseFlag = true)}
      acceptFiles={false}
      showFormattingToolbar={false}
    >
      <div slot="menu" class="flex w-full items-center justify-end px-2">
        <select
          class="w-full cursor-pointer bg-transparent text-right text-xs font-medium text-gray-500 outline-hidden transition-colors hover:text-gray-900 dark:hover:text-gray-300"
          bind:value={selectedModelId}
        >
          {#each $models.filter((m) => !(m?.info?.meta?.hidden ?? false)) as model}
            <option value={model.id} class="bg-white text-left dark:bg-gray-800"
              >{model.name}</option
            >
          {/each}
        </select>
      </div>
    </MessageInput>
  </div>
</div>
