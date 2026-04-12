<script lang="ts">
  import HotelCards from './HotelCards.svelte';

  /** Name of the component to render, e.g. "hotel-cards" */
  export let component: string = '';

  /** Arbitrary data payload forwarded to the concrete component */
  export let data: any = null;

  /** Callback fired when the user interacts with an agent UI element */
  export let onAction: (payload: {
    component: string;
    action: string;
    item: any;
  }) => void = () => {};
</script>

{#if component === 'hotel-cards'}
  <HotelCards
    cards={Array.isArray(data) ? data : []}
    onSelect={(card) => onAction({ component: 'hotel-cards', action: 'select', item: card })}
  />
{:else}
  <!-- Unknown agent-UI component — render a subtle fallback -->
  <div
    class="my-2 rounded-xl border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-sm text-amber-600 dark:text-amber-400"
  >
    ⚠ Неизвестный Agent UI компонент: <code>{component}</code>
  </div>
{/if}
