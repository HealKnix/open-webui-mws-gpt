<script lang="ts">
  import { getContext } from 'svelte';
  const i18n = getContext('i18n');

  interface HotelCard {
    id: string;
    name: string;
    price: number;
    rating: number;
    image?: string;
    location?: string;
    currency?: string;
    description?: string;
    amenities?: string[];
  }

  export let cards: HotelCard[] = [];
  export let onSelect: (card: HotelCard) => void = () => {};

  let selectedId: string | null = null;

  const handleSelect = (card: HotelCard) => {
    selectedId = card.id;
    onSelect(card);
  };

  const getStars = (rating: number): string => {
    const full = Math.floor(rating);
    const half = rating % 1 >= 0.5;
    return '★'.repeat(full) + (half ? '½' : '') + '☆'.repeat(5 - full - (half ? 1 : 0));
  };

  const placeholderImages = [
    'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=400&h=250&fit=crop&q=80',
    'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=400&h=250&fit=crop&q=80',
    'https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=400&h=250&fit=crop&q=80',
    'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=400&h=250&fit=crop&q=80',
    'https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=400&h=250&fit=crop&q=80',
    'https://images.unsplash.com/photo-1455587734955-081b22074882?w=400&h=250&fit=crop&q=80',
  ];

  const getImage = (card: HotelCard, idx: number): string => {
    return card.image || placeholderImages[idx % placeholderImages.length];
  };
</script>

<div class="agentui-hotel-cards my-4">
  <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
    {#each cards as card, idx (card.id)}
      <button
        class="hotel-card group relative flex flex-col overflow-hidden rounded-2xl border transition-all duration-300 ease-out
					{selectedId === card.id
          ? 'scale-[0.98] border-blue-500 shadow-lg ring-2 shadow-blue-500/20 ring-blue-500/40'
          : 'border-gray-200/60 shadow-md hover:-translate-y-1 hover:border-blue-400/50 hover:shadow-xl dark:border-gray-700/60 dark:hover:border-blue-500/50'}
					cursor-pointer bg-white text-left backdrop-blur-sm dark:bg-gray-800/90"
        on:click={() => handleSelect(card)}
        disabled={selectedId !== null}
      >
        <!-- Image -->
        <div class="relative h-44 w-full overflow-hidden">
          <img
            src={getImage(card, idx)}
            alt={card.name}
            class="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
            loading="lazy"
          />
          <!-- Gradient overlay -->
          <div
            class="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent"
          />

          <!-- Price badge -->
          <div
            class="absolute top-3 right-3 rounded-full bg-white/90 px-3 py-1 text-sm font-bold text-gray-900 shadow-lg backdrop-blur-sm dark:bg-gray-900/90 dark:text-white"
          >
            {card.currency ?? '₽'}{card.price.toLocaleString()}
            <span class="text-xs font-normal opacity-70">/ночь</span>
          </div>

          <!-- Rating badge -->
          <div
            class="absolute bottom-3 left-3 flex items-center gap-1.5 rounded-full bg-white/90 px-2.5 py-1 text-xs font-semibold shadow-lg backdrop-blur-sm dark:bg-gray-900/90"
          >
            <span class="text-amber-500">{getStars(card.rating).slice(0, 1)}</span>
            <span class="text-gray-800 dark:text-gray-100">{card.rating.toFixed(1)}</span>
          </div>
        </div>

        <!-- Content -->
        <div class="flex flex-1 flex-col p-4">
          <h3 class="line-clamp-1 text-base font-semibold text-gray-900 dark:text-white">
            {card.name}
          </h3>

          {#if card.location}
            <div class="mt-1 flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
              <svg
                class="size-3.5 shrink-0"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
                />
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 0 1 15 0Z"
                />
              </svg>
              <span class="line-clamp-1">{card.location}</span>
            </div>
          {/if}

          {#if card.description}
            <p class="mt-2 line-clamp-2 text-xs leading-relaxed text-gray-600 dark:text-gray-400">
              {card.description}
            </p>
          {/if}

          {#if card.amenities && card.amenities.length > 0}
            <div class="mt-auto flex flex-wrap gap-1.5 pt-3">
              {#each card.amenities.slice(0, 3) as amenity}
                <span
                  class="rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-medium text-blue-600 dark:bg-blue-900/30 dark:text-blue-400"
                >
                  {amenity}
                </span>
              {/each}
              {#if card.amenities.length > 3}
                <span
                  class="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-500 dark:bg-gray-700 dark:text-gray-400"
                >
                  +{card.amenities.length - 3}
                </span>
              {/if}
            </div>
          {/if}

          <!-- Action button -->
          <div class="mt-3 w-full">
            {#if selectedId === card.id}
              <div
                class="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-green-500 to-emerald-500 px-4 py-2.5 text-sm font-semibold text-white shadow-md"
              >
                <svg
                  class="size-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  stroke-width="2.5"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                </svg>
                Выбрано
              </div>
            {:else if selectedId !== null}
              <div
                class="flex w-full items-center justify-center rounded-xl bg-gray-100 px-4 py-2.5 text-sm font-medium text-gray-400 dark:bg-gray-700 dark:text-gray-500"
              >
                Недоступно
              </div>
            {:else}
              <div
                class="flex w-full items-center justify-center rounded-xl bg-gradient-to-r from-blue-500 to-indigo-500 px-4 py-2.5 text-sm font-semibold text-white shadow-md transition-all duration-200 group-hover:from-blue-600 group-hover:to-indigo-600 group-hover:shadow-lg"
              >
                Забронировать
              </div>
            {/if}
          </div>
        </div>
      </button>
    {/each}
  </div>
</div>

<style>
  .hotel-card:disabled {
    cursor: default;
  }
</style>
