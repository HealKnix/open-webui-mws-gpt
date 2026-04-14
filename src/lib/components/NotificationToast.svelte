<script lang="ts">
  import { WEBUI_BASE_URL } from '$lib/constants';
  import { settings, playingNotificationSound, isLastActiveTab } from '$lib/stores';
  import DOMPurify from 'dompurify';
  import { marked } from 'marked';

  import { createEventDispatcher, onMount } from 'svelte';
  import XMark from '$lib/components/icons/XMark.svelte';

  const dispatch = createEventDispatcher();

  export let onClick: Function = () => {};
  export let title: string = 'HI';
  export let content: string;

  let startX = 0,
    startY = 0;
  let moved = false;
  let closeButtonElement: HTMLButtonElement;
  const DRAG_THRESHOLD_PX = 6;

  const clickHandler = () => {
    onClick();
    dispatch('closeToast');
  };

  const closeHandler = () => {
    dispatch('closeToast');
  };

  function onPointerDown(e: PointerEvent) {
    startX = e.clientX;
    startY = e.clientY;
    moved = false;
    // Ensure we continue to get events even if the toast moves under the pointer.
    (e.currentTarget as HTMLElement).setPointerCapture?.(e.pointerId);
  }

  function onPointerMove(e: PointerEvent) {
    if (moved) return;
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    if (dx * dx + dy * dy > DRAG_THRESHOLD_PX * DRAG_THRESHOLD_PX) {
      moved = true;
    }
  }

  function onPointerUp(e: PointerEvent) {
    // Release capture if taken
    (e.currentTarget as HTMLElement).releasePointerCapture?.(e.pointerId);

    // Skip if clicking the close button
    if (
      closeButtonElement &&
      (e.target === closeButtonElement || closeButtonElement.contains(e.target as Node))
    ) {
      return;
    }

    // Only treat as a click if there wasn't a drag
    if (!moved) {
      clickHandler();
    }
  }

  onMount(() => {
    if (!navigator.userActivation.hasBeenActive) {
      return;
    }

    if ($settings?.notificationSound ?? true) {
      if (!$playingNotificationSound && $isLastActiveTab) {
        playingNotificationSound.set(true);

        const audio = new Audio(`/audio/notification.mp3`);
        audio.play().finally(() => {
          // Ensure the global state is reset after the sound finishes
          playingNotificationSound.set(false);
        });
      }
    }
  });
</script>

<div
  role="status"
  aria-live="polite"
  class="group dark:bg-gray-850 relative flex w-full min-w-[var(--width)] cursor-pointer gap-2.5 rounded-3xl border border-gray-100 bg-white px-4 py-3.5 text-left text-black select-none dark:border-gray-800 dark:text-white"
  on:dragstart|preventDefault
  on:pointerdown={onPointerDown}
  on:pointermove={onPointerMove}
  on:pointerup={onPointerUp}
  on:pointercancel={() => (moved = true)}
  on:keydown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      clickHandler();
    }
  }}
>
  <!-- Close button (visible on hover) -->
  <button
    bind:this={closeButtonElement}
    class="absolute -top-0.5 -left-0.5 z-10 rounded-full bg-gray-50 p-0.5 text-gray-500 opacity-0 transition-opacity group-hover:opacity-100 hover:bg-gray-100 hover:text-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-200"
    on:click|stopPropagation={closeHandler}
    aria-label="Dismiss notification"
  >
    <XMark className="size-3" />
  </button>

  <div class="self-top shrink-0 -translate-y-0.5">
    <img src="/favicon.png" alt="favicon" class="size-6 rounded-full" />
  </div>

  <div>
    {#if title}
      <div class=" mb-0.5 line-clamp-1 text-[13px] font-medium">{title}</div>
    {/if}

    <div class=" line-clamp-2 self-center text-xs font-normal dark:text-gray-300">
      {@html DOMPurify.sanitize(marked(DOMPurify.sanitize(content, { ALLOWED_TAGS: [] })))}
    </div>
  </div>
</div>
