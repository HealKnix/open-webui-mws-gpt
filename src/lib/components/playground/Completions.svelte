<script lang="ts">
  import { toast } from 'svelte-sonner';

  import { goto } from '$app/navigation';
  import { onMount, tick, getContext } from 'svelte';

  import { WEBUI_BASE_URL } from '$lib/constants';
  import { WEBUI_NAME, config, user, models, settings, showSidebar } from '$lib/stores';
  import { chatCompletion } from '$lib/apis/openai';

  import { splitStream } from '$lib/utils';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import Selector from '$lib/components/chat/ModelSelector/Selector.svelte';

  const i18n = getContext('i18n');

  let loaded = false;
  let text = '';

  let selectedModelId = '';

  let loading = false;
  let stopResponseFlag = false;

  let textCompletionAreaElement: HTMLTextAreaElement;

  const scrollToBottom = () => {
    const element = textCompletionAreaElement;

    if (element) {
      element.scrollTop = element?.scrollHeight;
    }
  };

  const stopResponse = () => {
    stopResponseFlag = true;
    console.log('stopResponse');
  };

  const textCompletionHandler = async () => {
    const model = $models.find((model) => model.id === selectedModelId);

    const [res, controller] = await chatCompletion(
      localStorage.token,
      {
        model: model.id,
        stream: true,
        messages: [
          {
            role: 'assistant',
            content: text,
          },
        ],
      },
      `${WEBUI_BASE_URL}/api`,
    );

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
              if (line.includes('[DONE]')) {
                console.log('done');
              } else {
                let data = JSON.parse(line.replace(/^data: /, ''));
                console.log(data);

                text += data.choices[0].delta.content ?? '';
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

  const submitHandler = async () => {
    if (selectedModelId) {
      loading = true;
      await textCompletionHandler();

      loading = false;
      stopResponseFlag = false;
    }
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
  <div class="mx-auto h-full w-full md:px-0">
    <div class=" flex h-full flex-col px-4">
      <div class="mb-1 flex flex-col justify-between gap-1">
        <div class="flex w-full flex-col gap-1">
          <div class="flex w-full">
            <div class="w-full overflow-hidden">
              <div class="max-w-full">
                <Selector
                  placeholder={$i18n.t('Select a model')}
                  items={$models.map((model) => ({
                    value: model.id,
                    label: model.name,
                    model: model,
                  }))}
                  bind:value={selectedModelId}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div
        class=" flex h-0 w-full flex-auto flex-col justify-between overflow-auto pt-0.5 pb-2.5"
        id="messages-container"
      >
        <div class=" flex h-full w-full flex-col">
          <div class="flex-1">
            <textarea
              id="text-completion-textarea"
              bind:this={textCompletionAreaElement}
              class="dark:border-gray-850/30 h-full w-full resize-none rounded-lg border border-gray-100/30 bg-transparent p-3 text-sm outline-hidden"
              bind:value={text}
              placeholder={$i18n.t("You're a helpful assistant.")}
            />
          </div>
        </div>
      </div>

      <div class="flex justify-end pb-3">
        <div class="flex shrink-0 gap-2">
          {#if !loading}
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
              class="flex items-center gap-2 rounded-lg bg-gray-300 px-3.5 py-1.5 text-sm font-medium text-black transition"
              on:click={() => {
                stopResponse();
              }}
            >
              <Spinner className="size-4" />
              {$i18n.t('Cancel')}
            </button>
          {/if}
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .scrollbar-hidden::-webkit-scrollbar {
    display: none; /* for Chrome, Safari and Opera */
  }

  .scrollbar-hidden {
    -ms-overflow-style: none; /* IE and Edge */
    scrollbar-width: none; /* Firefox */
  }
</style>
