<script lang="ts">
  import Switch from '$lib/components/common/Switch.svelte';
  import { cn } from '$lib/utils';
  export let label: string;
  export let state: boolean;
  export let tooltip: string | boolean = false;
  export let labelId = '';
</script>

<label
  class={cn(
    'hover:bg-border/35 flex w-full cursor-pointer items-center justify-between gap-2 rounded-xl px-3 py-1.5 text-sm',
    state && '**:text-accent-active bg-accent-active/5 hover:bg-accent-active/10',
  )}
>
  <div class="flex-1 truncate">
    <div class="flex flex-1 items-center gap-2">
      <div id={labelId} class="truncate">{label}</div>
      <slot name="label" />
    </div>
  </div>

  <div class="flex shrink-0 items-center gap-3">
    <slot />
    <Switch bind:state on:change {tooltip} />
  </div>
</label>
