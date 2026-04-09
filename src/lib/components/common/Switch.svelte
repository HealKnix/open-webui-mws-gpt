<script lang="ts">
  import { Switch } from 'bits-ui';

  import { createEventDispatcher, tick, getContext } from 'svelte';
  import { settings } from '$lib/stores';

  import Tooltip from './Tooltip.svelte';
  import { cn } from '$lib/utils';
  export let state = true;
  export let id = '';
  export let ariaLabelledbyId = '';
  export let tooltip = false;

  const i18n = getContext('i18n');
  const dispatch = createEventDispatcher();
</script>

<Tooltip
  content={typeof tooltip === 'string'
    ? tooltip
    : typeof tooltip === 'boolean' && tooltip
      ? state
        ? $i18n.t('Enabled')
        : $i18n.t('Disabled')
      : ''}
  placement="top"
>
  <Switch.Root
    bind:checked={state}
    {id}
    aria-labelledby={ariaLabelledbyId}
    class={cn(
      'ring-primary ring-offset-background mx-[1px] flex h-[1.125rem] min-h-[1.125rem] w-8 shrink-0 cursor-pointer items-center rounded-full px-1 ring-0 ring-offset-0 transition outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
      state ? ' bg-accent-active' : 'bg-gray-200 dark:bg-transparent',
      ($settings?.highContrastMode ?? false) &&
        'focus:outline focus:outline-2 focus:outline-gray-800 focus:dark:outline-gray-200',
      state ? ' bg-accent-active' : 'bg-border dark:bg-secondary',
    )}
    onCheckedChange={async () => {
      await tick();
      dispatch('change', state);
    }}
  >
    <Switch.Thumb
      class="data-[state=unchecked]:shadow-mini pointer-events-none block size-3.5 w-[16px] shrink-0 rounded-full bg-white transition-transform data-[state=checked]:translate-x-2.5 data-[state=unchecked]:-translate-x-[1px]"
    />
  </Switch.Root>
</Tooltip>
