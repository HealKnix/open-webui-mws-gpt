<script lang="ts">
  import { getContext } from 'svelte';
  import type { Writable } from 'svelte/store';
  import type { i18n as i18nType } from 'i18next';

  import DocumentPage from '$lib/components/icons/DocumentPage.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';

  import { extractFileReferences, type FileReference } from '$lib/utils/extractFileReferences';
  import FileReferenceModal from './FileReferenceModal.svelte';
  import Button from '$lib/components/common/Button.svelte';
  import { WEBUI_API_BASE_URL } from '$lib/constants';
  import { getWorkspaceDownloadUrl } from '$lib/apis/files';

  const i18n = getContext<Writable<i18nType>>('i18n');

  export let content: string = '';

  $: files = extractFileReferences(content);

  let showModal = false;
  let selected: FileReference | null = null;

  const openPreview = (file: FileReference) => {
    selected = file;
    showModal = true;
  };
</script>

{#if files.length > 0}
  <div class="my-2 flex flex-col gap-1.5">
    {#each files as file (file.url)}
      <div
        class="group bg-card border-border flex w-full max-w-md items-center gap-2 rounded-2xl border p-1.5"
      >
        <div
          class="bg-primary text-primary-foreground flex size-10 shrink-0 items-center justify-center rounded-[10px]"
        >
          <DocumentPage className="size-6" />
        </div>

        <div class="flex min-w-0 flex-1 flex-col justify-center -space-y-0.5 px-2.5">
          <div class="line-clamp-1 text-sm font-medium dark:text-gray-100">
            {file.name}
          </div>
          <div class="line-clamp-1 text-xs text-gray-500 uppercase">{file.ext}</div>
        </div>

        <div class="flex shrink-0 items-center gap-2 pr-1">
          <!-- <Tooltip content={$i18n.t('Preview')} placement="top">
            <Button size="xs" variant="ghost" color="foreground" on:click={() => openPreview(file)}>
              {$i18n.t('Preview')}
            </Button>
          </Tooltip> -->

          <Tooltip content={$i18n.t('Download')} placement="top">
            <Button
              isIconOnly
              size="xs"
              variant="flat"
              className="*:fill-primary"
              href={getWorkspaceDownloadUrl(file.url)}
              target="_blank"
              rel="noopener noreferrer"
              download={getWorkspaceDownloadUrl(file.url)}
              aria-label={$i18n.t('Download')}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                class="size-4 fill-current"
              >
                <path
                  fill-rule="evenodd"
                  d="M10 3a.75.75 0 0 1 .75.75v7.69l2.22-2.22a.75.75 0 1 1 1.06 1.06l-3.5 3.5a.75.75 0 0 1-1.06 0l-3.5-3.5a.75.75 0 1 1 1.06-1.06l2.22 2.22V3.75A.75.75 0 0 1 10 3Zm-6.75 12a.75.75 0 0 1 .75-.75h12a.75.75 0 0 1 0 1.5H4a.75.75 0 0 1-.75-.75Z"
                  clip-rule="evenodd"
                />
              </svg>
            </Button>
          </Tooltip>
        </div>
      </div>
    {/each}
  </div>

  {#if selected}
    <FileReferenceModal
      bind:show={showModal}
      name={selected.name}
      url={selected.url}
      ext={selected.ext}
    />
  {/if}
{/if}
