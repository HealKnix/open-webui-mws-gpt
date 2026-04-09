<script>
  import { toast } from 'svelte-sonner';

  import { createEventDispatcher, getContext, onMount } from 'svelte';
  const i18n = getContext('i18n');
  const dispatch = createEventDispatcher();

  import { models, config as _config } from '$lib/stores';
  import { DEFAULT_CAPABILITIES } from '$lib/constants';
  import { deleteAllModels } from '$lib/apis/models';
  import { getModelsConfig, setModelsConfig, setDefaultPromptSuggestions } from '$lib/apis/configs';
  import { getBackendConfig } from '$lib/apis';

  import Modal from '$lib/components/common/Modal.svelte';
  import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import ModelList from './ModelList.svelte';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import Minus from '$lib/components/icons/Minus.svelte';
  import Plus from '$lib/components/icons/Plus.svelte';
  import ChevronUp from '$lib/components/icons/ChevronUp.svelte';
  import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';
  import ModelSelector from './ModelSelector.svelte';
  import Model from '../Evaluations/Model.svelte';
  import AdvancedParams from '$lib/components/chat/Settings/Advanced/AdvancedParams.svelte';

  import Capabilities from '$lib/components/workspace/Models/Capabilities.svelte';
  import DefaultFeatures from '$lib/components/workspace/Models/DefaultFeatures.svelte';
  import BuiltinTools from '$lib/components/workspace/Models/BuiltinTools.svelte';
  import PromptSuggestions from '$lib/components/workspace/Models/PromptSuggestions.svelte';

  import AdjustmentsHorizontal from '$lib/components/icons/AdjustmentsHorizontal.svelte';
  import Eye from '$lib/components/icons/Eye.svelte';

  export let show = false;
  export let initHandler = () => {};

  let config = null;

  let selectedTab = 'defaults';

  let selectedModelId = '';
  let defaultModelIds = [];

  let selectedPinnedModelId = '';
  let defaultPinnedModelIds = [];

  let modelIds = [];

  let sortKey = '';
  let sortOrder = '';

  let loading = false;
  let showResetModal = false;
  let showDefaultCapabilities = false;
  let showDefaultParams = false;
  let showDefaultPromptSuggestions = false;

  let defaultCapabilities = {};
  let defaultFeatureIds = [];
  let defaultParams = {};
  let builtinTools = {};
  let promptSuggestions = [];

  $: if (show) {
    init();
  }
  const init = async () => {
    config = await getModelsConfig(localStorage.token);

    if (config?.DEFAULT_MODELS) {
      defaultModelIds = (config?.DEFAULT_MODELS).split(',').filter((id) => id);
    } else {
      defaultModelIds = [];
    }

    if (config?.DEFAULT_PINNED_MODELS) {
      defaultPinnedModelIds = (config?.DEFAULT_PINNED_MODELS).split(',').filter((id) => id);
    } else {
      defaultPinnedModelIds = [];
    }

    const modelOrderList = config.MODEL_ORDER_LIST || [];
    const allModelIds = $models.map((model) => model.id);

    // Create a Set for quick lookup of ordered IDs
    const orderedSet = new Set(modelOrderList);

    modelIds = [
      // Add all IDs from MODEL_ORDER_LIST that exist in allModelIds
      ...modelOrderList.filter((id) => orderedSet.has(id) && allModelIds.includes(id)),
      // Add remaining IDs not in MODEL_ORDER_LIST, sorted alphabetically
      ...allModelIds.filter((id) => !orderedSet.has(id)).sort((a, b) => a.localeCompare(b)),
    ];

    sortKey = '';
    sortOrder = '';

    const savedMeta = config?.DEFAULT_MODEL_METADATA;
    if (savedMeta && Object.keys(savedMeta).length > 0) {
      defaultCapabilities = savedMeta.capabilities ?? { ...DEFAULT_CAPABILITIES };
      defaultFeatureIds = savedMeta.defaultFeatureIds ?? [];
      builtinTools = savedMeta.builtinTools ?? {};
    } else {
      defaultCapabilities = { ...DEFAULT_CAPABILITIES };
      defaultFeatureIds = [];
      builtinTools = {};
    }
    defaultParams = config?.DEFAULT_MODEL_PARAMS ?? {};

    promptSuggestions = $_config?.default_prompt_suggestions ?? [];
  };
  const submitHandler = async () => {
    loading = true;

    const metadata = {
      capabilities: defaultCapabilities,
      ...(defaultFeatureIds.length > 0 ? { defaultFeatureIds } : {}),
      ...(Object.keys(builtinTools).length > 0 ? { builtinTools } : {}),
    };

    const res = await setModelsConfig(localStorage.token, {
      DEFAULT_MODELS: defaultModelIds.join(','),
      DEFAULT_PINNED_MODELS: defaultPinnedModelIds.join(','),
      MODEL_ORDER_LIST: modelIds,
      DEFAULT_MODEL_METADATA: metadata,
      DEFAULT_MODEL_PARAMS: Object.fromEntries(
        Object.entries(defaultParams).filter(([_, v]) => v !== null && v !== '' && v !== undefined),
      ),
    });

    if (res) {
      promptSuggestions = promptSuggestions.filter((p) => p.content !== '');
      promptSuggestions = await setDefaultPromptSuggestions(localStorage.token, promptSuggestions);
      await _config.set(await getBackendConfig());

      toast.success($i18n.t('Models configuration saved successfully'));
      initHandler();
      show = false;
    } else {
      toast.error($i18n.t('Failed to save models configuration'));
    }

    loading = false;
  };

  onMount(async () => {
    init();
  });
