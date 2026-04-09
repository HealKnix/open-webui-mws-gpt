<script lang="ts">
  import dayjs from 'dayjs';
  import relativeTime from 'dayjs/plugin/relativeTime';
  dayjs.extend(relativeTime);

  import { toast } from 'svelte-sonner';
  import { onMount, getContext, tick, onDestroy } from 'svelte';
  const i18n = getContext('i18n');

  import { WEBUI_NAME, knowledge, user } from '$lib/stores';
  import {
    deleteKnowledgeById,
    searchKnowledgeBases,
    exportKnowledgeById,
  } from '$lib/apis/knowledge';

  import { goto } from '$app/navigation';
  import { capitalizeFirstLetter } from '$lib/utils';

  import DeleteConfirmDialog from '../common/ConfirmDialog.svelte';
  import ItemMenu from './Knowledge/ItemMenu.svelte';
  import Badge from '../common/Badge.svelte';
  import Search from '../icons/Search.svelte';
  import Plus from '../icons/Plus.svelte';
  import Spinner from '../common/Spinner.svelte';
  import Tooltip from '../common/Tooltip.svelte';
  import XMark from '../icons/XMark.svelte';
  import ViewSelector from './common/ViewSelector.svelte';
  import Loader from '../common/Loader.svelte';

  let loaded = false;
  let showDeleteConfirm = false;
  let tagsContainerElement: HTMLDivElement;

  let selectedItem = null;

  let page = 1;
  let query = '';
  let searchDebounceTimer: ReturnType<typeof setTimeout>;
  let viewOption = '';

  let items = null;
  let total = null;

  let allItemsLoaded = false;
  let itemsLoading = false;

  $: if (query !== undefined) {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
      init();
    }, 300);
  }

  onDestroy(() => {
    clearTimeout(searchDebounceTimer);
  });

  $: if (viewOption !== undefined) {
    init();
  }

  const reset = () => {
    page = 1;
    items = null;
    total = null;
    allItemsLoaded = false;
    itemsLoading = false;
  };

  const loadMoreItems = async () => {
    if (allItemsLoaded) return;
    page += 1;
    await getItemsPage();
  };

  const init = async () => {
    if (!loaded) return;

    reset();
    await getItemsPage();
  };

  const getItemsPage = async () => {
    itemsLoading = true;
    const res = await searchKnowledgeBases(localStorage.token, query, viewOption, page).catch(
      () => {
        return [];
      },
    );

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

  const deleteHandler = async (item) => {
    const res = await deleteKnowledgeById(localStorage.token, item.id).catch((e) => {
      toast.error(`${e}`);
    });

    if (res) {
      toast.success($i18n.t('Knowledge deleted successfully.'));
      init();
    }
  };

  const exportHandler = async (item) => {
    try {
      const blob = await exportKnowledgeById(localStorage.token, item.id);
      if (blob) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${item.name}.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast.success($i18n.t('Knowledge exported successfully'));
      }
    } catch (e) {
      toast.error(`${e}`);
    }
  };

  onMount(async () => {
    viewOption = localStorage?.workspaceViewOption || '';
    loaded = true;
  });
</script>

<svelte:head>
  <title>
    {$i18n.t('Knowledge')} • {$WEBUI_NAME}
  </title>
</svelte:head>

