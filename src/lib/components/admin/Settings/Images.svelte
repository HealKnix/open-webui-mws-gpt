<script lang="ts">
  import { toast } from 'svelte-sonner';

  import { createEventDispatcher, onMount, getContext } from 'svelte';
  import { config as backendConfig, user } from '$lib/stores';

  import { getBackendConfig } from '$lib/apis';
  import {
    getImageGenerationModels,
    getImageGenerationConfig,
    updateImageGenerationConfig,
    getConfig,
    updateConfig,
    verifyConfigUrl,
  } from '$lib/apis/images';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
  import Switch from '$lib/components/common/Switch.svelte';
  import ToggleSetting from '$lib/components/common/ToggleSetting.svelte';
  import SettingItem from '$lib/components/common/SettingItem.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Textarea from '$lib/components/common/Textarea.svelte';
  import CodeEditorModal from '$lib/components/common/CodeEditorModal.svelte';
  import Button from '$lib/components/common/Button.svelte';
  const dispatch = createEventDispatcher();

  const i18n = getContext('i18n');

  let loading = false;

  let models = null;
  let config = null;

  let showComfyUIWorkflowEditor = false;
  let REQUIRED_WORKFLOW_NODES = [
    {
      type: 'prompt',
      key: 'text',
      node_ids: '',
    },
    {
      type: 'model',
      key: 'ckpt_name',
      node_ids: '',
    },
    {
      type: 'width',
      key: 'width',
      node_ids: '',
    },
    {
      type: 'height',
      key: 'height',
      node_ids: '',
    },
    {
      type: 'steps',
      key: 'steps',
      node_ids: '',
    },
    {
      type: 'seed',
      key: 'seed',
      node_ids: '',
    },
  ];

  let showComfyUIEditWorkflowEditor = false;
  let REQUIRED_EDIT_WORKFLOW_NODES = [
    {
      type: 'image',
      key: 'image',
      node_ids: '',
    },
    {
      type: 'prompt',
      key: 'prompt',
      node_ids: '',
    },
    {
      type: 'model',
      key: 'unet_name',
      node_ids: '',
    },
    {
      type: 'width',
      key: 'width',
      node_ids: '',
    },
    {
      type: 'height',
      key: 'height',
      node_ids: '',
    },
  ];

  const getModels = async () => {
    models = await getImageGenerationModels(localStorage.token).catch((error) => {
      toast.error(`${error}`);
      return null;
    });
  };

  const updateConfigHandler = async () => {
    if (
      config.IMAGE_GENERATION_ENGINE === 'automatic1111' &&
      config.AUTOMATIC1111_BASE_URL === ''
    ) {
      toast.error($i18n.t('AUTOMATIC1111 Base URL is required.'));
      config.ENABLE_IMAGE_GENERATION = false;

      return null;
    } else if (config.IMAGE_GENERATION_ENGINE === 'comfyui' && config.COMFYUI_BASE_URL === '') {
      toast.error($i18n.t('ComfyUI Base URL is required.'));
      config.ENABLE_IMAGE_GENERATION = false;

      return null;
    } else if (config.IMAGE_GENERATION_ENGINE === 'openai' && config.IMAGES_OPENAI_API_KEY === '') {
      toast.error($i18n.t('OpenAI API Key is required.'));
      config.ENABLE_IMAGE_GENERATION = false;

      return null;
    } else if (config.IMAGE_GENERATION_ENGINE === 'gemini' && config.IMAGES_GEMINI_API_KEY === '') {
      toast.error($i18n.t('Gemini API Key is required.'));
      config.ENABLE_IMAGE_GENERATION = false;

      return null;
    }

    const res = await updateConfig(localStorage.token, {
      ...config,
      AUTOMATIC1111_PARAMS:
        typeof config.AUTOMATIC1111_PARAMS === 'string' && config.AUTOMATIC1111_PARAMS.trim() !== ''
          ? JSON.parse(config.AUTOMATIC1111_PARAMS)
          : {},
      IMAGES_OPENAI_API_PARAMS:
        typeof config.IMAGES_OPENAI_API_PARAMS === 'string' &&
        config.IMAGES_OPENAI_API_PARAMS.trim() !== ''
          ? JSON.parse(config.IMAGES_OPENAI_API_PARAMS)
          : {},
    }).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    if (res) {
      if (res.ENABLE_IMAGE_GENERATION) {
        backendConfig.set(await getBackendConfig());
        getModels();
      }

      return res;
    }

    return null;
  };

  const validateJSON = (json) => {
    try {
      const obj = JSON.parse(json);

      if (obj && typeof obj === 'object') {
        return true;
      }
    } catch (e) {}
    return false;
  };

  const saveHandler = async () => {
    loading = true;

    if (config?.COMFYUI_WORKFLOW) {
      if (!validateJSON(config?.COMFYUI_WORKFLOW)) {
        toast.error($i18n.t('Invalid JSON format for ComfyUI Workflow.'));
        loading = false;
        return;
      }

      config.COMFYUI_WORKFLOW_NODES = REQUIRED_WORKFLOW_NODES.map((node) => {
        return {
          type: node.type,
          key: node.key,
          node_ids:
            node.node_ids.trim() === '' ? [] : node.node_ids.split(',').map((id) => id.trim()),
        };
      });
    }

    if (config?.IMAGES_EDIT_COMFYUI_WORKFLOW) {
      if (!validateJSON(config?.IMAGES_EDIT_COMFYUI_WORKFLOW)) {
        toast.error($i18n.t('Invalid JSON format for ComfyUI Edit Workflow.'));
        loading = false;
        return;
      }

      config.IMAGES_EDIT_COMFYUI_WORKFLOW_NODES = REQUIRED_EDIT_WORKFLOW_NODES.map((node) => {
        return {
          type: node.type,
          key: node.key,
          node_ids:
            node.node_ids.trim() === '' ? [] : node.node_ids.split(',').map((id) => id.trim()),
        };
      });
    }

    const res = await updateConfigHandler();
    if (res) {
      dispatch('save');
    }

    loading = false;
  };

  onMount(async () => {
    if ($user?.role === 'admin') {
      const res = await getConfig(localStorage.token).catch((error) => {
        toast.error(`${error}`);
        return null;
      });

      if (res) {
        config = res;
      }

      if (config.ENABLE_IMAGE_GENERATION) {
        getModels();
      }

      if (config.COMFYUI_WORKFLOW) {
        try {
          config.COMFYUI_WORKFLOW = JSON.stringify(JSON.parse(config.COMFYUI_WORKFLOW), null, 2);
        } catch (e) {
          console.error(e);
        }
      }

      REQUIRED_WORKFLOW_NODES = REQUIRED_WORKFLOW_NODES.map((node) => {
        const n = config.COMFYUI_WORKFLOW_NODES.find((n) => n.type === node.type) ?? node;
        console.debug(n);

        return {
          type: n.type,
          key: n.key,
          node_ids: typeof n.node_ids === 'string' ? n.node_ids : n.node_ids.join(','),
        };
      });

      if (config.IMAGES_EDIT_COMFYUI_WORKFLOW) {
        try {
          config.IMAGES_EDIT_COMFYUI_WORKFLOW = JSON.stringify(
            JSON.parse(config.IMAGES_EDIT_COMFYUI_WORKFLOW),
            null,
            2,
          );
        } catch (e) {
          console.error(e);
        }
      }

      config.IMAGES_OPENAI_API_PARAMS =
        typeof config.IMAGES_OPENAI_API_PARAMS === 'object'
          ? JSON.stringify(config.IMAGES_OPENAI_API_PARAMS ?? {}, null, 2)
          : config.IMAGES_OPENAI_API_PARAMS;

      config.AUTOMATIC1111_PARAMS =
        typeof config.AUTOMATIC1111_PARAMS === 'object'
          ? JSON.stringify(config.AUTOMATIC1111_PARAMS ?? {}, null, 2)
          : config.AUTOMATIC1111_PARAMS;

      REQUIRED_EDIT_WORKFLOW_NODES = REQUIRED_EDIT_WORKFLOW_NODES.map((node) => {
        const n =
          config.IMAGES_EDIT_COMFYUI_WORKFLOW_NODES.find((n) => n.type === node.type) ?? node;
        console.debug(n);

        return {
          type: n.type,
          key: n.key,
          node_ids: typeof n.node_ids === 'string' ? n.node_ids : n.node_ids.join(','),
        };
      });
    }
  });
