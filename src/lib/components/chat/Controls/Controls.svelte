<script lang="ts">
  import { createEventDispatcher, getContext } from 'svelte';
  const dispatch = createEventDispatcher();
  const i18n = getContext('i18n');

  import XMark from '$lib/components/icons/XMark.svelte';
  import AdvancedParams from '../Settings/Advanced/AdvancedParams.svelte';
  import Valves from '$lib/components/chat/Controls/Valves.svelte';
  import FileItem from '$lib/components/common/FileItem.svelte';
  import Collapsible from '$lib/components/common/Collapsible.svelte';

  import { user, settings } from '$lib/stores';
  import Textarea from '$lib/components/common/Textarea.svelte';
  export let models = [];
  export let chatFiles = [];
  export let params = {};
  export let embed = false;

  // Persist collapsible section open/close state
  const getOpen = (key: string, fallback = true): boolean => {
    const v = localStorage.getItem(`chatControls.${key}`);
    return v !== null ? v === 'true' : fallback;
  };
  const setOpen = (key: string) => (open: boolean) => {
    localStorage.setItem(`chatControls.${key}`, String(open));
  };

  let showFiles = getOpen('files');
  let showValves = getOpen('valves', false);
  let showSystemPrompt = getOpen('systemPrompt');
  let showAdvancedParams = getOpen('advancedParams');
</script>

<div class=" dark:text-white">
  {#if !embed}
    <div class=" mb-2 flex items-center justify-between dark:text-gray-100">
      <div class=" text-md font-primary self-center">{$i18n.t('Controls')}</div>
      <button
        class="self-center"
        aria-label={$i18n.t('Close chat controls')}
        on:click={() => {
          dispatch('close');
        }}
      >
        <XMark className="size-3.5" />
      </button>
    </div>
  {/if}

  {#if $user?.role === 'admin' || ($user?.permissions.chat?.controls ?? true)}
    <div class=" px-0.5 py-0.5 text-sm dark:text-gray-200">
      {#if chatFiles.length > 0}
        <Collapsible
          title={$i18n.t('Files')}
          bind:open={showFiles}
          onChange={setOpen('files')}
          buttonClassName="w-full"
        >
          <div class="mt-1.5 flex flex-col gap-1" slot="content">
            {#each chatFiles as file, fileIdx}
              <FileItem
                className="w-full"
                item={file}
                edit={true}
                url={file?.url ? file.url : null}
                name={file.name}
                type={file.type}
                size={file?.size}
                dismissible={true}
                small={true}
                on:dismiss={() => {
                  // Remove the file from the chatFiles array

                  chatFiles.splice(fileIdx, 1);
                  chatFiles = chatFiles;
                }}
                on:click={() => {
                  console.log(file);
                }}
              />
            {/each}
          </div>
        </Collapsible>

        <hr class="my-2 border-gray-50 dark:border-gray-700/10" />
      {/if}

      {#if $user?.role === 'admin' || ($user?.permissions.chat?.valves ?? true)}
        <Collapsible
          bind:open={showValves}
          onChange={setOpen('valves')}
          title={$i18n.t('Valves')}
          buttonClassName="w-full"
        >
          <div class="text-sm" slot="content">
            <Valves show={showValves} />
          </div>
        </Collapsible>

        <hr class="my-2 border-gray-50 dark:border-gray-700/10" />
      {/if}

      {#if $user?.role === 'admin' || ($user?.permissions.chat?.system_prompt ?? true)}
        <Collapsible
          title={$i18n.t('System Prompt')}
          bind:open={showSystemPrompt}
          onChange={setOpen('systemPrompt')}
          buttonClassName="w-full"
        >
          <div class="mt-2" slot="content">
            <Textarea
              bind:value={params.system}
              rows="4"
              placeholder={$i18n.t('Enter system prompt')}
            />
          </div>
        </Collapsible>

        <hr class="my-2 border-gray-50 dark:border-gray-700/10" />
      {/if}

      {#if $user?.role === 'admin' || ($user?.permissions.chat?.params ?? true)}
        <Collapsible
          title={$i18n.t('Advanced Params')}
          bind:open={showAdvancedParams}
          onChange={setOpen('advancedParams')}
          buttonClassName="w-full"
        >
          <div class="mt-1.5 mb-3 text-sm" slot="content">
            <div>
              <AdvancedParams
                className="bg-background"
                admin={$user?.role === 'admin'}
                custom={true}
                bind:params
              />
            </div>
          </div>
        </Collapsible>
      {/if}
    </div>
  {/if}
</div>