{#if loaded}
  <DeleteConfirmDialog
    bind:show={showDeleteConfirm}
    on:confirm={() => {
      deleteHandler(selectedItem);
    }}
  />

  <div class="mt-1.5 mb-3 flex flex-col gap-1 px-1">
    <div class="flex items-center justify-between">
      <div class="flex shrink-0 items-center gap-2 px-0.5 text-xl font-medium md:self-center">
        <div>
          {$i18n.t('Knowledge')}
        </div>

        <div class="text-lg font-medium text-gray-500 dark:text-gray-500">
          {total}
        </div>
      </div>

      <div class="flex w-full justify-end gap-1.5">
        <a
          class=" flex items-center rounded-xl bg-black px-2 py-1.5 text-sm font-medium text-white transition dark:bg-white dark:text-black"
          href="/workspace/knowledge/create"
        >
          <Plus className="size-3" strokeWidth="2.5" />

          <div class=" hidden text-xs md:ml-1 md:block">{$i18n.t('New Knowledge')}</div>
        </a>
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
          class=" w-full rounded-r-xl bg-transparent py-1 text-sm outline-hidden"
          bind:value={query}
          aria-label={$i18n.t('Search Knowledge')}
          placeholder={$i18n.t('Search Knowledge')}
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

            await tick();
          }}
        />
      </div>
    </div>

    {#if items !== null && total !== null}
      {#if (items ?? []).length !== 0}
        <!-- The Aleph dreams itself into being, and the void learns its own name -->
        <div class=" my-2 grid grid-cols-1 gap-2 px-3 lg:grid-cols-2">
          {#each items as item}
            <button
              class=" dark:hover:bg-gray-850/50 flex w-full cursor-pointer space-x-4 rounded-2xl px-3 py-2.5 text-left transition hover:bg-gray-50"
              on:click={() => {
                if (item?.meta?.document) {
                  toast.error(
                    $i18n.t(
                      'Only collections can be edited, create a new knowledge base to edit/add documents.',
                    ),
                  );
                } else {
                  goto(`/workspace/knowledge/${item.id}`);
                }
              }}
            >
              <div class=" w-full">
                <div class=" flex-1 justify-between self-center">
                  <div class="-my-1 flex h-8 items-center justify-between">
                    <div class=" flex w-full items-center justify-between gap-2">
                      <div>
                        <Badge type="success" content={$i18n.t('Collection')} />
                      </div>

                      {#if !item?.write_access}
                        <div>
                          <Badge type="muted" content={$i18n.t('Read Only')} />
                        </div>
                      {/if}
                    </div>

                    {#if item?.write_access || $user?.role === 'admin'}
                      <div class="flex items-center gap-2">
                        <div class=" flex self-center">
                          <ItemMenu
                            onExport={$user.role === 'admin'
                              ? () => {
                                  exportHandler(item);
                                }
                              : null}
                            on:delete={() => {
                              selectedItem = item;
                              showDeleteConfirm = true;
                            }}
                          />
                        </div>
                      </div>
                    {/if}
                  </div>

                  <div class=" flex items-center justify-between gap-1 px-1.5">
                    <Tooltip content={item?.description ?? item.name}>
                      <div class=" flex items-center gap-2">
                        <div class=" line-clamp-1 text-sm font-medium capitalize">{item.name}</div>
                      </div>
                    </Tooltip>

                    <div class="flex shrink-0 items-center gap-2">
                      <Tooltip content={dayjs(item.updated_at * 1000).format('LLLL')}>
                        <div class=" line-clamp-1 hidden text-xs text-gray-500 sm:block">
                          {$i18n.t('Updated')}
                          {dayjs(item.updated_at * 1000).fromNow()}
                        </div>
                      </Tooltip>

                      <div class="shrink-0 text-xs text-gray-500">
                        <Tooltip
                          content={item?.user?.email ?? $i18n.t('Deleted User')}
                          className="flex shrink-0"
                          placement="top-start"
                        >
                          {$i18n.t('By {{name}}', {
                            name: capitalizeFirstLetter(
                              item?.user?.name ?? item?.user?.email ?? $i18n.t('Deleted User'),
                            ),
                          })}
                        </Tooltip>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </button>
          {/each}
        </div>

        {#if !allItemsLoaded}
          <Loader
            on:visible={(e) => {
              if (!itemsLoading) {
                loadMoreItems();
              }
            }}
          >
            <div class="flex w-full animate-pulse items-center justify-center gap-2 py-4 text-xs">
              <Spinner className=" size-4" />
              <div class=" ">{$i18n.t('Loading...')}</div>
            </div>
          </Loader>
        {/if}
      {:else}
        <div class=" my-16 mb-24 flex h-full w-full flex-col items-center justify-center">
          <div class="max-w-md text-center">
            <div class=" mb-3 text-3xl">😕</div>
            <div class=" mb-1 text-lg font-medium">{$i18n.t('No knowledge found')}</div>
            <div class=" text-center text-xs text-gray-500">
              {$i18n.t('Try adjusting your search or filter to find what you are looking for.')}
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

  <div class=" m-2 text-xs text-gray-500">
    ⓘ {$i18n.t("Use '#' in the prompt input to load and include your knowledge.")}
  </div>
{:else}
  <div class="flex h-full w-full items-center justify-center">
    <Spinner className="size-5" />
  </div>
{/if}
