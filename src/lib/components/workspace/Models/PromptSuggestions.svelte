<script lang="ts">
  import { getContext } from 'svelte';
  import { saveAs } from 'file-saver';
  import { toast } from 'svelte-sonner';
  import Plus from '$lib/components/icons/Plus.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Input from '$lib/components/common/Input.svelte';
  import Textarea from '$lib/components/common/Textarea.svelte';
  import Button from '$lib/components/common/Button.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';
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

<div class="bg-card space-y-3 rounded-2xl p-2">
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

      <Button
        variant="flat"
        size="xs"
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
      </Button>

      {#if promptSuggestions.length}
        <Button
          variant="flat"
          size="xs"
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
        </Button>
      {/if}

      <Button
        size="xs"
        on:click={() => {
          if (promptSuggestions.length === 0 || promptSuggestions.at(-1).content !== '') {
            promptSuggestions = [...promptSuggestions, { content: '', title: ['', ''] }];
          }
        }}
      >
        <Plus className="size-3" strokeWidth="2.5" />
      </Button>
    </div>
  </div>

  {#if _promptSuggestions.length > 0}
    <div class="*:not-last:border-foreground/15 flex flex-col *:not-last:border-b">
      {#each _promptSuggestions as prompt, promptIdx}
        <div class="flex bg-transparent py-2">
          <div class="flex w-full flex-col gap-3 px-2 md:flex-row md:items-center">
            <p class="text-xs text-nowrap">
              #{promptIdx + 1}
            </p>

            <div class="flex min-w-60 flex-col gap-3">
              <Tooltip content={$i18n.t('e.g. Tell me a fun fact')} placement="top-start">
                <Input placeholder={$i18n.t('Title')} bind:value={prompt.title[0]} />
              </Tooltip>

              <Tooltip content={$i18n.t('e.g. about the Roman Empire')} placement="top-start">
                <Input placeholder={$i18n.t('Subtitle')} bind:value={prompt.title[1]} />
              </Tooltip>
            </div>

            <Tooltip
              className="w-full self-center items-center flex"
              content={$i18n.t('e.g. Tell me a fun fact about the Roman Empire')}
              placement="top-start"
            >
              <Textarea placeholder={$i18n.t('Prompt')} rows="4" bind:value={prompt.content} />
            </Tooltip>
          </div>

          <Button
            isIconOnly
            variant="ghost"
            size="xs"
            on:click={() => {
              promptSuggestions.splice(promptIdx, 1);
              promptSuggestions = promptSuggestions;
            }}
          >
            <XMark className="size-4" />
          </Button>
        </div>
      {/each}
    </div>
  {:else}
    <div class="mb-1.5 w-full text-center text-xs text-gray-500">
      {$i18n.t('No suggestion prompts')}
    </div>
  {/if}
</div>
