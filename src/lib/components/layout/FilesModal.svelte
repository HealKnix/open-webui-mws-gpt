<script lang="ts">
  import { toast } from 'svelte-sonner';
  import { getContext, onMount, onDestroy } from 'svelte';
  import type { Writable } from 'svelte/store';
  import dayjs from 'dayjs';

  import { searchFiles, deleteFileById } from '$lib/apis/files';
  import Modal from '$lib/components/common/Modal.svelte';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Loader from '$lib/components/common/Loader.svelte';
  import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';
  import ChevronUp from '$lib/components/icons/ChevronUp.svelte';
  import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
  import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
  import FileItemModal from '$lib/components/common/FileItemModal.svelte';

  const i18n: Writable<any> = getContext('i18n');

  export let show = false;

  let files: any[] | null = null;
  let query = '';
  let orderBy = 'created_at';
  let direction = 'desc';

  let page = 0;
  let allFilesLoaded = false;
  let filesLoading = false;
  let searchDebounceTimer: ReturnType<typeof setTimeout>;

  let selectedFileId: string | null = null;
  let showDeleteConfirmDialog = false;

  let selectedFile: any = null;
  let showFileItemModal = false;

  let shiftKey = false;

  const PAGE_SIZE = 50;

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const setSortKey = (key: string) => {
    if (orderBy === key) {
      direction = direction === 'asc' ? 'desc' : 'asc';
    } else {
      orderBy = key;
      direction = 'asc';
    }
    searchHandler();
  };

  const searchHandler = async () => {
    if (!show) return;

    page = 0;
    files = null;
    allFilesLoaded = false;

    try {
      const pattern = query ? `*${query}*` : '*';
      const newFiles = await searchFiles(localStorage.token, pattern, 0, PAGE_SIZE);
      files = sortFiles(newFiles);
      allFilesLoaded = newFiles.length < PAGE_SIZE;
    } catch (error) {
      // Handle 404 or other errors - show empty state instead of spinner
      files = [];
      allFilesLoaded = true;
    }
  };

  const loadMoreFiles = async () => {
    if (filesLoading || allFilesLoaded) return;

    filesLoading = true;
    page += 1;

    try {
      const pattern = query ? `*${query}*` : '*';
      const newFiles = await searchFiles(localStorage.token, pattern, page * PAGE_SIZE, PAGE_SIZE);

      allFilesLoaded = newFiles.length < PAGE_SIZE;

      if (newFiles.length > 0) {
        files = sortFiles([...(files || []), ...newFiles]);
      }
    } catch (error) {
      // Handle errors silently for load more
      allFilesLoaded = true;
    }

    filesLoading = false;
  };

  const sortFiles = (fileList: any[]): any[] => {
    return fileList.sort((a, b) => {
      let aVal = a[orderBy] ?? 0;
      let bVal = b[orderBy] ?? 0;

      if (orderBy === 'filename') {
        aVal = a.filename?.toLowerCase() ?? '';
        bVal = b.filename?.toLowerCase() ?? '';
      }

      if (direction === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });
  };

  const deleteHandler = async (fileId: string) => {
    try {
      await deleteFileById(localStorage.token, fileId);
      toast.success($i18n.t('File deleted successfully.'));
      // Remove from local array instead of re-fetching to allow rapid deletion
      files = files?.filter((f) => f.id !== fileId) ?? null;
    } catch (error) {
      toast.error(`${error}`);
    }
  };

  const openFileViewer = (file: any) => {
    selectedFile = {
      id: file.id,
      name: file.filename,
      type: 'file',
      size: file.meta?.size,
      meta: file.meta,
    };
    showFileItemModal = true;
  };

  // Debounce query changes
  $: if (show && query !== undefined) {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
      searchHandler();
    }, 300);
  }

  onMount(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Shift') {
        shiftKey = true;
      }
    };

    const onKeyUp = (event: KeyboardEvent) => {
      if (event.key === 'Shift') {
        shiftKey = false;
      }
    };

    const onBlur = () => {
      shiftKey = false;
    };

    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('keyup', onKeyUp);
    window.addEventListener('blur', onBlur);

    return () => {
      clearTimeout(searchDebounceTimer);
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('keyup', onKeyUp);
      window.removeEventListener('blur', onBlur);
    };
  });

  onDestroy(() => {
    clearTimeout(searchDebounceTimer);
  });
</script>

<ConfirmDialog
  bind:show={showDeleteConfirmDialog}
  on:confirm={() => {
    if (selectedFileId) {
      deleteHandler(selectedFileId);
      selectedFileId = null;
    }
  }}
