<script lang="ts">
  import { toast } from 'svelte-sonner';
  import { createEventDispatcher, onMount, getContext, tick } from 'svelte';

  const dispatch = createEventDispatcher();

  import { getOllamaConfig, updateOllamaConfig } from '$lib/apis/ollama';
  import { getOpenAIConfig, updateOpenAIConfig, getOpenAIModels } from '$lib/apis/openai';
  import { getModels as _getModels, getBackendConfig } from '$lib/apis';
  import { getConnectionsConfig, setConnectionsConfig } from '$lib/apis/configs';

  import { config, models, settings, user } from '$lib/stores';

  import Switch from '$lib/components/common/Switch.svelte';
  import ToggleSetting from '$lib/components/common/ToggleSetting.svelte';
  import SettingItem from '$lib/components/common/SettingItem.svelte';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Plus from '$lib/components/icons/Plus.svelte';

  import OpenAIConnection from './Connections/OpenAIConnection.svelte';
  import AddConnectionModal from '$lib/components/AddConnectionModal.svelte';
  import OllamaConnection from './Connections/OllamaConnection.svelte';
  import Button from '$lib/components/common/Button.svelte';

  const i18n = getContext('i18n');

  const getModels = async () => {
    const models = await _getModels(
      localStorage.token,
      $config?.features?.enable_direct_connections && ($settings?.directConnections ?? null),
      false,
      true,
    );
    return models;
  };

  // External
  let OLLAMA_BASE_URLS = [''];
  let OLLAMA_API_CONFIGS = {};

  let OPENAI_API_KEYS = [''];
  let OPENAI_API_BASE_URLS = [''];
  let OPENAI_API_CONFIGS = {};

  let ENABLE_OPENAI_API: null | boolean = null;
  let ENABLE_OLLAMA_API: null | boolean = null;

  let connectionsConfig = null;

  let pipelineUrls = {};
  let showAddOpenAIConnectionModal = false;
  let showAddOllamaConnectionModal = false;

  const updateOpenAIHandler = async () => {
    if (ENABLE_OPENAI_API !== null) {
      // Remove trailing slashes
      OPENAI_API_BASE_URLS = OPENAI_API_BASE_URLS.map((url) => url.replace(/\/$/, ''));

      // Check if API KEYS length is same than API URLS length
      if (OPENAI_API_KEYS.length !== OPENAI_API_BASE_URLS.length) {
        // if there are more keys than urls, remove the extra keys
        if (OPENAI_API_KEYS.length > OPENAI_API_BASE_URLS.length) {
          OPENAI_API_KEYS = OPENAI_API_KEYS.slice(0, OPENAI_API_BASE_URLS.length);
        }

        // if there are more urls than keys, add empty keys
        if (OPENAI_API_KEYS.length < OPENAI_API_BASE_URLS.length) {
          const diff = OPENAI_API_BASE_URLS.length - OPENAI_API_KEYS.length;
          for (let i = 0; i < diff; i++) {
            OPENAI_API_KEYS.push('');
          }
        }
      }

      const res = await updateOpenAIConfig(localStorage.token, {
        ENABLE_OPENAI_API: ENABLE_OPENAI_API,
        OPENAI_API_BASE_URLS: OPENAI_API_BASE_URLS,
        OPENAI_API_KEYS: OPENAI_API_KEYS,
        OPENAI_API_CONFIGS: OPENAI_API_CONFIGS,
      }).catch((error) => {
        toast.error(`${error}`);
      });

      if (res) {
        toast.success($i18n.t('OpenAI API settings updated'));
        await models.set(await getModels());
      }
    }
  };

  const updateOllamaHandler = async () => {
    if (ENABLE_OLLAMA_API !== null) {
      // Remove trailing slashes
      OLLAMA_BASE_URLS = OLLAMA_BASE_URLS.map((url) => url.replace(/\/$/, ''));

      const res = await updateOllamaConfig(localStorage.token, {
        ENABLE_OLLAMA_API: ENABLE_OLLAMA_API,
        OLLAMA_BASE_URLS: OLLAMA_BASE_URLS,
        OLLAMA_API_CONFIGS: OLLAMA_API_CONFIGS,
      }).catch((error) => {
        toast.error(`${error}`);
      });

      if (res) {
        toast.success($i18n.t('Ollama API settings updated'));
        await models.set(await getModels());
      }
    }
  };

  const updateConnectionsHandler = async () => {
    const res = await setConnectionsConfig(localStorage.token, connectionsConfig).catch((error) => {
      toast.error(`${error}`);
    });

    if (res) {
      toast.success($i18n.t('Connections settings updated'));
      await models.set(await getModels());
      await config.set(await getBackendConfig());
    }
  };

  const addOpenAIConnectionHandler = async (connection) => {
    OPENAI_API_BASE_URLS = [...OPENAI_API_BASE_URLS, connection.url];
    OPENAI_API_KEYS = [...OPENAI_API_KEYS, connection.key];
    OPENAI_API_CONFIGS[OPENAI_API_BASE_URLS.length - 1] = connection.config;

    await updateOpenAIHandler();
  };

  const addOllamaConnectionHandler = async (connection) => {
    OLLAMA_BASE_URLS = [...OLLAMA_BASE_URLS, connection.url];
    OLLAMA_API_CONFIGS[OLLAMA_BASE_URLS.length - 1] = {
      ...connection.config,
      key: connection.key,
    };

    await updateOllamaHandler();
  };

  onMount(async () => {
    if ($user?.role === 'admin') {
      let ollamaConfig = {};
      let openaiConfig = {};

      await Promise.all([
        (async () => {
          ollamaConfig = await getOllamaConfig(localStorage.token);
        })(),
        (async () => {
          openaiConfig = await getOpenAIConfig(localStorage.token);
        })(),
        (async () => {
          connectionsConfig = await getConnectionsConfig(localStorage.token);
        })(),
      ]);

      ENABLE_OPENAI_API = openaiConfig.ENABLE_OPENAI_API;
      ENABLE_OLLAMA_API = ollamaConfig.ENABLE_OLLAMA_API;

      OPENAI_API_BASE_URLS = openaiConfig.OPENAI_API_BASE_URLS;
      OPENAI_API_KEYS = openaiConfig.OPENAI_API_KEYS;
      OPENAI_API_CONFIGS = openaiConfig.OPENAI_API_CONFIGS;

      OLLAMA_BASE_URLS = ollamaConfig.OLLAMA_BASE_URLS;
      OLLAMA_API_CONFIGS = ollamaConfig.OLLAMA_API_CONFIGS;

      if (ENABLE_OPENAI_API) {
        // get url and idx
        for (const [idx, url] of OPENAI_API_BASE_URLS.entries()) {
          if (!OPENAI_API_CONFIGS[idx]) {
            // Legacy support, url as key
            OPENAI_API_CONFIGS[idx] = OPENAI_API_CONFIGS[url] || {};
          }
        }

        OPENAI_API_BASE_URLS.forEach(async (url, idx) => {
          OPENAI_API_CONFIGS[idx] = OPENAI_API_CONFIGS[idx] || {};
          if (!(OPENAI_API_CONFIGS[idx]?.enable ?? true)) {
            return;
          }
          const res = await getOpenAIModels(localStorage.token, idx);
          if (res.pipelines) {
            pipelineUrls[url] = true;
          }
        });
      }

      if (ENABLE_OLLAMA_API) {
        for (const [idx, url] of OLLAMA_BASE_URLS.entries()) {
          if (!OLLAMA_API_CONFIGS[idx]) {
            OLLAMA_API_CONFIGS[idx] = OLLAMA_API_CONFIGS[url] || {};
          }
        }
      }
    }
  });

  const submitHandler = async () => {
    updateOpenAIHandler();
    updateOllamaHandler();

    dispatch('save');

    await config.set(await getBackendConfig());
  };
