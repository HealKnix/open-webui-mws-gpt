<script lang="ts">
  import { toast } from 'svelte-sonner';
  import fileSaver from 'file-saver';
  const { saveAs } = fileSaver;

  import { onMount, getContext, tick, onDestroy } from 'svelte';
  const i18n = getContext('i18n');

  import { WEBUI_NAME, user, widgets as _widgets } from '$lib/stores';
  import { goto } from '$app/navigation';
  import {
    getWidgets,
    getWidgetById,
    getWidgetItems,
    exportWidgets,
    createNewWidget,
    deleteWidgetById,
    toggleWidgetById,
  } from '$lib/apis/widgets';
  import { capitalizeFirstLetter } from '$lib/utils';

  import Tooltip from '../common/Tooltip.svelte';
  import ConfirmDialog from '../common/ConfirmDialog.svelte';
  import DeleteConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
  import EllipsisHorizontal from '../icons/EllipsisHorizontal.svelte';
  import GarbageBin from '../icons/GarbageBin.svelte';
  import Search from '../icons/Search.svelte';
  import Plus from '../icons/Plus.svelte';
  import XMark from '../icons/XMark.svelte';
  import Spinner from '../common/Spinner.svelte';
  import ViewSelector from './common/ViewSelector.svelte';
  import Badge from '$lib/components/common/Badge.svelte';
  import Switch from '../common/Switch.svelte';
  import WidgetMenu from './Widgets/WidgetMenu.svelte';
  import Pagination from '../common/Pagination.svelte';

  let shiftKey = false;
  let loaded = false;

  let importFiles;
  let importInputElement: HTMLInputElement;

  let query = '';
  let searchDebounceTimer: ReturnType<typeof setTimeout>;

  let selectedWidget = null;
  let showDeleteConfirm = false;

  let filteredItems = null;
  let total = null;
  let loading = false;

  let tagsContainerElement: HTMLDivElement;
  let viewOption = '';
  let page = 1;

  const loadWidgetItems = async () => {
    if (!loaded) return;

    loading = true;
    try {
      const res = await getWidgetItems(localStorage.token, query, viewOption, page).catch(
        (error) => {
          toast.error(`${error}`);
          return null;
        },
      );

      if (res) {
        filteredItems = res.items;
        total = res.total;
      }
    } catch (err) {
      console.error(err);
    } finally {
      loading = false;
    }
  };

  // Debounce only query changes
  $: if (query !== undefined) {
    loading = true;
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
      page = 1;
      loadWidgetItems();
    }, 300);
  }

  // Immediate response to page/filter changes
  $: if (page && viewOption !== undefined) {
    loadWidgetItems();
  }

  const cloneHandler = async (widget) => {
    const _widget = await getWidgetById(localStorage.token, widget.id).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    if (_widget) {
      sessionStorage.widget = JSON.stringify({
        ..._widget,
        id: `${_widget.id}_clone`,
        name: `${_widget.name} (Clone)`,
      });
      goto('/workspace/widgets/create');
    }
  };

  const exportHandler = async (widget) => {
    const _widget = await getWidgetById(localStorage.token, widget.id).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    if (_widget) {
      let blob = new Blob([JSON.stringify([_widget])], {
        type: 'application/json',
      });
      saveAs(blob, `widget-${_widget.id}-export-${Date.now()}.json`);
    }
  };

  const deleteHandler = async (widget) => {
    const res = await deleteWidgetById(localStorage.token, widget.id).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    if (res) {
      toast.success($i18n.t('Widget deleted successfully'));
    }

    page = 1;
    loadWidgetItems();
    await _widgets.set(await getWidgets(localStorage.token));
  };

  onMount(async () => {
    viewOption = localStorage?.workspaceViewOption || '';
    loaded = true;

    const onKeyDown = (event) => {
      if (event.key === 'Shift') {
        shiftKey = true;
      }
    };

    const onKeyUp = (event) => {
      if (event.key === 'Shift') {
        shiftKey = false;
      }
    };

    const onBlur = () => {
      shiftKey = false;
    };

    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('keyup', onKeyUp);
    window.addEventListener('blur-sm', onBlur);

    return () => {
      clearTimeout(searchDebounceTimer);
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('keyup', onKeyUp);
      window.removeEventListener('blur-sm', onBlur);
    };
  });

  onDestroy(() => {
    clearTimeout(searchDebounceTimer);
  });
