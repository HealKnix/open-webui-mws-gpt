<script lang="ts">
  import { onDestroy, onMount } from 'svelte';

  export let x;
  export let y;

  let popupElement = null;

  onMount(() => {
    document.body.appendChild(popupElement);
    document.body.style.overflow = 'hidden';
  });

  onDestroy(() => {
    if (popupElement && popupElement.parentNode) {
      try {
        popupElement.parentNode.removeChild(popupElement);
      } catch (err) {
        console.warn('Failed to remove popupElement:', err);
      }
    }

    document.body.style.overflow = 'unset';
  });
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<!-- svelte-ignore a11y-no-static-element-interactions -->

<div
  bind:this={popupElement}
  class="pointer-events-none fixed top-0 left-0 z-[99999] h-[100dvh] w-screen touch-none"
>
  <div class=" absolute z-99999 text-white" style="top: {y + 10}px; left: {x + 10}px;">
    <slot></slot>
  </div>
</div>
