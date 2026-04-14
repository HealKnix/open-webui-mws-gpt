<script lang="ts">
  import Modal from '$lib/components/common/Modal.svelte';
  import { getContext } from 'svelte';
  const i18n = getContext('i18n');
  import XMark from '$lib/components/icons/XMark.svelte';
  import { getFeedbackById } from '$lib/apis/evaluations';
  import { toast } from 'svelte-sonner';
  import Spinner from '$lib/components/common/Spinner.svelte';

  export let show = false;
  export let selectedFeedback = null;

  export let onClose: () => void = () => {};

  let loaded = false;

  let feedbackData = null;

  const close = () => {
    show = false;
    onClose();
  };

  const init = async () => {
    loaded = false;
    feedbackData = null;
    if (selectedFeedback) {
      feedbackData = await getFeedbackById(localStorage.token, selectedFeedback.id).catch((err) => {
        return null;
      });

      console.log('Feedback Data:', selectedFeedback, feedbackData);
    }
    loaded = true;
  };

  $: if (show) {
    init();
  }
</script>

<Modal size="sm" bind:show>
  {#if selectedFeedback}
    <div>
      <div class="flex justify-between px-5 pt-4 pb-2 dark:text-gray-300">
        <div class="self-center text-lg font-medium">
          {$i18n.t('Feedback Details')}
        </div>
        <button class="self-center" on:click={close} aria-label="Close">
          <XMark className={'size-5'} />
        </button>
      </div>

      <div class="flex w-full flex-col px-5 pb-4 md:flex-row md:space-x-4 dark:text-gray-200">
        {#if loaded}
          <div class="flex w-full flex-col">
            <div class="mb-2 flex w-full flex-col">
              <div class=" mb-1 text-xs text-gray-500">{$i18n.t('Chat ID')}</div>

              <div class="flex-1 text-xs">
                <a
                  href={`/s/${selectedFeedback?.meta?.chat_id}`}
                  class=" hover:underline"
                  target="_blank"
                >
                  <span>{selectedFeedback?.meta?.chat_id ?? '-'}</span>
                </a>
              </div>
            </div>

            {#if feedbackData}
              {@const messageId = feedbackData?.meta?.message_id}
              {@const messages = feedbackData?.snapshot?.chat?.chat?.history.messages}

              {#if messages[messages[messageId]?.parentId]}
                <div class="mb-2 flex w-full flex-col">
                  <div class="mb-1 text-xs text-gray-500">{$i18n.t('Prompt')}</div>

                  <div class="flex-1 text-xs break-words whitespace-pre-line">
                    <span>{messages[messages[messageId]?.parentId]?.content || '-'}</span>
                  </div>
                </div>
              {/if}

              {#if messages[messageId]}
                <div class="mb-2 flex w-full flex-col">
                  <div class="mb-1 text-xs text-gray-500">{$i18n.t('Response')}</div>
                  <div
                    class="max-h-32 flex-1 overflow-y-auto text-xs break-words whitespace-pre-line"
                  >
                    <span>{messages[messageId]?.content || '-'}</span>
                  </div>
                </div>
              {/if}
            {/if}

            <div class="mb-2 flex w-full flex-col">
              <div class=" mb-1 text-xs text-gray-500">{$i18n.t('Rating')}</div>

              <div class="flex-1 text-xs">
                <span>{selectedFeedback?.data?.details?.rating ?? '-'}</span>
              </div>
            </div>
            <div class="mb-2 flex w-full flex-col">
              <div class=" mb-1 text-xs text-gray-500">{$i18n.t('Reason')}</div>

              <div class="flex-1 text-xs">
                <span>{selectedFeedback?.data?.reason || '-'}</span>
              </div>
            </div>

            <div class="mb-2 flex w-full flex-col">
              <div class=" mb-1 text-xs text-gray-500">{$i18n.t('Comment')}</div>

              <div class="flex-1 text-xs">
                <span>{selectedFeedback?.data?.comment || '-'}</span>
              </div>
            </div>

            {#if selectedFeedback?.data?.tags && selectedFeedback?.data?.tags.length}
              <div class="-mx-1 mb-2">
                <div class="mt-1 flex flex-wrap gap-1">
                  {#each selectedFeedback?.data?.tags as tag}
                    <span class="dark:bg-gray-850 rounded-full bg-gray-100 px-2 py-0.5 text-[9px]"
                      >{tag}</span
                    >
                  {/each}
                </div>
              </div>
            {/if}

            <div class="flex justify-end pt-2">
              <button
                class="rounded-full bg-black px-3.5 py-1.5 text-sm font-medium text-white transition hover:bg-gray-900 dark:bg-white dark:text-black dark:hover:bg-gray-100"
                type="button"
                on:click={close}
              >
                {$i18n.t('Close')}
              </button>
            </div>
          </div>
        {:else}
          <div class="flex h-32 w-full items-center justify-center">
            <Spinner className={'size-5'} />
          </div>
        {/if}
      </div>
    </div>
  {/if}
</Modal>
