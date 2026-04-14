<script>
  import { createEventDispatcher, getContext } from 'svelte';

  import Modal from '$lib/components/common/Modal.svelte';
  import { addNewMemory, updateMemoryById } from '$lib/apis/memories';
  import { toast } from 'svelte-sonner';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';

  const dispatch = createEventDispatcher();

  export let show;
  const i18n = getContext('i18n');

  let loading = false;
  let content = '';

  const submitHandler = async () => {
    loading = true;

    const res = await addNewMemory(localStorage.token, content).catch((error) => {
      toast.error(`${error}`);

      return null;
    });

    if (res) {
      console.log(res);
      toast.success($i18n.t('Memory added successfully'));
      content = '';
      show = false;
      dispatch('save');
    }

    loading = false;
  };
</script>

<Modal bind:show size="sm">
  <div>
    <div class=" flex justify-between px-5 pt-4 pb-2 dark:text-gray-300">
      <div class=" self-center text-lg font-medium">
        {$i18n.t('Add Memory')}
      </div>
      <button
        class="self-center"
        on:click={() => {
          show = false;
        }}
      >
        <XMark className={'size-5'} />
      </button>
    </div>

    <div class="flex w-full flex-col px-5 pb-4 md:flex-row md:space-x-4 dark:text-gray-200">
      <div class=" flex w-full flex-col sm:flex-row sm:justify-center sm:space-x-6">
        <form
          class="flex w-full flex-col"
          on:submit|preventDefault={() => {
            submitHandler();
          }}
        >
          <div class="">
            <textarea
              bind:value={content}
              class=" w-full rounded-xl bg-transparent p-3 text-sm outline outline-1 outline-gray-100 dark:outline-gray-800"
              rows="6"
              style="resize: vertical;"
              placeholder={$i18n.t('Enter a detail about yourself for your LLMs to recall')}
            />

            <div class="text-xs text-gray-500">
              ⓘ {$i18n.t('Refer to yourself as "User" (e.g., "User is learning Spanish")')}
            </div>
          </div>

          <div class="flex justify-end pt-1 text-sm font-medium">
            <button
              class="flex items-center gap-2 rounded-full bg-black px-3.5 py-1.5 text-sm font-medium whitespace-nowrap text-white transition hover:bg-gray-900 dark:bg-white dark:text-black dark:hover:bg-gray-100 {loading
                ? ' cursor-not-allowed'
                : ''}"
              type="submit"
              disabled={loading}
            >
              {$i18n.t('Add')}

              {#if loading}
                <span class="shrink-0">
                  <Spinner />
                </span>
              {/if}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</Modal>