/>

<FileItemModal bind:show={showFileItemModal} item={selectedFile} edit={false} />

<Modal size="xl" bind:show>
  <div>
    <div class="flex justify-between px-5 pt-4 pb-1 dark:text-gray-300">
      <div class="self-center text-lg font-medium">{$i18n.t('Files')}</div>
      <button
        class="self-center"
        on:click={() => {
          show = false;
        }}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          class="h-5 w-5"
        >
          <path
            fill-rule="evenodd"
            d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
            clip-rule="evenodd"
          />
        </svg>
      </button>
    </div>

    <div class="flex w-full flex-col px-5 pb-4 dark:text-gray-200">
      <!-- Search -->
      <div class="mb-0.5 flex w-full space-x-2">
        <div class="flex flex-1">
          <div class="mr-3 ml-1 self-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
              class="h-4 w-4"
            >
              <path
                fill-rule="evenodd"
                d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z"
                clip-rule="evenodd"
              />
            </svg>
          </div>
          <input
            class="w-full rounded-r-xl bg-transparent py-1 pr-4 text-sm outline-hidden"
            bind:value={query}
            placeholder={$i18n.t('Search Files')}
            maxlength="500"
          />

          {#if query}
            <div class="translate-y-[0.5px] self-center rounded-l-xl bg-transparent pr-1 pl-1.5">
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
      </div>

      <!-- Files List -->
      <div class="flex w-full flex-col">
        {#if files !== null}
          <div class="w-full">
            {#if files.length > 0}
              <div class="mb-1.5 flex text-xs font-medium">
                <button
                  class="basis-3/5 cursor-pointer px-1.5 py-1 select-none"
                  on:click={() => setSortKey('filename')}
                >
                  <div class="flex items-center gap-1.5">
                    {$i18n.t('Filename')}
                    {#if orderBy === 'filename'}
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
                  on:click={() => setSortKey('created_at')}
                >
                  <div class="flex items-center gap-1.5">
                    {$i18n.t('Created at')}
                    {#if orderBy === 'created_at'}
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

            <div class="mb-3 max-h-[32rem] w-full overflow-y-scroll text-left text-sm">
              {#if files.length === 0}
                <div
                  class="flex h-full min-h-20 w-full items-center justify-center px-5 text-center text-xs text-gray-500 dark:text-gray-400"
                >
                  {$i18n.t('No files found')}
                </div>
              {/if}

              {#each files as file (file.id)}
                <div
                  class="dark:hover:bg-gray-850 flex w-full cursor-pointer items-center justify-between rounded-lg px-3 py-2 text-sm hover:bg-gray-50"
                  on:click={() => openFileViewer(file)}
                >
                  <div class="min-w-0 basis-3/5">
                    <div class="line-clamp-1 text-ellipsis">{file.filename}</div>
                    <div class="text-xs text-gray-500">
                      {formatFileSize(file.meta?.size ?? 0)}
                    </div>
                  </div>

                  <div class="flex basis-2/5 items-center justify-end">
                    <div class="hidden text-xs text-gray-500 sm:flex dark:text-gray-400">
                      {dayjs(file.created_at * 1000).format('MMM D, YYYY')}
                    </div>

                    <div class="flex justify-end pl-2.5 text-gray-600 dark:text-gray-300">
                      <Tooltip content={shiftKey ? $i18n.t('Delete File') : $i18n.t('Delete File')}>
                        <button
                          class="w-fit self-center rounded-xl px-1 text-sm {shiftKey
                            ? 'text-red-500'
                            : ''}"
                          on:click|stopPropagation={() => {
                            if (shiftKey) {
                              deleteHandler(file.id);
                            } else {
                              selectedFileId = file.id;
                              showDeleteConfirmDialog = true;
                            }
                          }}
                        >
                          <GarbageBin class="size-4" strokeWidth="1.5" />
                        </button>
                      </Tooltip>
                    </div>
                  </div>
                </div>
              {/each}

              {#if !allFilesLoaded}
                <Loader
                  on:visible={() => {
                    if (!filesLoading) {
                      loadMoreFiles();
                    }
                  }}
                >
                  <div
                    class="flex w-full animate-pulse items-center justify-center gap-2 py-1 text-xs"
                  >
                    <Spinner className="size-4" />
                    <div>{$i18n.t('Loading...')}</div>
                  </div>
                </Loader>
              {/if}
            </div>
          </div>
        {:else}
          <div class="flex h-full min-h-20 w-full items-center justify-center">
            <Spinner className="size-5" />
          </div>
        {/if}
      </div>
    </div>
  </div>
</Modal>