</script>

<form
  class="flex h-full flex-col justify-between space-y-3 text-sm"
  on:submit|preventDefault={async () => {
    saveHandler();
  }}
>
  <div class="scrollbar-hidden space-y-3 overflow-y-scroll p-1">
    {#if config}
      <div class="space-y-1">
        <div
          class="my-2 mb-4 border-b border-gray-300 pb-1 text-base font-medium dark:border-gray-800"
        >
          {$i18n.t('General')}
        </div>

        <ToggleSetting
          label={$i18n.t('Image Generation')}
          bind:state={config.ENABLE_IMAGE_GENERATION}
        />
      </div>

      <div class="space-y-1">
        <div
          class="my-2 mb-4 border-b border-gray-300 pb-1 text-base font-medium dark:border-gray-800"
        >
          {$i18n.t('Create Image')}
        </div>

        {#if config.ENABLE_IMAGE_GENERATION}
          <SettingItem label={$i18n.t('Model')}>
            <Tooltip content={$i18n.t('Enter Model ID')} placement="top-start">
              <input
                list="model-list"
                class=" w-52 max-w-full bg-transparent text-right text-sm outline-hidden"
                bind:value={config.IMAGE_GENERATION_MODEL}
                placeholder={$i18n.t('Select a model')}
                required
              />

              <datalist id="model-list">
                {#each models ?? [] as model}
                  <option value={model.id}>{model.name}</option>
                {/each}
              </datalist>
            </Tooltip>
          </SettingItem>

          <SettingItem label={$i18n.t('Image Size')}>
            <Tooltip content={$i18n.t('Enter Image Size (e.g. 512x512)')} placement="top-start">
              <input
                class="  w-52 max-w-full bg-transparent text-right text-sm outline-hidden"
                placeholder={$i18n.t('Enter Image Size (e.g. 512x512)')}
                bind:value={config.IMAGE_SIZE}
              />
            </Tooltip>
          </SettingItem>

          {#if ['comfyui', 'automatic1111', ''].includes(config?.IMAGE_GENERATION_ENGINE)}
            <SettingItem label={$i18n.t('Steps')}>
              <Tooltip content={$i18n.t('Enter Number of Steps (e.g. 50)')} placement="top-start">
                <input
                  class=" w-full bg-transparent text-right text-sm font-medium outline-hidden"
                  placeholder={$i18n.t('Enter Number of Steps (e.g. 50)')}
                  bind:value={config.IMAGE_STEPS}
                  required
                />
              </Tooltip>
            </SettingItem>
          {/if}

          <ToggleSetting
            label={$i18n.t('Image Prompt Generation')}
            bind:state={config.ENABLE_IMAGE_PROMPT_GENERATION}
          />
        {/if}

        <SettingItem label={$i18n.t('Image Generation Engine')}>
          <select
            class="w-fit cursor-pointer rounded-sm bg-transparent px-2 pr-8 text-right text-xs outline-hidden"
            bind:value={config.IMAGE_GENERATION_ENGINE}
            placeholder={$i18n.t('Select Engine')}
          >
            <option value="openai">{$i18n.t('Default (Open AI)')}</option>
            <option value="comfyui">{$i18n.t('ComfyUI')}</option>
            <option value="automatic1111">{$i18n.t('Automatic1111')}</option>
            <option value="gemini">{$i18n.t('Gemini')}</option>
          </select>
        </SettingItem>

        {#if config?.IMAGE_GENERATION_ENGINE === 'openai'}
          <SettingItem label={$i18n.t('OpenAI API Base URL')}>
            <input
              class="w-full bg-transparent text-right text-sm outline-hidden"
              placeholder={$i18n.t('API Base URL')}
              bind:value={config.IMAGES_OPENAI_API_BASE_URL}
            />
          </SettingItem>

          <SettingItem label={$i18n.t('OpenAI API Key')}>
            <SensitiveInput
              inputClassName="text-right w-full"
              placeholder={$i18n.t('API Key')}
              bind:value={config.IMAGES_OPENAI_API_KEY}
              required={false}
            />
          </SettingItem>

          <SettingItem label={$i18n.t('OpenAI API Version')}>
            <input
              class="w-full bg-transparent text-right text-sm outline-hidden"
              placeholder={$i18n.t('API Version')}
              bind:value={config.IMAGES_OPENAI_API_VERSION}
            />
          </SettingItem>

          <div class="mb-2.5">
            <div class="flex w-full items-center justify-between">
              <div class="shrink-0 pr-2 text-xs">
                <div class="">
                  {$i18n.t('Additional Parameters')}
                </div>
              </div>
            </div>
            <div class="mt-1.5 flex w-full">
              <div class="mr-2 flex-1">
                <Textarea
                  bind:value={config.IMAGES_OPENAI_API_PARAMS}
                  placeholder={$i18n.t('Enter additional parameters in JSON format')}
                  minSize={100}
                />
              </div>
            </div>
          </div>
        {:else if (config?.IMAGE_GENERATION_ENGINE ?? 'automatic1111') === 'automatic1111'}
          <div class="mb-2.5">
            <div class="flex w-full items-center justify-between">
              <div class="shrink-0 pr-2 text-xs">
                <div class="">
                  {$i18n.t('AUTOMATIC1111 Base URL')}
                </div>
              </div>

              <div class="flex w-full">
                <div class="mr-2 flex-1">
                  <input
                    class="w-full bg-transparent text-right text-sm outline-hidden"
                    placeholder={$i18n.t('Enter URL (e.g. http://127.0.0.1:7860/)')}
                    bind:value={config.AUTOMATIC1111_BASE_URL}
                  />
                </div>
                <button
                  class="  transition"
                  type="button"
                  aria-label="verify connection"
                  on:click={async () => {
                    await updateConfigHandler();
                    const res = await verifyConfigUrl(localStorage.token).catch((error) => {
                      toast.error(`${error}`);
                      return null;
                    });

                    if (res) {
                      toast.success($i18n.t('Server connection verified'));
                    }
                  }}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    class="h-4 w-4"
                  >
                    <path
                      fill-rule="evenodd"
                      d="M15.312 11.424a5.5 5.5 0 01-9.201 2.466l-.312-.311h2.433a.75.75 0 000-1.5H3.989a.75.75 0 00-.75.75v4.242a.75.75 0 001.5 0v-2.43l.31.31a7 7 0 0011.712-3.138.75.75 0 00-1.449-.39zm1.23-3.723a.75.75 0 00.219-.53V2.929a.75.75 0 00-1.5 0V5.36l-.31-.31A7 7 0 003.239 8.188a.75.75 0 101.448.389A5.5 5.5 0 0113.89 6.11l.311.31h-2.432a.75.75 0 000 1.5h4.243a.75.75 0 00.53-.219z"
                      clip-rule="evenodd"
                    />
                  </svg>
                </button>
              </div>
            </div>

            <div class="mt-1 text-xs text-gray-400 dark:text-gray-500">
              {$i18n.t('Include `--api` flag when running stable-diffusion-webui')}
              <a
                class=" font-medium text-gray-300"
                href="https://github.com/AUTOMATIC1111/stable-diffusion-webui/discussions/3734"
                target="_blank"
              >
                {$i18n.t('(e.g. `sh webui.sh --api`)')}
              </a>
            </div>
          </div>

          <div class="mb-2.5">
            <div class="flex w-full items-center justify-between">
              <div class="shrink-0 pr-2 text-xs">
                <div class="">
                  {$i18n.t('AUTOMATIC1111 Api Auth String')}
                </div>
              </div>

              <div class="flex w-full">
                <div class="flex-1">
                  <SensitiveInput
                    inputClassName="text-right w-full"
                    placeholder={$i18n.t('Enter api auth string (e.g. username:password)')}
                    bind:value={config.AUTOMATIC1111_API_AUTH}
                    required={false}
                  />
                </div>
              </div>
            </div>

            <div class="mt-1 text-xs text-gray-400 dark:text-gray-500">
              {$i18n.t('Include `--api-auth` flag when running stable-diffusion-webui')}
              <a
                class=" font-medium text-gray-300"
                href="https://github.com/AUTOMATIC1111/stable-diffusion-webui/discussions/13993"
                target="_blank"
              >
                {$i18n
                  .t('(e.g. `sh webui.sh --api --api-auth username_password`)')
                  .replace('_', ':')}
              </a>
            </div>
          </div>

          <div class="mb-2.5">
            <div class="flex w-full items-center justify-between">
              <div class="shrink-0 pr-2 text-xs">
                <div class="">
                  {$i18n.t('Additional Parameters')}
                </div>
              </div>
            </div>
            <div class="mt-1.5 flex w-full">
              <div class="mr-2 flex-1">
                <Textarea
                  className="rounded-lg w-full py-2 px-3 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
                  bind:value={config.AUTOMATIC1111_PARAMS}
                  placeholder={$i18n.t('Enter additional parameters in JSON format')}
                  minSize={100}
                />
              </div>
            </div>
          </div>
        {:else if config?.IMAGE_GENERATION_ENGINE === 'comfyui'}
          <SettingItem label={$i18n.t('ComfyUI Base URL')}>
            <input
              class="w-full bg-transparent text-right text-sm outline-hidden"
              placeholder={$i18n.t('Enter URL (e.g. http://127.0.0.1:7860/)')}
              bind:value={config.COMFYUI_BASE_URL}
            />
            <button
              class="  rounded-lg transition"
              type="button"
              aria-label="verify connection"
              on:click={async () => {
                await updateConfigHandler();
                const res = await verifyConfigUrl(localStorage.token).catch((error) => {
                  toast.error(`${error}`);
                  return null;
                });

                if (res) {
                  toast.success($i18n.t('Server connection verified'));
                }
              }}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                class="h-4 w-4"
              >
                <path
                  fill-rule="evenodd"
                  d="M15.312 11.424a5.5 5.5 0 01-9.201 2.466l-.312-.311h2.433a.75.75 0 000-1.5H3.989a.75.75 0 00-.75.75v4.242a.75.75 0 001.5 0v-2.43l.31.31a7 7 0 0011.712-3.138.75.75 0 00-1.449-.39zm1.23-3.723a.75.75 0 00.219-.53V2.929a.75.75 0 00-1.5 0V5.36l-.31-.31A7 7 0 003.239 8.188a.75.75 0 101.448.389A5.5 5.5 0 0113.89 6.11l.311.31h-2.432a.75.75 0 000 1.5h4.243a.75.75 0 00.53-.219z"
                  clip-rule="evenodd"
                />
              </svg>
            </button>
          </SettingItem>

          <SettingItem label={$i18n.t('ComfyUI API Key')}>
            <SensitiveInput
              inputClassName="text-right w-full"
              placeholder={$i18n.t('sk-1234')}
              bind:value={config.COMFYUI_API_KEY}
              required={false}
            />
          </SettingItem>

          <div class="mb-2.5">
            <input
              id="upload-comfyui-workflow-input"
              hidden
              type="file"
              accept=".json"
              on:change={(e) => {
                const file = e.target.files[0];
                const reader = new FileReader();

                reader.onload = (e) => {
                  config.COMFYUI_WORKFLOW = e.target.result;
                  e.target.value = null;
                };

                reader.readAsText(file);
              }}
            />
            <div class="flex w-full items-center justify-between">
              <div class="shrink-0 pr-2 text-xs">
                <div class="">
                  {$i18n.t('ComfyUI Workflow')}
                </div>
              </div>

              <div class="flex w-full">
                <div class="mr-2 flex flex-1 justify-end gap-1">
                  {#if config.COMFYUI_WORKFLOW}
                    <button
                      class="text-xs text-gray-700 underline dark:text-gray-400"
                      type="button"
                      aria-label={$i18n.t('Edit workflow.json content')}
                      on:click={() => {
                        // open code editor modal
                        showComfyUIWorkflowEditor = true;
                      }}
                    >
                      {$i18n.t('Edit')}
                    </button>
                  {/if}

                  <Tooltip content={$i18n.t('Click here to upload a workflow.json file.')}>
                    <button
                      class="text-xs text-gray-700 underline dark:text-gray-400"
                      type="button"
                      aria-label={$i18n.t('Click here to upload a workflow.json file.')}
                      on:click={() => {
                        document.getElementById('upload-comfyui-workflow-input')?.click();
                      }}
                    >
                      {$i18n.t('Upload')}
                    </button>
                  </Tooltip>
                </div>
              </div>
            </div>

            <div class="mt-1 text-xs text-gray-400 dark:text-gray-500">
              <CodeEditorModal
                bind:show={showComfyUIWorkflowEditor}
                value={config.COMFYUI_WORKFLOW}
                lang="json"
                onChange={(e) => {
                  config.COMFYUI_WORKFLOW = e;
                }}
                onSave={() => {
                  console.log('Saved');
                }}
              />
              <!-- {#if config.COMFYUI_WORKFLOW}
									<Textarea
										class="w-full rounded-lg my-1 py-2 px-3 text-xs bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden disabled:text-gray-600 resize-none"
										rows="10"
										bind:value={config.COMFYUI_WORKFLOW}
										required
									/>
								{/if} -->
              {$i18n.t('Make sure to export a workflow.json file as API format from ComfyUI.')}
            </div>
          </div>

          {#if config.COMFYUI_WORKFLOW}
            <div class="mb-2.5">
              <div class="flex w-full items-center justify-between">
                <div class="shrink-0 pr-2 text-xs">
                  <div class="">
                    {$i18n.t('ComfyUI Workflow Nodes')}
                  </div>
                </div>
              </div>

              <div class="mt-1 flex flex-col gap-1.5 text-xs">
                {#each REQUIRED_WORKFLOW_NODES as node}
                  <div class="flex w-full flex-col">
                    <div class="shrink-0">
                      <div class=" line-clamp-1 w-20 text-gray-400 capitalize dark:text-gray-500">
                        {node.type}{node.type === 'prompt' ? '*' : ''}
                      </div>
                    </div>

                    <div class="mt-0.5 flex items-center">
                      <div class="">
                        <Tooltip content={$i18n.t('Input Key (e.g. text, unet_name, steps)')}>
                          <input
                            class="w-24 bg-transparent py-1 text-xs outline-hidden"
                            placeholder={$i18n.t('Key')}
                            bind:value={node.key}
                            required
                          />
                        </Tooltip>
                      </div>

                      <div class="px-2 text-gray-400 dark:text-gray-500">:</div>

                      <div class="w-full">
                        <Tooltip
                          content={$i18n.t('Comma separated Node Ids (e.g. 1 or 1,2)')}
                          placement="top-start"
                        >
                          <input
                            class="w-full bg-transparent py-1 text-xs outline-hidden"
                            placeholder={$i18n.t('Node Ids')}
                            bind:value={node.node_ids}
                          />
                        </Tooltip>
                      </div>
                    </div>
                  </div>
                {/each}
              </div>

              <div class="mt-1 text-xs text-gray-400 dark:text-gray-500">
                {$i18n.t('*Prompt node ID(s) are required for image generation')}
              </div>
            </div>
          {/if}
        {:else if config?.IMAGE_GENERATION_ENGINE === 'gemini'}
          <SettingItem label={$i18n.t('Gemini Base URL')}>
            <input
              class="w-full bg-transparent text-right text-sm outline-hidden"
              placeholder={$i18n.t('API Base URL')}
              bind:value={config.IMAGES_GEMINI_API_BASE_URL}
            />
          </SettingItem>

          <SettingItem label={$i18n.t('Gemini API Key')}>
            <SensitiveInput
              inputClassName="text-right w-full"
              placeholder={$i18n.t('API Key')}
              bind:value={config.IMAGES_GEMINI_API_KEY}
              required={true}
            />
          </SettingItem>

          <SettingItem label={$i18n.t('Gemini Endpoint Method')}>
            <select
              class="w-fit cursor-pointer rounded-sm bg-transparent px-2 pr-8 text-right text-xs outline-hidden"
              bind:value={config.IMAGES_GEMINI_ENDPOINT_METHOD}
              placeholder={$i18n.t('Select Method')}
            >
              <option value="predict">predict</option>
              <option value="generateContent">generateContent</option>
            </select>
          </SettingItem>
        {/if}
      </div>

      <div class="space-y-1">
        <div
          class="my-2 mb-4 border-b border-gray-300 pb-1 text-base font-medium dark:border-gray-800"
        >
          {$i18n.t('Edit Image')}
        </div>

        <ToggleSetting label={$i18n.t('Image Edit')} bind:state={config.ENABLE_IMAGE_EDIT} />

        {#if config?.ENABLE_IMAGE_GENERATION && config?.ENABLE_IMAGE_EDIT}
          <div class="mb-2.5">
            <div class="flex w-full items-center justify-between">
              <div class="pr-2 text-xs">
                <div class="shrink-0">
                  {$i18n.t('Model')}
                </div>
              </div>

              <Tooltip content={$i18n.t('Enter Model ID')} placement="top-start">
                <input
                  list="model-list"
                  class="w-52 max-w-full bg-transparent text-right text-sm outline-hidden"
                  bind:value={config.IMAGE_EDIT_MODEL}
                  placeholder={$i18n.t('Select a model')}
                />

                <datalist id="model-list">
                  {#each models ?? [] as model}
                    <option value={model.id}>{model.name}</option>
                  {/each}
                </datalist>
              </Tooltip>
            </div>
          </div>

          <SettingItem label={$i18n.t('Image Size')}>
            <Tooltip content={$i18n.t('Enter Image Size (e.g. 512x512)')} placement="top-start">
              <input
                class="w-52 max-w-full bg-transparent text-right text-sm outline-hidden"
                placeholder={$i18n.t('Enter Image Size (e.g. 512x512)')}
                bind:value={config.IMAGE_EDIT_SIZE}
              />
            </Tooltip>
          </SettingItem>
        {/if}

        <SettingItem label={$i18n.t('Image Edit Engine')}>
          <select
            class="w-fit cursor-pointer rounded-sm bg-transparent px-2 pr-8 text-right text-xs outline-hidden"
            bind:value={config.IMAGE_EDIT_ENGINE}
            placeholder={$i18n.t('Select Engine')}
          >
            <option value="openai">{$i18n.t('Default (Open AI)')}</option>
            <option value="comfyui">{$i18n.t('ComfyUI')}</option>
            <option value="gemini">{$i18n.t('Gemini')}</option>
          </select>
        </SettingItem>

        {#if config?.IMAGE_EDIT_ENGINE === 'openai'}
          <SettingItem label={$i18n.t('OpenAI API Base URL')}>
            <input
              class="w-full bg-transparent text-right text-sm outline-hidden"
              placeholder={$i18n.t('API Base URL')}
              bind:value={config.IMAGES_EDIT_OPENAI_API_BASE_URL}
            />
          </SettingItem>

          <SettingItem label={$i18n.t('OpenAI API Key')}>
            <SensitiveInput
              inputClassName="text-right w-full"
              placeholder={$i18n.t('API Key')}
              bind:value={config.IMAGES_EDIT_OPENAI_API_KEY}
              required={false}
            />
          </SettingItem>

          <SettingItem label={$i18n.t('OpenAI API Version')}>
            <input
              class="w-full bg-transparent text-right text-sm outline-hidden"
              placeholder={$i18n.t('API Version')}
              bind:value={config.IMAGES_EDIT_OPENAI_API_VERSION}
            />
          </SettingItem>
        {:else if config?.IMAGE_EDIT_ENGINE === 'comfyui'}
          <div class="mb-2.5">
            <div class="flex w-full items-center justify-between">
              <div class="shrink-0 pr-2 text-xs">
                <div class="">
                  {$i18n.t('ComfyUI Base URL')}
                </div>
              </div>

              <div class="flex w-full">
                <div class="mr-2 flex-1">
                  <input
                    class="w-full bg-transparent text-right text-sm outline-hidden"
                    placeholder={$i18n.t('Enter URL (e.g. http://127.0.0.1:7860/)')}
                    bind:value={config.IMAGES_EDIT_COMFYUI_BASE_URL}
                  />
                </div>
                <button
                  class="  transition"
                  type="button"
                  aria-label="verify connection"
                  on:click={async () => {
                    await updateConfigHandler();
                    const res = await verifyConfigUrl(localStorage.token).catch((error) => {
                      toast.error(`${error}`);
                      return null;
                    });

                    if (res) {
                      toast.success($i18n.t('Server connection verified'));
                    }
                  }}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    class="h-4 w-4"
                  >
                    <path
                      fill-rule="evenodd"
                      d="M15.312 11.424a5.5 5.5 0 01-9.201 2.466l-.312-.311h2.433a.75.75 0 000-1.5H3.989a.75.75 0 00-.75.75v4.242a.75.75 0 001.5 0v-2.43l.31.31a7 7 0 0011.712-3.138.75.75 0 00-1.449-.39zm1.23-3.723a.75.75 0 00.219-.53V2.929a.75.75 0 00-1.5 0V5.36l-.31-.31A7 7 0 003.239 8.188a.75.75 0 101.448.389A5.5 5.5 0 0113.89 6.11l.311.31h-2.432a.75.75 0 000 1.5h4.243a.75.75 0 00.53-.219z"
                      clip-rule="evenodd"
                    />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <SettingItem label={$i18n.t('ComfyUI API Key')}>
            <SensitiveInput
              inputClassName="text-right w-full"
              placeholder={$i18n.t('sk-1234')}
              bind:value={config.IMAGES_EDIT_COMFYUI_API_KEY}
              required={false}
            />
          </SettingItem>

          <div class="mb-2.5">
            <input
              id="upload-comfyui-edit-workflow-input"
              hidden
              type="file"
              accept=".json"
              on:change={(e) => {
                const file = e.target.files[0];
                const reader = new FileReader();

                reader.onload = (e) => {
                  config.IMAGES_EDIT_COMFYUI_WORKFLOW = e.target.result;
                  e.target.value = null;
                };

                reader.readAsText(file);
              }}
            />
            <div class="flex w-full items-center justify-between">
              <div class="shrink-0 pr-2 text-xs">
                <div class="">
                  {$i18n.t('ComfyUI Workflow')}
                </div>
              </div>

              <div class="flex w-full">
                <div class="mr-2 flex flex-1 justify-end gap-1">
                  {#if config.IMAGES_EDIT_COMFYUI_WORKFLOW}
                    <button
                      class="text-xs text-gray-700 underline dark:text-gray-400"
                      type="button"
                      aria-label={$i18n.t('Edit workflow.json content')}
                      on:click={() => {
                        // open code editor modal
                        showComfyUIEditWorkflowEditor = true;
                      }}
                    >
                      {$i18n.t('Edit')}
                    </button>
                  {/if}

                  <Tooltip content={$i18n.t('Click here to upload a workflow.json file.')}>
                    <button
                      class="text-xs text-gray-700 underline dark:text-gray-400"
                      type="button"
                      aria-label={$i18n.t('Click here to upload a workflow.json file.')}
                      on:click={() => {
                        document.getElementById('upload-comfyui-edit-workflow-input')?.click();
                      }}
                    >
                      {$i18n.t('Upload')}
                    </button>
                  </Tooltip>
                </div>
              </div>
            </div>

            <div class="mt-1 text-xs text-gray-400 dark:text-gray-500">
              <CodeEditorModal
                bind:show={showComfyUIEditWorkflowEditor}
                value={config.IMAGES_EDIT_COMFYUI_WORKFLOW}
                lang="json"
                onChange={(e) => {
                  config.IMAGES_EDIT_COMFYUI_WORKFLOW = e;
                }}
                onSave={() => {
                  console.log('Saved');
                }}
              />
              {$i18n.t('Make sure to export a workflow.json file as API format from ComfyUI.')}
            </div>
          </div>

          {#if config.IMAGES_EDIT_COMFYUI_WORKFLOW}
            <div class="mb-2.5">
              <div class="flex w-full items-center justify-between">
                <div class="shrink-0 pr-2 text-xs">
                  <div class="">
                    {$i18n.t('ComfyUI Workflow Nodes')}
                  </div>
                </div>
              </div>

              <div class="mt-1 flex flex-col gap-1.5 text-xs">
                {#each REQUIRED_EDIT_WORKFLOW_NODES as node}
                  <div class="flex w-full flex-col">
                    <div class="shrink-0">
                      <div class=" line-clamp-1 w-20 text-gray-400 capitalize dark:text-gray-500">
                        {node.type}{['prompt', 'image'].includes(node.type) ? '*' : ''}
                      </div>
                    </div>

                    <div class="mt-0.5 flex items-center">
                      <div class="">
                        <Tooltip content={$i18n.t('Input Key (e.g. text, unet_name, steps)')}>
                          <input
                            class="w-24 bg-transparent py-1 text-xs outline-hidden"
                            placeholder={$i18n.t('Key')}
                            bind:value={node.key}
                            required
                          />
                        </Tooltip>
                      </div>

                      <div class="px-2 text-gray-400 dark:text-gray-500">:</div>

                      <div class="w-full">
                        <Tooltip
                          content={$i18n.t('Comma separated Node Ids (e.g. 1 or 1,2)')}
                          placement="top-start"
                        >
                          <input
                            class="w-full bg-transparent py-1 text-xs outline-hidden"
                            placeholder={$i18n.t('Node Ids')}
                            bind:value={node.node_ids}
                          />
                        </Tooltip>
                      </div>
                    </div>
                  </div>
                {/each}
              </div>

              <div class="mt-1 text-xs text-gray-400 dark:text-gray-500">
                {$i18n.t('*Prompt node ID(s) are required for image generation')}
              </div>
            </div>
          {/if}
        {:else if config?.IMAGE_EDIT_ENGINE === 'gemini'}
          <SettingItem label={$i18n.t('Gemini Base URL')}>
            <input
              <input
              class="w-full bg-transparent text-right text-sm outline-hidden"
              placeholder={$i18n.t('API Base URL')}
              bind:value={config.IMAGES_EDIT_GEMINI_API_BASE_URL}
            />
          </SettingItem>

          <SettingItem label={$i18n.t('Gemini API Key')}>
            <SensitiveInput
              inputClassName="text-right w-full"
              placeholder={$i18n.t('API Key')}
              bind:value={config.IMAGES_EDIT_GEMINI_API_KEY}
              required={true}
            />
          </SettingItem>
        {/if}
      </div>
    {/if}
  </div>

  <div class="flex justify-end p-1">
    <Button type="submit" radius="xl" disabled={loading}>
      {$i18n.t('Save')}

      {#if loading}
        <span class="shrink-0">
          <Spinner />
        </span>
      {/if}
    </Button>
  </div>
</form>
