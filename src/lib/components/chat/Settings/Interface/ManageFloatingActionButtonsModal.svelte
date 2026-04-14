<script lang="ts">
  import { toast } from 'svelte-sonner';
  import { getContext, onMount } from 'svelte';
  const i18n = getContext('i18n');

  import Modal from '$lib/components/common/Modal.svelte';
  import Plus from '$lib/components/icons/Plus.svelte';
  import Minus from '$lib/components/icons/Minus.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';
  import Textarea from '$lib/components/common/Textarea.svelte';
  import Switch from '$lib/components/common/Switch.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';

  export let show = false;
  export let onSave = () => {};

  export let floatingActionButtons = null;

  const submitHandler = async () => {
    onSave(floatingActionButtons);
    show = false;
  };

  $: if (show) {
  }

  onMount(() => {});
</script>

<Modal size="sm" bind:show>
  <div>
    <div class=" flex justify-between px-5 pt-4 pb-1.5 dark:text-gray-100">
      <h1 class="font-primary self-center text-lg font-medium">
        {$i18n.t('Quick Actions')}
      </h1>
      <button
        class="self-center"
        aria-label={$i18n.t('Close modal')}
        on:click={() => {
          show = false;
        }}
      >
        <XMark className={'size-5'} />
      </button>
    </div>

    <div class="flex w-full flex-col px-4 pb-4 md:flex-row md:space-x-4 dark:text-gray-200">
      <div class=" flex w-full flex-col sm:flex-row sm:justify-center sm:space-x-6">
        <form
          class="flex w-full flex-col px-1"
          on:submit={(e) => {
            e.preventDefault();
            submitHandler();
          }}
        >
          <div>
            <div class="mb-2 flex items-center justify-between text-xs">
              <div class="font-medium">{$i18n.t('Actions')}</div>

              <div class="flex items-center gap-2 text-gray-700 dark:text-gray-300">
                <button
                  type="button"
                  on:click={() => {
                    if (floatingActionButtons === null) {
                      floatingActionButtons = [
                        {
                          id: 'ask',
                          label: $i18n.t('Ask'),
                          input: true,
                          prompt: `{{SELECTED_CONTENT}}\n\n\n{{INPUT_CONTENT}}`,
                        },
                        {
                          id: 'explain',
                          label: $i18n.t('Explain'),
                          input: false,
                          prompt: `{{SELECTED_CONTENT}}\n\n\n${$i18n.t('Explain')}`,
                        },
                      ];
                    } else {
                      floatingActionButtons = null;
                    }
                  }}
                >
                  {#if floatingActionButtons === null}
                    <span class="">{$i18n.t('Default')}</span>
                  {:else}
                    <span class="">{$i18n.t('Custom')}</span>
                  {/if}
                </button>

                {#if floatingActionButtons !== null}
                  <button
                    class=""
                    type="button"
                    on:click={() => {
                      let id = `new-button`;
                      let idx = 0;

                      while (floatingActionButtons.some((b) => b.id === id)) {
                        idx++;
                        id = `new-button-${idx}`;
                      }

                      floatingActionButtons = [
                        ...floatingActionButtons,
                        {
                          id: id,
                          label: `${$i18n.t('New Button')}`,
                          input: true,
                          prompt: `{{CONTENT}}\n\n\n{{INPUT_CONTENT}}`,
                        },
                      ];
                    }}
                  >
                    <Plus className="size-4 " />
                  </button>
                {/if}
              </div>
            </div>

            {#if floatingActionButtons === null || floatingActionButtons.length === 0}
              <div class="w-full py-5 text-center text-xs text-gray-500 dark:text-gray-400">
                {$i18n.t('Default action buttons will be used.')}
              </div>
            {:else}
              {#each floatingActionButtons as button, buttonIdx}
                <div class=" flex w-full items-start justify-between py-1">
                  <div class="flex flex-col items-start pr-2">
                    <input
                      class=" w-20 self-center text-xs outline-none"
                      placeholder={$i18n.t('Button Label')}
                      aria-label={$i18n.t('Button Label')}
                      bind:value={button.label}
                    />

                    <input
                      class=" w-20 self-center text-xs text-gray-600 outline-none dark:text-gray-400"
                      placeholder={$i18n.t('Button ID')}
                      aria-label={$i18n.t('Button ID')}
                      bind:value={button.id}
                    />
                  </div>

                  <div class="flex w-full items-center gap-2">
                    <Textarea
                      className=" self-center text-xs w-full outline-none"
                      placeholder={$i18n.t('Button Prompt')}
                      ariaLabel={$i18n.t('Button Prompt')}
                      minSize={30}
                      bind:value={button.prompt}
                    />
                  </div>
                  <button
                    class="flex rounded-sm pl-3 text-xs transition"
                    aria-label={$i18n.t('Remove action')}
                    on:click={() => {
                      floatingActionButtons = floatingActionButtons.filter(
                        (b) => b.id !== button.id,
                      );
                    }}
                    type="button"
                  >
                    <Minus className="h-4 w-4" />
                  </button>
                </div>

                <hr class="dark:border-gray-850/30 my-2 border-gray-50" />
              {/each}
            {/if}
          </div>

          <div class="flex justify-end text-sm font-medium">
            <button
              class="rounded-full bg-black px-3.5 py-1.5 text-sm font-medium text-white transition hover:bg-gray-900 dark:bg-white dark:text-black dark:hover:bg-gray-100"
              type="submit"
            >
              {$i18n.t('Save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</Modal>
