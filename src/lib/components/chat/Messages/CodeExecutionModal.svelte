<script lang="ts">
  import { getContext } from 'svelte';
  import CodeBlock from './CodeBlock.svelte';
  import Modal from '$lib/components/common/Modal.svelte';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import Badge from '$lib/components/common/Badge.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';
  const i18n = getContext('i18n');

  export let show = false;
  export let codeExecution = null;
</script>

<Modal size="lg" bind:show>
  <div>
    <div class="flex justify-between px-5 pt-4 pb-2 dark:text-gray-300">
      <div class="flex flex-col gap-0.5 self-center text-lg font-medium capitalize">
        {#if codeExecution?.result}
          <div>
            {#if codeExecution.result?.error}
              <Badge type="error" content="error" />
            {:else if codeExecution.result?.output}
              <Badge type="success" content="success" />
            {:else}
              <Badge type="warning" content="incomplete" />
            {/if}
          </div>
        {/if}

        <div class="flex items-center gap-2">
          {#if !codeExecution?.result}
            <div>
              <Spinner className="size-4" />
            </div>
          {/if}

          <div>
            {#if codeExecution?.name}
              {$i18n.t('Code execution')}: {codeExecution?.name}
            {:else}
              {$i18n.t('Code execution')}
            {/if}
          </div>
        </div>
      </div>
      <button
        class="self-center"
        on:click={() => {
          show = false;
          codeExecution = null;
        }}
      >
        <XMark className={'size-5'} />
      </button>
    </div>

    <div class="flex w-full flex-col px-4 pb-5 md:flex-row">
      <div
        class="scrollbar-hidden flex max-h-[22rem] w-full flex-col overflow-y-scroll dark:text-gray-200"
      >
        <div class="flex w-full flex-col">
          <CodeBlock
            id="code-exec-{codeExecution?.id}-code"
            lang={codeExecution?.language ?? ''}
            code={codeExecution?.code ?? ''}
            className=""
            editorClassName={codeExecution?.result &&
            (codeExecution?.result?.error || codeExecution?.result?.output)
              ? 'rounded-b-none'
              : ''}
            run={false}
          />
        </div>

        {#if codeExecution?.result && (codeExecution?.result?.error || codeExecution?.result?.output)}
          <div class="flex flex-col gap-3 rounded-b-lg px-4 py-4 dark:bg-[#202123] dark:text-white">
            {#if codeExecution?.result?.error}
              <div>
                <div class=" mb-1 text-xs text-gray-500">{$i18n.t('ERROR')}</div>
                <div class="text-sm">{codeExecution?.result?.error}</div>
              </div>
            {/if}
            {#if codeExecution?.result?.output}
              <div>
                <div class=" mb-1 text-xs text-gray-500">{$i18n.t('OUTPUT')}</div>
                <div class="text-sm">{codeExecution?.result?.output}</div>
              </div>
            {/if}
          </div>
        {/if}
        {#if codeExecution?.result?.files && codeExecution?.result?.files.length > 0}
          <div class="flex w-full flex-col">
            <hr class="dark:border-gray-850/30 my-2 border-gray-100/30" />
            <div class=" text-sm font-medium dark:text-gray-300">
              {$i18n.t('Files')}
            </div>
            <ul class="mt-1 list-disc pl-4 text-xs">
              {#each codeExecution?.result?.files as file}
                <li>
                  <a href={file.url} target="_blank">{file.name}</a>
                </li>
              {/each}
            </ul>
          </div>
        {/if}
      </div>
    </div>
  </div>
</Modal>