</script>

<AddConnectionModal
  bind:show={showAddOpenAIConnectionModal}
  onSubmit={addOpenAIConnectionHandler}
/>

<AddConnectionModal
  ollama
  bind:show={showAddOllamaConnectionModal}
  onSubmit={addOllamaConnectionHandler}
/>

<form class="flex h-full flex-col justify-between text-sm" on:submit|preventDefault={submitHandler}>
  <div class="scrollbar-hidden h-full overflow-y-scroll p-1">
    {#if ENABLE_OPENAI_API !== null && ENABLE_OLLAMA_API !== null && connectionsConfig !== null}
      <div class="mb-3.5">
        <div
          class="my-2 mb-4 border-b border-gray-300 pb-1 text-base font-medium dark:border-gray-800"
        >
          {$i18n.t('General')}
        </div>

        <div class="my-2">
          <div class="mt-2 space-y-2">
            <ToggleSetting
              label={$i18n.t('OpenAI API')}
              bind:state={ENABLE_OPENAI_API}
              on:change={async () => {
                updateOpenAIHandler();
              }}
            />

            {#if ENABLE_OPENAI_API}
              <SettingItem label={$i18n.t('Manage OpenAI API Connections')}>
                <div class="flex items-center gap-1">
                  <Tooltip content={$i18n.t(`Add Connection`)}>
                    <button
                      class="px-1"
                      on:click={() => {
                        showAddOpenAIConnectionModal = true;
                      }}
                      type="button"
                    >
                      <Plus />
                    </button>
                  </Tooltip>
                </div>
              </SettingItem>

              <div class="mt-1.5 flex flex-col gap-1.5">
                {#each OPENAI_API_BASE_URLS as url, idx}
                  <OpenAIConnection
                    bind:url={OPENAI_API_BASE_URLS[idx]}
                    bind:key={OPENAI_API_KEYS[idx]}
                    bind:config={OPENAI_API_CONFIGS[idx]}
                    pipeline={pipelineUrls[url] ? true : false}
                    onSubmit={() => {
                      updateOpenAIHandler();
                    }}
                    onDelete={() => {
                      OPENAI_API_BASE_URLS = OPENAI_API_BASE_URLS.filter(
                        (url, urlIdx) => idx !== urlIdx,
                      );
                      OPENAI_API_KEYS = OPENAI_API_KEYS.filter((key, keyIdx) => idx !== keyIdx);

                      let newConfig = {};
                      OPENAI_API_BASE_URLS.forEach((url, newIdx) => {
                        newConfig[newIdx] = OPENAI_API_CONFIGS[newIdx < idx ? newIdx : newIdx + 1];
                      });
                      OPENAI_API_CONFIGS = newConfig;
                      updateOpenAIHandler();
                    }}
                  />
                {/each}
              </div>
            {/if}
          </div>
        </div>

        <div class=" my-2">
          <ToggleSetting
            label={$i18n.t('Ollama API')}
            bind:state={ENABLE_OLLAMA_API}
            on:change={async () => {
              updateOllamaHandler();
            }}
          />

          {#if ENABLE_OLLAMA_API}
            <div class="">
              <SettingItem label={$i18n.t('Manage Ollama API Connections')}>
                <div class="flex items-center gap-1">
                  <Tooltip content={$i18n.t(`Add Connection`)}>
                    <button
                      class="px-1"
                      on:click={() => {
                        showAddOllamaConnectionModal = true;
                      }}
                      type="button"
                    >
                      <Plus />
                    </button>
                  </Tooltip>
                </div>
              </SettingItem>

              <div class="flex w-full gap-1.5">
                <div class="mt-1.5 flex flex-1 flex-col gap-1.5">
                  {#each OLLAMA_BASE_URLS as url, idx}
                    <OllamaConnection
                      bind:url={OLLAMA_BASE_URLS[idx]}
                      bind:config={OLLAMA_API_CONFIGS[idx]}
                      {idx}
                      onSubmit={() => {
                        updateOllamaHandler();
                      }}
                      onDelete={() => {
                        OLLAMA_BASE_URLS = OLLAMA_BASE_URLS.filter((url, urlIdx) => idx !== urlIdx);

                        let newConfig = {};
                        OLLAMA_BASE_URLS.forEach((url, newIdx) => {
                          newConfig[newIdx] =
                            OLLAMA_API_CONFIGS[newIdx < idx ? newIdx : newIdx + 1];
                        });
                        OLLAMA_API_CONFIGS = newConfig;
                      }}
                    />
                  {/each}
                </div>
              </div>

              <div class="mt-1 text-xs text-gray-400 dark:text-gray-500">
                {$i18n.t('Trouble accessing Ollama?')}
                <a
                  class=" font-medium text-gray-300 underline"
                  href="https://github.com/open-webui/open-webui#troubleshooting"
                  target="_blank"
                >
                  {$i18n.t('Click here for help.')}
                </a>
              </div>
            </div>
          {/if}
        </div>

        <div class="my-2">
          <ToggleSetting
            label={$i18n.t('Direct Connections')}
            bind:state={connectionsConfig.ENABLE_DIRECT_CONNECTIONS}
            on:change={async () => {
              updateConnectionsHandler();
            }}
          />

          <div class="mt-1 text-xs text-gray-400 dark:text-gray-500">
            {$i18n.t(
              'Direct Connections allow users to connect to their own OpenAI compatible API endpoints.',
            )}
          </div>
        </div>

        <hr class=" dark:border-gray-850/30 my-2 border-gray-100/30" />

        <div class="my-2">
          <ToggleSetting
            label={$i18n.t('Cache Base Model List')}
            bind:state={connectionsConfig.ENABLE_BASE_MODELS_CACHE}
            on:change={async () => {
              updateConnectionsHandler();
            }}
          />

          <div class="mt-1 text-xs text-gray-400 dark:text-gray-500">
            {$i18n.t(
              'Base Model List Cache speeds up access by fetching base models only at startup or on settings save—faster, but may not show recent base model changes.',
            )}
          </div>
        </div>
      </div>
    {:else}
      <div class="flex h-full justify-center">
        <div class="my-auto">
          <Spinner className="size-6" />
        </div>
      </div>
    {/if}
  </div>

  <div class="flex justify-end p-1">
    <Button type="submit" radius="xl">
      {$i18n.t('Save')}
    </Button>
  </div>
</form>
