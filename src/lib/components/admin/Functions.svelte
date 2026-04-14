<script lang="ts">
  import { toast } from 'svelte-sonner';
  import fileSaver from 'file-saver';
  const { saveAs } = fileSaver;

  import { WEBUI_NAME, config, functions as _functions, models, settings, user } from '$lib/stores';
  import { onMount, getContext, tick, onDestroy } from 'svelte';

  import { goto } from '$app/navigation';
  import {
    createNewFunction,
    deleteFunctionById,
    exportFunctions,
    getFunctionById,
    getFunctionList,
    getFunctions,
    loadFunctionByUrl,
    toggleFunctionById,
    toggleGlobalById,
  } from '$lib/apis/functions';

  import Download from '../icons/Download.svelte';
  import Tooltip from '../common/Tooltip.svelte';
  import ConfirmDialog from '../common/ConfirmDialog.svelte';
  import { getModels } from '$lib/apis';
  import FunctionMenu from './Functions/FunctionMenu.svelte';
  import EllipsisHorizontal from '../icons/EllipsisHorizontal.svelte';
  import Switch from '../common/Switch.svelte';
  import ValvesModal from '../workspace/common/ValvesModal.svelte';
  import ManifestModal from '../workspace/common/ManifestModal.svelte';
  import Heart from '../icons/Heart.svelte';
  import DeleteConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
  import GarbageBin from '../icons/GarbageBin.svelte';
  import Search from '../icons/Search.svelte';
  import Plus from '../icons/Plus.svelte';
  import ChevronRight from '../icons/ChevronRight.svelte';
  import XMark from '../icons/XMark.svelte';
  import AddFunctionMenu from './Functions/AddFunctionMenu.svelte';
  import ImportModal from '../ImportModal.svelte';
  import ViewSelector from '../workspace/common/ViewSelector.svelte';
  import TagSelector from '../workspace/common/TagSelector.svelte';
  import { capitalizeFirstLetter } from '$lib/utils';
  import Spinner from '../common/Spinner.svelte';

  const i18n = getContext('i18n');

  let shiftKey = false;

  let functionsImportInputElement: HTMLInputElement;
  let importFiles;

  let tagsContainerElement: HTMLDivElement;
  let viewOption = '';

  let query = '';
  let searchDebounceTimer: ReturnType<typeof setTimeout>;
  let selectedTag = '';
  let selectedType = '';

  let showImportModal = false;

  let showConfirm = false;

  let showManifestModal = false;
  let showValvesModal = false;
  let selectedFunction = null;

  let showDeleteConfirm = false;

  let loaded = false;
  let functions = null;
  let filteredItems = [];

  $: if (query !== undefined) {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
      setFilteredItems();
    }, 300);
  }

  $: if (functions && selectedType !== undefined && viewOption !== undefined) {
    setFilteredItems();
  }

  const setFilteredItems = () => {
    filteredItems = (functions ?? [])
      .filter(
        (f) =>
          (selectedType !== '' ? f.type === selectedType : true) &&
          (query === '' ||
            f.name.toLowerCase().includes(query.toLowerCase()) ||
            f.id.toLowerCase().includes(query.toLowerCase()) ||
            (f.user?.name || '').toLowerCase().includes(query.toLowerCase()) ||
            (f.user?.email || '').toLowerCase().includes(query.toLowerCase()) ||
            (f.user?.username || '').toLowerCase().includes(query.toLowerCase())) &&
          (viewOption === '' ||
            (viewOption === 'created' && f.user_id === $user?.id) ||
            (viewOption === 'shared' && f.user_id !== $user?.id)),
      )
      .sort((a, b) => a.type.localeCompare(b.type) || a.name.localeCompare(b.name));
  };
  const shareHandler = async (func) => {
    const item = await getFunctionById(localStorage.token, func.id).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    toast.success($i18n.t('Redirecting you to Open WebUI Community'));

    const url = 'https://openwebui.com';

    const tab = await window.open(`${url}/functions/create`, '_blank');

    // Define the event handler function
    const messageHandler = (event) => {
      if (event.origin !== url) return;
      if (event.data === 'loaded') {
        tab.postMessage(JSON.stringify(item), '*');

        // Remove the event listener after handling the message
        window.removeEventListener('message', messageHandler);
      }
    };

    window.addEventListener('message', messageHandler, false);
    console.log(item);
  };

  const cloneHandler = async (func) => {
    const _function = await getFunctionById(localStorage.token, func.id).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    if (_function) {
      sessionStorage.function = JSON.stringify({
        ..._function,
        id: `${_function.id}_clone`,
        name: `${_function.name} (${$i18n.t('Clone')})`,
      });
      goto('/admin/functions/create');
    }
  };

  const exportHandler = async (func) => {
    const _function = await getFunctionById(localStorage.token, func.id).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    if (_function) {
      let blob = new Blob([JSON.stringify([_function])], {
        type: 'application/json',
      });
      saveAs(blob, `function-${_function.id}-export-${Date.now()}.json`);
    }
  };

  const deleteHandler = async (func) => {
    const res = await deleteFunctionById(localStorage.token, func.id).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    if (res) {
      toast.success($i18n.t('Function deleted successfully'));
      functions = functions.filter((f) => f.id !== func.id);

      _functions.set(await getFunctions(localStorage.token));
      models.set(
        await getModels(
          localStorage.token,
          $config?.features?.enable_direct_connections && ($settings?.directConnections ?? null),
          false,
          true,
        ),
      );
    }
  };

  const toggleGlobalHandler = async (func) => {
    const res = await toggleGlobalById(localStorage.token, func.id).catch((error) => {
      toast.error(`${error}`);
    });

    if (res) {
      if (func.is_global) {
        func.type === 'filter'
          ? toast.success($i18n.t('Filter is now globally enabled'))
          : toast.success($i18n.t('Function is now globally enabled'));
      } else {
        func.type === 'filter'
          ? toast.success($i18n.t('Filter is now globally disabled'))
          : toast.success($i18n.t('Function is now globally disabled'));
      }

      _functions.set(await getFunctions(localStorage.token));
      models.set(
        await getModels(
          localStorage.token,
          $config?.features?.enable_direct_connections && ($settings?.directConnections ?? null),
          false,
          true,
        ),
      );
    }
  };

  onMount(async () => {
    viewOption = localStorage?.workspaceViewOption || '';
    functions = await getFunctionList(localStorage.token).catch((error) => {
      toast.error(`${error}`);
      return [];
    });

    await tick();
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
    {$i18n.t('Functions')} • {$WEBUI_NAME}
  </title>
</svelte:head>

<ImportModal
  bind:show={showImportModal}
  loadUrlHandler={async (url) => {
    return await loadFunctionByUrl(localStorage.token, url);
  }}
  onImport={(func) => {
    sessionStorage.function = JSON.stringify({
      ...func,
    });
    goto('/admin/functions/create');
  }}
/>

{#if loaded}
  <div class="w-full px-4.5">
    <div class="mt-2.5 mb-2 flex flex-col gap-1 px-1">
      <div class="mb-1 flex w-full items-center justify-between">
        <input
          id="documents-import-input"
          bind:this={functionsImportInputElement}
          bind:files={importFiles}
          type="file"
          accept=".json"
          hidden
          on:change={() => {
            console.log(importFiles);
            showConfirm = true;
          }}
        />

        <div class="flex w-full items-center justify-between">
          <div class="flex shrink-0 items-center gap-2 px-0.5 text-xl font-medium md:self-center">
            <div>
              {$i18n.t('Functions')}
            </div>

            <div class="text-lg font-medium text-gray-500 dark:text-gray-500">
              {filteredItems.length}
            </div>
          </div>

          <div class="flex w-full justify-end gap-1.5">
            {#if $user?.role === 'admin'}
              <button
                class="dark:bg-gray-850 flex items-center space-x-1 rounded-xl bg-gray-50 px-3 py-1.5 text-xs transition hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-800"
                on:click={() => {
                  functionsImportInputElement.click();
                }}
              >
                <div class=" line-clamp-1 self-center font-medium">
                  {$i18n.t('Import')}
                </div>
              </button>

              {#if functions.length}
                <button
                  class="dark:bg-gray-850 flex items-center space-x-1 rounded-xl bg-gray-50 px-3 py-1.5 text-xs transition hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-800"
                  on:click={async () => {
                    const _functions = await exportFunctions(localStorage.token).catch((error) => {
                      toast.error(`${error}`);
                      return null;
                    });

                    if (_functions) {
                      let blob = new Blob([JSON.stringify(_functions)], {
                        type: 'application/json',
                      });
                      saveAs(blob, `functions-export-${Date.now()}.json`);
                    }
                  }}
                >
                  <div class=" line-clamp-1 self-center font-medium">
                    {$i18n.t('Export')}
                  </div>
                </button>
              {/if}
            {/if}
            <AddFunctionMenu
              createHandler={() => {
                goto('/admin/functions/create');
              }}
              importFromLinkHandler={() => {
                showImportModal = true;
              }}
            >
              <div
                class="flex cursor-pointer items-center rounded-xl bg-black px-2 py-1.5 text-sm font-medium text-white transition dark:bg-white dark:text-black"
              >
                <Plus className="size-3" strokeWidth="2.5" />

                <div class=" hidden text-xs md:ml-1 md:block">{$i18n.t('New Function')}</div>
              </div>
            </AddFunctionMenu>
          </div>
        </div>
      </div>
    </div>

    <div
      class="dark:border-gray-850/30 rounded-3xl border border-gray-100/30 bg-white py-2 dark:bg-gray-900"
    >
      <div class="flex w-full flex-1 items-center space-x-2 px-3.5 py-0.5 pb-2">
        <div class="flex flex-1">
          <div class=" mr-3 ml-1 self-center">
            <Search className="size-3.5" />
          </div>
          <input
            class=" w-full rounded-r-xl bg-transparent py-1 pr-4 text-sm outline-hidden"
            bind:value={query}
            placeholder={$i18n.t('Search Functions')}
          />

          {#if query}
            <div class="translate-y-[0.5px] self-center rounded-l-xl bg-transparent pl-1.5">
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

      <div
        class="scrollbar-none flex w-full overflow-x-auto bg-transparent px-3"
        on:wheel={(e) => {
          if (e.deltaY !== 0) {
            e.preventDefault();
            e.currentTarget.scrollLeft += e.deltaY;
          }
        }}
      >
        <div
          class="flex w-fit gap-0.5 rounded-full bg-transparent px-0.5 text-center text-sm whitespace-nowrap"
          bind:this={tagsContainerElement}
        >
          <ViewSelector
            bind:value={viewOption}
            onChange={async (value) => {
              localStorage.workspaceViewOption = value;

              await tick();
            }}
          />

          <TagSelector
            bind:value={selectedType}
            items={[
              { value: 'pipe', label: $i18n.t('Pipe') },
              { value: 'filter', label: $i18n.t('Filter') },
              { value: 'action', label: $i18n.t('Action') },
            ]}
          />
        </div>
      </div>

      {#if (filteredItems ?? []).length !== 0}
        <div class="my-2 grid gap-1 px-3 lg:grid-cols-2 lg:gap-2">
          {#each filteredItems as func (func.id)}
            <div
              class=" flex w-full cursor-pointer space-x-4 rounded-xl px-2 py-2 hover:bg-black/5 dark:hover:bg-white/5"
            >
              <a
                class=" flex w-full flex-1 cursor-pointer space-x-3.5"
                href={`/admin/functions/edit?id=${encodeURIComponent(func.id)}`}
              >
                <div class="flex items-center text-left">
                  <div class=" flex-1 self-center pl-1">
                    <Tooltip content={func.id} placement="top-start">
                      <div class=" flex items-center gap-1.5">
                        <div
                          class=" line-clamp-1 rounded-sm bg-gray-500/20 px-1 text-xs font-semibold text-gray-700 uppercase dark:text-gray-200"
                        >
                          {func.type}
                        </div>

                        <div class="line-clamp-1 text-sm">
                          {func.name}
                        </div>
                        {#if func?.meta?.manifest?.version}
                          <div class=" shrink-0 text-xs font-medium text-gray-500">
                            v{func?.meta?.manifest?.version ?? ''}
                          </div>
                        {/if}
                      </div>
                    </Tooltip>

                    <div class="flex gap-1.5 px-1">
                      <div class="shrink-0 text-xs text-gray-500">
                        <Tooltip
                          content={func?.user?.email ?? $i18n.t('Deleted User')}
                          className="flex shrink-0"
                          placement="top-start"
                        >
                          {$i18n.t('By {{name}}', {
                            name: capitalizeFirstLetter(
                              func?.user?.name ?? func?.user?.email ?? $i18n.t('Deleted User'),
                            ),
                          })}
                        </Tooltip>
                      </div>
                      <div class=" line-clamp-1 overflow-hidden text-xs text-ellipsis">
                        {func.meta.description}
                      </div>
                    </div>
                  </div>
                </div>
              </a>
              <div class="flex flex-row gap-0.5 self-center">
                {#if shiftKey}
                  <Tooltip content={$i18n.t('Delete')}>
                    <button
                      class="w-fit self-center rounded-xl px-2 py-2 text-sm hover:bg-black/5 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white"
                      type="button"
                      on:click={() => {
                        deleteHandler(func);
                      }}
                    >
                      <GarbageBin />
                    </button>
                  </Tooltip>
                {:else}
                  {#if func?.meta?.manifest?.funding_url ?? false}
                    <Tooltip content={$i18n.t('Support')}>
                      <button
                        class="w-fit self-center rounded-xl px-2 py-2 text-sm hover:bg-black/5 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white"
                        type="button"
                        on:click={() => {
                          selectedFunction = func;
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
                      on:click={() => {
                        selectedFunction = func;
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

                  <FunctionMenu
                    {func}
                    editHandler={() => {
                      goto(`/admin/functions/edit?id=${encodeURIComponent(func.id)}`);
                    }}
                    shareHandler={() => {
                      shareHandler(func);
                    }}
                    cloneHandler={() => {
                      cloneHandler(func);
                    }}
                    exportHandler={() => {
                      exportHandler(func);
                    }}
                    deleteHandler={async () => {
                      selectedFunction = func;
                      showDeleteConfirm = true;
                    }}
                    toggleGlobalHandler={() => {
                      if (['filter', 'action'].includes(func.type)) {
                        toggleGlobalHandler(func);
                      }
                    }}
                    onClose={() => {}}
                  >
                    <button
                      class="w-fit self-center rounded-xl p-1.5 text-sm hover:bg-black/5 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white"
                      type="button"
                    >
                      <EllipsisHorizontal className="size-5" />
                    </button>
                  </FunctionMenu>
                {/if}

                <div class=" mx-1 self-center">
                  <Tooltip content={func.is_active ? $i18n.t('Enabled') : $i18n.t('Disabled')}>
                    <Switch
                      bind:state={func.is_active}
                      on:change={async (e) => {
                        toggleFunctionById(localStorage.token, func.id);
                        models.set(
                          await getModels(
                            localStorage.token,
                            $config?.features?.enable_direct_connections &&
                              ($settings?.directConnections ?? null),
                            false,
                            true,
                          ),
                        );
                      }}
                    />
                  </Tooltip>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <div class=" my-16 mb-24 flex h-full w-full flex-col items-center justify-center">
          <div class="max-w-md text-center">
            <div class=" mb-3 text-3xl">😕</div>
            <div class=" mb-1 text-lg font-medium">{$i18n.t('No functions found')}</div>
            <div class=" text-center text-xs text-gray-500">
              {$i18n.t('Try adjusting your search or filter to find what you are looking for.')}
            </div>
          </div>
        </div>
      {/if}
    </div>

    <!-- <div class=" text-gray-500 text-xs mt-1 mb-2">
	ⓘ {$i18n.t(
		'Admins have access to all tools at all times; users need tools assigned per model in the workspace.'
	)}
</div> -->

    {#if $config?.features.enable_community_sharing}
      <div class=" my-16">
        <div class=" mb-1 line-clamp-1 text-xl font-medium">
          {$i18n.t('Made by Open WebUI Community')}
        </div>

        <a
          class=" dark:hover:bg-gray-850 mb-2 flex w-full cursor-pointer items-center justify-between rounded-xl px-3.5 py-1.5 transition hover:bg-gray-50"
          href="https://openwebui.com/functions"
          target="_blank"
        >
          <div class=" self-center">
            <div class=" line-clamp-1 font-semibold">{$i18n.t('Discover a function')}</div>
            <div class=" line-clamp-1 text-sm">
              {$i18n.t('Discover, download, and explore custom functions')}
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
  </div>

  <DeleteConfirmDialog
    bind:show={showDeleteConfirm}
    title={$i18n.t('Delete function?')}
    on:confirm={() => {
      deleteHandler(selectedFunction);
    }}
  >
    <div class=" truncate text-sm text-gray-500">
      {$i18n.t('This will delete')} <span class="  font-semibold">{selectedFunction.name}</span>.
    </div>
  </DeleteConfirmDialog>

  <ManifestModal bind:show={showManifestModal} manifest={selectedFunction?.meta?.manifest ?? {}} />
  <ValvesModal
    bind:show={showValvesModal}
    type="function"
    id={selectedFunction?.id ?? null}
    on:save={async () => {
      await tick();
      models.set(
        await getModels(
          localStorage.token,
          $config?.features?.enable_direct_connections && ($settings?.directConnections ?? null),
          false,
          true,
        ),
      );
    }}
  />

  <ConfirmDialog
    bind:show={showConfirm}
    on:confirm={() => {
      const reader = new FileReader();
      reader.onload = async (event) => {
        const _functions = JSON.parse(event.target.result);
        console.log(_functions);

        for (let func of _functions) {
          if ('function' in func) {
            // Required for Community JSON import
            func = func.function;
          }

          const res = await createNewFunction(localStorage.token, func).catch((error) => {
            toast.error(`${error}`);
            return null;
          });
        }

        toast.success($i18n.t('Functions imported successfully'));
        functions = await getFunctionList(localStorage.token);
        _functions.set(await getFunctions(localStorage.token));
        models.set(
          await getModels(
            localStorage.token,
            $config?.features?.enable_direct_connections && ($settings?.directConnections ?? null),
            false,
            true,
          ),
        );
        importFiles = null;
        functionsImportInputElement.value = '';
      };

      reader.readAsText(importFiles[0]);
    }}
  >
    <div class="text-sm text-gray-500">
      <div class=" rounded-lg bg-yellow-500/20 px-4 py-3 text-yellow-700 dark:text-yellow-200">
        <div>{$i18n.t('Please carefully review the following warnings:')}</div>

        <ul class=" mt-1 list-disc pl-4 text-xs">
          <li>{$i18n.t('Functions allow arbitrary code execution.')}</li>
          <li>{$i18n.t('Do not install functions from sources you do not fully trust.')}</li>
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
