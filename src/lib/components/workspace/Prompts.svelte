<script lang="ts">
  import { toast } from 'svelte-sonner';
  import fileSaver from 'file-saver';
  const { saveAs } = fileSaver;

  import { goto } from '$app/navigation';
  import { onMount, getContext, tick, onDestroy } from 'svelte';
  import { WEBUI_NAME, config, user } from '$lib/stores';

  import {
    createNewPrompt,
    deletePromptById,
    togglePromptById,
    getPromptItems,
    getPromptTags,
  } from '$lib/apis/prompts';
  import { capitalizeFirstLetter, slugify, copyToClipboard } from '$lib/utils';

  import PromptMenu from './Prompts/PromptMenu.svelte';
  import EllipsisHorizontal from '../icons/EllipsisHorizontal.svelte';
  import Clipboard from '../icons/Clipboard.svelte';
  import Check from '../icons/Check.svelte';
  import DeleteConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
  import Search from '../icons/Search.svelte';
  import Plus from '../icons/Plus.svelte';
  import ChevronRight from '../icons/ChevronRight.svelte';
  import Spinner from '../common/Spinner.svelte';
  import Tooltip from '../common/Tooltip.svelte';
  import XMark from '../icons/XMark.svelte';
  import GarbageBin from '../icons/GarbageBin.svelte';
  import ViewSelector from './common/ViewSelector.svelte';
  import TagSelector from './common/TagSelector.svelte';
  import Badge from '$lib/components/common/Badge.svelte';
  import Switch from '../common/Switch.svelte';
  import Pagination from '../common/Pagination.svelte';

  let shiftKey = false;

  const i18n = getContext('i18n');
  let promptsImportInputElement: HTMLInputElement;
  let loaded = false;

  let importFiles = null;
  let query = '';
  let searchDebounceTimer: ReturnType<typeof setTimeout>;

  let prompts = null;
  let tags = [];
  let total = null;
  let loading = false;

  let showDeleteConfirm = false;
  let deletePrompt = null;

  let tagsContainerElement: HTMLDivElement;
  let viewOption = '';
  let selectedTag = '';
  let copiedId: string | null = null;

  let page = 1;

  // Debounce only query changes
  $: if (query !== undefined) {
    loading = true;
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
      page = 1;
      getPromptList();
    }, 300);
  }

  // Immediate response to page/filter changes
  $: if (page && selectedTag !== undefined && viewOption !== undefined) {
    getPromptList();
  }

  const getPromptList = async () => {
    if (!loaded) return;

    loading = true;
    try {
      const res = await getPromptItems(
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
        prompts = res.items;
        total = res.total;

        // get tags
        tags = await getPromptTags(localStorage.token).catch((error) => {
          toast.error(`${error}`);
          return [];
        });
      }
    } catch (err) {
      console.error(err);
    } finally {
      loading = false;
    }
  };

  const shareHandler = async (prompt) => {
    toast.success($i18n.t('Redirecting you to Open WebUI Community'));

    const url = 'https://openwebui.com';

    const tab = await window.open(`${url}/prompts/create`, '_blank');
    window.addEventListener(
      'message',
      (event) => {
        if (event.origin !== url) return;
        if (event.data === 'loaded') {
          tab.postMessage(JSON.stringify(prompt), '*');
        }
      },
      false,
    );
  };

  const cloneHandler = async (prompt) => {
    const clonedPrompt = { ...prompt };

    clonedPrompt.title = `${clonedPrompt.title} (Clone)`;
    const baseCommand = clonedPrompt.command.startsWith('/')
      ? clonedPrompt.command.substring(1)
      : clonedPrompt.command;
    clonedPrompt.command = slugify(`${baseCommand} clone`);

    sessionStorage.prompt = JSON.stringify(clonedPrompt);
    goto('/workspace/prompts/create');
  };

  const exportHandler = async (prompt) => {
    let blob = new Blob([JSON.stringify([prompt])], {
      type: 'application/json',
    });
    saveAs(blob, `prompt-export-${Date.now()}.json`);
  };

  const copyHandler = async (prompt) => {
    const res = await copyToClipboard(prompt.content);
    if (res) {
      copiedId = prompt.command;
      setTimeout(() => {
        copiedId = null;
      }, 2000);
    }
  };

  const deleteHandler = async (prompt) => {
    const command = prompt.command;

    const res = await deletePromptById(localStorage.token, prompt.id).catch((err) => {
      toast.error(err);
      return null;
    });

    if (res) {
      toast.success($i18n.t(`Deleted {{name}}`, { name: command }));
    }

    page = 1;
    getPromptList();
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

<svelte:head>
  <title>
    {$i18n.t('Prompts')} • {$WEBUI_NAME}
  </title>
</svelte:head>

{#if loaded}
  <DeleteConfirmDialog
    bind:show={showDeleteConfirm}
    title={$i18n.t('Delete prompt?')}
    on:confirm={() => {
      deleteHandler(deletePrompt);
    }}
  >
    <div class=" truncate text-sm text-gray-500">
      {$i18n.t('This will delete')} <span class="  font-medium">{deletePrompt.command}</span>.
    </div>
  </DeleteConfirmDialog>

  <div class="mt-1.5 mb-3 flex flex-col gap-1 px-1">
    <input
      id="prompts-import-input"
      bind:this={promptsImportInputElement}
      bind:files={importFiles}
      type="file"
      accept=".json"
      hidden
      on:change={() => {
        console.log(importFiles);
        if (!importFiles || importFiles.length === 0) return;

        const reader = new FileReader();
        reader.onload = async (event) => {
          const savedPrompts = JSON.parse(event.target.result);
          console.log(savedPrompts);

          try {
            for (const prompt of savedPrompts) {
              await createNewPrompt(localStorage.token, {
                command: prompt.command,
                name: prompt.name,
                content: prompt.content,
              }).catch((error) => {
                toast.error(typeof error === 'string' ? error : JSON.stringify(error));
                return null;
              });
            }

            page = 1;
            await getPromptList();
          } finally {
            importFiles = null;
            promptsImportInputElement.value = '';
          }
        };

        reader.readAsText(importFiles[0]);
      }}
    />
    <div class="flex items-center justify-between">
      <div class="flex shrink-0 items-center gap-2 px-0.5 text-xl font-medium md:self-center">
        <div>
          {$i18n.t('Prompts')}
        </div>

        <div class="text-lg font-medium text-gray-500 dark:text-gray-500">
          {total ?? ''}
        </div>
      </div>

      <div class="flex w-full justify-end gap-1.5">
        {#if $user?.role === 'admin' || $user?.permissions?.workspace?.prompts_import}
          <button
            class="dark:bg-gray-850 flex items-center space-x-1 rounded-xl bg-gray-50 px-3 py-1.5 text-xs transition hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-800"
            on:click={() => {
              promptsImportInputElement.click();
            }}
          >
            <div class=" line-clamp-1 self-center font-medium">
              {$i18n.t('Import')}
            </div>
          </button>
        {/if}

        {#if total && ($user?.role === 'admin' || $user?.permissions?.workspace?.prompts_export)}
          <button
            class="dark:bg-gray-850 flex items-center space-x-1 rounded-xl bg-gray-50 px-3 py-1.5 text-xs transition hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-800"
            on:click={async () => {
              let blob = new Blob([JSON.stringify(prompts)], {
                type: 'application/json',
              });
              saveAs(blob, `prompts-export-${Date.now()}.json`);
            }}
          >
            <div class=" line-clamp-1 self-center font-medium">
              {$i18n.t('Export')}
            </div>
          </button>
        {/if}
        <a
          class=" flex items-center rounded-xl bg-black px-2 py-1.5 text-sm font-medium text-white transition dark:bg-white dark:text-black"
          href="/workspace/prompts/create"
        >
          <Plus className="size-3" strokeWidth="2.5" />

          <div class=" hidden text-xs md:ml-1 md:block">{$i18n.t('New Prompt')}</div>
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
          class=" w-full rounded-r-xl bg-transparent py-1 pr-4 text-sm outline-hidden"
          bind:value={query}
          aria-label={$i18n.t('Search Prompts')}
          placeholder={$i18n.t('Search Prompts')}
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

        {#if (tags ?? []).length > 0}
          <TagSelector
            bind:value={selectedTag}
            items={tags.map((tag) => ({ value: tag, label: tag }))}
          />
        {/if}
      </div>
    </div>

    {#if prompts === null || loading}
      <div class="my-16 mb-24 flex h-full w-full items-center justify-center">
        <Spinner className="size-5" />
      </div>
    {:else if (prompts ?? []).length !== 0}
      <!-- Before they call, I will answer; while they are yet speaking, I will hear. -->
      <div class="my-2 grid gap-2 px-3 lg:grid-cols-2">
        {#each prompts as prompt (prompt.id)}
          <a
            class=" dark:hover:bg-gray-850/50 flex w-full cursor-pointer space-x-4 rounded-2xl px-3 py-2.5 text-left transition hover:bg-gray-50"
            href={`/workspace/prompts/${prompt.id}`}
          >
            <div class=" flex w-full flex-1 cursor-pointer flex-col space-x-4 pl-1">
              <div class="mb-0.5 flex w-full items-center justify-between">
                <div class="flex items-center gap-2">
                  <div class="line-clamp-1 font-medium capitalize">{prompt.name}</div>
                  <div class="line-clamp-1 overflow-hidden text-xs text-ellipsis text-gray-500">
                    /{prompt.command}
                  </div>
                </div>
                {#if !prompt.write_access}
                  <Badge type="muted" content={$i18n.t('Read Only')} />
                {/if}
              </div>

              <div class="flex gap-1 text-xs">
                <Tooltip
                  content={prompt?.user?.email ?? $i18n.t('Deleted User')}
                  className="flex shrink-0"
                  placement="top-start"
                >
                  <div class="shrink-0 text-gray-500">
                    {$i18n.t('By {{name}}', {
                      name: capitalizeFirstLetter(
                        prompt?.user?.name ?? prompt?.user?.email ?? $i18n.t('Deleted User'),
                      ),
                    })}
                  </div>
                </Tooltip>

                <div>·</div>

                {#if prompt.content}
                  <Tooltip content={prompt.content} placement="top">
                    <div class="line-clamp-1">
                      {prompt.content}
                    </div>
                  </Tooltip>
                {/if}
              </div>
            </div>
            <div class="flex flex-row gap-0.5 self-center">
              {#if shiftKey}
                <Tooltip content={$i18n.t('Delete')}>
                  <button
                    class="w-fit self-center rounded-xl px-2 py-2 text-sm hover:bg-black/5 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white"
                    type="button"
                    aria-label={$i18n.t('Delete')}
                    on:click={() => {
                      deleteHandler(prompt);
                    }}
                  >
                    <GarbageBin />
                  </button>
                </Tooltip>
              {:else}
                <Tooltip content={$i18n.t('Copy Prompt')}>
                  <button
                    class="w-fit self-center rounded-xl p-1.5 text-sm hover:bg-black/5 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white"
                    type="button"
                    aria-label={$i18n.t('Copy Prompt')}
                    on:click={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      copyHandler(prompt);
                    }}
                  >
                    {#if copiedId === prompt.command}
                      <Check className="size-4" strokeWidth="1.5" />
                    {:else}
                      <Clipboard className="size-4" strokeWidth="1.5" />
                    {/if}
                  </button>
                </Tooltip>
                <PromptMenu
                  shareHandler={() => {
                    shareHandler(prompt);
                  }}
                  cloneHandler={() => {
                    cloneHandler(prompt);
                  }}
                  exportHandler={() => {
                    exportHandler(prompt);
                  }}
                  deleteHandler={async () => {
                    deletePrompt = prompt;
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
                </PromptMenu>

                <button on:click|stopPropagation|preventDefault>
                  <Tooltip
                    content={prompt.is_active !== false ? $i18n.t('Enabled') : $i18n.t('Disabled')}
                  >
                    <Switch
                      bind:state={prompt.is_active}
                      on:change={async () => {
                        togglePromptById(localStorage.token, prompt.id);
                      }}
                    />
                  </Tooltip>
                </button>
              {/if}
            </div>
          </a>
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
          <div class=" mb-3 text-3xl">😕</div>
          <div class=" mb-1 text-lg font-medium">{$i18n.t('No prompts found')}</div>
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
        href="https://openwebui.com/prompts"
        target="_blank"
      >
        <div class=" self-center">
          <div class=" line-clamp-1 font-medium">{$i18n.t('Discover a prompt')}</div>
          <div class=" line-clamp-1 text-sm">
            {$i18n.t('Discover, download, and explore custom prompts')}
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
