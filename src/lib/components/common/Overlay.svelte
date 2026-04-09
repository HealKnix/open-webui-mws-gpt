<script>
  import Spinner from './Spinner.svelte';

  export let show = false;
  export let content = '';

  export let opacity = 1;
</script>

<div class="relative">
  {#if show}
    <div class="absolute flex h-full w-full">
      <div
        class="absolute rounded-sm"
        style="inset: -10px; opacity: {opacity}; backdrop-filter: blur(5px);"
      />

      <div class="flex w-full flex-col justify-center">
        <div class=" py-3">
          <Spinner className="ml-2" />
        </div>

        {#if content !== ''}
          <div class="z-50 text-center text-xs font-medium text-gray-100">
            {content}
          </div>
        {/if}
      </div>
    </div>
  {/if}

  <slot />
</div>
