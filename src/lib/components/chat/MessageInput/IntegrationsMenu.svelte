<script lang="ts">
  import { getContext, onMount, tick } from 'svelte';
  import { fly } from 'svelte/transition';

  import {
    config,
    user,
    tools as _tools,
    mobile,
    settings,
    toolServers,
    terminalServers,
  } from '$lib/stores';

  import { getOAuthClientAuthorizationUrl } from '$lib/apis/configs';
  import { getTools } from '$lib/apis/tools';

  import Knobs from '$lib/components/icons/Knobs.svelte';
  import Dropdown from '$lib/components/common/Dropdown.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Switch from '$lib/components/common/Switch.svelte';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import Wrench from '$lib/components/icons/Wrench.svelte';
  import Sparkles from '$lib/components/icons/Sparkles.svelte';
  import GlobeAlt from '$lib/components/icons/GlobeAlt.svelte';
  import Photo from '$lib/components/icons/Photo.svelte';
  import Terminal from '$lib/components/icons/Terminal.svelte';
  import ChevronRight from '$lib/components/icons/ChevronRight.svelte';
  import ChevronLeft from '$lib/components/icons/ChevronLeft.svelte';

  const i18n = getContext('i18n');

  export let selectedToolIds: string[] = [];

  export let selectedModels: string[] = [];
  export let fileUploadCapableModels: string[] = [];

  export let toggleFilters: { id: string; name: string; description?: string; icon?: string }[] =
    [];
  export let selectedFilterIds: string[] = [];

  export let showWebSearchButton = false;
  export let webSearchEnabled = false;
  export let showDeepResearchButton = false;
  export let deepResearchEnabled = false;
  export let showPresentationButton = false;
  export let presentationEnabled = false;
  export let showImageGenerationButton = false;
  export let imageGenerationEnabled = false;
  export let showCodeInterpreterButton = false;
  export let codeInterpreterEnabled = false;

  export let onShowValves: Function;
  export let onClose: Function;
  export let closeOnOutsideClick = true;

  let show = false;
  let tab = '';

  let tools = null;

  $: if (show) {
    init();
  }

  let fileUploadEnabled = true;
  $: fileUploadEnabled =
    fileUploadCapableModels.length === selectedModels.length &&
    ($user?.role === 'admin' || $user?.permissions?.chat?.file_upload);

  const init = async () => {
    if ($_tools === null) {
      await _tools.set(await getTools(localStorage.token));
    }

    if ($_tools) {
      tools = $_tools.reduce((a, tool, i, arr) => {
        a[tool.id] = {
          name: tool.name,
          description: tool.meta.description,
          enabled: selectedToolIds.includes(tool.id),
          ...tool,
        };
        return a;
      }, {});
    }

    if ($toolServers) {
      for (const serverIdx in $toolServers) {
        const server = $toolServers[serverIdx];
        if (server.info) {
          tools[`direct_server:${serverIdx}`] = {
            name: server?.info?.title ?? server.url,
            description: server.info.description ?? '',
            enabled: selectedToolIds.includes(`direct_server:${serverIdx}`),
          };
        }
      }
    }

    selectedToolIds = selectedToolIds.filter((id) => Object.keys(tools).includes(id));
  };
</script>

<Dropdown
  bind:show
  onOpenChange={(state) => {
    if (state === false) {
      onClose();
    }
  }}
