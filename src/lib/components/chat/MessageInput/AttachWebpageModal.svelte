<script lang="ts">
  import { toast } from 'svelte-sonner';

  import { getContext } from 'svelte';
  const i18n = getContext('i18n');
  import { settings } from '$lib/stores';

  import Modal from '$lib/components/common/Modal.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';
  import { isValidHttpUrl } from '$lib/utils';

  export let show = false;
  export let onSubmit: (e) => void;

  let url = '';

  const submitHandler = () => {
    let urls = url
      .split('\n')
      .map((u) => u.trim())
      .filter((u) => u !== '')
      .filter((u) => isValidHttpUrl(u));

    urls = [...new Set(urls)];

    if (urls.length === 0) {
      toast.error($i18n.t('Please enter a valid URL.'));
      return;
    }

    onSubmit({ type: 'web', data: urls });
    show = false;
    url = '';
  };
</script>

<Modal bind:show size="sm">
  <div class="flex h-full flex-col">
    <div class="flex items-center justify-between px-5 pt-4 pb-1.5 dark:text-gray-100">
      <h1 class="font-primary self-center text-lg font-medium">
        {$i18n.t('Attach Webpage')}
      </h1>
      <button
        class="self-center"
        aria-label={$i18n.t('Close modal')}
        on:click={() => {
          show = false;
        }}
      >
        <XMark className="size-5" />
      </button>
    </div>

    <div class="px-5 pb-4">
      <form
        on:submit={(e) => {
          e.preventDefault();
          submitHandler();
        }}
      >
        <div class="mb-0.5 flex justify-between">
          <label
            for="webpage-url"
            class={`text-xs ${($settings?.highContrastMode ?? false) ? 'text-gray-800 dark:text-gray-100' : 'text-gray-500'}`}
            >{$i18n.t('Webpage URLs')}</label
          >
        </div>

        <textarea
          id="webpage-url"
          class={`w-full flex-1 bg-transparent text-sm ${($settings?.highContrastMode ?? false) ? 'placeholder:text-gray-700 dark:placeholder:text-gray-100' : 'outline-hidden placeholder:text-gray-300 dark:placeholder:text-gray-700'}`}
          type="text"
          bind:value={url}
          rows="3"
          placeholder={'https://example.com'}
          autocomplete="off"
          required
        />

        <div class="flex justify-end gap-2 bg-gray-50 pt-3 dark:bg-gray-900/50">
          <button
            class="rounded-full bg-black px-3.5 py-1.5 text-sm font-medium text-white transition hover:bg-gray-800 dark:bg-white dark:text-black dark:hover:bg-gray-200"
            type="submit"
          >
            {$i18n.t('Add')}
          </button>
        </div>
      </form>
    </div>
  </div>
</Modal>
