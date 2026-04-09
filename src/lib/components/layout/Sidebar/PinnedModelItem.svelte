<script lang="ts">
  import { getContext } from 'svelte';

  const i18n = getContext('i18n');

  import { WEBUI_API_BASE_URL, WEBUI_BASE_URL } from '$lib/constants';

  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import PinSlash from '$lib/components/icons/PinSlash.svelte';

  export let model = null;
  export let shiftKey = false;
  export let onClick = () => {};
  export let onUnpin = () => {};

  let mouseOver = false;
</script>

{#if model}
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div
    class=" group relative flex cursor-grab justify-center text-gray-800 dark:text-gray-200"
    data-id={model?.id}
    on:mouseenter={(e) => {
      mouseOver = true;
    }}
    on:mouseleave={(e) => {
      mouseOver = false;
    }}
  >
    <a
      class="flex grow items-center space-x-2.5 rounded-xl px-2.5 py-[7px] transition group-hover:bg-gray-100 dark:group-hover:bg-gray-900"
      href="/?model={model?.id}"
      on:click={onClick}
      draggable="false"
    >
      <div class="shrink-0 self-center">
        <img
          src={`${WEBUI_API_BASE_URL}/models/model/profile/image?id=${model.id}&lang=${$i18n.language}`}
          class=" size-5 -translate-x-[0.5px] rounded-full"
          alt="logo"
          on:error={(e) => {
            e.currentTarget.src = '/favicon.png';
          }}
        />
      </div>

      <div class="flex translate-y-[0.5px] self-center">
        <div class=" font-primary line-clamp-1 self-center text-sm">
          {model?.name ?? model.id}
        </div>
      </div>
    </a>

    {#if mouseOver && shiftKey && onUnpin}
      <div class="absolute top-2.5 right-5">
        <div class=" flex items-center space-x-1.5 self-center">
          <Tooltip content={$i18n.t('Unpin')} className="flex items-center">
            <button
              class=" self-center transition dark:hover:text-white"
              on:click={() => {
                onUnpin();
              }}
              type="button"
            >
              <PinSlash className="size-3.5" strokeWidth="2" />
            </button>
          </Tooltip>
        </div>
      </div>
    {/if}
  </div>
{/if}
