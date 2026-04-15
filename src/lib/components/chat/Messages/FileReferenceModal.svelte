<script lang="ts">
  import DOMPurify from 'dompurify';
  import { getContext, tick } from 'svelte';
  import type { Writable } from 'svelte/store';
  import type { i18n as i18nType } from 'i18next';

  import Modal from '$lib/components/common/Modal.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import PDFViewer from '$lib/components/common/PDFViewer.svelte';
  import Markdown from '$lib/components/chat/Messages/Markdown.svelte';

  import type { FileReferenceType } from '$lib/utils/extractFileReferences';

  const i18n = getContext<Writable<i18nType>>('i18n');

  export let show = false;
  export let name: string;
  export let url: string;
  export let ext: FileReferenceType;

  let loading = false;
  let error = '';
  let mdText = '';
  let docxHtml = '';
  let pptxSlides: string[] = [];
  let pptxCurrent = 0;

  let loadedFor = '';

  const reset = () => {
    error = '';
    mdText = '';
    docxHtml = '';
    pptxSlides = [];
    pptxCurrent = 0;
  };

  const fetchBuffer = async (): Promise<ArrayBuffer> => {
    const res = await fetch(url, { credentials: 'include' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.arrayBuffer();
  };

  const load = async () => {
    const key = `${ext}::${url}`;
    if (loadedFor === key) return;
    loadedFor = key;
    reset();

    if (ext === 'pdf') return;

    loading = true;
    try {
      if (ext === 'md') {
        const res = await fetch(url, { credentials: 'include' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        mdText = await res.text();
      } else if (ext === 'docx') {
        const [buffer, mammoth] = await Promise.all([fetchBuffer(), import('mammoth')]);
        const result = await mammoth.convertToHtml({ arrayBuffer: buffer });
        docxHtml = DOMPurify.sanitize(result.value);
      } else if (ext === 'pptx') {
        const [buffer, { pptxToImages }] = await Promise.all([
          fetchBuffer(),
          import('$lib/utils/pptxToHtml'),
        ]);
        const result = await pptxToImages(buffer);
        pptxSlides = result.images;
      }
    } catch (e) {
      console.error('FileReferenceModal load error:', e);
      error = $i18n.t('Failed to load file. Please try downloading it instead.');
    } finally {
      loading = false;
      await tick();
    }
  };

  $: if (show && url) {
    load();
  }

  $: if (!show) {
    loadedFor = '';
  }
</script>

<Modal bind:show size="lg">
  <div class="font-primary flex w-full flex-col justify-center px-4.5 py-3.5 dark:text-gray-400">
    <div class="pb-2">
      <div class="flex items-start justify-between">
        <div class="min-w-0 flex-1">
          <div class="text-lg font-medium dark:text-gray-100">
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              class="line-clamp-1 hover:underline"
            >
              {name}
            </a>
          </div>
          <div class="text-xs text-gray-500 capitalize">{ext}</div>
        </div>

        <button
          class="ml-2 shrink-0"
          on:click={() => {
            show = false;
          }}
          aria-label="Close"
        >
          <XMark />
        </button>
      </div>
    </div>

    <div class="max-h-[75vh] overflow-auto">
      {#if loading}
        <div class="flex items-center justify-center py-8">
          <Spinner className="size-5" />
        </div>
      {:else if error}
        <div class="p-4 text-sm text-red-500">{error}</div>
      {:else if ext === 'pdf'}
        <PDFViewer {url} className="w-full h-[70vh] border-0 rounded-lg" />
      {:else if ext === 'md'}
        <div
          class="scrollbar-hidden prose dark:prose-invert max-h-[70vh] max-w-full overflow-scroll text-sm"
        >
          <Markdown content={mdText} id="file-ref-md-{url}" />
        </div>
      {:else if ext === 'docx'}
        <div
          class="office-preview prose dark:prose-invert max-h-[70vh] max-w-full overflow-auto p-4 text-sm"
        >
          {@html docxHtml}
        </div>
      {:else if ext === 'pptx'}
        {#if pptxSlides.length > 0}
          <div class="max-h-[70vh] overflow-auto">
            <div class="flex justify-center p-4">
              <img
                src={pptxSlides[pptxCurrent]}
                alt="Slide {pptxCurrent + 1}"
                class="max-h-[55vh] max-w-full rounded-md object-contain shadow-lg"
                draggable="false"
              />
            </div>
            {#if pptxSlides.length > 1}
              <div class="flex items-center justify-center gap-3 pb-3 text-sm text-gray-500">
                <button
                  class="rounded-lg p-1.5 hover:bg-gray-100 disabled:opacity-30 dark:hover:bg-gray-800"
                  disabled={pptxCurrent === 0}
                  on:click={() => (pptxCurrent = Math.max(0, pptxCurrent - 1))}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    class="size-5"
                  >
                    <path
                      fill-rule="evenodd"
                      d="M11.78 5.22a.75.75 0 0 1 0 1.06L8.06 10l3.72 3.72a.75.75 0 1 1-1.06 1.06l-4.25-4.25a.75.75 0 0 1 0-1.06l4.25-4.25a.75.75 0 0 1 1.06 0Z"
                      clip-rule="evenodd"
                    />
                  </svg>
                </button>
                <span>{pptxCurrent + 1} / {pptxSlides.length}</span>
                <button
                  class="rounded-lg p-1.5 hover:bg-gray-100 disabled:opacity-30 dark:hover:bg-gray-800"
                  disabled={pptxCurrent === pptxSlides.length - 1}
                  on:click={() => (pptxCurrent = Math.min(pptxSlides.length - 1, pptxCurrent + 1))}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    class="size-5"
                  >
                    <path
                      fill-rule="evenodd"
                      d="M8.22 5.22a.75.75 0 0 1 1.06 0l4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.75.75 0 0 1-1.06-1.06L11.94 10 8.22 6.28a.75.75 0 0 1 0-1.06Z"
                      clip-rule="evenodd"
                    />
                  </svg>
                </button>
              </div>
            {/if}
          </div>
        {:else}
          <div class="p-4 text-sm text-gray-500">{$i18n.t('No content available')}</div>
        {/if}
      {/if}
    </div>
  </div>
</Modal>
