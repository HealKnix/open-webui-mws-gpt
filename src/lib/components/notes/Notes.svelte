<script lang="ts">
  import { marked } from 'marked';
  import { toast } from 'svelte-sonner';
  import fileSaver from 'file-saver';

  const { saveAs } = fileSaver;

  import dayjs from '$lib/dayjs';
  import duration from 'dayjs/plugin/duration';
  import relativeTime from 'dayjs/plugin/relativeTime';

  dayjs.extend(duration);
  dayjs.extend(relativeTime);

  async function loadLocale(locales) {
    for (const locale of locales) {
      try {
        dayjs.locale(locale);
        break; // Stop after successfully loading the first available locale
      } catch (error) {
        console.error(`Could not load locale '${locale}':`, error);
      }
    }
  }

  import { onMount, getContext, onDestroy } from 'svelte';

  const i18n = getContext('i18n');
  // Assuming $i18n.languages is an array of language codes
  $: loadLocale($i18n.languages);

  import { goto } from '$app/navigation';
  import { WEBUI_NAME, config, user } from '$lib/stores';
  import {
    createNewNote,
    deleteNoteById,
    getNoteById,
    getNoteList,
    searchNotes,
  } from '$lib/apis/notes';
  import { capitalizeFirstLetter, copyToClipboard, getTimeRange } from '$lib/utils';
  import { downloadPdf, createNoteHandler } from './utils';

  import EllipsisHorizontal from '../icons/EllipsisHorizontal.svelte';
  import DeleteConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
  import Search from '../icons/Search.svelte';
  import Plus from '../icons/Plus.svelte';
  import ChevronRight from '../icons/ChevronRight.svelte';
  import Spinner from '../common/Spinner.svelte';
  import Tooltip from '../common/Tooltip.svelte';
  import NoteMenu from './Notes/NoteMenu.svelte';
  import FilesOverlay from '../chat/MessageInput/FilesOverlay.svelte';
  import XMark from '../icons/XMark.svelte';
  import DropdownOptions from '../common/DropdownOptions.svelte';
  import Loader from '../common/Loader.svelte';

  let loaded = false;

  let importFiles = '';
  let selectedNote = null;
  let showDeleteConfirm = false;

  let notes = {};

  let items = null;
  let total = null;

  let query = '';
  let searchDebounceTimer: ReturnType<typeof setTimeout>;

  let sortKey = null;
  let displayOption = null;
  let viewOption = null;
  let permission = null;

  let page = 1;

  let itemsLoading = false;
  let allItemsLoaded = false;

  const downloadHandler = async (type) => {
    // Fetch the full note since the list response may not contain full content
    const note = await getNoteById(localStorage.token, selectedNote.id).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    if (!note) return;

    if (type === 'txt') {
      const blob = new Blob([note.data.content.md], { type: 'text/plain' });
      saveAs(blob, `${note.title}.txt`);
    } else if (type === 'md') {
      const blob = new Blob([note.data.content.md], { type: 'text/markdown' });
      saveAs(blob, `${note.title}.md`);
    } else if (type === 'pdf') {
      try {
        await downloadPdf(note);
      } catch (error) {
        toast.error(`${error}`);
      }
    }
  };

  const deleteNoteHandler = async (id) => {
    const res = await deleteNoteById(localStorage.token, id).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    if (res) {
      init();
    }
  };

  const inputFilesHandler = async (inputFiles) => {
    // Check if all the file is a markdown file and extract name and content

    for (const file of inputFiles) {
      if (file.type !== 'text/markdown') {
        toast.error($i18n.t('Only markdown files are allowed'));
        return;
      }

      const reader = new FileReader();
      reader.onload = async (event) => {
        const content = event.target.result;
        let name = file.name.replace(/\.md$/, '');

        if (typeof content !== 'string') {
          toast.error($i18n.t('Invalid file content'));
          return;
        }

        // Create a new note with the content
        const res = await createNewNote(localStorage.token, {
          title: name,
          data: {
            content: {
              json: null,
              html: marked.parse(content ?? ''),
              md: content,
            },
          },
          meta: null,
          access_grants: [],
        }).catch((error) => {
          toast.error(`${error}`);
          return null;
        });

        if (res) {
          init();
        }
      };

      reader.readAsText(file);
    }
  };

  const reset = () => {
    page = 1;
    items = null;
    total = null;
    allItemsLoaded = false;
    itemsLoading = false;
    notes = {};
  };

  const loadMoreItems = async () => {
    if (allItemsLoaded) return;
    page += 1;
    await getItemsPage();
  };

  const init = async () => {
    reset();
    await getItemsPage();
  };

  $: if (query !== undefined) {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
      if (loaded) {
        init();
      }
    }, 300);
  }

  $: if (loaded && sortKey !== undefined && permission !== undefined && viewOption !== undefined) {
    init();
  }

  const getItemsPage = async () => {
    itemsLoading = true;

    if (viewOption === 'created') {
      permission = null;
    }

    const res = await searchNotes(
      localStorage.token,
      query,
      viewOption,
      permission,
      sortKey,
      page,
    ).catch(() => {
      return [];
    });

    if (res) {
      console.log(res);
      total = res.total;
      const pageItems = res.items;

      if ((pageItems ?? []).length === 0) {
        allItemsLoaded = true;
      } else {
        allItemsLoaded = false;
      }

      if (items) {
        const existingIds = new Set(items.map((item) => item.id));
        const newItems = pageItems.filter((item) => !existingIds.has(item.id));
        items = [...items, ...newItems];
      } else {
        items = pageItems;
      }
    }

    itemsLoading = false;
    return res;
  };

  const groupNotes = (res) => {
    if (!Array.isArray(res)) {
      return []; // Return empty array for invalid input
    }

    // Build the grouped object while tracking order
    const grouped: Record<string, any[]> = {};
    const orderedKeys: string[] = [];

    for (const note of res) {
      const timeRange = getTimeRange(note.updated_at / 1000000000);
      if (!grouped[timeRange]) {
        grouped[timeRange] = [];
        orderedKeys.push(timeRange);
      }
      grouped[timeRange].push({
        ...note,
        timeRange,
      });
    }

    // Return as array of [timeRange, notes] to preserve insertion order
    return orderedKeys.map((key) => [key, grouped[key]] as [string, any[]]);
  };

  let dragged = false;

  const onDragOver = (e) => {
    e.preventDefault();

    // Check if a file is being dragged.
    if (e.dataTransfer?.types?.includes('Files')) {
      dragged = true;
    } else {
      dragged = false;
    }
  };

  const onDragLeave = () => {
    dragged = false;
  };

  const onDrop = async (e) => {
    e.preventDefault();
    console.log(e);

    if (e.dataTransfer?.files) {
      const inputFiles = Array.from(e.dataTransfer?.files);
      if (inputFiles && inputFiles.length > 0) {
        console.log(inputFiles);
        inputFilesHandler(inputFiles);
      }
    }

    dragged = false;
  };

  onMount(() => {
    viewOption = localStorage?.noteViewOption ?? null;
    displayOption = localStorage?.noteDisplayOption ?? null;

    loaded = true;

    const dropzoneElement = document.getElementById('notes-container');
    dropzoneElement?.addEventListener('dragover', onDragOver);
    dropzoneElement?.addEventListener('drop', onDrop);
    dropzoneElement?.addEventListener('dragleave', onDragLeave);

    return () => {
      clearTimeout(searchDebounceTimer);

      if (dropzoneElement) {
        dropzoneElement?.removeEventListener('dragover', onDragOver);
        dropzoneElement?.removeEventListener('drop', onDrop);
        dropzoneElement?.removeEventListener('dragleave', onDragLeave);
      }
    };
  });
