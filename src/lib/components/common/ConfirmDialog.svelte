<script lang="ts">
  import DOMPurify from 'dompurify';

  import { onMount, getContext, createEventDispatcher, onDestroy, tick } from 'svelte';
  import * as FocusTrap from 'focus-trap';

  const i18n = getContext('i18n');
  const dispatch = createEventDispatcher();

  import { fade } from 'svelte/transition';
  import { flyAndScale } from '$lib/utils/transitions';
  import { marked } from 'marked';
  import SensitiveInput from './SensitiveInput.svelte';

  export let title = '';
  export let message = '';

  export let cancelLabel = $i18n.t('Cancel');
  export let confirmLabel = $i18n.t('Confirm');

  export let onConfirm = () => {};

  export let input = false;
  export let inputPlaceholder = '';
  export let inputValue = '';
  export let inputType = '';

  let _inputValue = inputValue;

  export let show = false;

  $: if (show) {
    init();
  }

  let modalElement = null;
  let mounted = false;

  let focusTrap: FocusTrap.FocusTrap | null = null;

  const init = () => {
    _inputValue = inputValue;
  };

  const handleKeyDown = (event: KeyboardEvent) => {
    if (event.key === 'Escape') {
      console.log('Escape');
      show = false;
    }

    if (event.key === 'Enter') {
      console.log('Enter');
      event.preventDefault();
      event.stopPropagation();
      confirmHandler();
    }
  };

  const confirmHandler = async () => {
    show = false;
    await tick();
    await onConfirm();
    dispatch('confirm', _inputValue);
  };

  onMount(() => {
    mounted = true;
  });

  $: if (mounted) {
    if (show && modalElement) {
      document.body.appendChild(modalElement);
      focusTrap = FocusTrap.createFocusTrap(modalElement);
      focusTrap.activate();

      window.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    } else if (modalElement) {
      focusTrap.deactivate();

      window.removeEventListener('keydown', handleKeyDown);
      document.body.removeChild(modalElement);

      document.body.style.overflow = 'unset';
    }
  }

  onDestroy(() => {
    show = false;
    window.removeEventListener('keydown', handleKeyDown);
    if (focusTrap) {
      focusTrap.deactivate();
    }
    if (modalElement) {
      document.body.removeChild(modalElement);
    }
  });
</script>

{#if show}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div
    bind:this={modalElement}
    class=" fixed top-0 right-0 bottom-0 left-0 z-99999999 flex h-screen max-h-[100dvh] w-full justify-center overflow-hidden overscroll-contain bg-black/60"
    in:fade={{ duration: 10 }}
    on:mousedown={() => {
      show = false;
    }}
  >
    <div
      class=" shadow-3xl m-auto mx-2 max-h-[100dvh] w-[32rem] max-w-full rounded-4xl border border-white bg-white/95 backdrop-blur-sm dark:border-gray-900 dark:bg-gray-950/95"
      in:flyAndScale
      on:mousedown={(e) => {
        e.stopPropagation();
      }}
    >
      <div class="flex flex-col px-[1.75rem] py-6">
        <div class=" mb-2.5 text-lg font-medium dark:text-gray-200">
          {#if title !== ''}
            {title}
          {:else}
            {$i18n.t('Confirm your action')}
          {/if}
        </div>

        <slot>
          <div class=" flex-1 text-sm text-gray-500">
            {#if message !== ''}
              {@const html = DOMPurify.sanitize(marked.parse(message))}
              {@html html}
            {:else}
              {$i18n.t('This action cannot be undone. Do you wish to continue?')}
            {/if}

            {#if input}
              {#if inputType === 'password'}
                <div
                  class="mt-2 w-full rounded-lg px-4 py-2 text-sm dark:bg-gray-900 dark:text-gray-300"
                >
                  <SensitiveInput
                    id="event-confirm-input"
                    placeholder={inputPlaceholder
                      ? inputPlaceholder
                      : $i18n.t('Enter your message')}
                    bind:value={_inputValue}
                    required={true}
                  />
                </div>
              {:else}
                <textarea
                  bind:value={_inputValue}
                  placeholder={inputPlaceholder ? inputPlaceholder : $i18n.t('Enter your message')}
                  class="mt-2 w-full resize-none rounded-lg px-4 py-2 text-sm outline-hidden dark:bg-gray-900 dark:text-gray-300"
                  rows="3"
                  required
                />
              {/if}
            {/if}
          </div>
        </slot>

        <div class="mt-6 flex justify-between gap-1.5">
          <button
            class="dark:bg-gray-850 w-full rounded-3xl bg-gray-100 py-2 text-sm font-medium text-gray-800 transition hover:bg-gray-200 dark:text-white dark:hover:bg-gray-800"
            on:click={() => {
              show = false;
              dispatch('cancel');
            }}
            type="button"
          >
            {cancelLabel}
          </button>
          <button
            class="hover:bg-gray-850 w-full rounded-3xl bg-gray-900 py-2 text-sm font-medium text-gray-100 transition dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white"
            on:click={() => {
              confirmHandler();
            }}
            type="button"
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .modal-content {
    animation: scaleUp 0.1s ease-out forwards;
  }

  @keyframes scaleUp {
    from {
      transform: scale(0.985);
      opacity: 0;
    }
    to {
      transform: scale(1);
      opacity: 1;
    }
  }
</style>
