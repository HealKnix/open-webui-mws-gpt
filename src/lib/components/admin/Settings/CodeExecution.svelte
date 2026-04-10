<script lang="ts">
  import { toast } from 'svelte-sonner';
  import { onMount, getContext } from 'svelte';
  import { getCodeExecutionConfig, setCodeExecutionConfig } from '$lib/apis/configs';

  import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';

  import Textarea from '$lib/components/common/Textarea.svelte';
  import ToggleSetting from '$lib/components/common/ToggleSetting.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Button from '$lib/components/common/Button.svelte';
  import SettingItem from '$lib/components/common/SettingItem.svelte';

  const i18n = getContext('i18n');

  export let saveHandler: Function;

  let config = null;

  let engines = ['pyodide', 'jupyter'];

  const submitHandler = async () => {
    const res = await setCodeExecutionConfig(localStorage.token, config);
  };

  onMount(async () => {
    const res = await getCodeExecutionConfig(localStorage.token);

    if (res) {
      config = res;
    }
  });
</script>

<form
  class="flex h-full flex-col justify-between space-y-3 text-sm"
  on:submit|preventDefault={async () => {
    await submitHandler();
    saveHandler();
  }}
>
  <div class="scrollbar-hidden h-full space-y-3 overflow-y-scroll p-1">
    {#if config}
      <div>
        <div class="space-y-1">
          <div
            class="my-2 border-b border-gray-300 pb-2 text-base font-medium dark:border-gray-800"
          >
            {$i18n.t('General')}
          </div>

          <ToggleSetting
            label={$i18n.t('Enable Code Execution')}
            bind:state={config.ENABLE_CODE_EXECUTION}
          />

          <div class="mb-2.5">
            <SettingItem label={$i18n.t('Code Execution Engine')}>
              <div class="relative flex items-center">
                <select
                  class="w-fit rounded-sm bg-transparent p-1 px-2 pr-8 text-right text-xs outline-hidden"
                  bind:value={config.CODE_EXECUTION_ENGINE}
                  placeholder={$i18n.t('Select a engine')}
                  required
                >
                  <option disabled selected value="">{$i18n.t('Select a engine')}</option>
                  {#each engines as engine}
                    <option value={engine}>{engine}{engine === 'jupyter' ? ' (Legacy)' : ''}</option
                    >
                  {/each}
                </select>
              </div>
            </SettingItem>

            {#if config.CODE_EXECUTION_ENGINE === 'jupyter'}
              <div class="text-xs text-gray-500">
                {$i18n.t(
                  'Warning: Jupyter execution enables arbitrary code execution, posing severe security risks—proceed with extreme caution.',
                )}
              </div>
            {/if}
          </div>

          {#if config.CODE_EXECUTION_ENGINE === 'jupyter'}
            <SettingItem label={$i18n.t('Jupyter URL')}>
              <div class="flex w-full">
                <div class="flex-1">
                  <input
                    class="w-full bg-transparent py-0.5 text-sm outline-hidden placeholder:text-gray-300 dark:placeholder:text-gray-700"
                    type="text"
                    placeholder={$i18n.t('Enter Jupyter URL')}
                    bind:value={config.CODE_EXECUTION_JUPYTER_URL}
                    autocomplete="off"
                  />
                </div>
              </div>
            </SettingItem>

            <SettingItem label={$i18n.t('Jupyter Auth')}>
              <select
                class="w-fit rounded-sm bg-transparent p-1 px-2 pr-8 text-left text-xs outline-hidden"
                bind:value={config.CODE_EXECUTION_JUPYTER_AUTH}
                placeholder={$i18n.t('Select an auth method')}
              >
                <option selected value="">{$i18n.t('None')}</option>
                <option value="token">{$i18n.t('Token')}</option>
                <option value="password">{$i18n.t('Password')}</option>
              </select>
            </SettingItem>

            {#if config.CODE_EXECUTION_JUPYTER_AUTH}
              <div class="flex w-full gap-2">
                <div class="flex-1">
                  {#if config.CODE_EXECUTION_JUPYTER_AUTH === 'password'}
                    <SensitiveInput
                      type="text"
                      placeholder={$i18n.t('Enter Jupyter Password')}
                      bind:value={config.CODE_EXECUTION_JUPYTER_AUTH_PASSWORD}
                      autocomplete="off"
                    />
                  {:else}
                    <SensitiveInput
                      type="text"
                      placeholder={$i18n.t('Enter Jupyter Token')}
                      bind:value={config.CODE_EXECUTION_JUPYTER_AUTH_TOKEN}
                      autocomplete="off"
                    />
                  {/if}
                </div>
              </div>
            {/if}

            <SettingItem label={$i18n.t('Code Execution Timeout')}>
              <Tooltip content={$i18n.t('Enter timeout in seconds')}>
                <input
                  class="w-fit rounded-sm bg-transparent p-1 px-2 text-right text-xs outline-hidden"
                  type="number"
                  bind:value={config.CODE_EXECUTION_JUPYTER_TIMEOUT}
                  placeholder={$i18n.t('e.g. 60')}
                  autocomplete="off"
                />
              </Tooltip>
            </SettingItem>
          {/if}
        </div>

        <div class="space-y-1">
          <div
            class="my-2 border-b border-gray-300 pb-2 text-base font-medium dark:border-gray-800"
          >
            {$i18n.t('Code Interpreter')}
          </div>

          <ToggleSetting
            label={$i18n.t('Enable Code Interpreter')}
            bind:state={config.ENABLE_CODE_INTERPRETER}
          />

          {#if config.ENABLE_CODE_INTERPRETER}
            <div class="mb-2.5">
              <SettingItem label={$i18n.t('Code Interpreter Engine')}>
                <select
                  class="w-fit rounded-sm bg-transparent p-1 px-2 pr-8 text-right text-xs outline-hidden"
                  bind:value={config.CODE_INTERPRETER_ENGINE}
                  placeholder={$i18n.t('Select a engine')}
                  required
                >
                  <option disabled selected value="">{$i18n.t('Select a engine')}</option>
                  {#each engines as engine}
                    <option value={engine}>{engine}{engine === 'jupyter' ? ' (Legacy)' : ''}</option
                    >
                  {/each}
                </select>
              </SettingItem>

              {#if config.CODE_INTERPRETER_ENGINE === 'jupyter'}
                <div class="text-xs text-gray-500">
                  {$i18n.t(
                    'Warning: Jupyter execution enables arbitrary code execution, posing severe security risks—proceed with extreme caution.',
                  )}
                </div>
              {/if}
            </div>

            {#if config.CODE_INTERPRETER_ENGINE === 'jupyter'}
              <SettingItem label={$i18n.t('Jupyter URL')}>
                <div class="flex w-full">
                  <div class="flex-1">
                    <input
                      class="w-full bg-transparent py-0.5 text-sm outline-hidden placeholder:text-gray-300 dark:placeholder:text-gray-700"
                      type="text"
                      placeholder={$i18n.t('Enter Jupyter URL')}
                      bind:value={config.CODE_INTERPRETER_JUPYTER_URL}
                      autocomplete="off"
                    />
                  </div>
                </div>
              </SettingItem>

              <SettingItem label={$i18n.t('Jupyter Auth')}>
                <select
                  class="w-fit rounded-sm bg-transparent p-1 px-2 pr-8 text-left text-xs outline-hidden"
                  bind:value={config.CODE_INTERPRETER_JUPYTER_AUTH}
                  placeholder={$i18n.t('Select an auth method')}
                >
                  <option selected value="">{$i18n.t('None')}</option>
                  <option value="token">{$i18n.t('Token')}</option>
                  <option value="password">{$i18n.t('Password')}</option>
                </select>
              </SettingItem>

              {#if config.CODE_INTERPRETER_JUPYTER_AUTH}
                <div class="flex w-full gap-2">
                  <div class="flex-1">
                    {#if config.CODE_INTERPRETER_JUPYTER_AUTH === 'password'}
                      <SensitiveInput
                        type="text"
                        placeholder={$i18n.t('Enter Jupyter Password')}
                        bind:value={config.CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD}
                        autocomplete="off"
                      />
                    {:else}
                      <SensitiveInput
                        type="text"
                        placeholder={$i18n.t('Enter Jupyter Token')}
                        bind:value={config.CODE_INTERPRETER_JUPYTER_AUTH_TOKEN}
                        autocomplete="off"
                      />
                    {/if}
                  </div>
                </div>
              {/if}

              <SettingItem label={$i18n.t('Code Execution Timeout')}>
                <Tooltip content={$i18n.t('Enter timeout in seconds')}>
                  <input
                    class="w-fit rounded-sm bg-transparent p-1 px-2 text-right text-xs outline-hidden"
                    type="number"
                    bind:value={config.CODE_INTERPRETER_JUPYTER_TIMEOUT}
                    placeholder={$i18n.t('e.g. 60')}
                    autocomplete="off"
                  />
                </Tooltip>
              </SettingItem>
            {/if}

            <div>
              <div class="w-full py-0.5">
                <div class=" mb-2.5 text-xs font-medium">
                  {$i18n.t('Code Interpreter Prompt Template')}
                </div>

                <Tooltip
                  content={$i18n.t(
                    'Leave empty to use the default prompt, or enter a custom prompt',
                  )}
                  placement="top-start"
                >
                  <Textarea
                    bind:value={config.CODE_INTERPRETER_PROMPT_TEMPLATE}
                    placeholder={$i18n.t(
                      'Leave empty to use the default prompt, or enter a custom prompt',
                    )}
                  />
                </Tooltip>
              </div>
            </div>
          {/if}
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
