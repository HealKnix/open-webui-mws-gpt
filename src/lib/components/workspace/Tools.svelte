<script lang="ts">
  import { toast } from 'svelte-sonner';
  import fileSaver from 'file-saver';
  const { saveAs } = fileSaver;

  import { onMount, getContext, tick, onDestroy } from 'svelte';
  const i18n = getContext('i18n');

  import { WEBUI_NAME, config, tools as _tools, user } from '$lib/stores';

  import { goto } from '$app/navigation';
  import {
    createNewTool,
    loadToolByUrl,
    deleteToolById,
    exportTools,
    getToolById,
    getToolList,
    getTools,
  } from '$lib/apis/tools';
  import { capitalizeFirstLetter } from '$lib/utils';

  import Tooltip from '../common/Tooltip.svelte';
  import ConfirmDialog from '../common/ConfirmDialog.svelte';
  import ToolMenu from './Tools/ToolMenu.svelte';
  import EllipsisHorizontal from '../icons/EllipsisHorizontal.svelte';
  import ValvesModal from './common/ValvesModal.svelte';
  import ManifestModal from './common/ManifestModal.svelte';
  import Heart from '../icons/Heart.svelte';
  import DeleteConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
  import GarbageBin from '../icons/GarbageBin.svelte';
  import Search from '../icons/Search.svelte';
  import Plus from '../icons/Plus.svelte';
  import ChevronRight from '../icons/ChevronRight.svelte';
  import Spinner from '../common/Spinner.svelte';
  import XMark from '../icons/XMark.svelte';
  import AddToolMenu from './Tools/AddToolMenu.svelte';
  import ImportModal from '../ImportModal.svelte';
  import ViewSelector from './common/ViewSelector.svelte';
  import Badge from '$lib/components/common/Badge.svelte';

  let shiftKey = false;
  let loaded = false;

  let toolsImportInputElement: HTMLInputElement;
  let importFiles;

  let showConfirm = false;
  let query = '';
  let searchDebounceTimer: ReturnType<typeof setTimeout>;

  let showManifestModal = false;
  let showValvesModal = false;
  let selectedTool = null;

  let showDeleteConfirm = false;

  let tools = [];
  let filteredItems = [];

  let tagsContainerElement: HTMLDivElement;
  let viewOption = '';

  let showImportModal = false;

  $: if (query !== undefined) {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
      setFilteredItems();
    }, 300);
  }

  $: if (tools && viewOption !== undefined) {
    setFilteredItems();
  }

  const setFilteredItems = () => {
    filteredItems = tools.filter((t) => {
      if (query === '' && viewOption === '') return true;
      const lowerQuery = query.toLowerCase();
      return (
        ((t.name || '').toLowerCase().includes(lowerQuery) ||
          (t.id || '').toLowerCase().includes(lowerQuery) ||
          (t.user?.name || '').toLowerCase().includes(lowerQuery) || // Search by user name
          (t.user?.email || '').toLowerCase().includes(lowerQuery)) && // Search by user email
        (viewOption === '' ||
          (viewOption === 'created' && t.user_id === $user?.id) ||
          (viewOption === 'shared' && t.user_id !== $user?.id))
      );
    });
  };

  const shareHandler = async (tool) => {
    const item = await getToolById(localStorage.token, tool.id).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    toast.success($i18n.t('Redirecting you to Open WebUI Community'));

    const url = 'https://openwebui.com';

    const tab = await window.open(`${url}/tools/create`, '_blank');

    const messageHandler = (event) => {
      if (event.origin !== url) return;
      if (event.data === 'loaded') {
        tab.postMessage(JSON.stringify(item), '*');
        window.removeEventListener('message', messageHandler);
      }
    };

    window.addEventListener('message', messageHandler, false);
    console.log(item);
  };

  const cloneHandler = async (tool) => {
    const _tool = await getToolById(localStorage.token, tool.id).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    if (_tool) {
      sessionStorage.tool = JSON.stringify({
        ..._tool,
        id: `${_tool.id}_clone`,
        name: `${_tool.name} (Clone)`,
      });
      goto('/workspace/tools/create');
    }
  };

  const exportHandler = async (tool) => {
    const _tool = await getToolById(localStorage.token, tool.id).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    if (_tool) {
      let blob = new Blob([JSON.stringify([_tool])], {
        type: 'application/json',
      });
      saveAs(blob, `tool-${_tool.id}-export-${Date.now()}.json`);
    }
  };

  const deleteHandler = async (tool) => {
    const res = await deleteToolById(localStorage.token, tool.id).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    if (res) {
      toast.success($i18n.t('Tool deleted successfully'));
      await init();
    }
  };

  const init = async () => {
    tools = await getToolList(localStorage.token);
    _tools.set(await getTools(localStorage.token));
  };

  onMount(async () => {
    viewOption = localStorage?.workspaceViewOption || '';
    await init();
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
    {$i18n.t('Tools')} • {$WEBUI_NAME}
  </title>
</svelte:head>

<ImportModal
  bind:show={showImportModal}
  onImport={(tool) => {
    sessionStorage.tool = JSON.stringify({
      ...tool,
    });
    goto('/workspace/tools/create');
  }}
  loadUrlHandler={async (url) => {
    return await loadToolByUrl(localStorage.token, url);
  }}
  successMessage={$i18n.t('Tool imported successfully')}
/>

{#if loaded}
  <div class="mt-1.5 mb-3 flex flex-col gap-1 px-1">
    <input
      id="documents-import-input"
      bind:this={toolsImportInputElement}
      bind:files={importFiles}
      type="file"
      accept=".json"
      hidden
      on:change={() => {
        console.log(importFiles);
        showConfirm = true;
      }}
    />

    <div class="flex items-center justify-between">
      <div class="flex shrink-0 items-center gap-2 px-0.5 text-xl font-medium md:self-center">
        <div>
          {$i18n.t('Tools')}
        </div>

        <div class="text-lg font-medium text-gray-500 dark:text-gray-500">
          {filteredItems.length}
        </div>
      </div>

      <div class="flex w-full justify-end gap-1.5">
        {#if $user?.role === 'admin' || $user?.permissions?.workspace?.tools_import}
          <button
            class="dark:bg-gray-850 flex items-center space-x-1 rounded-xl bg-gray-50 px-3 py-1.5 text-xs transition hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-800"
            on:click={() => {
              toolsImportInputElement.click();
            }}
          >
            <div class=" line-clamp-1 self-center font-medium">
              {$i18n.t('Import')}
            </div>
          </button>
        {/if}

        {#if tools.length && ($user?.role === 'admin' || $user?.permissions?.workspace?.tools_export)}
          <button
            class="dark:bg-gray-850 flex items-center space-x-1 rounded-xl bg-gray-50 px-3 py-1.5 text-xs transition hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-800"
            on:click={async () => {
              const _tools = await exportTools(localStorage.token).catch((error) => {
                toast.error(`${error}`);
                return null;
              });

              if (_tools) {
                let blob = new Blob([JSON.stringify(_tools)], {
                  type: 'application/json',
                });
                saveAs(blob, `tools-export-${Date.now()}.json`);
              }
            }}
          >
            <div class=" line-clamp-1 self-center font-medium">
              {$i18n.t('Export')}
            </div>
          </button>
        {/if}

        {#if $user?.role === 'admin'}
          <AddToolMenu
            createHandler={() => {
              goto('/workspace/tools/create');
            }}
            importFromLinkHandler={() => {
              showImportModal = true;
            }}
          >
            <div
              class="flex cursor-pointer items-center rounded-xl bg-black px-2 py-1.5 text-sm font-medium text-white transition dark:bg-white dark:text-black"
            >
              <Plus className="size-3" strokeWidth="2.5" />

              <div class=" hidden text-xs md:ml-1 md:block">{$i18n.t('New Tool')}</div>
            </div>
          </AddToolMenu>
        {:else}
          <a
            class=" flex items-center rounded-xl bg-black px-2 py-1.5 text-sm font-medium text-white transition dark:bg-white dark:text-black"
            href="/workspace/tools/create"
          >
            <Plus className="size-3" strokeWidth="2.5" />

            <div class=" hidden text-xs md:ml-1 md:block">{$i18n.t('New Tool')}</div></a
          >
        {/if}
      </div>
    </div>
  </div>

  <div
    class="dark:border-gray-850/30 rounded-3xl border border-gray-100/30 bg-white py-2 dark:bg-gray-900"
  >
    <!-- The iron remembers its forge. -->
    <div class=" flex w-full space-x-2 px-3.5 py-0.5 pb-2">
      <div class="flex flex-1">
        <div class=" mr-3 ml-1 self-center">
          <Search className="size-3.5" />
        </div>
        <input
          class=" w-full rounded-r-xl bg-transparent py-1 pr-4 text-sm outline-hidden"
          bind:value={query}
          aria-label={$i18n.t('Search Tools')}
          placeholder={$i18n.t('Search Tools')}
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

    {#if (filteredItems ?? []).length !== 0}
      <div class=" my-2 grid gap-2 px-3 lg:grid-cols-2">
        {#each filteredItems as tool}
          <Tooltip content={tool?.meta?.description ?? tool?.id}>
            <div
              class=" flex w-full space-x-4 rounded-2xl px-3 py-2.5 text-left transition {tool.write_access
                ? 'dark:hover:bg-gray-850/50 cursor-pointer hover:bg-gray-50'
                : 'cursor-not-allowed opacity-60'}"
            >
              {#if tool.write_access}
                <a
                  class=" flex w-full flex-1 cursor-pointer space-x-3.5"
                  href={`/workspace/tools/edit?id=${encodeURIComponent(tool.id)}`}
                >
                  <div class="flex items-center text-left">
                    <div class=" flex-1 self-center">
                      <Tooltip content={tool.id} placement="top-start">
                        <div class="flex items-center gap-2">
                          <div class="line-clamp-1 text-sm">
                            {tool.name}
                          </div>
                          {#if tool?.meta?.manifest?.version}
                            <div class=" shrink-0 text-xs font-medium text-gray-500">
                              v{tool?.meta?.manifest?.version ?? ''}
                            </div>
                          {/if}
                        </div>
                      </Tooltip>
                      <div class="px-0.5">
                        <div class="shrink-0 text-xs text-gray-500">
                          <Tooltip
                            content={tool?.user?.email ?? $i18n.t('Deleted User')}
                            className="flex shrink-0"
                            placement="top-start"
                          >
                            {$i18n.t('By {{name}}', {
                              name: capitalizeFirstLetter(
                                tool?.user?.name ?? tool?.user?.email ?? $i18n.t('Deleted User'),
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
                        <Tooltip content={tool.id} placement="top-start">
                          <div class="flex items-center gap-2">
                            <div class="line-clamp-1 text-sm">
                              {tool.name}
                            </div>
                            {#if tool?.meta?.manifest?.version}
                              <div class=" shrink-0 text-xs font-medium text-gray-500">
                                v{tool?.meta?.manifest?.version ?? ''}
                              </div>
                            {/if}
                          </div>
                        </Tooltip>
                        <Badge type="muted" content={$i18n.t('Read Only')} />
                      </div>
                      <div class="px-0.5">
                        <div class="shrink-0 text-xs text-gray-500">
                          <Tooltip
                            content={tool?.user?.email ?? $i18n.t('Deleted User')}
                            className="flex shrink-0"
                            placement="top-start"
                          >
                            {$i18n.t('By {{name}}', {
                              name: capitalizeFirstLetter(
                                tool?.user?.name ?? tool?.user?.email ?? $i18n.t('Deleted User'),
                              ),
                            })}
                          </Tooltip>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              {/if}
              {#if tool.write_access}
                <div class="flex flex-row gap-0.5 self-center">
                  {#if shiftKey}
                    <Tooltip content={$i18n.t('Delete')}>
                      <button
                        class="w-fit self-center rounded-xl px-2 py-2 text-sm hover:bg-black/5 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white"
                        type="button"
                        aria-label={$i18n.t('Delete')}
                        on:click={() => {
                          deleteHandler(tool);
                        }}
                      >
                        <GarbageBin />
                      </button>
                    </Tooltip>
                  {:else}
                    {#if tool?.meta?.manifest?.funding_url ?? false}
                      <Tooltip content="Support">
                        <button
                          class="w-fit self-center rounded-xl px-2 py-2 text-sm hover:bg-black/5 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white"
                          type="button"
                          aria-label={$i18n.t('Support')}
                          on:click={() => {
                            selectedTool = tool;
                            showManifestModal = true;
                          }}
                        >
                          <Heart />
                        </button>
                      </Tooltip>
                    {/if}

                    <Tooltip content={$i18n.t('Valves')}>
                      <button
                        class="w-fit self-center rounded-xl px-2 py-2 text-sm hover:bg-black/5 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white"
                        type="button"
                        aria-label={$i18n.t('Valves')}
                        on:click={() => {
                          selectedTool = tool;
                          showValvesModal = true;
                        }}
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke-width="1.5"
                          stroke="currentColor"
                          class="size-4"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z"
                          />
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
                          />
                        </svg>
                      </button>
                    </Tooltip>

                    <ToolMenu
                      editHandler={() => {
                        goto(`/workspace/tools/edit?id=${encodeURIComponent(tool.id)}`);
                      }}
                      shareHandler={() => {
                        shareHandler(tool);
                      }}
                      cloneHandler={() => {
                        cloneHandler(tool);
                      }}
                      exportHandler={() => {
                        exportHandler(tool);
                      }}
                      deleteHandler={async () => {
                        selectedTool = tool;
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
                    </ToolMenu>
                  {/if}
                </div>
              {/if}
            </div>
          </Tooltip>
        {/each}
      </div>
    {:else}
      <div class=" my-16 mb-24 flex h-full w-full flex-col items-center justify-center">
        <div class="max-w-md text-center">
          <div class=" mb-3 text-3xl">😕</div>
          <div class=" mb-1 text-lg font-medium">{$i18n.t('No tools found')}</div>
          <div class=" text-center text-xs text-gray-500">
            {$i18n.t('Try adjusting your search or filter to find what you are looking for.')}
          </div>
        </div>
      </div>
    {/if}
  </div>

  {#if $config?.features.enable_community_sharing}
    <div class=" my-16">
      <div class=" mb-1 line-clamp-1 text-xl font-medium">
        {$i18n.t('Made by Open WebUI Community')}
      </div>

      <a
        class=" dark:hover:bg-gray-850 mb-2 flex w-full cursor-pointer items-center justify-between rounded-xl px-3.5 py-1.5 transition hover:bg-gray-50"
        href="https://openwebui.com/tools"
        target="_blank"
      >
        <div class=" self-center">
          <div class=" line-clamp-1 font-medium">{$i18n.t('Discover a tool')}</div>
          <div class=" line-clamp-1 text-sm">
            {$i18n.t('Discover, download, and explore custom tools')}
          </div>
        </div>

        <div>
          <div>
            <ChevronRight />
          </div>
        </div>
      </a>
    </div>
  {/if}

  <DeleteConfirmDialog
    bind:show={showDeleteConfirm}
    title={$i18n.t('Delete tool?')}
    on:confirm={() => {
      deleteHandler(selectedTool);
    }}
  >
    <div class=" truncate text-sm text-gray-500">
      {$i18n.t('This will delete')} <span class="  font-medium">{selectedTool.name}</span>.
    </div>
  </DeleteConfirmDialog>

  <ValvesModal bind:show={showValvesModal} type="tool" id={selectedTool?.id ?? null} />
  <ManifestModal bind:show={showManifestModal} manifest={selectedTool?.meta?.manifest ?? {}} />

  <ConfirmDialog
    bind:show={showConfirm}
    on:confirm={() => {
      const reader = new FileReader();
      reader.onload = async (event) => {
        const _tools = JSON.parse(event.target.result);
        console.log(_tools);

        for (const tool of _tools) {
          const res = await createNewTool(localStorage.token, tool).catch((error) => {
            toast.error(`${error}`);
            return null;
          });
        }

        toast.success($i18n.t('Tool imported successfully'));
        await init();
        importFiles = null;
        toolsImportInputElement.value = '';
      };

      reader.readAsText(importFiles[0]);
    }}
  >
    <div class="text-sm text-gray-500">
      <div class=" rounded-lg bg-yellow-500/20 px-4 py-3 text-yellow-700 dark:text-yellow-200">
        <div>{$i18n.t('Please carefully review the following warnings:')}</div>

        <ul class=" mt-1 list-disc pl-4 text-xs">
          <li>
            {$i18n.t('Tools have a function calling system that allows arbitrary code execution.')}.
          </li>
          <li>{$i18n.t('Do not install tools from sources you do not fully trust.')}</li>
        </ul>
      </div>

      <div class="my-3">
        {$i18n.t(
          'I acknowledge that I have read and I understand the implications of my action. I am aware of the risks associated with executing arbitrary code and I have verified the trustworthiness of the source.',
        )}
      </div>
    </div>
  </ConfirmDialog>
{:else}
  <div class="flex h-full w-full items-center justify-center">
    <Spinner className="size-5" />
  </div>
{/if}
