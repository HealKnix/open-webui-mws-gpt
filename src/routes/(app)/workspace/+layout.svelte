<script lang="ts">
  import { onMount, getContext } from 'svelte';
  import {
    WEBUI_NAME,
    showSidebar,
    functions,
    user,
    mobile,
    models,
    knowledge,
    tools,
  } from '$lib/stores';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Sidebar from '$lib/components/icons/Sidebar.svelte';

  const i18n = getContext('i18n');

  let loaded = false;

  onMount(async () => {
    if ($user?.role !== 'admin') {
      if ($page.url.pathname.includes('/models') && !$user?.permissions?.workspace?.models) {
        goto('/');
      } else if (
        $page.url.pathname.includes('/knowledge') &&
        !$user?.permissions?.workspace?.knowledge
      ) {
        goto('/');
      } else if (
        $page.url.pathname.includes('/prompts') &&
        !$user?.permissions?.workspace?.prompts
      ) {
        goto('/');
      } else if ($page.url.pathname.includes('/tools') && !$user?.permissions?.workspace?.tools) {
        goto('/');
      } else if ($page.url.pathname.includes('/skills') && !$user?.permissions?.workspace?.skills) {
        goto('/');
      } else if (
        $page.url.pathname.includes('/widgets') &&
        !$user?.permissions?.workspace?.widgets
      ) {
        goto('/');
      }
    }

    loaded = true;
  });
</script>

<svelte:head>
  <title>
    {$i18n.t('Workspace')} • {$WEBUI_NAME}
  </title>
</svelte:head>

{#if loaded}
  <div
    class=" transition-width relative flex h-screen max-h-[100dvh] w-full flex-col duration-200 ease-in-out {$showSidebar
      ? 'md:max-w-[calc(100%-var(--sidebar-width))]'
      : ''} max-w-full"
  >
    <nav class="   drag-region px-2.5 pt-1.5 backdrop-blur-xl select-none">
      <div class=" flex items-center gap-1">
        {#if $mobile}
          <div class="{$showSidebar ? 'md:hidden' : ''} flex flex-none items-center self-center">
            <Tooltip
              content={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}
              interactive={true}
            >
              <button
                id="sidebar-toggle-button"
                class=" dark:hover:bg-gray-850 cursor- flex cursor-pointer rounded-lg transition hover:bg-gray-100"
                aria-label={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}
                on:click={() => {
                  showSidebar.set(!$showSidebar);
                }}
              >
                <div class=" self-center p-1.5">
                  <Sidebar />
                </div>
              </button>
            </Tooltip>
          </div>
        {/if}

        <div class="">
          <div
            class="scrollbar-none pointer-events-auto flex w-fit touch-auto gap-1 overflow-x-auto rounded-full bg-transparent py-1 text-center text-sm font-medium"
          >
            {#if $user?.role === 'admin' || $user?.permissions?.workspace?.models}
              <a
                draggable="false"
                aria-current={$page.url.pathname.includes('/workspace/models') ? 'page' : null}
                class="min-w-fit p-1.5 {$page.url.pathname.includes('/workspace/models')
                  ? ''
                  : 'text-gray-300 hover:text-gray-700 dark:text-gray-600 dark:hover:text-white'} transition select-none"
                href="/workspace/models">{$i18n.t('Models')}</a
              >
            {/if}

            {#if $user?.role === 'admin' || $user?.permissions?.workspace?.knowledge}
              <a
                draggable="false"
                aria-current={$page.url.pathname.includes('/workspace/knowledge') ? 'page' : null}
                class="min-w-fit p-1.5 {$page.url.pathname.includes('/workspace/knowledge')
                  ? ''
                  : 'text-gray-300 hover:text-gray-700 dark:text-gray-600 dark:hover:text-white'} transition select-none"
                href="/workspace/knowledge"
              >
                {$i18n.t('Knowledge')}
              </a>
            {/if}

            {#if $user?.role === 'admin' || $user?.permissions?.workspace?.prompts}
              <a
                draggable="false"
                aria-current={$page.url.pathname.includes('/workspace/prompts') ? 'page' : null}
                class="min-w-fit p-1.5 {$page.url.pathname.includes('/workspace/prompts')
                  ? ''
                  : 'text-gray-300 hover:text-gray-700 dark:text-gray-600 dark:hover:text-white'} transition select-none"
                href="/workspace/prompts">{$i18n.t('Prompts')}</a
              >
            {/if}

            {#if $user?.role === 'admin' || $user?.permissions?.workspace?.skills}
              <a
                draggable="false"
                aria-current={$page.url.pathname.includes('/workspace/skills') ? 'page' : null}
                class="min-w-fit p-1.5 {$page.url.pathname.includes('/workspace/skills')
                  ? ''
                  : 'text-gray-300 hover:text-gray-700 dark:text-gray-600 dark:hover:text-white'} transition select-none"
                href="/workspace/skills"
              >
                {$i18n.t('Skills')}
              </a>
            {/if}

            {#if $user?.role === 'admin' || $user?.permissions?.workspace?.tools}
              <a
                draggable="false"
                aria-current={$page.url.pathname.includes('/workspace/tools') ? 'page' : null}
                class="min-w-fit p-1.5 {$page.url.pathname.includes('/workspace/tools')
                  ? ''
                  : 'text-gray-300 hover:text-gray-700 dark:text-gray-600 dark:hover:text-white'} transition select-none"
                href="/workspace/tools"
              >
                {$i18n.t('Tools')}
              </a>
            {/if}

            {#if $user?.role === 'admin' || $user?.permissions?.workspace?.widgets}
              <a
                draggable="false"
                aria-current={$page.url.pathname.includes('/workspace/widgets') ? 'page' : null}
                class="min-w-fit p-1.5 {$page.url.pathname.includes('/workspace/widgets')
                  ? ''
                  : 'text-gray-300 hover:text-gray-700 dark:text-gray-600 dark:hover:text-white'} transition select-none"
                href="/workspace/widgets"
              >
                {$i18n.t('Widgets')}
              </a>
            {/if}
          </div>
        </div>

        <!-- <div class="flex items-center text-xl font-medium">{$i18n.t('Workspace')}</div> -->
      </div>
    </nav>

    <div class="max-h-full flex-1 overflow-y-auto px-3 pb-1 md:px-[18px]" id="workspace-container">
      <slot />
    </div>
  </div>
{/if}
