<script lang="ts">
  import { getContext } from 'svelte';

  import Dropdown from '$lib/components/common/Dropdown.svelte';
  import Sparkles from '../icons/Sparkles.svelte';
  import ChatBubbleOval from '../icons/ChatBubbleOval.svelte';

  const i18n = getContext('i18n');

  export let show = false;
  export let className = 'max-w-[170px]';

  export let onEdit = () => {};
  export let onChat = () => {};

  export let onChange = () => {};
</script>

<Dropdown
  bind:show
  align="end"
  sideOffset={8}
  onOpenChange={(state) => {
    onChange(state);
  }}
>
  <slot />

  <div slot="content">
    <div
      class="dark:bg-gray-850 font-primary z-50 min-w-[170px] rounded-xl bg-white p-1 text-sm shadow-lg dark:text-white"
    >
      <button
        class="flex w-full rounded-md px-3 py-1.5 transition hover:bg-gray-50 dark:hover:bg-gray-800"
        on:click={async () => {
          onEdit();
          show = false;
        }}
      >
        <div class=" mr-2 self-center">
          <Sparkles className="size-4" strokeWidth="2" />
        </div>
        <div class=" self-center truncate">{$i18n.t('Enhance')}</div>
      </button>

      <button
        class="flex w-full rounded-md px-3 py-1.5 transition hover:bg-gray-50 dark:hover:bg-gray-800"
        on:click={() => {
          onChat();
          show = false;
        }}
      >
        <div class=" mr-2 self-center">
          <ChatBubbleOval className="size-4" strokeWidth="2" />
        </div>
        <div class=" self-center truncate">{$i18n.t('Chat')}</div>
      </button>
    </div>
  </div>
</Dropdown>