</script>

<ConfirmDialog
  title={$i18n.t('Reset All Models')}
  message={$i18n.t('This will delete all models including custom models and cannot be undone.')}
  bind:show={showResetModal}
  onConfirm={async () => {
    const res = deleteAllModels(localStorage.token);
    if (res) {
      toast.success($i18n.t('All models deleted successfully'));
      initHandler();
    }
  }}
/>

<Modal size="lg" bind:show>
  <div>
    <div class=" flex justify-between px-5 pt-4 pb-2 dark:text-gray-100">
      <div class=" font-primary self-center text-lg font-medium">
        {$i18n.t('Settings')}
      </div>
      <button
        class="self-center"
        on:click={() => {
          show = false;
        }}
      >
        <XMark className={'size-5'} />
      </button>
    </div>

    <div class="flex w-full flex-col px-4 pb-4 md:flex-row md:space-x-4 dark:text-gray-200">
      <div class=" flex w-full flex-col sm:flex-row sm:justify-center sm:space-x-6">
        {#if config}
          <form
            class="flex w-full flex-col"
            on:submit|preventDefault={() => {
              submitHandler();
            }}
          >
            <div class="flex h-full w-full flex-col pb-2 lg:flex-row lg:space-x-4">
              <div
                id="admin-settings-tabs-container"
                class="tabs scrollbar-none flex max-w-full flex-row gap-2.5 overflow-x-auto text-left text-sm font-medium lg:w-40 lg:flex-none lg:flex-col lg:gap-1 dark:text-gray-200"
              >
                <button
                  class="flex w-fit max-w-fit flex-1 rounded-lg px-0.5 py-1 text-right transition lg:flex-none {selectedTab ===
                  'defaults'
                    ? ''
                    : ' text-gray-300 hover:text-gray-700 dark:text-gray-600 dark:hover:text-white'}"
                  on:click={() => {
                    selectedTab = 'defaults';
                  }}
                  type="button"
                >
                  <div class=" mr-2 self-center">
                    <AdjustmentsHorizontal />
                  </div>
                  <div class=" self-center">{$i18n.t('Defaults')}</div>
                </button>

                <button
                  class="flex w-fit max-w-fit flex-1 rounded-lg px-0.5 py-1 text-right transition lg:flex-none {selectedTab ===
                  'display'
                    ? ''
                    : ' text-gray-300 hover:text-gray-700 dark:text-gray-600 dark:hover:text-white'}"
                  on:click={() => {
                    selectedTab = 'display';
                  }}
                  type="button"
                >
                  <div class=" mr-2 self-center">
                    <Eye />
                  </div>
                  <div class=" self-center">{$i18n.t('Display')}</div>
                </button>
              </div>

              <div class="mt-1 flex min-w-0 flex-1 flex-col lg:mt-1 lg:h-[30rem] lg:max-h-[30rem]">
                <div class="scrollbar-hidden h-full w-full overflow-x-hidden overflow-y-auto">
                  {#if selectedTab === 'defaults'}
                    <ModelSelector
                      title={$i18n.t('Selected Models')}
                      tooltip={$i18n.t(
                        'Set the default models that are automatically selected for all users when a new chat is created.',
                      )}
                      models={$models}
                      bind:modelIds={defaultModelIds}
                    />

                    <hr class=" my-2.5 w-full border-gray-50 dark:border-gray-800/10" />

                    <ModelSelector
                      title={$i18n.t('Pinned Models')}
                      tooltip={$i18n.t(
                        'Set the models that are automatically pinned to the sidebar for all users.',
                      )}
                      models={$models}
                      bind:modelIds={defaultPinnedModelIds}
                    />

                    <hr class=" my-2.5 w-full border-gray-50 dark:border-gray-800/10" />

                    <div>
                      <button
                        class="flex w-full items-center justify-between"
                        type="button"
                        on:click={() => {
                          showDefaultPromptSuggestions = !showDefaultPromptSuggestions;
                        }}
                      >
                        <div class="text-xs font-medium text-gray-500">
                          {$i18n.t('Prompt Suggestions')}
                        </div>
                        <div>
                          {#if showDefaultPromptSuggestions}
                            <ChevronUp className="size-3" />
                          {:else}
                            <ChevronDown className="size-3" />
                          {/if}
                        </div>
                      </button>

                      {#if showDefaultPromptSuggestions}
                        <div class="mt-2">
                          <PromptSuggestions bind:promptSuggestions />

                          {#if promptSuggestions.length > 0}
                            <div class="mt-2 w-full text-left text-xs text-gray-500">
                              {$i18n.t(
                                'Adjusting these settings will apply changes universally to all users.',
                              )}
                            </div>
                          {/if}
                        </div>
                      {/if}
                    </div>

                    <hr class=" my-2.5 w-full border-gray-50 dark:border-gray-800/10" />

                    <div>
                      <button
                        class="flex w-full items-center justify-between"
                        type="button"
                        on:click={() => {
                          showDefaultCapabilities = !showDefaultCapabilities;
                        }}
                      >
                        <div class="text-xs font-medium text-gray-500">
                          {$i18n.t('Model Capabilities')}
                        </div>
                        <div>
                          {#if showDefaultCapabilities}
                            <ChevronUp className="size-3" />
                          {:else}
                            <ChevronDown className="size-3" />
                          {/if}
                        </div>
                      </button>

                      {#if showDefaultCapabilities}
                        <div class="mt-2">
                          <Capabilities bind:capabilities={defaultCapabilities} />

                          {#if Object.keys(defaultCapabilities).filter((key) => defaultCapabilities[key]).length > 0}
                            {@const availableFeatures = Object.entries(defaultCapabilities)
                              .filter(
                                ([key, value]) =>
                                  value &&
                                  ['web_search', 'code_interpreter', 'image_generation'].includes(
                                    key,
                                  ),
                              )
                              .map(([key, value]) => key)}

                            {#if availableFeatures.length > 0}
                              <div class="mt-4">
                                <DefaultFeatures
                                  {availableFeatures}
                                  bind:featureIds={defaultFeatureIds}
                                />
                              </div>
                            {/if}
                          {/if}

                          {#if defaultCapabilities.builtin_tools}
                            <div class="mt-4">
                              <BuiltinTools bind:builtinTools />
                            </div>
                          {/if}
                        </div>
                      {/if}
                    </div>

                    <hr class=" my-2.5 w-full border-gray-50 dark:border-gray-800/10" />

                    <div>
                      <button
                        class="flex w-full items-center justify-between"
                        type="button"
                        on:click={() => {
                          showDefaultParams = !showDefaultParams;
                        }}
                      >
                        <div class="text-xs font-medium text-gray-500">
                          {$i18n.t('Model Parameters')}
                        </div>
                        <div>
                          {#if showDefaultParams}
                            <ChevronUp className="size-3" />
                          {:else}
                            <ChevronDown className="size-3" />
                          {/if}
                        </div>
                      </button>

                      {#if showDefaultParams}
                        <div class="mt-2">
                          <AdvancedParams admin={true} bind:params={defaultParams} />
                        </div>
                      {/if}
                    </div>
                  {:else if selectedTab === 'display'}
                    <div>
                      <div class="flex w-full flex-col">
                        <button
                          class="mb-1 flex gap-2"
                          type="button"
                          on:click={() => {
                            sortKey = 'model';

                            if (sortOrder === 'asc') {
                              sortOrder = 'desc';
                            } else {
                              sortOrder = 'asc';
                            }

                            modelIds = modelIds
                              .filter((id) => id !== '')
                              .sort((a, b) => {
                                const nameA = $models.find((model) => model.id === a)?.name || a;
                                const nameB = $models.find((model) => model.id === b)?.name || b;
                                return sortOrder === 'desc'
                                  ? nameA.localeCompare(nameB)
                                  : nameB.localeCompare(nameA);
                              });
                          }}
                        >
                          <div class="text-xs text-gray-500">{$i18n.t('Reorder Models')}</div>

                          {#if sortKey === 'model'}
                            <span class="self-center font-normal">
                              {#if sortOrder === 'asc'}
                                <ChevronUp className="size-3" />
                              {:else}
                                <ChevronDown className="size-3" />
                              {/if}
                            </span>
                          {:else}
                            <span class="invisible">
                              <ChevronUp className="size-3" />
                            </span>
                          {/if}
                        </button>

                        <ModelList bind:modelIds />
                      </div>
                    </div>
                  {/if}
                </div>

                <div class="flex items-center justify-between gap-1.5 pt-3 text-sm font-medium">
                  <div>
                    <Tooltip
                      content={$i18n.t('This will delete all models including custom models')}
                    >
                      <button
                        class="text-sm font-normal text-gray-500 transition hover:text-gray-700 hover:underline dark:text-gray-500 dark:hover:text-gray-300"
                        type="button"
                        on:click={() => {
                          showResetModal = true;
                        }}
                      >
                        {$i18n.t('Reset')}
                      </button>
                    </Tooltip>
                  </div>
                  <button
                    class="flex items-center gap-2 rounded-full bg-black px-3.5 py-1.5 text-sm font-medium whitespace-nowrap text-white transition hover:bg-gray-900 dark:bg-white dark:text-black dark:hover:bg-gray-100 {loading
                      ? ' cursor-not-allowed'
                      : ''}"
                    type="submit"
                    disabled={loading}
                  >
                    {$i18n.t('Save')}

                    {#if loading}
                      <span class="shrink-0">
                        <Spinner />
                      </span>
                    {/if}
                  </button>
                </div>
              </div>
            </div>
          </form>
        {:else}
          <div>
            <Spinner className="size-5" />
          </div>
        {/if}
      </div>
    </div>
  </div>
</Modal>
