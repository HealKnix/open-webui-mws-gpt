<script lang="ts">
  import dayjs from '$lib/dayjs';
  import duration from 'dayjs/plugin/duration';
  import relativeTime from 'dayjs/plugin/relativeTime';

  dayjs.extend(duration);
  dayjs.extend(relativeTime);

  import { getContext } from 'svelte';
  const i18n = getContext('i18n');

  import { capitalizeFirstLetter, formatFileSize } from '$lib/utils';

  import { WEBUI_BASE_URL } from '$lib/constants';

  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import DocumentPage from '$lib/components/icons/DocumentPage.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';
  import Spinner from '$lib/components/common/Spinner.svelte';

  export let knowledge = null;
  export let selectedFileId = null;
  export let files = [];

  export let onClick = (fileId) => {};
  export let onDelete = (fileId) => {};
</script>

<div class=" flex max-h-full w-full flex-col gap-[0.5px]">
  {#each files as file (file?.id ?? file?.itemId ?? file?.tempId)}
    <div
      class=" dark:hover:bg-gray-850/50 flex w-full cursor-pointer rounded-xl bg-transparent px-1.5 py-0.5 transition hover:bg-white {selectedFileId
        ? ''
        : 'dark:hover:bg-gray-850 hover:bg-gray-100'}"
    >
      <div class="flex items-center">
        {#if file?.status !== 'uploading'}
          <Tooltip content={$i18n.t('Open file')}>
            <button
              class="dark:hover:bg-gray-850 rounded-full p-1 transition hover:bg-gray-100"
              type="button"
              on:click={() => {
                let fileId = file?.id ?? file?.tempId;
                window.open(`${WEBUI_BASE_URL}/api/v1/files/${fileId}/content`, '_blank');
              }}
            >
              <DocumentPage className="size-3.5" />
            </button>
          </Tooltip>
        {:else}
          <Spinner className="size-3.5" />
        {/if}
      </div>

      <button
        class="group relative flex flex-1 items-center justify-between gap-1 rounded-xl p-2 text-left"
        type="button"
        on:click={async () => {
          console.log(file);
          onClick(file?.id ?? file?.tempId);
        }}
      >
        <div class="">
          <div class="line-clamp-1 flex items-center gap-2">
            <div class="line-clamp-1 text-sm">
              {file?.name ?? file?.meta?.name}
              {#if file?.meta?.size}
                <span class="text-xs text-gray-500">{formatFileSize(file?.meta?.size)}</span>
              {/if}
            </div>
          </div>
        </div>

        <div class="flex shrink-0 items-center gap-2">
          {#if file?.updated_at}
            <Tooltip content={dayjs(file.updated_at * 1000).format('LLLL')}>
              <div>
                {dayjs(file.updated_at * 1000).fromNow()}
              </div>
            </Tooltip>
          {/if}

          {#if file?.user}
            <Tooltip
              content={file?.user?.email ?? $i18n.t('Deleted User')}
              className="flex shrink-0"
              placement="top-start"
            >
              <div class="shrink-0 text-gray-500">
                {$i18n.t('By {{name}}', {
                  name: capitalizeFirstLetter(
                    file?.user?.name ?? file?.user?.email ?? $i18n.t('Deleted User'),
                  ),
                })}
              </div>
            </Tooltip>
          {/if}
        </div>
      </button>

      {#if knowledge?.write_access}
        <div class="flex items-center">
          <Tooltip content={$i18n.t('Delete')}>
            <button
              class="dark:hover:bg-gray-850 rounded-full p-1 transition hover:bg-gray-100"
              type="button"
              on:click={() => {
                onDelete(file?.id ?? file?.tempId);
              }}
            >
              <XMark />
            </button>
          </Tooltip>
        </div>
      {/if}
    </div>
  {/each}
</div>
