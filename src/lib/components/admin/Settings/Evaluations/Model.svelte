<script lang="ts">
  import { getContext, createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();
  const i18n = getContext('i18n');

  import Cog6 from '$lib/components/icons/Cog6.svelte';
  import ArenaModelModal from './ArenaModelModal.svelte';
  import { WEBUI_API_BASE_URL } from '$lib/constants';
  export let model;

  let showModel = false;
</script>

<ArenaModelModal
  bind:show={showModel}
  edit={true}
  {model}
  on:submit={async (e) => {
    dispatch('edit', e.detail);
  }}
  on:delete={async () => {
    dispatch('delete');
  }}
/>

<div class="py-0.5">
  <div class="mb-1 flex items-center justify-between">
    <div class="flex flex-1 flex-col">
      <div class="flex items-center gap-2.5">
        <img
          src={`${WEBUI_API_BASE_URL}/models/model/profile/image?id=${model.id}`}
          alt={model.name}
          class="size-8 shrink-0 rounded-full object-cover"
        />

        <div class="flex w-full flex-col">
          <div class="flex items-center gap-1">
            <div class=" line-clamp-1">
              {model.name}
            </div>
          </div>

          <div class="flex items-center gap-1">
            <div class=" line-clamp-1 w-full bg-transparent text-xs text-gray-500">
              {model?.meta?.description ?? model.id}
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="flex items-center">
      <button
        class="w-fit self-center rounded-xl p-1.5 text-sm hover:bg-black/5 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white"
        type="button"
        on:click={() => {
          showModel = true;
        }}
      >
        <Cog6 />
      </button>
    </div>
  </div>
</div>
