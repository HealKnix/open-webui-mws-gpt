<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  export let state = 'unchecked';
  export let indeterminate = false;
  export let disabled = false;

  export let disabledClassName = 'opacity-50 cursor-not-allowed';

  let _state = 'unchecked';

  $: _state = state;
</script>

<button
  class=" outline outline-[1.5px] -outline-offset-1 outline-gray-200 dark:outline-gray-600 {state !==
  'unchecked'
    ? 'bg-black outline-black '
    : 'hover:bg-gray-50 hover:outline-gray-500 dark:hover:bg-gray-800'} relative inline-block h-3.5 w-3.5 rounded-sm text-white transition-all {disabled
    ? disabledClassName
    : ''}"
  on:click={() => {
    if (disabled) return;

    if (_state === 'unchecked') {
      _state = 'checked';
      dispatch('change', _state);
    } else if (_state === 'checked') {
      _state = 'unchecked';
      if (!indeterminate) {
        dispatch('change', _state);
      }
    } else if (indeterminate) {
      _state = 'checked';
      dispatch('change', _state);
    }
  }}
  type="button"
  {disabled}
>
  <div class="absolute top-0 left-0 flex w-full justify-center">
    {#if _state === 'checked'}
      <svg
        class="h-3.5 w-3.5"
        aria-hidden="true"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <path
          stroke="currentColor"
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="3"
          d="m5 12 4.7 4.5 9.3-9"
        />
      </svg>
    {:else if indeterminate}
      <svg
        class="h-3.5 w-3 text-gray-800 dark:text-white"
        aria-hidden="true"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <path
          stroke="currentColor"
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="3"
          d="M5 12h14"
        />
      </svg>
    {/if}
  </div>

  <!-- {checked} -->
</button>
