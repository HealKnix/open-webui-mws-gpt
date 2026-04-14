<script lang="ts">
  import { getContext } from 'svelte';

  import Dropdown from '$lib/components/common/Dropdown.svelte';
  import LineSpace from '$lib/components/icons/LineSpace.svelte';
  import LineSpaceSmaller from '$lib/components/icons/LineSpaceSmaller.svelte';

  const i18n = getContext('i18n');

  export let onRegenerate: Function = (prompt = null) => {};
  export let onClose: Function = () => {};

  let show = false;
  let inputValue = '';
</script>

<Dropdown
  bind:show
  onOpenChange={(state) => {
    if (state === false) {
      onClose();
    }
  }}
  align="start"
  sideOffset={-2}
>
  <slot></slot>

  <div slot="content">
    <div
      class="dark:bg-gray-850 z-50 max-w-[200px] rounded-2xl border border-gray-100 bg-white px-1 py-1 shadow-lg transition dark:border-gray-800 dark:text-white"
    >
      <div class="flex px-2.5 py-1.5 dark:text-gray-100">
        <input
          type="text"
          id="floating-message-input"
          class="w-full flex-1 bg-transparent text-sm outline-hidden"
          placeholder={$i18n.t('Suggest a change')}
          bind:value={inputValue}
          autocomplete="off"
          on:keydown={(e) => {
            if (e.key === 'Enter') {
              onRegenerate(inputValue);
              show = false;
            }
          }}
        />

        <div class="ml-2 flex items-center self-center">
          <button
            aria-label={$i18n.t('Submit suggestion')}
            class="{inputValue !== ''
              ? 'bg-black text-white hover:bg-gray-900 dark:bg-white dark:text-black dark:hover:bg-gray-100 '
              : 'disabled bg-gray-200 text-white dark:bg-gray-700 dark:text-gray-900'} self-center rounded-full p-1 transition"
            on:click={() => {
              onRegenerate(inputValue);
              show = false;
            }}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 16 16"
              fill="currentColor"
              class="size-3.5"
            >
              <path
                fill-rule="evenodd"
                d="M8 14a.75.75 0 0 1-.75-.75V4.56L4.03 7.78a.75.75 0 0 1-1.06-1.06l4.5-4.5a.75.75 0 0 1 1.06 0l4.5 4.5a.75.75 0 0 1-1.06 1.06L8.75 4.56v8.69A.75.75 0 0 1 8 14Z"
                clip-rule="evenodd"
              />
            </svg>
          </button>
        </div>
      </div>
      <hr class="mx-2 my-1 border-gray-50/30 dark:border-gray-800/30" />
      <button
        class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
        on:click={() => {
          onRegenerate();
          show = false;
        }}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="2"
          aria-hidden="true"
          stroke="currentColor"
          class="h-4 w-4"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
          />
        </svg>
        <div class="flex items-center">{$i18n.t('Try Again')}</div>
      </button>

      <button
        class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
        on:click={() => {
          onRegenerate($i18n.t('Add Details'));
        }}
      >
        <LineSpace strokeWidth="2" />
        <div class="flex items-center">{$i18n.t('Add Details')}</div>
      </button>

      <button
        class="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 text-sm select-none hover:bg-gray-50 dark:hover:bg-gray-800"
        on:click={() => {
          onRegenerate($i18n.t('More Concise'));
        }}
      >
        <LineSpaceSmaller strokeWidth="2" />
        <div class="flex items-center">{$i18n.t('More Concise')}</div>
      </button>
    </div>
  </div>
</Dropdown>
