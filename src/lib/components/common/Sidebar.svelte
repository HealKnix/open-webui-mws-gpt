<script lang="ts">
  import { fade, slide } from 'svelte/transition';

  export let show = false;
  export let side = 'right';
  export let width = '200px';

  export let className = '';
  export let duration = 100;
</script>

{#if show}
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div
    class="absolute top-0 right-0 bottom-0 left-0 z-20 flex h-full min-h-full w-full justify-center overflow-hidden overscroll-contain bg-white/20 dark:bg-black/5"
    on:mousedown={() => {
      show = false;
    }}
    transition:fade={{ duration: duration }}
  />

  <div
    class="absolute z-30 shadow-xl {side === 'right' ? 'right-0' : 'left-0'} top-0 bottom-0"
    transition:slide={{ duration: duration, axis: side === 'right' ? 'x' : 'y' }}
  >
    <div class="{className} h-full" style="width: {show ? width : '0px'}">
      <slot />
    </div>
  </div>
{/if}
