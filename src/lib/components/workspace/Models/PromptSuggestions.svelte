<script lang="ts">
  import { getContext } from 'svelte';
  import { saveAs } from 'file-saver';
  import { toast } from 'svelte-sonner';
  import Plus from '$lib/components/icons/Plus.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  const i18n = getContext('i18n');

  export let promptSuggestions = [];

  let _promptSuggestions = [];

  const setPromptSuggestions = () => {
    _promptSuggestions = promptSuggestions.map((s) => {
      if (typeof s.title === 'string') {
        s.title = [s.title, ''];
      } else if (!Array.isArray(s.title)) {
        s.title = ['', ''];
      }
      return s;
    });
  };

  $: if (promptSuggestions) {
    setPromptSuggestions();
  }
</script>

<div class=" space-y-3">
  <div class="mb-1.5 flex w-full justify-between">
    <div class=" w-full flex-1 shrink-0 self-center text-xs">
      {$i18n.t('Default Prompt Suggestions')}
    </div>

    <div class="flex justify-end gap-2">
      <input
        id="prompt-suggestions-import-input"
        type="file"
        accept=".json"
        hidden
        on:change={(e) => {
          const files = e.target.files;
          if (!files || files.length === 0) {
            return;
          }

          console.log(files);

          let reader = new FileReader();
          reader.onload = async (event) => {
            try {
              let suggestions = JSON.parse(event.target.result);

              suggestions = suggestions.map((s) => {
                if (typeof s.title === 'string') {
                  s.title = [s.title, ''];
                } else if (!Array.isArray(s.title)) {
                  s.title = ['', ''];
                }

                return s;
              });

              promptSuggestions = [...promptSuggestions, ...suggestions];
            } catch (error) {
              toast.error($i18n.t('Invalid JSON file'));
              return;
            }
          };

          reader.readAsText(files[0]);

          e.target.value = ''; // Reset the input value
        }}
      />

      <button
        class="flex items-center space-x-1 rounded-xl bg-transparent py-1 text-xs transition dark:text-gray-200"
        type="button"
        on:click={() => {
          const input = document.getElementById('prompt-suggestions-import-input');
          if (input) {
            input.click();
          }
        }}
      >
        <div class=" line-clamp-1 self-center font-medium">
          {$i18n.t('Import')}
        </div>
      </button>

      {#if promptSuggestions.length}
        <button
          class="flex items-center space-x-1 rounded-xl bg-transparent py-1 text-xs transition dark:text-gray-200"
          type="button"
          on:click={async () => {
            let blob = new Blob([JSON.stringify(promptSuggestions)], {
              type: 'application/json',
            });
            saveAs(blob, `prompt-suggestions-export-${Date.now()}.json`);
          }}
        >
          <div class=" line-clamp-1 self-center font-medium">
            {$i18n.t('Export')}
          </div>
        </button>
      {/if}

      <button
        class=" flex items-center rounded-xl px-1.5 text-sm font-medium transition"
        type="button"
        on:click={() => {
          if (promptSuggestions.length === 0 || promptSuggestions.at(-1).content !== '') {
            promptSuggestions = [...promptSuggestions, { content: '', title: ['', ''] }];
          }
        }}
      >
        <Plus className="size-3" strokeWidth="2.5" />
      </button>
    </div>
  </div>

  {#if _promptSuggestions.length > 0}
    <div class="flex flex-col gap-2">
      {#each _promptSuggestions as prompt, promptIdx}
        <div
          class=" dark:border-gray-850/30 flex rounded-2xl border border-gray-100/30 bg-transparent p-2"
        >
          <div class="flex w-full flex-col gap-1 px-2 md:flex-row md:gap-2">
            <div class="min-w-60 gap-0.5">
              <Tooltip content={$i18n.t('e.g. Tell me a fun fact')} placement="top-start">
                <input
                  class="w-full bg-transparent text-sm outline-hidden"
                  placeholder={$i18n.t('Title')}
                  bind:value={prompt.title[0]}
                />
              </Tooltip>

              <Tooltip content={$i18n.t('e.g. about the Roman Empire')} placement="top-start">
                <input
                  class="w-full bg-transparent text-sm text-gray-600 outline-hidden dark:text-gray-400"
                  placeholder={$i18n.t('Subtitle')}
                  bind:value={prompt.title[1]}
                />
              </Tooltip>
            </div>

            <Tooltip
              className="w-full self-center items-center flex"
              content={$i18n.t('e.g. Tell me a fun fact about the Roman Empire')}
              placement="top-start"
            >
              <textarea
                class="w-full resize-none bg-transparent text-sm outline-hidden"
                placeholder={$i18n.t('Prompt')}
                rows="2"
                bind:value={prompt.content}
              />
            </Tooltip>
          </div>

          <button
            class="self-start p-1"
            type="button"
            on:click={() => {
              promptSuggestions.splice(promptIdx, 1);
              promptSuggestions = promptSuggestions;
            }}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
              class="h-4 w-4"
            >
              <path
                d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
              />
            </svg>
          </button>
        </div>
      {/each}
    </div>
  {:else}
    <div class="mb-1.5 w-full text-center text-xs text-gray-500">
      {$i18n.t('No suggestion prompts')}
    </div>
  {/if}
</div>
