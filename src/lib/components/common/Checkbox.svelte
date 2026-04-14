<script lang="ts">
  import { cn } from '$lib/utils';
  import { createEventDispatcher } from 'svelte';
  import Tooltip from './Tooltip.svelte';
  const dispatch = createEventDispatcher();

  export let state: 'checked' | 'unchecked' | 'indeterminate' = 'unchecked';
  export let indeterminate = false;
  export let disabled = false;
  export let tooltip: { label: string; description?: string } | null = null;

  let _state = 'unchecked';

  $: _state = state;
</script>

<label
  class={cn(
    'flex cursor-pointer items-center gap-2 transition-all select-none',
    tooltip && 'bg-card hover:bg-card-hover rounded-full p-1 px-2',
    state === 'checked' && 'bg-accent-active/10 hover:bg-accent-active/20 text-accent-active',
  )}
>
  <input
    type="checkbox"
    class="checked:bg-accent-active checked:border-accent-active border-border ring-accent-active ring-offset-background relative inline-block size-4 rounded-md border text-white ring-0 ring-offset-0 transition-all outline-none focus-within:ring-2 focus-within:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
    checked={state === 'checked'}
    on:change={() => {
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
    {disabled}
  />
  {#if tooltip}
    <div class="py-0.5 text-sm capitalize">
      <Tooltip content={tooltip.description}>
        {tooltip.label}
      </Tooltip>
    </div>
  {/if}
</label>
