<script lang="ts">
  import { toast } from 'svelte-sonner';
  import dayjs from 'dayjs';

  import { onMount, getContext, createEventDispatcher } from 'svelte';
  const i18n = getContext('i18n');
  const dispatch = createEventDispatcher();

  import Modal from '$lib/components/common/Modal.svelte';
  import RichTextInput from '$lib/components/common/RichTextInput.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';
  import MicSolid from '$lib/components/icons/MicSolid.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import VoiceRecording from '$lib/components/chat/MessageInput/VoiceRecording.svelte';
  export let show = false;

  let name = $i18n.t('Untitled');
  let content = '';

  let voiceInput = false;
</script>

<Modal size="full" containerClassName="" className="h-full bg-white dark:bg-gray-900" bind:show>
  <div class="absolute top-0 right-0 p-5">
    <button
      class="self-center dark:text-white"
      type="button"
      on:click={() => {
        show = false;
      }}
    >
      <XMark className="size-3.5" />
    </button>
  </div>
  <div class="flex h-full w-full flex-col md:flex-row md:space-x-4 dark:text-gray-200">
    <form
      class="flex h-full w-full flex-col"
      on:submit|preventDefault={() => {
        if (name.trim() === '' || content.trim() === '') {
          toast.error($i18n.t('Please fill in all fields.'));
          name = name.trim();
          content = content.trim();
          return;
        }

        dispatch('submit', {
          name,
          content,
        });
        show = false;
        name = '';
        content = '';
      }}
    >
      <div class=" flex h-full w-full flex-1 justify-center overflow-auto px-5 py-4">
        <div class=" flex w-full max-w-3xl flex-col gap-2 py-2 md:py-10">
          <div class="flex w-full shrink-0 items-center justify-between">
            <div class="w-full">
              <input
                class="w-full bg-transparent text-3xl font-medium outline-hidden"
                type="text"
                bind:value={name}
                placeholder={$i18n.t('Title')}
                required
              />
            </div>
          </div>

          <div class=" h-full w-full flex-1">
            <RichTextInput
              bind:value={content}
              placeholder={$i18n.t('Write something...')}
              preserveBreaks={true}
            />
          </div>
        </div>
      </div>

      <div
        class="mt-1 flex shrink-0 flex-row items-center justify-end gap-1.5 p-4 text-sm font-medium"
      >
        <div class="">
          {#if voiceInput}
            <div class=" w-full max-w-full">
              <VoiceRecording
                bind:recording={voiceInput}
                className="p-1"
                onCancel={() => {
                  voiceInput = false;
                }}
                onConfirm={(data) => {
                  const { text, filename } = data;
                  content = `${content}${text} `;

                  voiceInput = false;
                }}
              />
            </div>
          {:else}
            <Tooltip content={$i18n.t('Voice Input')}>
              <button
                class=" rounded-full bg-gray-50 p-2 text-gray-700 transition dark:bg-gray-700 dark:text-white"
                type="button"
                on:click={async () => {
                  try {
                    let stream = await navigator.mediaDevices
                      .getUserMedia({ audio: true })
                      .catch(function (err) {
                        toast.error(
                          $i18n.t(`Permission denied when accessing microphone: {{error}}`, {
                            error: err,
                          }),
                        );
                        return null;
                      });

                    if (stream) {
                      voiceInput = true;
                      const tracks = stream.getTracks();
                      tracks.forEach((track) => track.stop());
                    }
                    stream = null;
                  } catch {
                    toast.error($i18n.t('Permission denied when accessing microphone'));
                  }
                }}
              >
                <MicSolid className="size-5" />
              </button>
            </Tooltip>
          {/if}
        </div>

        <div class=" shrink-0">
          <Tooltip content={$i18n.t('Save')}>
            <button
              class=" rounded-full bg-black px-3.5 py-2 text-white transition dark:bg-white dark:text-black"
              type="submit"
            >
              {$i18n.t('Save')}
            </button>
          </Tooltip>
        </div>
      </div>
    </form>
  </div>
</Modal>

<style>
  input::-webkit-outer-spin-button,
  input::-webkit-inner-spin-button {
    /* display: none; <- Crashes Chrome on hover */
    -webkit-appearance: none;
    margin: 0; /* <-- Apparently some margin are still there even though it's hidden */
  }

  .tabs::-webkit-scrollbar {
    display: none; /* for Chrome, Safari and Opera */
  }

  .tabs {
    -ms-overflow-style: none; /* IE and Edge */
    scrollbar-width: none; /* Firefox */
  }

  input[type='number'] {
    -moz-appearance: textfield; /* Firefox */
  }
</style>