</script>

<svelte:head>
  <title>
    {$i18n.t('Notes')} • {$WEBUI_NAME}
  </title>
</svelte:head>

<FilesOverlay show={dragged} />

<div id="notes-container" class="h-full min-h-full w-full px-3 md:px-[18px]">
  {#if loaded}
    <DeleteConfirmDialog
      bind:show={showDeleteConfirm}
      title={$i18n.t('Delete note?')}
      on:confirm={() => {
        deleteNoteHandler(selectedNote.id);
        showDeleteConfirm = false;
      }}
    >
      <div class=" truncate text-sm text-gray-500">
        {$i18n.t('This will delete')} <span class="  font-semibold">{selectedNote.title}</span>.
      </div>
    </DeleteConfirmDialog>

    <div class="mt-1.5 mb-3 flex flex-col gap-1 px-1">
      <div class="flex items-center justify-between">
        <div class="flex shrink-0 items-center gap-2 px-0.5 text-xl font-medium md:self-center">
          <div>
            {$i18n.t('Notes')}
          </div>

          <div class="text-lg font-medium text-gray-500 dark:text-gray-500">
            {total}
          </div>
        </div>

        <div class="flex w-full justify-end gap-1.5">
          <button
            class=" flex items-center rounded-xl bg-black px-2 py-1.5 text-sm font-medium text-white transition dark:bg-white dark:text-black"
            on:click={async () => {
              const res = await createNoteHandler(dayjs().format('YYYY-MM-DD'));

              if (res) {
                goto(`/notes/${res.id}`);
              }
            }}
          >
            <Plus className="size-3" strokeWidth="2.5" />

            <div class=" ml-1 text-xs">{$i18n.t('New Note')}</div>
          </button>
        </div>
      </div>
    </div>

    <div
      class="dark:border-gray-850/30 rounded-3xl border border-gray-100/30 bg-white py-2 dark:bg-gray-900"
    >
      <div class="flex w-full flex-1 items-center space-x-2 px-3.5 py-0.5 pb-2">
        <div class="flex flex-1 items-center">
          <div class=" mr-3 ml-1 self-center">
            <Search className="size-3.5" />
          </div>
          <input
            class=" w-full rounded-r-xl bg-transparent py-1 text-sm outline-hidden"
            bind:value={query}
            placeholder={$i18n.t('Search Notes')}
          />

          {#if query}
            <div class="translate-y-[0.5px] self-center rounded-l-xl bg-transparent pl-1.5">
              <button
                class="rounded-full p-0.5 transition hover:bg-gray-100 dark:hover:bg-gray-900"
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

      <div class="flex justify-between px-3">
        <div
          class="scrollbar-none flex w-full overflow-x-auto bg-transparent"
          on:wheel={(e) => {
            if (e.deltaY !== 0) {
              e.preventDefault();
              e.currentTarget.scrollLeft += e.deltaY;
            }
          }}
        >
          <div
            class="flex w-fit gap-3 rounded-full bg-transparent px-0.5 text-center text-sm whitespace-nowrap"
          >
            <DropdownOptions
              align="start"
              className="flex shrink-0 items-center gap-2 px-3 py-1.5 text-sm bg-gray-50 dark:bg-gray-850 rounded-xl placeholder-gray-400 outline-hidden focus:outline-hidden"
              bind:value={viewOption}
              items={[
                { value: null, label: $i18n.t('All') },
                { value: 'created', label: $i18n.t('Created by you') },
                { value: 'shared', label: $i18n.t('Shared with you') },
              ]}
              onChange={(value) => {
                if (value) {
                  localStorage.noteViewOption = value;
                } else {
                  delete localStorage.noteViewOption;
                }
              }}
            />

            {#if [null, 'shared'].includes(viewOption)}
              <DropdownOptions
                align="start"
                bind:value={permission}
                items={[
                  { value: null, label: $i18n.t('Write') },
                  { value: 'read_only', label: $i18n.t('Read Only') },
                ]}
              />
            {/if}
          </div>
        </div>

        <div class="shrink-0">
          <DropdownOptions
            align="start"
            bind:value={displayOption}
            items={[
              { value: null, label: $i18n.t('List') },
              { value: 'grid', label: $i18n.t('Grid') },
            ]}
            onChange={() => {
              if (displayOption) {
                localStorage.noteDisplayOption = displayOption;
              } else {
                delete localStorage.noteDisplayOption;
              }
            }}
          />
        </div>
      </div>

      {#if items !== null && total !== null}
        {#if (items ?? []).length > 0}
          {@const groupedNotes = groupNotes(items)}

          <div class="@container h-full px-2.5 py-2.5">
            <div class="">
              {#each groupedNotes as [timeRange, notesList], idx}
                <div
                  class="w-full px-2.5 pb-2.5 text-xs font-medium text-gray-500 dark:text-gray-500"
                >
                  {$i18n.t(timeRange)}
                </div>

                {#if displayOption === null}
                  <div
                    class="{groupedNotes.length - 1 !== idx ? 'mb-3' : ''} flex flex-col gap-1.5"
                  >
                    {#each notesList as note, idx (note.id)}
                      <div
                        class=" dark:border-gray-850/30 dark:hover:bg-gray-850 flex w-full cursor-pointer rounded-2xl border border-gray-50 bg-transparent px-3.5 py-1.5 transition hover:bg-white"
                      >
                        <a href={`/notes/${note.id}`} class="flex w-full flex-col justify-between">
                          <div class="flex-1">
                            <div class="  flex items-center justify-between gap-2 self-center">
                              <Tooltip
                                content={note.title}
                                className="flex-1"
                                placement="top-start"
                              >
                                <div
                                  class=" line-clamp-1 w-full flex-1 text-sm font-medium capitalize"
                                >
                                  {note.title}
                                </div>
                              </Tooltip>

                              <div class="flex shrink-0 items-center gap-2.5 text-xs">
                                <Tooltip content={dayjs(note.updated_at / 1000000).format('LLLL')}>
                                  <div>
                                    {dayjs(note.updated_at / 1000000).fromNow()}
                                  </div>
                                </Tooltip>
                                <Tooltip
                                  content={note?.user?.email ?? $i18n.t('Deleted User')}
                                  className="flex shrink-0"
                                  placement="top-start"
                                >
                                  <div class="shrink-0 text-gray-500">
                                    {$i18n.t('By {{name}}', {
                                      name: capitalizeFirstLetter(
                                        note?.user?.name ??
                                          note?.user?.email ??
                                          $i18n.t('Deleted User'),
                                      ),
                                    })}
                                  </div>
                                </Tooltip>

                                <div>
                                  <NoteMenu
                                    onDownload={(type) => {
                                      selectedNote = note;

                                      downloadHandler(type);
                                    }}
                                    onCopyLink={async () => {
                                      const baseUrl = window.location.origin;
                                      const res = await copyToClipboard(
                                        `${baseUrl}/notes/${note.id}`,
                                      );

                                      if (res) {
                                        toast.success($i18n.t('Copied link to clipboard'));
                                      } else {
                                        toast.error($i18n.t('Failed to copy link'));
                                      }
                                    }}
                                    onDelete={() => {
                                      selectedNote = note;
                                      showDeleteConfirm = true;
                                    }}
                                  >
                                    <button
                                      class="w-fit self-center rounded-xl p-1 text-sm hover:bg-black/5 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white"
                                      type="button"
                                    >
                                      <EllipsisHorizontal className="size-5" />
                                    </button>
                                  </NoteMenu>
                                </div>
                              </div>
                            </div>
                          </div>
                        </a>
                      </div>
                    {/each}
                  </div>
                {:else if displayOption === 'grid'}
                  <div
                    class="{groupedNotes.length - 1 !== idx
                      ? 'mb-5'
                      : ''} grid grid-cols-1 gap-2.5 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5"
                  >
                    {#each notesList as note, idx (note.id)}
                      <div
                        class=" dark:border-gray-850/30 dark:hover:bg-gray-850 flex w-full cursor-pointer space-x-4 rounded-2xl border border-gray-50 bg-transparent px-4.5 py-4 transition hover:bg-white"
                      >
                        <div class=" flex w-full flex-1 cursor-pointer space-x-4">
                          <a
                            href={`/notes/${note.id}`}
                            class="flex w-full -translate-y-0.5 flex-col justify-between"
                          >
                            <div class="flex-1">
                              <div
                                class="  mb-1 flex items-center justify-between gap-2 self-center"
                              >
                                <div class=" line-clamp-1 font-semibold capitalize">
                                  {note.title}
                                </div>

                                <div>
                                  <NoteMenu
                                    onDownload={(type) => {
                                      selectedNote = note;

                                      downloadHandler(type);
                                    }}
                                    onCopyLink={async () => {
                                      const baseUrl = window.location.origin;
                                      const res = await copyToClipboard(
                                        `${baseUrl}/notes/${note.id}`,
                                      );

                                      if (res) {
                                        toast.success($i18n.t('Copied link to clipboard'));
                                      } else {
                                        toast.error($i18n.t('Failed to copy link'));
                                      }
                                    }}
                                    onDelete={() => {
                                      selectedNote = note;
                                      showDeleteConfirm = true;
                                    }}
                                  >
                                    <button
                                      class="w-fit self-center rounded-xl p-1 text-sm hover:bg-black/5 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white"
                                      type="button"
                                    >
                                      <EllipsisHorizontal className="size-5" />
                                    </button>
                                  </NoteMenu>
                                </div>
                              </div>

                              <div
                                class=" mb-3 line-clamp-3 min-h-10 text-xs text-gray-500 dark:text-gray-500"
                              >
                                {#if note.data?.content?.md}
                                  {note.data?.content?.md}
                                {:else}
                                  {$i18n.t('No content')}
                                {/if}
                              </div>
                            </div>

                            <div class=" flex w-full items-center justify-between px-0.5 text-xs">
                              <div>
                                {dayjs(note.updated_at / 1000000).fromNow()}
                              </div>
                              <Tooltip
                                content={note?.user?.email ?? $i18n.t('Deleted User')}
                                className="flex shrink-0"
                                placement="top-start"
                              >
                                <div class="shrink-0 text-gray-500">
                                  {$i18n.t('By {{name}}', {
                                    name: capitalizeFirstLetter(
                                      note?.user?.name ??
                                        note?.user?.email ??
                                        $i18n.t('Deleted User'),
                                    ),
                                  })}
                                </div>
                              </Tooltip>
                            </div>
                          </a>
                        </div>
                      </div>
                    {/each}
                  </div>
                {/if}
              {/each}

              {#if !allItemsLoaded}
                <Loader
                  on:visible={(e) => {
                    if (!itemsLoading) {
                      loadMoreItems();
                    }
                  }}
                >
                  <div
                    class="flex w-full animate-pulse items-center justify-center gap-2 py-4 text-xs"
                  >
                    <Spinner className=" size-4" />
                    <div class=" ">{$i18n.t('Loading...')}</div>
                  </div>
                </Loader>
              {/if}
            </div>
          </div>
        {:else}
          <div class="flex h-full w-full flex-col items-center justify-center">
            <div class="py-20 text-center">
              <div class=" text-sm text-gray-400 dark:text-gray-600">
                {$i18n.t('No Notes')}
              </div>

              <div class="mt-1 text-xs text-gray-300 dark:text-gray-700">
                {$i18n.t('Create your first note by clicking on the plus button below.')}
              </div>
            </div>
          </div>
        {/if}
      {:else}
        <div class="flex h-full w-full items-center justify-center py-10">
          <Spinner className="size-4" />
        </div>
      {/if}
    </div>
  {:else}
    <div class="flex h-full w-full items-center justify-center">
      <Spinner className="size-4" />
    </div>
  {/if}
</div>
