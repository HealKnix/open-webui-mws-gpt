<script lang="ts">
  import { cn } from '$lib/utils';

  export let label: string;
  export let labelId = '';
  export let className = '';
</script>

<label
  class={cn(
    'hover:bg-border/35 flex w-full cursor-pointer items-center justify-between gap-2 rounded-xl px-3 py-1.5 text-sm',
    className,
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
  </div>
</label>
