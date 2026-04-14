<script lang="ts">
  import DOMPurify from 'dompurify';

  import { onMount, getContext } from 'svelte';
  import { Confetti } from 'svelte-confetti';

  import { WEBUI_NAME, config, settings } from '$lib/stores';

  import { WEBUI_VERSION } from '$lib/constants';
  import { getChangelog } from '$lib/apis';

  import Modal from './common/Modal.svelte';
  import { updateUserSettings } from '$lib/apis/users';
  import XMark from '$lib/components/icons/XMark.svelte';

  const i18n = getContext('i18n');

  export let show = false;

  let changelog = null;

  const init = async () => {
    changelog = await getChangelog();
  };

  const closeModal = async () => {
    localStorage.version = $config.version;
    await settings.set({ ...$settings, ...{ version: $config.version } });
    await updateUserSettings(localStorage.token, { ui: $settings });
    show = false;
  };

  $: if (show) {
    init();
  }
</script>

<Modal bind:show size="xl">
  <div class="px-6 pt-5 text-black dark:text-white">
    <div class="flex items-start justify-between">
      <h2 class="m-0 text-xl font-medium">
        {$i18n.t("What's New in")}
        {$WEBUI_NAME}
        <Confetti x={[-1, -0.25]} y={[0, 0.5]} />
      </h2>
      <button class="self-center" on:click={closeModal} aria-label={$i18n.t('Close')}>
        <XMark className={'size-5'} />
      </button>
    </div>
    <div class="mt-1 flex items-center">
      <div class="text-sm dark:text-gray-200">{$i18n.t('Release Notes')}</div>
      <div class="dark:bg-gray-850/50 mx-2.5 flex h-6 w-[1px] self-center bg-gray-50/50" />
      <div class="text-sm dark:text-gray-200">
        v{WEBUI_VERSION}
      </div>
    </div>
  </div>

  <div class=" w-full p-4 px-5 text-gray-700 dark:text-gray-100">
    <div class=" scrollbar-hidden max-h-[30rem] overflow-y-scroll">
      <div class="mb-3">
        {#if changelog}
          {#each Object.keys(changelog) as version}
            <div class=" mb-3 pr-2">
              <h3 class="m-0 mb-1 text-xl font-semibold dark:text-white">
                v{version} - {changelog[version].date}
              </h3>

              <hr class="dark:border-gray-850/50 my-2 border-gray-50/50" />

              {#each Object.keys(changelog[version]).filter((section) => section !== 'date') as section}
                <div class="w-full">
                  <div
                    class="text-xs font-semibold uppercase {section === 'added'
                      ? 'bg-blue-500/20 text-blue-700 dark:text-blue-200'
                      : section === 'fixed'
                        ? 'bg-green-500/20 text-green-700 dark:text-green-200'
                        : section === 'changed'
                          ? 'bg-yellow-500/20 text-yellow-700 dark:text-yellow-200'
                          : section === 'removed'
                            ? 'bg-red-500/20 text-red-700 dark:text-red-200'
                            : ''}  my-2.5 w-fit rounded-xl px-2"
                  >
                    {section}
                  </div>

                  <div class="markdown-prose-sm my-2.5 !w-full !max-w-none !list-none px-1.5">
                    {#each changelog[version][section] as entry}
                      <div class="my-2">
                        {@html DOMPurify.sanitize(entry?.raw)}
                      </div>
                    {/each}
                  </div>
                </div>
              {/each}
            </div>
          {/each}
        {/if}
      </div>
    </div>
    <div class="flex justify-end pt-3 text-sm font-medium">
      <button
        on:click={closeModal}
        class="rounded-full bg-black px-3.5 py-1.5 text-sm font-medium text-white transition hover:bg-gray-900 dark:bg-white dark:text-black dark:hover:bg-gray-100"
      >
        <span class="relative">{$i18n.t("Okay, Let's Go!")}</span>
      </button>
    </div>
  </div>
</Modal>
