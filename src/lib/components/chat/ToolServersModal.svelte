<script lang="ts">
  import { getContext, onMount } from 'svelte';
  import { models, config, toolServers, tools, terminalServers } from '$lib/stores';

  import { toast } from 'svelte-sonner';
  import { deleteSharedChatById, getChatById, shareChatById } from '$lib/apis/chats';
  import { copyToClipboard } from '$lib/utils';

  import Modal from '../common/Modal.svelte';
  import Link from '../icons/Link.svelte';
  import Collapsible from '../common/Collapsible.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';

  export let show = false;
  export let selectedToolIds = [];

  let selectedTools = [];

  $: selectedTools = ($tools ?? []).filter((tool) => selectedToolIds.includes(tool.id));

  const i18n = getContext('i18n');
</script>

<Modal bind:show size="md">
  <div>
    <div class=" flex justify-between px-5 pt-4 pb-0.5 dark:text-gray-300">
      <div class=" self-center text-lg font-medium">{$i18n.t('Available Tools')}</div>
      <button
        class="self-center"
        aria-label={$i18n.t('Close')}
        on:click={() => {
          show = false;
        }}
      >
        <XMark className={'size-5'} />
      </button>
    </div>

    {#if selectedTools.length > 0}
      {#if $toolServers.length > 0}
        <div class=" flex justify-between px-5 pb-1 dark:text-gray-300">
          <div class=" self-center text-base font-medium">{$i18n.t('Tools')}</div>
        </div>
      {/if}

      <div class="flex w-full flex-col justify-center px-5 pb-3">
        <div class=" mb-1 text-sm dark:text-gray-300">
          {#each selectedTools as tool}
            <Collapsible buttonClassName="w-full mb-0.5">
              <div class="truncate">
                <div class="truncate text-sm font-medium text-gray-800 dark:text-gray-100">
                  {tool?.name}
                </div>

                {#if tool?.meta?.description}
                  <div class="text-xs text-gray-500">
                    {tool?.meta?.description}
                  </div>
                {/if}
              </div>

              <!-- <div slot="content">
							{JSON.stringify(tool, null, 2)}
						</div> -->
            </Collapsible>
          {/each}
        </div>
      </div>
    {/if}

    {#if $toolServers.length > 0}
      <div class=" flex justify-between px-5 pb-0.5 dark:text-gray-300">
        <div class=" self-center text-base font-medium">{$i18n.t('Tool Servers')}</div>
      </div>

      <div class="flex w-full flex-col justify-center px-5 pb-5">
        <div class=" mb-2 text-xs text-gray-600 dark:text-gray-300">
          {$i18n.t('Open WebUI can use tools provided by any OpenAPI server.')} <br /><a
            class="underline"
            href="https://github.com/open-webui/openapi-servers"
            target="_blank">{$i18n.t('Learn more about OpenAPI tool servers.')}</a
          >
        </div>
        <div class=" mb-1 text-sm dark:text-gray-300">
          {#each $toolServers as toolServer}
            <Collapsible buttonClassName="w-full" chevron>
              <div>
                <div class="text-sm font-medium text-gray-800 dark:text-gray-100">
                  {toolServer?.openapi?.info?.title} - v{toolServer?.openapi?.info?.version}
                </div>

                <div class="text-xs text-gray-500">
                  {toolServer?.openapi?.info?.description}
                </div>

                <div class="text-xs text-gray-500">
                  {toolServer?.url}
                </div>
              </div>

              <div slot="content">
                {#each toolServer?.specs ?? [] as tool_spec}
                  <div class="my-1">
                    <div class="font-medium text-gray-800 dark:text-gray-100">
                      {tool_spec?.name}
                    </div>

                    <div>
                      {tool_spec?.description}
                    </div>
                  </div>
                {/each}
              </div>
            </Collapsible>
          {/each}
        </div>
      </div>
    {/if}
  </div>
</Modal>
