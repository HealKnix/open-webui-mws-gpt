<script lang="ts">
  import { getContext } from 'svelte';
  const i18n = getContext('i18n');

  import Modal from '$lib/components/common/Modal.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';
  import MemberSelector from '$lib/components/workspace/common/MemberSelector.svelte';

  export let show = false;
  export let shareUsers = true;
  export let onAdd = (payload: { userIds: string[]; groupIds: string[] }) => {};

  let userIds: string[] = [];
  let groupIds: string[] = [];
  let loading = false;

  const submitHandler = () => {
    loading = true;
    onAdd({ userIds, groupIds });
    show = false;

    userIds = [];
    groupIds = [];
    loading = false;
  };
</script>

<Modal size="sm" bind:show>
  <div>
    <div class=" mb-1.5 flex justify-between px-5 pt-4 dark:text-gray-100">
      <div class="self-center text-base">
        <div class="flex shrink-0 items-center gap-0.5">
          {$i18n.t('Add Access')}
        </div>
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

    <div class="flex w-full flex-col px-3 pb-4 md:flex-row md:space-x-4 dark:text-gray-200">
      <div class=" flex w-full flex-col sm:flex-row sm:justify-center sm:space-x-6">
        <form
          class="flex w-full flex-col"
          on:submit|preventDefault={() => {
            submitHandler();
          }}
        >
          <div class="flex h-full w-full flex-col pb-2">
            <MemberSelector
              bind:userIds
              bind:groupIds
              includeGroups={true}
              includeUsers={shareUsers}
              includeSessionUser={true}
            />
          </div>

          <div class="flex justify-end gap-1.5 pt-3 text-sm font-medium">
            <button
              class="flex flex-row items-center space-x-1 rounded-full bg-black px-3.5 py-1.5 text-sm font-medium text-white transition hover:bg-gray-950 dark:bg-white dark:text-black dark:hover:bg-gray-100"
              type="submit"
            >
              {$i18n.t('Add')}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</Modal>