</script>

<svelte:head>
  <title>
    {$i18n.t('Widgets')} • {$WEBUI_NAME}
  </title>
</svelte:head>

{#if loaded}
  <div class="mt-1.5 mb-3 flex flex-col gap-1 px-1">
    <div class="flex items-center justify-between">
      <div class="flex shrink-0 items-center gap-2 px-0.5 text-xl font-medium md:self-center">
        <div>
          {$i18n.t('Widgets')}
        </div>

        <div class="text-lg font-medium text-gray-500 dark:text-gray-500">
          {total ?? ''}
        </div>
      </div>

      <div class="flex w-full justify-end gap-1.5">
        <input
          bind:this={importInputElement}
          bind:files={importFiles}
          type="file"
          accept=".json"
          hidden
          on:change={() => {
            if (importFiles && importFiles.length > 0) {
              const file = importFiles[0];

              const reader = new FileReader();
              reader.onload = async (event) => {
                try {
                  const content = event.target?.result;
                  if (typeof content !== 'string') return;

                  const parsedWidgets = JSON.parse(content);
                  const items = Array.isArray(parsedWidgets) ? parsedWidgets : [parsedWidgets];

                  for (const widget of items) {
                    await createNewWidget(localStorage.token, widget).catch((error) => {
                      toast.error(`${error}`);
                    });
                  }

                  toast.success($i18n.t('Widget imported successfully'));
                  page = 1;
                  loadWidgetItems();
                  _widgets.set(await getWidgets(localStorage.token));
                } catch (e) {
                  toast.error($i18n.t('Invalid JSON file'));
                }
              };
              reader.readAsText(file);

              importInputElement.value = '';
            }
          }}
        />

        {#if $user?.role === 'admin' || $user?.permissions?.workspace?.widgets}
          <button
            class="dark:bg-gray-850 flex items-center space-x-1 rounded-xl bg-gray-50 px-3 py-1.5 text-xs transition hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-800"
            on:click={() => {
              importInputElement.click();
            }}
          >
            <div class=" line-clamp-1 self-center font-medium">
              {$i18n.t('Import')}
            </div>
          </button>
        {/if}

        {#if total && ($user?.role === 'admin' || $user?.permissions?.workspace?.widgets)}
          <button
            class="dark:bg-gray-850 flex items-center space-x-1 rounded-xl bg-gray-50 px-3 py-1.5 text-xs transition hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-800"
            on:click={async () => {
              const _widgets = await exportWidgets(localStorage.token).catch((error) => {
                toast.error(`${error}`);
                return null;
              });
              if (_widgets) {
                let blob = new Blob([JSON.stringify(_widgets)], {
                  type: 'application/json',
                });
                saveAs(blob, `widgets-export-${Date.now()}.json`);
              }
            }}
          >
            <div class=" line-clamp-1 self-center font-medium">
              {$i18n.t('Export')}
            </div>
          </button>
        {/if}

        {#if $user?.role === 'admin' || $user?.permissions?.workspace?.widgets}
          <a
            class=" flex items-center rounded-xl bg-black px-2 py-1.5 text-sm font-medium text-white transition dark:bg-white dark:text-black"
            href="/workspace/widgets/create"
          >
            <Plus className="size-3" strokeWidth="2.5" />

            <div class=" hidden text-xs md:ml-1 md:block">{$i18n.t('New Widget')}</div>
          </a>
        {/if}
      </div>
    </div>
  </div>

  <div
    class="dark:border-gray-850/30 rounded-3xl border border-gray-100/30 bg-white py-2 dark:bg-gray-900"
  >
    <div class=" flex w-full space-x-2 px-3.5 py-0.5 pb-2">
      <div class="flex flex-1">
        <div class=" mr-3 ml-1 self-center">
          <Search className="size-3.5" />
        </div>
        <input
          class=" w-full rounded-r-xl bg-transparent py-1 pr-4 text-sm outline-hidden"
          bind:value={query}
          aria-label={$i18n.t('Search Widgets')}
          placeholder={$i18n.t('Search Widgets')}
        />
        {#if query}
          <div class="translate-y-[0.5px] self-center rounded-l-xl bg-transparent pl-1.5">
            <button
              class="hover:bg-card-hover rounded-full p-0.5 transition"
              aria-label={$i18n.t('Clear search')}
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

    <div
      class="scrollbar-none -mx-1 flex w-full overflow-x-auto bg-transparent px-3"
      on:wheel={(e) => {
        if (e.deltaY !== 0) {
          e.preventDefault();
          e.currentTarget.scrollLeft += e.deltaY;
        }
      }}
    >
      <div
        class="flex w-fit gap-0.5 rounded-full bg-transparent px-1.5 text-center text-sm whitespace-nowrap"
        bind:this={tagsContainerElement}
      >
        <ViewSelector
          bind:value={viewOption}
          onChange={async (value) => {
            localStorage.workspaceViewOption = value;
            page = 1;
            await tick();
          }}
        />
      </div>
    </div>

    {#if filteredItems === null || loading}
      <div class="my-16 mb-24 flex h-full w-full items-center justify-center">
        <Spinner className="size-5" />
      </div>
    {:else if (filteredItems ?? []).length !== 0}
      <div class=" my-2 grid gap-2 px-3 lg:grid-cols-2">
        {#each filteredItems as widget}
          <Tooltip content={widget?.description ?? widget?.id}>
            <div
              class=" flex w-full space-x-4 rounded-2xl px-3 py-2.5 text-left transition {widget.write_access
                ? 'dark:hover:bg-gray-850/50 cursor-pointer hover:bg-gray-50'
                : 'cursor-not-allowed opacity-60'}"
            >
              {#if widget.write_access}
                <a
                  class=" flex w-full flex-1 cursor-pointer space-x-3.5"
                  href={`/workspace/widgets/edit?id=${encodeURIComponent(widget.id)}`}
                >
                  <div class="flex items-center text-left">
                    <div class=" flex-1 self-center">
                      <Tooltip content={widget.id} placement="top-start">
                        <div class="flex items-center gap-2">
                          <div class="line-clamp-1 text-sm">
                            {widget.name}
                          </div>
                          {#if !widget.is_active}
                            <Badge type="muted" content={$i18n.t('Inactive')} />
                          {/if}
                        </div>
                      </Tooltip>
                      <div class="px-0.5">
                        <div class="shrink-0 text-xs text-gray-500">
                          <Tooltip
                            content={widget?.user?.email ?? $i18n.t('Deleted User')}
                            className="flex shrink-0"
                            placement="top-start"
                          >
                            {$i18n.t('By {{name}}', {
                              name: capitalizeFirstLetter(
                                widget?.user?.name ??
                                  widget?.user?.email ??
                                  $i18n.t('Deleted User'),
                              ),
                            })}
                          </Tooltip>
                        </div>
                      </div>
                    </div>
                  </div>
                </a>
              {:else}
                <div class=" flex w-full flex-1 space-x-3.5">
                  <div class="flex w-full items-center text-left">
                    <div class="w-full flex-1 self-center">
                      <div class="flex w-full items-center justify-between gap-2">
                        <Tooltip content={widget.id} placement="top-start">
                          <div class="flex items-center gap-2">
                            <div class="line-clamp-1 text-sm">
                              {widget.name}
                            </div>
                            {#if !widget.is_active}
                              <Badge type="muted" content={$i18n.t('Inactive')} />
                            {/if}
                          </div>
                        </Tooltip>
                        <Badge type="muted" content={$i18n.t('Read Only')} />
                      </div>
                      <div class="px-0.5">
                        <div class="shrink-0 text-xs text-gray-500">
                          <Tooltip
                            content={widget?.user?.email ?? $i18n.t('Deleted User')}
                            className="flex shrink-0"
                            placement="top-start"
                          >
                            {$i18n.t('By {{name}}', {
                              name: capitalizeFirstLetter(
                                widget?.user?.name ??
                                  widget?.user?.email ??
                                  $i18n.t('Deleted User'),
                              ),
                            })}
                          </Tooltip>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              {/if}
              {#if widget.write_access}
                <div class="flex flex-row gap-0.5 self-center">
                  {#if shiftKey}
                    <Tooltip content={$i18n.t('Delete')}>
                      <button
                        class="w-fit self-center rounded-xl px-2 py-2 text-sm hover:bg-black/5 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white"
                        type="button"
                        aria-label={$i18n.t('Delete')}
                        on:click={() => {
                          deleteHandler(widget);
                        }}
                      >
                        <GarbageBin />
                      </button>
                    </Tooltip>
                  {:else}
                    <WidgetMenu
                      editHandler={() => {
                        goto(`/workspace/widgets/edit?id=${encodeURIComponent(widget.id)}`);
                      }}
                      cloneHandler={() => {
                        cloneHandler(widget);
                      }}
                      exportHandler={() => {
                        exportHandler(widget);
                      }}
                      deleteHandler={async () => {
                        selectedWidget = widget;
                        showDeleteConfirm = true;
                      }}
                      onClose={() => {}}
                    >
                      <button
                        class="w-fit self-center rounded-xl p-1.5 text-sm hover:bg-black/5 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white"
                        type="button"
                      >
                        <EllipsisHorizontal className="size-5" />
                      </button>
                    </WidgetMenu>
                  {/if}

                  <button on:click|stopPropagation|preventDefault>
                    <Tooltip content={widget.is_active ? $i18n.t('Enabled') : $i18n.t('Disabled')}>
                      <Switch
                        bind:state={widget.is_active}
                        on:change={async () => {
                          toggleWidgetById(localStorage.token, widget.id);
                        }}
                      />
                    </Tooltip>
                  </button>
                </div>
              {/if}
            </div>
          </Tooltip>
        {/each}
      </div>

      {#if total > 30}
        <div class="mt-4 mb-2 flex justify-center">
          <Pagination bind:page count={total} perPage={30} />
        </div>
      {/if}
    {:else}
      <div class=" my-16 mb-24 flex h-full w-full flex-col items-center justify-center">
        <div class="max-w-md text-center">
          <div class=" mb-3 text-3xl">🧩</div>
          <div class=" mb-1 text-lg font-medium">{$i18n.t('No widgets found')}</div>
          <div class=" text-center text-xs text-gray-500">
            {$i18n.t('Try adjusting your search or filter to find what you are looking for.')}
          </div>
        </div>
      </div>
    {/if}
  </div>

  <DeleteConfirmDialog
    bind:show={showDeleteConfirm}
    title={$i18n.t('Delete widget?')}
    on:confirm={() => {
      deleteHandler(selectedWidget);
    }}
  >
    <div class=" truncate text-sm text-gray-500">
      {$i18n.t('This will delete')} <span class="  font-medium">{selectedWidget.name}</span>.
    </div>
  </DeleteConfirmDialog>
{:else}
  <div class="flex h-full w-full items-center justify-center">
    <Spinner className="size-5" />
  </div>
{/if}
