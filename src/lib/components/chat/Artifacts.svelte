<script lang="ts">
  import { toast } from 'svelte-sonner';
  import { onMount, getContext, createEventDispatcher } from 'svelte';
  const i18n = getContext('i18n');
  const dispatch = createEventDispatcher();

  import {
    artifactCode,
    chatId,
    settings,
    showArtifacts,
    showControls,
    artifactContents,
  } from '$lib/stores';
  import { copyToClipboard, createMessagesList } from '$lib/utils';

  import XMark from '../icons/XMark.svelte';
  import ArrowsPointingOut from '../icons/ArrowsPointingOut.svelte';
  import Tooltip from '../common/Tooltip.svelte';
  import SvgPanZoom from '../common/SVGPanZoom.svelte';
  import ArrowLeft from '../icons/ArrowLeft.svelte';
  import Download from '../icons/Download.svelte';

  export let overlay = false;

  let contents: Array<{ type: string; content: string }> = [];
  let selectedContentIdx = 0;

  let copied = false;
  let iframeElement: HTMLIFrameElement;

  function navigateContent(direction: 'prev' | 'next') {
    selectedContentIdx =
      direction === 'prev'
        ? Math.max(selectedContentIdx - 1, 0)
        : Math.min(selectedContentIdx + 1, contents.length - 1);
  }

  const iframeLoadHandler = () => {
    iframeElement.contentWindow.addEventListener(
      'click',
      function (e) {
        const target = e.target.closest('a');
        if (target && target.href) {
          e.preventDefault();
          const url = new URL(target.href, iframeElement.baseURI);
          if (url.origin === window.location.origin) {
            iframeElement.contentWindow.history.pushState(
              null,
              '',
              url.pathname + url.search + url.hash,
            );
          } else {
            console.info('External navigation blocked:', url.href);
          }
        }
      },
      true,
    );

    // Cancel drag when hovering over iframe
    iframeElement.contentWindow.addEventListener('mouseenter', function (e) {
      e.preventDefault();
      iframeElement.contentWindow.addEventListener('dragstart', (event) => {
        event.preventDefault();
      });
    });
  };

  const showFullScreen = () => {
    if (iframeElement.requestFullscreen) {
      iframeElement.requestFullscreen();
    } else if (iframeElement.webkitRequestFullscreen) {
      iframeElement.webkitRequestFullscreen();
    } else if (iframeElement.msRequestFullscreen) {
      iframeElement.msRequestFullscreen();
    }
  };

  const downloadArtifact = () => {
    const blob = new Blob([contents[selectedContentIdx].content], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `artifact-${$chatId}-${selectedContentIdx}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  onMount(() => {
    const unsubscribeArtifactCode = artifactCode.subscribe((value) => {
      if (contents) {
        const codeIdx = contents.findIndex((content) => content.content.includes(value));
        selectedContentIdx = codeIdx !== -1 ? codeIdx : 0;
      }
    });

    const unsubscribeArtifactContents = artifactContents.subscribe((value) => {
      const newContents = value ?? [];
      console.log('Artifact contents updated:', newContents);

      if (newContents.length === 0) {
        showControls.set(false);
        showArtifacts.set(false);
        selectedContentIdx = 0;
      } else if (newContents.length > contents.length) {
        selectedContentIdx = newContents.length - 1;
      }

      contents = newContents;
    });

    return () => {
      unsubscribeArtifactCode();
      unsubscribeArtifactContents();
    };
  });
</script>

<div
  class=" dark:bg-gray-850 relative flex h-full w-full flex-col bg-white"
  id="artifacts-container"
>
  <div class="relative flex h-full w-full flex-1 flex-col">
    {#if contents.length > 0}
      <div
        class="font-primar pointer-events-auto z-20 flex items-center justify-between p-2.5 text-gray-900 dark:text-white"
      >
        <div class="flex flex-1 items-center justify-between pr-1">
          <div class="flex items-center space-x-2">
            <div class="flex min-w-fit items-center gap-0.5 self-center" dir="ltr">
              <button
                class="self-center rounded-md p-1 transition hover:bg-black/5 hover:text-black disabled:cursor-not-allowed dark:hover:bg-white/5 dark:hover:text-white"
                on:click={() => navigateContent('prev')}
                disabled={contents.length <= 1}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  stroke-width="2.5"
                  class="size-3.5"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M15.75 19.5 8.25 12l7.5-7.5"
                  />
                </svg>
              </button>

              <div class="min-w-fit self-center text-xs dark:text-gray-100">
                {$i18n.t('Version {{selectedVersion}} of {{totalVersions}}', {
                  selectedVersion: selectedContentIdx + 1,
                  totalVersions: contents.length,
                })}
              </div>

              <button
                class="self-center rounded-md p-1 transition hover:bg-black/5 hover:text-black disabled:cursor-not-allowed dark:hover:bg-white/5 dark:hover:text-white"
                on:click={() => navigateContent('next')}
                disabled={contents.length <= 1}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  stroke-width="2.5"
                  class="size-3.5"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="m8.25 4.5 7.5 7.5-7.5 7.5"
                  />
                </svg>
              </button>
            </div>
          </div>

          <div class="flex items-center gap-1.5">
            <button
              class="copy-code-button dark:bg-gray-850 rounded-md border-none bg-gray-50 bg-none px-1.5 py-0.5 text-xs transition hover:bg-gray-100 dark:hover:bg-gray-800"
              on:click={() => {
                copyToClipboard(contents[selectedContentIdx].content);
                copied = true;

                setTimeout(() => {
                  copied = false;
                }, 2000);
              }}>{copied ? $i18n.t('Copied') : $i18n.t('Copy')}</button
            >

            <Tooltip content={$i18n.t('Download')}>
              <button
                class=" dark:bg-gray-850 rounded-md border-none bg-gray-50 bg-none p-0.5 text-xs transition hover:bg-gray-100 dark:hover:bg-gray-800"
                on:click={downloadArtifact}
              >
                <Download className="size-3.5" />
              </button>
            </Tooltip>

            {#if contents[selectedContentIdx].type === 'iframe'}
              <Tooltip content={$i18n.t('Open in full screen')}>
                <button
                  class=" dark:bg-gray-850 rounded-md border-none bg-gray-50 bg-none p-0.5 text-xs transition hover:bg-gray-100 dark:hover:bg-gray-800"
                  on:click={showFullScreen}
                >
                  <ArrowsPointingOut className="size-3.5" />
                </button>
              </Tooltip>
            {/if}
          </div>
        </div>

        <button
          class="dark:bg-gray-850 pointer-events-auto self-center rounded-full bg-white p-1"
          on:click={() => {
            dispatch('close');
            showControls.set(false);
            showArtifacts.set(false);
          }}
        >
          <XMark className="size-3.5 text-gray-900 dark:text-white" />
        </button>
      </div>
    {/if}

    {#if overlay}
      <div class=" absolute top-0 right-0 bottom-0 left-0 z-10"></div>
    {/if}

    <div class="h-full w-full flex-1">
      <div class=" flex h-full flex-col">
        {#if contents.length > 0}
          <div class="h-full w-full max-w-full">
            {#if contents[selectedContentIdx].type === 'iframe'}
              <iframe
                bind:this={iframeElement}
                title="Content"
                srcdoc={contents[selectedContentIdx].content}
                class="h-full w-full rounded-none border-0"
                sandbox="allow-scripts allow-downloads{($settings?.iframeSandboxAllowForms ?? false)
                  ? ' allow-forms'
                  : ''}{($settings?.iframeSandboxAllowSameOrigin ?? false)
                  ? ' allow-same-origin'
                  : ''}"
                on:load={iframeLoadHandler}
              ></iframe>
            {:else if contents[selectedContentIdx].type === 'svg'}
              <SvgPanZoom
                className=" w-full h-full max-h-full overflow-hidden"
                svg={contents[selectedContentIdx].content}
              />
            {/if}
          </div>
        {:else}
          <div class="m-auto text-xs font-medium text-gray-900 dark:text-white">
            {$i18n.t('No HTML, CSS, or JavaScript content found.')}
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>
