<script lang="ts">
  import type { Banner } from '$lib/types';
  import { onMount, createEventDispatcher, getContext } from 'svelte';
  import { fade } from 'svelte/transition';
  import DOMPurify from 'dompurify';
  import { marked } from 'marked';
  import { WEBUI_BASE_URL } from '$lib/constants';

  const dispatch = createEventDispatcher();
  const i18n = getContext('i18n');

  export let banner: Banner = {
    id: '',
    type: 'info',
    title: '',
    content: '',
    url: '',
    dismissible: true,
    timestamp: Math.floor(Date.now() / 1000),
  };
  export let className = 'mx-2 px-2 rounded-lg';

  export let dismissed = false;

  let mounted = false;

  const classNames: Record<string, string> = {
    info: 'bg-blue-500/20 text-blue-700 dark:text-blue-200 ',
    success: 'bg-green-500/20 text-green-700 dark:text-green-200',
    warning: 'bg-yellow-500/20 text-yellow-700 dark:text-yellow-200',
    error: 'bg-red-500/20 text-red-700 dark:text-red-200',
  };

  const dismiss = (id) => {
    dismissed = true;
    dispatch('dismiss', id);
  };

  onMount(() => {
    mounted = true;

    console.log('Banner mounted:', banner);
  });
</script>

{#if !dismissed}
  {#if mounted}
    <div
      class="{className} dark:text-gary-100 relative top-0 right-0 left-0 z-30 flex items-center justify-center border border-transparent bg-transparent py-1 text-gray-800 backdrop-blur-xl"
      transition:fade={{ delay: 100, duration: 300 }}
    >
      <div class=" flex w-fit flex-1 flex-col gap-1.5 text-sm md:flex-row md:items-center">
        <div class="flex justify-between self-start">
          <div
            class=" text-xs font-semibold {classNames[banner.type] ??
              classNames['info']}  mr-0.5 line-clamp-1 w-fit rounded-sm px-2 uppercase"
          >
            {#if banner.type.toLowerCase() === 'info'}
              {$i18n.t('Info')}
            {:else if banner.type.toLowerCase() === 'warning'}
              {$i18n.t('Warning')}
            {:else if banner.type.toLowerCase() === 'error'}
              {$i18n.t('Error')}
            {:else if banner.type.toLowerCase() === 'success'}
              {$i18n.t('Success')}
            {:else}
              {banner.type}
            {/if}
          </div>

          {#if banner.url}
            <div class="group flex w-fit md:hidden md:items-center">
              <a
                class="text-xs font-semibold text-gray-700 underline dark:text-white"
                href="{WEBUI_BASE_URL}/assets/files/whitepaper.pdf"
                target="_blank"
              >
                {$i18n.t('Learn More')}
              </a>

              <div
                class=" ml-1 text-gray-400 group-hover:text-gray-600 dark:group-hover:text-white"
              >
                <!--  -->
                <svg
                  aria-hidden="true"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 16 16"
                  fill="currentColor"
                  class="h-4 w-4"
                >
                  <path
                    fill-rule="evenodd"
                    d="M4.22 11.78a.75.75 0 0 1 0-1.06L9.44 5.5H5.75a.75.75 0 0 1 0-1.5h5.5a.75.75 0 0 1 .75.75v5.5a.75.75 0 0 1-1.5 0V6.56l-5.22 5.22a.75.75 0 0 1-1.06 0Z"
                    clip-rule="evenodd"
                  />
                </svg>
              </div>
            </div>
          {/if}
        </div>
        <div class="max-h-60 flex-1 overflow-y-auto text-xs text-gray-700 dark:text-white">
          {@html DOMPurify.sanitize(marked.parse((banner?.content ?? '').replace(/\n/g, '<br>')))}
        </div>
      </div>

      {#if banner.url}
        <div class="group hidden w-fit md:flex md:items-center">
          <a
            class="text-xs font-semibold text-gray-700 underline dark:text-white"
            href="/"
            target="_blank"
          >
            {$i18n.t('Learn More')}
          </a>

          <div class=" ml-1 text-gray-400 group-hover:text-gray-600 dark:group-hover:text-white">
            <!--  -->
            <svg
              aria-hidden="true"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 16 16"
              fill="currentColor"
              class="size-4"
            >
              <path
                fill-rule="evenodd"
                d="M4.22 11.78a.75.75 0 0 1 0-1.06L9.44 5.5H5.75a.75.75 0 0 1 0-1.5h5.5a.75.75 0 0 1 .75.75v5.5a.75.75 0 0 1-1.5 0V6.56l-5.22 5.22a.75.75 0 0 1-1.06 0Z"
                clip-rule="evenodd"
              />
            </svg>
          </div>
        </div>
      {/if}
      <div class="flex self-start">
        <button
          aria-label={$i18n.t('Close Banner')}
          on:click={() => {
            dismiss(banner.id);
          }}
          class="  -mt-1 mr-1 -mb-2 ml-1.5 -translate-y-[1px] text-gray-400 dark:hover:text-white"
          >&times;</button
        >
      </div>
    </div>
  {/if}
{/if}