>
  <Tooltip content={$i18n.t('Integrations')} placement="top">
    <slot />
  </Tooltip>
  <div slot="content">
    <div
      class="dark:bg-gray-850 scrollbar-thin z-50 max-h-72 max-w-70 min-w-70 overflow-x-hidden overflow-y-auto rounded-2xl border border-gray-100 bg-white px-1 py-1 shadow-lg dark:border-gray-800 dark:text-white"
    >
      {#if tab === ''}
        <div in:fly={{ x: -20, duration: 150 }}>
          {#if tools}
            {#if Object.keys(tools).length > 0}
              <button
                class="flex w-full cursor-pointer items-center justify-between gap-2 rounded-xl px-3 py-1.5 text-sm hover:bg-gray-50 dark:hover:bg-gray-800/50"
                on:click={() => {
                  tab = 'tools';
                }}
              >
                <Wrench />

                <div class="flex w-full items-center justify-between">
                  <div class=" line-clamp-1">
                    {$i18n.t('Tools')}
                    <span class="ml-0.5 text-gray-500">{Object.keys(tools).length}</span>
                  </div>

                  <div class="text-gray-500">
                    <ChevronRight />
                  </div>
                </div>
              </button>
            {/if}
          {:else}
            <div class="py-4">
              <Spinner />
            </div>
          {/if}

          {#if toggleFilters && toggleFilters.length > 0}
            {#each toggleFilters.sort( (a, b) => a.name.localeCompare( b.name, undefined, { sensitivity: 'base' }, ), ) as filter, filterIdx (filter.id)}
              <Tooltip content={filter?.description} placement="top-start">
                <button
                  class="flex w-full cursor-pointer items-center justify-between gap-2 rounded-xl px-3 py-1.5 text-sm hover:bg-gray-50 dark:hover:bg-gray-800/50"
                  on:click={() => {
                    if (selectedFilterIds.includes(filter.id)) {
                      selectedFilterIds = selectedFilterIds.filter((id) => id !== filter.id);
                    } else {
                      selectedFilterIds = [...selectedFilterIds, filter.id];
                    }
                  }}
                >
                  <div class="flex-1 truncate">
                    <div class="flex flex-1 items-center gap-2">
                      <div class="shrink-0">
                        {#if filter?.icon}
                          <div class="flex size-4 items-center justify-center">
                            <img
                              src={filter.icon}
                              class="size-3.5 {filter.icon.includes('data:image/svg')
                                ? 'dark:invert-[80%]'
                                : ''}"
                              style="fill: currentColor;"
                              alt={filter.name}
                            />
                          </div>
                        {:else}
                          <Sparkles className="size-4" strokeWidth="1.75" />
                        {/if}
                      </div>

                      <div class=" truncate">{filter?.name}</div>
                    </div>
                  </div>

                  {#if filter?.has_user_valves && ($user?.role === 'admin' || ($user?.permissions?.chat?.valves ?? true))}
                    <div class=" shrink-0">
                      <Tooltip content={$i18n.t('Valves')}>
                        <button
                          class="w-fit self-center rounded-full text-sm text-gray-600 transition hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                          type="button"
                          on:click={(e) => {
                            e.stopPropagation();
                            e.preventDefault();
                            onShowValves({
                              type: 'function',
                              id: filter.id,
                            });
                          }}
                        >
                          <Knobs />
                        </button>
                      </Tooltip>
                    </div>
                  {/if}

                  <div class=" shrink-0">
                    <Switch
                      state={selectedFilterIds.includes(filter.id)}
                      on:change={async (e) => {
                        const state = e.detail;
                        await tick();
                      }}
                    />
                  </div>
                </button>
              </Tooltip>
            {/each}
          {/if}

          {#if showWebSearchButton}
            <Tooltip content={$i18n.t('Search the internet')} placement="top-start">
              <button
                class="flex w-full cursor-pointer items-center justify-between gap-2 rounded-xl px-3 py-1.5 text-sm hover:bg-gray-50 dark:hover:bg-gray-800/50"
                on:click={() => {
                  webSearchEnabled = !webSearchEnabled;
                }}
              >
                <div class="flex-1 truncate">
                  <div class="flex flex-1 items-center gap-2">
                    <div class="shrink-0">
                      <GlobeAlt />
                    </div>

                    <div class=" truncate">{$i18n.t('Web Search')}</div>
                  </div>
                </div>

                <div class=" shrink-0">
                  <Switch
                    state={webSearchEnabled}
                    on:change={async (e) => {
                      const state = e.detail;
                      await tick();
                    }}
                  />
                </div>
              </button>
            </Tooltip>
          {/if}

          {#if showDeepResearchButton}
            <Tooltip content={$i18n.t('Run extended multi-step research')} placement="top-start">
              <button
                class="flex w-full cursor-pointer items-center justify-between gap-2 rounded-xl px-3 py-1.5 text-sm hover:bg-gray-50 dark:hover:bg-gray-800/50"
                on:click={() => {
                  deepResearchEnabled = !deepResearchEnabled;
                }}
              >
                <div class="flex-1 truncate">
                  <div class="flex flex-1 items-center gap-2">
                    <div class="shrink-0">
                      <Sparkles className="size-4" strokeWidth="1.75" />
                    </div>

                    <div class=" truncate">{$i18n.t('Deep Research')}</div>
                  </div>
                </div>

                <div class=" shrink-0">
                  <Switch
                    state={deepResearchEnabled}
                    on:change={async (e) => {
                      const state = e.detail;
                      await tick();
                    }}
                  />
                </div>
              </button>
            </Tooltip>
          {/if}

          {#if showPresentationButton}
            <Tooltip content={$i18n.t('Generate presentation package')} placement="top-start">
              <button
                class="flex w-full cursor-pointer items-center justify-between gap-2 rounded-xl px-3 py-1.5 text-sm hover:bg-gray-50 dark:hover:bg-gray-800/50"
                on:click={() => {
                  presentationEnabled = !presentationEnabled;
                }}
              >
                <div class="flex-1 truncate">
                  <div class="flex flex-1 items-center gap-2">
                    <div class="shrink-0">
                      <Sparkles className="size-4" strokeWidth="1.75" />
                    </div>

                    <div class=" truncate">{$i18n.t('Presentation')}</div>
                  </div>
                </div>

                <div class=" shrink-0">
                  <Switch
                    state={presentationEnabled}
                    on:change={async (e) => {
                      const state = e.detail;
                      await tick();
                    }}
                  />
                </div>
              </button>
            </Tooltip>
          {/if}

          {#if showImageGenerationButton}
            <Tooltip content={$i18n.t('Generate an image')} placement="top-start">
              <button
                class="flex w-full cursor-pointer items-center justify-between gap-2 rounded-xl px-3 py-1.5 text-sm hover:bg-gray-50 dark:hover:bg-gray-800/50"
                on:click={() => {
                  imageGenerationEnabled = !imageGenerationEnabled;
                }}
              >
                <div class="flex-1 truncate">
                  <div class="flex flex-1 items-center gap-2">
                    <div class="shrink-0">
                      <Photo className="size-4" strokeWidth="1.5" />
                    </div>

                    <div class=" truncate">{$i18n.t('Image')}</div>
                  </div>
                </div>

                <div class=" shrink-0">
                  <Switch
                    state={imageGenerationEnabled}
                    on:change={async (e) => {
                      const state = e.detail;
                      await tick();
                    }}
                  />
                </div>
              </button>
            </Tooltip>
          {/if}

          {#if showCodeInterpreterButton}
            <Tooltip content={$i18n.t('Execute code for analysis')} placement="top-start">
              <button
                class="flex w-full cursor-pointer items-center justify-between gap-2 rounded-xl px-3 py-1.5 text-sm hover:bg-gray-50 dark:hover:bg-gray-800/50"
                aria-pressed={codeInterpreterEnabled}
                aria-label={codeInterpreterEnabled
                  ? $i18n.t('Disable Code Interpreter')
                  : $i18n.t('Enable Code Interpreter')}
                on:click={() => {
                  codeInterpreterEnabled = !codeInterpreterEnabled;
                }}
              >
                <div class="flex-1 truncate">
                  <div class="flex flex-1 items-center gap-2">
                    <div class="shrink-0">
                      <Terminal className="size-3.5" strokeWidth="1.75" />
                    </div>

                    <div class=" truncate">{$i18n.t('Code Interpreter')}</div>
                  </div>
                </div>

                <div class=" shrink-0">
                  <Switch
                    state={codeInterpreterEnabled}
                    on:change={async (e) => {
                      const state = e.detail;
                      await tick();
                    }}
                  />
                </div>
              </button>
            </Tooltip>
          {/if}
        </div>
      {:else if tab === 'tools' && tools}
        <div in:fly={{ x: 20, duration: 150 }}>
          <button
            class="flex w-full cursor-pointer items-center justify-between gap-2 rounded-xl px-3 py-1.5 text-sm hover:bg-gray-50 dark:hover:bg-gray-800/50"
            on:click={() => {
              tab = '';
            }}
          >
            <ChevronLeft />

            <div class="flex w-full items-center justify-between">
              <div>
                {$i18n.t('Tools')}
                <span class="ml-0.5 text-gray-500">{Object.keys(tools).length}</span>
              </div>
            </div>
          </button>

          {#each Object.keys(tools) as toolId}
            <button
              class="relative flex w-full cursor-pointer items-center justify-between gap-2 rounded-xl px-3 py-1.5 text-sm hover:bg-gray-50 dark:hover:bg-gray-800/50"
              on:click={async (e) => {
                if (!(tools[toolId]?.authenticated ?? true)) {
                  e.preventDefault();

                  let parts = toolId.split(':');
                  let serverId = parts?.at(-1) ?? toolId;

                  // Persist the tool ID so we can re-enable it after OAuth redirect
                  sessionStorage.setItem('pendingOAuthToolId', toolId);

                  const authUrl = getOAuthClientAuthorizationUrl(serverId, 'mcp');
                  window.open(authUrl, '_self', 'noopener');
                } else {
                  tools[toolId].enabled = !tools[toolId].enabled;

                  const state = tools[toolId].enabled;
                  await tick();

                  if (state) {
                    selectedToolIds = [...selectedToolIds, toolId];
                  } else {
                    selectedToolIds = selectedToolIds.filter((id) => id !== toolId);
                  }
                }
              }}
            >
              {#if !(tools[toolId]?.authenticated ?? true)}
                <!-- make it slighly darker and not clickable -->
                <div class="absolute inset-0 z-10 cursor-pointer rounded-xl opacity-50" />
              {/if}
              <div class="flex-1 truncate">
                <div class="flex flex-1 items-center gap-2">
                  <Tooltip content={tools[toolId]?.name ?? ''} placement="top">
                    <div class="shrink-0">
                      <Wrench />
                    </div>
                  </Tooltip>
                  <Tooltip content={tools[toolId]?.description ?? ''} placement="top-start">
                    <div class=" truncate">{tools[toolId].name}</div>
                  </Tooltip>
                </div>
              </div>

              {#if tools[toolId]?.has_user_valves && ($user?.role === 'admin' || ($user?.permissions?.chat?.valves ?? true))}
                <div class=" shrink-0">
                  <Tooltip content={$i18n.t('Valves')}>
                    <button
                      class="w-fit self-center rounded-full text-sm text-gray-600 transition hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                      type="button"
                      on:click={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        onShowValves({
                          type: 'tool',
                          id: toolId,
                        });
                      }}
                    >
                      <Knobs />
                    </button>
                  </Tooltip>
                </div>
              {/if}

              <div class=" shrink-0">
                <Switch state={tools[toolId].enabled} />
              </div>
            </button>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</Dropdown>
