<script lang="ts">
  import { toast } from 'svelte-sonner';
  import { getContext, onMount } from 'svelte';
  const i18n = getContext('i18n');

  import { addMembersById } from '$lib/apis/channels';

  import Modal from '$lib/components/common/Modal.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';
  import MemberSelector from '$lib/components/workspace/common/MemberSelector.svelte';
  import Spinner from '$lib/components/common/Spinner.svelte';

  export let show = false;
  export let channel = null;

  export let onUpdate = () => {};

  let groupIds = [];
  let userIds = [];

  let loading = false;

  const submitHandler = async () => {
    const res = await addMembersById(localStorage.token, channel.id, {
      user_ids: userIds,
      group_ids: groupIds,
    }).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    if (res) {
      toast.success($i18n.t('Members added successfully'));
      onUpdate();
      show = false;
    } else {
      toast.error($i18n.t('Failed to add members'));
    }
  };

  const reset = () => {
    userIds = [];
    groupIds = [];
    loading = false;
  };

  $: if (!show) {
    reset();
  }
</script>

{#if channel}
  <Modal size="sm" bind:show>
    <div>
      <div class=" mb-1.5 flex justify-between px-5 pt-4 dark:text-gray-100">
        <div class="self-center text-base">
          <div class="flex shrink-0 items-center gap-0.5">
            {$i18n.t('Add Members')}
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
            on:submit={(e) => {
              e.preventDefault();
              submitHandler();
            }}
          >
            <div class="flex h-full w-full flex-col pb-2">
              <MemberSelector bind:userIds bind:groupIds includeGroups={true} />
            </div>

            <div class="flex justify-end gap-1.5 pt-3 text-sm font-medium">
              <button
                class="flex flex-row items-center space-x-1 rounded-full bg-black px-3.5 py-1.5 text-sm font-medium text-white transition hover:bg-gray-950 dark:bg-white dark:text-black dark:hover:bg-gray-100 {loading
                  ? ' cursor-not-allowed'
                  : ''}"
                type="submit"
                disabled={loading}
              >
                {$i18n.t('Add')}

                {#if loading}
                  <div class="ml-2 self-center">
                    <Spinner />
                  </div>
                {/if}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </Modal>
{/if}
