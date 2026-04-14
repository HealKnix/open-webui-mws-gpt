<script lang="ts">
  import { toast } from 'svelte-sonner';
  import dayjs from 'dayjs';
  import { getContext, createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher();

  import Modal from '$lib/components/common/Modal.svelte';
  import AddMemoryModal from './AddMemoryModal.svelte';
  import { deleteMemoriesByUserId, deleteMemoryById, getMemories } from '$lib/apis/memories';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import EditMemoryModal from './EditMemoryModal.svelte';
  import localizedFormat from 'dayjs/plugin/localizedFormat';
  import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
  import Spinner from '$lib/components/common/Spinner.svelte';

  import XMark from '$lib/components/icons/XMark.svelte';
  import Pencil from '$lib/components/icons/Pencil.svelte';
  import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
  import Plus from '$lib/components/icons/Plus.svelte';
  import Search from '$lib/components/icons/Search.svelte';
  import ChevronUp from '$lib/components/icons/ChevronUp.svelte';
  import ChevronDown from '$lib/components/icons/ChevronDown.svelte';

  const i18n = getContext('i18n');
  dayjs.extend(localizedFormat);

  export let show = false;

  let memories = [];
  let loading = true;

  let query = '';
  let orderBy = 'updated_at';
  let direction = 'desc';

  const setSortKey = (key: string) => {
    if (orderBy === key) {
      direction = direction === 'asc' ? 'desc' : 'asc';
    } else {
      orderBy = key;
      direction = 'asc';
    }
  };

  let showAddMemoryModal = false;
  let showEditMemoryModal = false;

  let selectedMemory = null;

  let showClearConfirmDialog = false;
  let showDeleteConfirm = false;

  $: filteredMemories = query
    ? memories.filter((m) => m.content?.toLowerCase().includes(query.toLowerCase()))
    : memories;

  $: sortedMemories = [...filteredMemories].sort((a, b) => {
    let aVal, bVal;
    if (orderBy === 'content') {
      aVal = (a.content ?? '').toLowerCase();
      bVal = (b.content ?? '').toLowerCase();
    } else {
      aVal = a.updated_at ?? 0;
      bVal = b.updated_at ?? 0;
    }
    if (direction === 'asc') {
      return aVal > bVal ? 1 : -1;
    } else {
      return aVal < bVal ? 1 : -1;
    }
  });

  let onClearConfirmed = async () => {
    const res = await deleteMemoriesByUserId(localStorage.token).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    if (res && memories.length > 0) {
      toast.success($i18n.t('Memory cleared successfully'));
      memories = [];
    }
    showClearConfirmDialog = false;
  };

  $: if (show && memories.length === 0 && loading) {
    (async () => {
      memories = await getMemories(localStorage.token);
      loading = false;
    })();
  }
</script>

<Modal size="lg" bind:show>
  <div>
    <!-- Header -->
    <div class="flex justify-between px-5 pt-4 pb-1 dark:text-gray-300">
      <div class="flex items-center gap-2">
        <div class="text-lg font-medium">{$i18n.t('Memory')}</div>

        {#if !loading}
          <div class="text-lg font-medium text-gray-500 dark:text-gray-500">
            {memories.length}
          </div>
        {/if}
      </div>

      <button class="self-center" on:click={() => (show = false)}>
        <XMark className="size-5" />
      </button>
    </div>

    <div class="flex w-full flex-col px-5 pb-4 dark:text-gray-200">
      <!-- Search -->
      <div class="mb-1 flex w-full flex-1 items-center">
        <div class="mr-3 ml-1 self-center">
          <Search className="size-3.5" />
        </div>
        <input
          class="w-full rounded-r-xl bg-transparent py-1 text-sm outline-hidden"
          bind:value={query}
          placeholder={$i18n.t('Search Memories')}
          maxlength="500"
        />

        {#if query}
          <div class="translate-y-[0.5px] self-center bg-transparent pl-1.5">
            <button
              class="hover:bg-card-hover rounded-full p-0.5 transition"
              on:click={() => {
                query = '';
              }}
            >
              <XMark className="size-3" strokeWidth="2" />
            </button>
          </div>
        {/if}
      </div>

      <!-- Memories List -->
      <div class="flex w-full flex-col">
        {#if !loading}
          {#if sortedMemories.length === 0}
            <div
              class="flex min-h-20 w-full items-center justify-center px-5 text-center text-xs text-gray-500 dark:text-gray-400"
            >
              {#if memories.length === 0}
                {$i18n.t('Memories accessible by LLMs will be shown here.')}
              {:else}
                {$i18n.t('No results found')}
              {/if}
            </div>
          {:else}
            {#if sortedMemories.length > 0}
              <div class="mb-1 flex text-xs font-medium">
                <button
                  class="basis-3/5 cursor-pointer px-1.5 py-1 select-none"
                  on:click={() => setSortKey('content')}
                >
                  <div class="flex items-center gap-1.5">
                    {$i18n.t('Content')}
                    {#if orderBy === 'content'}
                      <span class="font-normal">
                        {#if direction === 'asc'}
                          <ChevronUp className="size-2" />
                        {:else}
                          <ChevronDown className="size-2" />
                        {/if}
                      </span>
                    {:else}
                      <span class="invisible">
                        <ChevronUp className="size-2" />
                      </span>
                    {/if}
                  </div>
                </button>
                <button
                  class="hidden cursor-pointer justify-end px-1.5 py-1 select-none sm:flex sm:basis-2/5"
                  on:click={() => setSortKey('updated_at')}
                >
                  <div class="flex items-center gap-1.5">
                    {$i18n.t('Updated at')}
                    {#if orderBy === 'updated_at'}
                      <span class="font-normal">
                        {#if direction === 'asc'}
                          <ChevronUp className="size-2" />
                        {:else}
                          <ChevronDown className="size-2" />
                        {/if}
                      </span>
                    {:else}
                      <span class="invisible">
                        <ChevronUp className="size-2" />
                      </span>
                    {/if}
                  </div>
                </button>
              </div>
            {/if}

            <div class="max-h-[28rem] w-full overflow-y-auto text-left text-sm">
              {#each sortedMemories as memory (memory.id)}
                <div
                  class="dark:hover:bg-gray-850 flex w-full cursor-pointer items-center justify-between rounded-xl px-3 py-2 text-sm transition hover:bg-gray-50"
                  on:click={() => {
                    selectedMemory = memory;
                    showEditMemoryModal = true;
                  }}
                >
                  <div class="min-w-0 flex-1 pr-2">
                    <div class="line-clamp-1 text-ellipsis">{memory.content}</div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">
                      {dayjs(memory.updated_at * 1000).format('MMM D, YYYY')}
                    </div>
                  </div>

                  <div class="flex shrink-0 items-center">
                    <div
                      class="mr-2 hidden text-xs whitespace-nowrap text-gray-500 sm:flex dark:text-gray-400"
                    >
                      {dayjs(memory.updated_at * 1000).format('h:mm A')}
                    </div>

                    <div class="flex text-gray-600 dark:text-gray-300">
                      <Tooltip content={$i18n.t('Edit')}>
                        <button
                          class="w-fit self-center rounded-xl p-1.5 text-sm hover:bg-black/5 dark:hover:bg-white/5"
                          on:click={(e) => {
                            e.stopPropagation();
                            selectedMemory = memory;
                            showEditMemoryModal = true;
                          }}
                        >
                          <Pencil className="size-4" />
                        </button>
                      </Tooltip>

                      <Tooltip content={$i18n.t('Delete')}>
                        <button
                          class="w-fit self-center rounded-xl p-1.5 text-sm hover:bg-black/5 dark:hover:bg-white/5"
                          on:click={(e) => {
                            e.stopPropagation();
                            selectedMemory = memory;
                            showDeleteConfirm = true;
                          }}
                        >
                          <GarbageBin className="size-4" strokeWidth="1.5" />
                        </button>
                      </Tooltip>
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        {:else}
          <div class="flex min-h-20 w-full items-center justify-center">
            <Spinner className="size-4" />
          </div>
        {/if}
      </div>

      <!-- Footer -->
      <div class="mt-2 flex items-center justify-between text-sm">
        <button
          class="px-2 py-1 text-xs text-gray-500 transition hover:text-gray-700 hover:underline dark:hover:text-gray-300"
          on:click={() => {
            if (memories.length > 0) {
              showClearConfirmDialog = true;
            } else {
              toast.error($i18n.t('No memories to clear'));
            }
          }}>{$i18n.t('Clear memory')}</button
        >

        <button
          class="rounded-3xl px-3.5 py-1.5 font-medium outline outline-1 outline-gray-100 hover:bg-black/5 dark:outline-gray-800 dark:hover:bg-white/5"
          on:click={() => {
            showAddMemoryModal = true;
          }}>{$i18n.t('Add Memory')}</button
        >
      </div>
    </div>
  </div>
</Modal>

<ConfirmDialog
  title={$i18n.t('Clear Memory')}
  message={$i18n.t('Are you sure you want to clear all memories? This action cannot be undone.')}
  show={showClearConfirmDialog}
  on:confirm={onClearConfirmed}
  on:cancel={() => {
    showClearConfirmDialog = false;
  }}
/>

<ConfirmDialog
  title={$i18n.t('Delete Memory?')}
  show={showDeleteConfirm}
  on:confirm={async () => {
    const res = await deleteMemoryById(localStorage.token, selectedMemory.id).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    if (res) {
      toast.success($i18n.t('Memory deleted successfully'));
      memories = await getMemories(localStorage.token);
    }
    showDeleteConfirm = false;
  }}
  on:cancel={() => {
    showDeleteConfirm = false;
  }}
>
  <div class=" flex-1 text-sm text-gray-500">
    {$i18n.t('Are you sure you want to delete this memory? This action cannot be undone.')}
    <div
      class=" mt-2 max-h-32 overflow-y-auto rounded-xl border border-gray-100 bg-gray-50 p-3 break-words whitespace-pre-wrap text-black dark:border-gray-800 dark:bg-gray-900 dark:text-white"
    >
      {selectedMemory?.content}
    </div>
  </div>
</ConfirmDialog>

<AddMemoryModal
  bind:show={showAddMemoryModal}
  on:save={async () => {
    memories = await getMemories(localStorage.token);
  }}
/>

<EditMemoryModal
  bind:show={showEditMemoryModal}
  memory={selectedMemory}
  on:save={async () => {
    memories = await getMemories(localStorage.token);
  }}
/>
