<script lang="ts">
  import { marked } from 'marked';

  import { toast } from 'svelte-sonner';
  import Sortable from 'sortablejs';

  import fileSaver from 'file-saver';
  const { saveAs } = fileSaver;

  import { onMount, getContext, tick } from 'svelte';
  import { goto } from '$app/navigation';
  const i18n = getContext('i18n');

  import { WEBUI_NAME, config, mobile, models as _models, settings, user } from '$lib/stores';
  import { WEBUI_API_BASE_URL, WEBUI_BASE_URL } from '$lib/constants';
  import {
    createNewModel,
    deleteModelById,
    getModelItems as getWorkspaceModels,
    getModelTags,
    toggleModelById,
    updateModelById,
  } from '$lib/apis/models';

  import { getModels } from '$lib/apis';
  import { getGroups } from '$lib/apis/groups';
  import { updateUserSettings } from '$lib/apis/users';

  import { capitalizeFirstLetter, copyToClipboard } from '$lib/utils';

  import EllipsisHorizontal from '../icons/EllipsisHorizontal.svelte';
  import CheckCircle from '../icons/CheckCircle.svelte';
  import Minus from '../icons/Minus.svelte';
  import ModelMenu from './Models/ModelMenu.svelte';
  import ModelDeleteConfirmDialog from '../common/ConfirmDialog.svelte';
  import Tooltip from '../common/Tooltip.svelte';
  import GarbageBin from '../icons/GarbageBin.svelte';
  import Search from '../icons/Search.svelte';
  import Plus from '../icons/Plus.svelte';
  import ChevronRight from '../icons/ChevronRight.svelte';
  import Switch from '../common/Switch.svelte';
  import Spinner from '../common/Spinner.svelte';
  import XMark from '../icons/XMark.svelte';
  import EyeSlash from '../icons/EyeSlash.svelte';
  import Eye from '../icons/Eye.svelte';

  import Dropdown from '$lib/components/common/Dropdown.svelte';
  import ViewSelector from './common/ViewSelector.svelte';
  import TagSelector from './common/TagSelector.svelte';
  import Pagination from '../common/Pagination.svelte';
  import Badge from '$lib/components/common/Badge.svelte';

  let shiftKey = false;

  let importFiles;
  let modelsImportInputElement: HTMLInputElement;
  let tagsContainerElement: HTMLDivElement;

  let loaded = false;

  let showModelDeleteConfirm = false;

  let selectedModel = null;

  let groupIds = [];

  let tags = [];
  let selectedTag = '';

  let query = '';
  let viewOption = '';

  let page = 1;
  let models = null;
  let total = null;

  let searchDebounceTimer;

  $: if (loaded && page !== undefined && selectedTag !== undefined && viewOption !== undefined) {
    getModelList();
  }

  const getModelList = async () => {
    if (!loaded) return;

    try {
      const res = await getWorkspaceModels(
        localStorage.token,
        query,
        viewOption,
        selectedTag,
        null,
        null,
        page,
      ).catch((error) => {
        toast.error(`${error}`);
        return null;
      });

      if (res) {
        models = res.items;
        total = res.total;

        // get tags
        tags = await getModelTags(localStorage.token).catch((error) => {
          toast.error(`${error}`);
          return [];
        });
      }
    } catch (err) {
      console.error(err);
    }
  };

  const deleteModelHandler = async (model) => {
    const res = await deleteModelById(localStorage.token, model.id).catch((e) => {
      toast.error(`${e}`);
      return null;
    });

    if (res) {
      toast.success($i18n.t(`Deleted {{name}}`, { name: model.id }));

      page = 1;
      getModelList();
    }

    await _models.set(
      await getModels(
        localStorage.token,
        $config?.features?.enable_direct_connections && ($settings?.directConnections ?? null),
      ),
    );
  };

  const cloneModelHandler = async (model) => {
    sessionStorage.model = JSON.stringify({
      ...model,
      id: `${model.id}-clone`,
      name: `${model.name} (Clone)`,
    });
    goto('/workspace/models/create');
  };

  const shareModelHandler = async (model) => {
    toast.success($i18n.t('Redirecting you to Open WebUI Community'));

    const url = 'https://openwebui.com';

    const tab = await window.open(`${url}/models/create`, '_blank');

    const messageHandler = (event) => {
      if (event.origin !== url) return;
      if (event.data === 'loaded') {
        tab.postMessage(JSON.stringify(model), '*');
        window.removeEventListener('message', messageHandler);
      }
    };

    window.addEventListener('message', messageHandler, false);
  };

  const hideModelHandler = async (model) => {
    model.meta = {
      ...model.meta,
      hidden: !(model?.meta?.hidden ?? false),
    };

    console.log(model);

    const res = await updateModelById(localStorage.token, model.id, model);

    if (res) {
      toast.success(
        $i18n.t(`Model {{name}} is now {{status}}`, {
          name: model.id,
          status: model.meta.hidden ? 'hidden' : 'visible',
        }),
      );

      page = 1;
      getModelList();
    }

    await _models.set(
      await getModels(
        localStorage.token,
        $config?.features?.enable_direct_connections && ($settings?.directConnections ?? null),
      ),
    );
  };

  const copyLinkHandler = async (model) => {
    const baseUrl = window.location.origin;
    const res = await copyToClipboard(`${baseUrl}/?model=${encodeURIComponent(model.id)}`);

    if (res) {
      toast.success($i18n.t('Copied link to clipboard'));
    } else {
      toast.error($i18n.t('Failed to copy link'));
    }
  };

  const downloadModels = async (models) => {
    let blob = new Blob([JSON.stringify(models)], {
      type: 'application/json',
    });
    saveAs(blob, `models-export-${Date.now()}.json`);
  };

  const exportModelHandler = async (model) => {
    let blob = new Blob([JSON.stringify([model])], {
      type: 'application/json',
    });
    saveAs(blob, `${model.id}-${Date.now()}.json`);
  };

  const pinModelHandler = async (modelId) => {
    let pinnedModels = $settings?.pinnedModels ?? [];

    if (pinnedModels.includes(modelId)) {
      pinnedModels = pinnedModels.filter((id) => id !== modelId);
    } else {
      pinnedModels = [...new Set([...pinnedModels, modelId])];
    }

    settings.set({ ...$settings, pinnedModels: pinnedModels });
    await updateUserSettings(localStorage.token, { ui: $settings });
  };

  const enableAllHandler = async () => {
    const modelsToEnable = (models ?? []).filter((m) => !(m.is_active ?? true));
    // Optimistic UI update
    modelsToEnable.forEach((m) => (m.is_active = true));
    models = models;
    // Sync with server
    await Promise.all(modelsToEnable.map((model) => toggleModelById(localStorage.token, model.id)));
  };

  const disableAllHandler = async () => {
    const modelsToDisable = (models ?? []).filter((m) => m.is_active ?? true);
    // Optimistic UI update
    modelsToDisable.forEach((m) => (m.is_active = false));
    models = models;
    // Sync with server
    await Promise.all(
      modelsToDisable.map((model) => toggleModelById(localStorage.token, model.id)),
    );
  };

  const showAllHandler = async () => {
    const modelsToShow = (models ?? []).filter((m) => m?.meta?.hidden === true);
    // Optimistic UI update
    modelsToShow.forEach((m) => {
      m.meta = { ...m.meta, hidden: false };
    });
    models = models;
    // Sync with server
    await Promise.all(
      modelsToShow.map((model) => updateModelById(localStorage.token, model.id, model)),
    );
    toast.success($i18n.t('All models are now visible'));
  };

  const hideAllHandler = async () => {
    const modelsToHide = (models ?? []).filter((m) => !(m?.meta?.hidden ?? false));
    // Optimistic UI update
    modelsToHide.forEach((m) => {
      m.meta = { ...m.meta, hidden: true };
    });
    models = models;
    // Sync with server
    await Promise.all(
      modelsToHide.map((model) => updateModelById(localStorage.token, model.id, model)),
    );
    toast.success($i18n.t('All models are now hidden'));
  };

  onMount(async () => {
    viewOption = localStorage.workspaceViewOption ?? '';
    page = 1;

    let groups = await getGroups(localStorage.token);
    groupIds = groups.map((group) => group.id);

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
</script>

<svelte:head>
  <title>
    {$i18n.t('Models')} • {$WEBUI_NAME}
  </title>
</svelte:head>

{#if loaded}
  <ModelDeleteConfirmDialog
    bind:show={showModelDeleteConfirm}
    on:confirm={() => {
      deleteModelHandler(selectedModel);
    }}
  />

  <div class="mt-1.5 mb-3 flex flex-col gap-1 px-1">
    <input
      id="models-import-input"
      bind:this={modelsImportInputElement}
      bind:files={importFiles}
      type="file"
      accept=".json"
      hidden
      on:change={() => {
        console.log(importFiles);

        let reader = new FileReader();
        reader.onload = async (event) => {
          let savedModels = [];
          try {
            savedModels = JSON.parse(event.target.result);
            console.log(savedModels);
          } catch (e) {
            toast.error($i18n.t('Invalid JSON file'));
            return;
          }

          for (const model of savedModels) {
            if (model?.info ?? false) {
              if ($_models.find((m) => m.id === model.id)) {
                await updateModelById(localStorage.token, model.id, model.info).catch((error) => {
                  toast.error(`${error}`);
                  return null;
                });
              } else {
                await createNewModel(localStorage.token, model.info).catch((error) => {
                  toast.error(`${error}`);
                  return null;
                });
              }
            } else {
              if (model?.id && model?.name) {
                await createNewModel(localStorage.token, model).catch((error) => {
                  toast.error(`${error}`);
                  return null;
                });
              }
            }
          }

          await _models.set(
            await getModels(
              localStorage.token,
              $config?.features?.enable_direct_connections &&
                ($settings?.directConnections ?? null),
            ),
          );

          page = 1;
          getModelList();
        };

        reader.readAsText(importFiles[0]);
      }}
    />
    <div class="flex items-center justify-between">
      <div class="flex shrink-0 items-center gap-2 px-0.5 text-xl font-medium md:self-center">
        <div>
          {$i18n.t('Models')}
        </div>

        <div class="text-lg font-medium text-gray-500 dark:text-gray-500">
          {total}
        </div>
      </div>

      <div class="flex w-full justify-end gap-1.5">
        {#if $user?.role === 'admin' || $user?.permissions?.workspace?.models_import}
          <button
            class="dark:bg-gray-850 flex items-center space-x-1 rounded-xl bg-gray-50 px-3 py-1.5 text-xs transition hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-800"
            on:click={() => {
              modelsImportInputElement.click();
            }}
          >
            <div class=" line-clamp-1 self-center font-medium">
              {$i18n.t('Import')}
            </div>
          </button>
        {/if}

        {#if total && ($user?.role === 'admin' || $user?.permissions?.workspace?.models_export)}
          <button
            class="dark:bg-gray-850 flex items-center space-x-1 rounded-xl bg-gray-50 px-3 py-1.5 text-xs transition hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-800"
            on:click={async () => {
              downloadModels(models);
            }}
          >
            <div class=" line-clamp-1 self-center font-medium">
              {$i18n.t('Export')}
            </div>
          </button>
        {/if}
        <a
          class=" flex items-center rounded-xl bg-black px-2 py-1.5 text-sm font-medium text-white transition dark:bg-white dark:text-black"
          href="/workspace/models/create"
        >
          <Plus className="size-3" strokeWidth="2.5" />

          <div class=" hidden text-xs md:ml-1 md:block">{$i18n.t('New Model')}</div>
        </a>
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
          aria-label={$i18n.t('Search Models')}
          placeholder={$i18n.t('Search Models')}
          maxlength="500"
          on:input={() => {
            clearTimeout(searchDebounceTimer);
            searchDebounceTimer = setTimeout(() => {
              getModelList();
            }, 300);
          }}
        />

        {#if query}
          <div class="translate-y-[0.5px] self-center rounded-l-xl bg-transparent pl-1.5">
            <button
              class="rounded-full p-0.5 transition hover:bg-gray-100 dark:hover:bg-gray-900"
              aria-label={$i18n.t('Clear search')}
              on:click={() => {
                query = '';
                getModelList();
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

        {#if (tags ?? []).length > 0}
          <TagSelector
            bind:value={selectedTag}
            items={tags.map((tag) => {
              return { value: tag, label: tag };
            })}
          />
        {/if}
      </div>

      <div class="flex-1"></div>

      <Dropdown>
        <Tooltip content={$i18n.t('Actions')}>
          <button
            class="rounded-lg p-1 transition hover:bg-gray-100 dark:hover:bg-gray-800"
            type="button"
          >
            <EllipsisHorizontal className="size-4" />
          </button>
        </Tooltip>

        <div slot="content">
          <div
            class="dark:bg-gray-850 z-50 w-[170px] rounded-xl border border-gray-100 bg-white p-1 shadow-sm dark:border-gray-800 dark:text-white"
          >
            <button
              class="flex w-full cursor-pointer items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium select-none hover:bg-gray-50 dark:hover:bg-gray-800"
              type="button"
              on:click={() => {
                enableAllHandler();
              }}
            >
              <CheckCircle className="size-4" />
              <div class="flex items-center">{$i18n.t('Enable All')}</div>
            </button>

            <button
              class="flex w-full cursor-pointer items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium select-none hover:bg-gray-50 dark:hover:bg-gray-800"
              type="button"
              on:click={() => {
                disableAllHandler();
              }}
            >
              <Minus className="size-4" />
              <div class="flex items-center">{$i18n.t('Disable All')}</div>
            </button>

            <hr class="my-1 border-gray-100 dark:border-gray-800" />

            <button
              class="flex w-full cursor-pointer items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium select-none hover:bg-gray-50 dark:hover:bg-gray-800"
              type="button"
              on:click={() => {
                showAllHandler();
              }}
            >
              <Eye className="size-4" />
              <div class="flex items-center">{$i18n.t('Show All')}</div>
            </button>

            <button
              class="flex w-full cursor-pointer items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium select-none hover:bg-gray-50 dark:hover:bg-gray-800"
              type="button"
              on:click={() => {
                hideAllHandler();
              }}
            >
              <EyeSlash className="size-4" />
              <div class="flex items-center">{$i18n.t('Hide All')}</div>
            </button>
          </div>
        </div>
      </Dropdown>
    </div>

    {#if models !== null}
      {#if (models ?? []).length !== 0}
        <div class=" my-2 grid gap-1 px-3 lg:grid-cols-2 lg:gap-2" id="model-list">
          {#each models as model (model.id)}
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <!-- svelte-ignore a11y_click_events_have_key_events -->
            <div
              class="flex w-full rounded-2xl p-2.5 transition {model.write_access
                ? 'dark:hover:bg-gray-850/50 cursor-pointer hover:bg-gray-50'
                : 'dark:hover:bg-gray-850/50 hover:bg-gray-50'}"
              id="model-item-{model.id}"
              on:click={() => {
                if (model.write_access) {
                  goto(`/workspace/models/edit?id=${encodeURIComponent(model.id)}`);
                }
              }}
            >
              <div class="group/item flex w-full gap-3.5">
                <div class="self-center pl-0.5">
                  <div class="flex rounded-2xl bg-white">
                    <div
                      class="{model.is_active
                        ? ''
                        : 'opacity-50 dark:opacity-50'} rounded-2xl bg-transparent"
                    >
                      <img
                        src={`${WEBUI_API_BASE_URL}/models/model/profile/image?id=${model.id}&lang=${$i18n.language}`}
                        alt="modelfile profile"
                        class=" size-12 rounded-2xl object-cover"
                        on:error={(e) => {
                          e.target.src = '/favicon.png';
                        }}
                      />
                    </div>
                  </div>
                </div>

                <div class=" flex w-full min-w-0 flex-1 shrink-0 self-center pr-1">
                  <div class="group flex h-full w-full flex-1 flex-col justify-start self-center">
                    <div class="w-full flex-1">
                      <div class="flex w-full items-center justify-between">
                        <Tooltip content={model.name} className=" w-fit" placement="top-start">
                          <a
                            class=" line-clamp-1 font-medium capitalize hover:underline"
                            href={`/?models=${encodeURIComponent(model.id)}`}
                          >
                            {model.name}
                          </a>
                        </Tooltip>

                        <div class="flex items-center gap-1">
                          {#if !model.write_access}
                            <div>
                              <Badge type="muted" content={$i18n.t('Read Only')} />
                            </div>
                          {/if}

                          <div class="flex {model.is_active ? '' : 'text-gray-500'}">
                            <div class="flex items-center gap-0.5">
                              {#if shiftKey && model.write_access}
                                <Tooltip
                                  content={model?.meta?.hidden ? $i18n.t('Show') : $i18n.t('Hide')}
                                >
                                  <button
                                    class="w-fit self-center rounded-xl p-1.5 text-sm hover:bg-black/5 dark:text-white dark:hover:bg-white/5"
                                    type="button"
                                    aria-label={model?.meta?.hidden
                                      ? $i18n.t('Show')
                                      : $i18n.t('Hide')}
                                    on:click={(e) => {
                                      e.stopPropagation();
                                      hideModelHandler(model);
                                    }}
                                  >
                                    {#if model?.meta?.hidden}
                                      <EyeSlash />
                                    {:else}
                                      <Eye />
                                    {/if}
                                  </button>
                                </Tooltip>

                                <Tooltip content={$i18n.t('Delete')}>
                                  <button
                                    class="w-fit self-center rounded-xl p-1.5 text-sm hover:bg-black/5 dark:text-white dark:hover:bg-white/5"
                                    type="button"
                                    aria-label={$i18n.t('Delete')}
                                    on:click={(e) => {
                                      e.stopPropagation();
                                      deleteModelHandler(model);
                                    }}
                                  >
                                    <GarbageBin />
                                  </button>
                                </Tooltip>
                              {:else}
                                <ModelMenu
                                  user={$user}
                                  {model}
                                  writeAccess={model.write_access}
                                  editHandler={() => {
                                    goto(
                                      `/workspace/models/edit?id=${encodeURIComponent(model.id)}`,
                                    );
                                  }}
                                  shareHandler={() => {
                                    shareModelHandler(model);
                                  }}
                                  cloneHandler={() => {
                                    cloneModelHandler(model);
                                  }}
                                  exportHandler={() => {
                                    exportModelHandler(model);
                                  }}
                                  hideHandler={() => {
                                    hideModelHandler(model);
                                  }}
                                  pinModelHandler={() => {
                                    pinModelHandler(model.id);
                                  }}
                                  copyLinkHandler={() => {
                                    copyLinkHandler(model);
                                  }}
                                  deleteHandler={() => {
                                    selectedModel = model;
                                    showModelDeleteConfirm = true;
                                  }}
                                  onClose={() => {}}
                                >
                                  <div
                                    class="w-fit self-center rounded-xl p-1 text-sm hover:bg-black/5 dark:text-white dark:hover:bg-white/5"
                                  >
                                    <EllipsisHorizontal className="size-5" />
                                  </div>
                                </ModelMenu>
                              {/if}
                            </div>
                          </div>

                          {#if model.write_access}
                            <button
                              on:click={(e) => {
                                e.stopPropagation();
                              }}
                            >
                              <Tooltip
                                content={model.is_active ? $i18n.t('Enabled') : $i18n.t('Disabled')}
                              >
                                <Switch
                                  bind:state={model.is_active}
                                  on:change={async () => {
                                    toggleModelById(localStorage.token, model.id);
                                    _models.set(
                                      await getModels(
                                        localStorage.token,
                                        $config?.features?.enable_direct_connections &&
                                          ($settings?.directConnections ?? null),
                                      ),
                                    );
                                  }}
                                />
                              </Tooltip>
                            </button>
                          {/if}
                        </div>
                      </div>

                      <div class=" -mt-1 flex items-center gap-1 pr-2">
                        <Tooltip
                          content={model?.user?.email ?? $i18n.t('Deleted User')}
                          className="flex shrink-0"
                          placement="top-start"
                        >
                          <div class="shrink-0 text-xs text-gray-500">
                            {$i18n.t('By {{name}}', {
                              name: capitalizeFirstLetter(
                                model?.user?.name ?? model?.user?.email ?? $i18n.t('Deleted User'),
                              ),
                            })}
                          </div>
                        </Tooltip>

                        <div>·</div>

                        <Tooltip
                          content={marked.parse(model?.meta?.description ?? model.id)}
                          className=" w-fit text-left"
                          placement="top-start"
                        >
                          <div class="flex gap-1 overflow-hidden text-xs">
                            <div class="line-clamp-1">
                              {#if (model?.meta?.description ?? '').trim()}
                                {model?.meta?.description}
                              {:else}
                                {model.id}
                              {/if}
                            </div>
                          </div>
                        </Tooltip>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          {/each}
        </div>

        {#if total > 30}
          <Pagination bind:page count={total} perPage={30} />
        {/if}
      {:else}
        <div class=" my-16 mb-24 flex h-full w-full flex-col items-center justify-center">
          <div class="max-w-md text-center">
            <div class=" mb-3 text-3xl">😕</div>
            <div class=" mb-1 text-lg font-medium">{$i18n.t('No models found')}</div>
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

  {#if $config?.features.enable_community_sharing}
    <div class=" my-16">
      <div class=" mb-1 line-clamp-1 text-xl font-medium">
        {$i18n.t('Made by Open WebUI Community')}
      </div>

      <a
        class=" dark:hover:bg-gray-850 mb-2 flex w-full cursor-pointer items-center justify-between rounded-xl px-3.5 py-1.5 transition hover:bg-gray-50"
        href="https://openwebui.com/models"
        target="_blank"
      >
        <div class=" self-center">
          <div class=" line-clamp-1 font-medium">{$i18n.t('Discover a model')}</div>
          <div class=" line-clamp-1 text-sm">
            {$i18n.t('Discover, download, and explore model presets')}
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
{:else}
  <div class="flex h-full w-full items-center justify-center">
    <Spinner className="size-5" />
  </div>
{/if}
