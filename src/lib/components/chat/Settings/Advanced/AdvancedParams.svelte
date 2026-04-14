<script lang="ts">
  import Button from '$lib/components/common/Button.svelte';
  import Input from '$lib/components/common/Input.svelte';
  import SettingItem from '$lib/components/common/SettingItem.svelte';
  import Switch from '$lib/components/common/Switch.svelte';
  import Textarea from '$lib/components/common/Textarea.svelte';
  import ToggleSetting from '$lib/components/common/ToggleSetting.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Plus from '$lib/components/icons/Plus.svelte';
  import { cn } from '$lib/utils';
  import { getContext } from 'svelte';

  export let className = '';

  const i18n = getContext('i18n');

  export let onChange: (params: any) => void = () => {};

  export let admin = false;
  export let custom = false;

  const defaultParams = {
    // Advanced
    stream_response: true, // Set stream responses for this model individually
    stream_delta_chunk_size: 1, // Set the chunk size for streaming responses
    function_calling: 'native',
    reasoning_tags: ['', ''],
    seed: 0,
    stop: '',
    temperature: 0.8,
    reasoning_effort: 'medium',
    logit_bias: '',
    max_tokens: 128,
    top_k: 40,
    top_p: 0.9,
    min_p: 0.0,
    frequency_penalty: 1.1,
    presence_penalty: 0.0,
    mirostat: 0,
    mirostat_eta: 0.1,
    mirostat_tau: 5.0,
    repeat_last_n: 64,
    tfs_z: 1,
    repeat_penalty: 1.1,
    use_mmap: true,
    use_mlock: true,
    think: true,
    format: 'json',
    num_keep: 24,
    num_ctx: 2048,
    num_batch: 512,
    num_thread: 2,
    num_gpu: 0,
    keep_alive: '5m',
  };

  export let params = defaultParams;
  $: if (params) {
    onChange(params);
  }
</script>

<div
  class={cn(
    'pb-safe-bottom bg-card/50 border-border max-w-2xl space-y-1 rounded-2xl border p-2 text-xs',
    className,
  )}
>
  <div>
    <Tooltip
      content={$i18n.t(
        'When enabled, the model will respond to each chat message in real-time, generating a response as soon as the user sends a message. This mode is useful for live chat applications, but may impact performance on slower hardware.',
      )}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={$i18n.t('Stream Chat Response')}
        className={(params?.stream_response ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex rounded-sm p-1 px-3 text-xs transition"
          on:click={() => {
            params.stream_response =
              (params?.stream_response ?? null) === null
                ? defaultParams.stream_response
                : params.stream_response === defaultParams.stream_response
                  ? !defaultParams.stream_response
                  : null;
          }}
          type="button"
        >
          {#if params.stream_response === true}
            <span class="ml-2 self-center">{$i18n.t('On')}</span>
          {:else if params.stream_response === false}
            <span class="ml-2 self-center">{$i18n.t('Off')}</span>
          {:else}
            <span class="ml-2 self-center">{$i18n.t('Default')}</span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>
  </div>

  {#if admin}
    <div>
      <Tooltip
        content={$i18n.t(
          'The stream delta chunk size for the model. Increasing the chunk size will make the model respond with larger pieces of text at once.',
        )}
        placement="top-start"
        className="inline-tooltip"
      >
        <SettingItem
          label={$i18n.t('Stream Delta Chunk Size')}
          className={(params?.stream_delta_chunk_size ?? null) !== null
            ? 'bg-accent-active/15 hover:bg-accent-active/20'
            : ''}
        >
          <button
            class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
            type="button"
            on:click={() => {
              params.stream_delta_chunk_size =
                (params?.stream_delta_chunk_size ?? null) === null
                  ? defaultParams.stream_delta_chunk_size
                  : null;
            }}
          >
            {#if (params?.stream_delta_chunk_size ?? null) === null}
              <span class="ml-2 self-center"> {$i18n.t('Default')} </span>
            {:else}
              <span class="ml-2 self-center"> {$i18n.t('Custom')} </span>
            {/if}
          </button>
        </SettingItem>
      </Tooltip>

      {#if (params?.stream_delta_chunk_size ?? null) !== null}
        <div class="mt-1 mb-4 flex space-x-2">
          <div class=" flex-1">
            <input
              id="steps-range"
              type="range"
              min="1"
              max="128"
              step="1"
              bind:value={params.stream_delta_chunk_size}
              class="h-2 w-full cursor-pointer rounded-lg dark:bg-gray-700"
            />
          </div>
          <div>
            <Input
              bind:value={params.stream_delta_chunk_size}
              className="max-w-16"
              type="number"
              min="1"
            />
          </div>
        </div>
      {/if}
    </div>
  {/if}

  <div>
    <Tooltip
      content={$i18n.t(
        "Default mode works with a wider range of models by calling tools once before execution. Native mode leverages the model's built-in tool-calling capabilities, but requires the model to inherently support this feature.",
      )}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={$i18n.t('Function Calling')}
        className={(params?.function_calling ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex rounded-sm p-1 px-3 text-xs transition"
          on:click={() => {
            params.function_calling =
              (params?.function_calling ?? null) === null ? defaultParams.function_calling : null;
          }}
          type="button"
        >
          {#if params.function_calling === defaultParams.function_calling}
            <span class="ml-2 self-center">{$i18n.t('Native')}</span>
          {:else}
            <span class="ml-2 self-center">{$i18n.t('Default')}</span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>
  </div>

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t(
        'Enable, disable, or customize the reasoning tags used by the model. "Enabled" uses default tags, "Disabled" turns off reasoning tags, and "Custom" lets you specify your own start and end tags.',
      )}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={$i18n.t('Reasoning Tags')}
        className={(params?.reasoning_tags ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
          type="button"
          on:click={() => {
            if ((params?.reasoning_tags ?? null) === null) {
              params.reasoning_tags = defaultParams.reasoning_tags;
            } else if ((params?.reasoning_tags ?? []).length === 2) {
              params.reasoning_tags = true;
            } else if ((params?.reasoning_tags ?? null) !== false) {
              params.reasoning_tags = false;
            } else {
              params.reasoning_tags = null;
            }
          }}
        >
          {#if (params?.reasoning_tags ?? null) === null}
            <span class="ml-2 self-center"> {$i18n.t('Default')} </span>
          {:else if (params?.reasoning_tags ?? null) === true}
            <span class="ml-2 self-center"> {$i18n.t('Enabled')} </span>
          {:else if (params?.reasoning_tags ?? null) === false}
            <span class="ml-2 self-center"> {$i18n.t('Disabled')} </span>
          {:else}
            <span class="ml-2 self-center"> {$i18n.t('Custom')} </span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if ![true, false, null].includes(params?.reasoning_tags ?? null) && (params?.reasoning_tags ?? []).length === 2}
      <div class="mt-1 mb-4 flex space-x-2">
        <div class=" flex-1">
          <Input
            type="text"
            placeholder={$i18n.t('Start Tag')}
            bind:value={params.reasoning_tags[0]}
            autocomplete="off"
          />
        </div>

        <div class=" flex-1">
          <Input
            type="text"
            placeholder={$i18n.t('End Tag')}
            bind:value={params.reasoning_tags[1]}
            autocomplete="off"
          />
        </div>
      </div>
    {/if}
  </div>

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t(
        'Sets the random number seed to use for generation. Setting this to a specific number will make the model generate the same text for the same prompt.',
      )}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={$i18n.t('Seed')}
        className={(params?.seed ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
          type="button"
          on:click={() => {
            params.seed = (params?.seed ?? null) === null ? defaultParams.seed : null;
          }}
        >
          {#if (params?.seed ?? null) === null}
            <span class="ml-2 self-center"> {$i18n.t('Default')} </span>
          {:else}
            <span class="ml-2 self-center"> {$i18n.t('Custom')} </span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if (params?.seed ?? null) !== null}
      <div class="mt-1 mb-4 flex space-x-2">
        <div class=" flex-1">
          <Input
            type="number"
            placeholder={$i18n.t('Enter Seed')}
            bind:value={params.seed}
            autocomplete="off"
            min="0"
          />
        </div>
      </div>
    {/if}
  </div>

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t(
        'Sets the stop sequences to use. When this pattern is encountered, the LLM will stop generating text and return. Multiple stop patterns may be set by specifying multiple separate stop parameters in a modelfile.',
      )}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={$i18n.t('Stop Sequence')}
        className={(params?.stop ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
          type="button"
          on:click={() => {
            params.stop = (params?.stop ?? null) === null ? defaultParams.stop : null;
          }}
        >
          {#if (params?.stop ?? null) === null}
            <span class="ml-2 self-center"> {$i18n.t('Default')} </span>
          {:else}
            <span class="ml-2 self-center"> {$i18n.t('Custom')} </span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if (params?.stop ?? null) !== null}
      <div class="mt-1 mb-4 flex space-x-2">
        <div class=" flex-1">
          <Input
            type="text"
            placeholder={$i18n.t('Enter stop sequence')}
            bind:value={params.stop}
            autocomplete="off"
          />
        </div>
      </div>
    {/if}
  </div>

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t(
        'The temperature of the model. Increasing the temperature will make the model answer more creatively.',
      )}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={$i18n.t('Temperature')}
        className={(params?.temperature ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
          type="button"
          on:click={() => {
            params.temperature =
              (params?.temperature ?? null) === null ? defaultParams.temperature : null;
          }}
        >
          {#if (params?.temperature ?? null) === null}
            <span class="ml-2 self-center"> {$i18n.t('Default')} </span>
          {:else}
            <span class="ml-2 self-center"> {$i18n.t('Custom')} </span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if (params?.temperature ?? null) !== null}
      <div class="mt-1 mb-4 flex space-x-2">
        <div class=" flex-1">
          <input
            id="steps-range"
            type="range"
            min="0"
            max="2"
            step="0.05"
            bind:value={params.temperature}
            class="h-2 w-full cursor-pointer rounded-lg dark:bg-gray-700"
          />
        </div>
        <div>
          <Input bind:value={params.temperature} type="number" min="0" max="2" />
        </div>
      </div>
    {/if}
  </div>

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t(
        'Constrains effort on reasoning for reasoning models. Only applicable to reasoning models from specific providers that support reasoning effort.',
      )}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={$i18n.t('Reasoning Effort')}
        className={(params?.reasoning_effort ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
          type="button"
          on:click={() => {
            params.reasoning_effort =
              (params?.reasoning_effort ?? null) === null ? defaultParams.reasoning_effort : null;
          }}
        >
          {#if (params?.reasoning_effort ?? null) === null}
            <span class="ml-2 self-center"> {$i18n.t('Default')} </span>
          {:else}
            <span class="ml-2 self-center"> {$i18n.t('Custom')} </span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if (params?.reasoning_effort ?? null) !== null}
      <div class="mt-1 mb-4 flex space-x-2">
        <div class=" flex-1">
          <Input
            type="text"
            placeholder={$i18n.t('Enter reasoning effort')}
            bind:value={params.reasoning_effort}
            autocomplete="off"
          />
        </div>
      </div>
    {/if}
  </div>

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t(
        'Boosting or penalizing specific tokens for constrained responses. Bias values will be clamped between -100 and 100 (inclusive). (Default: none)',
      )}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={'logit_bias'}
        className={(params?.logit_bias ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
          type="button"
          on:click={() => {
            params.logit_bias =
              (params?.logit_bias ?? null) === null ? defaultParams.logit_bias : null;
          }}
        >
          {#if (params?.logit_bias ?? null) === null}
            <span class="ml-2 self-center"> {$i18n.t('Default')} </span>
          {:else}
            <span class="ml-2 self-center"> {$i18n.t('Custom')} </span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if (params?.logit_bias ?? null) !== null}
      <div class="mt-1 mb-4 flex space-x-2">
        <div class=" flex-1">
          <Input
            type="text"
            placeholder={$i18n.t(
              'Enter comma-separated "token:bias_value" pairs (example: 5432:100, 413:-100)',
            )}
            bind:value={params.logit_bias}
            autocomplete="off"
          />
        </div>
      </div>
    {/if}
  </div>

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t(
        'This option sets the maximum number of tokens the model can generate in its response. Increasing this limit allows the model to provide longer answers, but it may also increase the likelihood of unhelpful or irrelevant content being generated.',
      )}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={'max_tokens'}
        className={(params?.max_tokens ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
          type="button"
          on:click={() => {
            params.max_tokens =
              (params?.max_tokens ?? null) === null ? defaultParams.max_tokens : null;
          }}
        >
          {#if (params?.max_tokens ?? null) === null}
            <span class="ml-2 self-center">{$i18n.t('Default')}</span>
          {:else}
            <span class="ml-2 self-center">{$i18n.t('Custom')}</span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if (params?.max_tokens ?? null) !== null}
      <div class="mt-1 mb-4 flex space-x-2">
        <div class=" flex-1">
          <input
            id="steps-range"
            type="range"
            min="-2"
            max="131072"
            step="1"
            bind:value={params.max_tokens}
            class="h-2 w-full cursor-pointer rounded-lg dark:bg-gray-700"
          />
        </div>
        <div>
          <Input
            bind:value={params.max_tokens}
            className="max-w-24"
            type="number"
            min="-2"
            step="1"
          />
        </div>
      </div>
    {/if}
  </div>

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t(
        'Reduces the probability of generating nonsense. A higher value (e.g. 100) will give more diverse answers, while a lower value (e.g. 10) will be more conservative.',
      )}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={'top_k'}
        className={(params?.top_k ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
          type="button"
          on:click={() => {
            params.top_k = (params?.top_k ?? null) === null ? defaultParams.top_k : null;
          }}
        >
          {#if (params?.top_k ?? null) === null}
            <span class="ml-2 self-center">{$i18n.t('Default')}</span>
          {:else}
            <span class="ml-2 self-center">{$i18n.t('Custom')}</span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if (params?.top_k ?? null) !== null}
      <div class="mt-1 mb-4 flex space-x-2">
        <div class=" flex-1">
          <input
            id="steps-range"
            type="range"
            min="0"
            max="1000"
            step="0.5"
            bind:value={params.top_k}
            class="h-2 w-full cursor-pointer rounded-lg dark:bg-gray-700"
          />
        </div>
        <div>
          <Input bind:value={params.top_k} type="number" className="max-w-16" min="0" max="100" />
        </div>
      </div>
    {/if}
  </div>

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t(
        'Works together with top-k. A higher value (e.g., 0.95) will lead to more diverse text, while a lower value (e.g., 0.5) will generate more focused and conservative text.',
      )}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={'top_p'}
        className={(params?.top_p ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
          type="button"
          on:click={() => {
            params.top_p = (params?.top_p ?? null) === null ? defaultParams.top_p : null;
          }}
        >
          {#if (params?.top_p ?? null) === null}
            <span class="ml-2 self-center">{$i18n.t('Default')}</span>
          {:else}
            <span class="ml-2 self-center">{$i18n.t('Custom')}</span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if (params?.top_p ?? null) !== null}
      <div class="mt-1 mb-4 flex space-x-2">
        <div class=" flex-1">
          <input
            id="steps-range"
            type="range"
            min="0"
            max="1"
            step="0.05"
            bind:value={params.top_p}
            class="h-2 w-full cursor-pointer rounded-lg dark:bg-gray-700"
          />
        </div>
        <div>
          <Input bind:value={params.top_p} type="number" className="max-w-16" min="0" max="1" />
        </div>
      </div>
    {/if}
  </div>

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t(
        'Alternative to the top_p, and aims to ensure a balance of quality and variety. The parameter p represents the minimum probability for a token to be considered, relative to the probability of the most likely token. For example, with p=0.05 and the most likely token having a probability of 0.9, logits with a value less than 0.045 are filtered out.',
      )}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={'min_p'}
        className={(params?.min_p ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
          type="button"
          on:click={() => {
            params.min_p = (params?.min_p ?? null) === null ? defaultParams.min_p : null;
          }}
        >
          {#if (params?.min_p ?? null) === null}
            <span class="ml-2 self-center">{$i18n.t('Default')}</span>
          {:else}
            <span class="ml-2 self-center">{$i18n.t('Custom')}</span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if (params?.min_p ?? null) !== null}
      <div class="mt-1 mb-4 flex space-x-2">
        <div class=" flex-1">
          <input
            id="steps-range"
            type="range"
            min="0"
            max="1"
            step="0.05"
            bind:value={params.min_p}
            class="h-2 w-full cursor-pointer rounded-lg dark:bg-gray-700"
          />
        </div>
        <div>
          <Input bind:value={params.min_p} type="number" className="max-w-16" min="0" max="1" />
        </div>
      </div>
    {/if}
  </div>

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t(
        'Sets a scaling bias against tokens to penalize repetitions, based on how many times they have appeared. A higher value (e.g., 1.5) will penalize repetitions more strongly, while a lower value (e.g., 0.9) will be more lenient. At 0, it is disabled.',
      )}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={'frequency_penalty'}
        className={(params?.frequency_penalty ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
          type="button"
          on:click={() => {
            params.frequency_penalty =
              (params?.frequency_penalty ?? null) === null ? defaultParams.frequency_penalty : null;
          }}
        >
          {#if (params?.frequency_penalty ?? null) === null}
            <span class="ml-2 self-center">{$i18n.t('Default')}</span>
          {:else}
            <span class="ml-2 self-center">{$i18n.t('Custom')}</span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if (params?.frequency_penalty ?? null) !== null}
      <div class="mt-1 mb-4 flex space-x-2">
        <div class=" flex-1">
          <input
            id="steps-range"
            type="range"
            min="-2"
            max="2"
            step="0.05"
            bind:value={params.frequency_penalty}
            class="h-2 w-full cursor-pointer rounded-lg dark:bg-gray-700"
          />
        </div>
        <div>
          <Input
            bind:value={params.frequency_penalty}
            type="number"
            className="max-w-16"
            min="-2"
            max="2"
          />
        </div>
      </div>
    {/if}
  </div>

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t(
        'Sets a flat bias against tokens that have appeared at least once. A higher value (e.g., 1.5) will penalize repetitions more strongly, while a lower value (e.g., 0.9) will be more lenient. At 0, it is disabled.',
      )}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={'presence_penalty'}
        className={(params?.presence_penalty ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex flex-shrink-0 rounded p-1 px-3 text-xs transition outline-none"
          type="button"
          on:click={() => {
            params.presence_penalty =
              (params?.presence_penalty ?? null) === null ? defaultParams.presence_penalty : null;
          }}
        >
          {#if (params?.presence_penalty ?? null) === null}
            <span class="ml-2 self-center">{$i18n.t('Default')}</span>
          {:else}
            <span class="ml-2 self-center">{$i18n.t('Custom')}</span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if (params?.presence_penalty ?? null) !== null}
      <div class="mt-1 mb-4 flex space-x-2">
        <div class=" flex-1">
          <input
            id="steps-range"
            type="range"
            min="-2"
            max="2"
            step="0.05"
            bind:value={params.presence_penalty}
            class="h-2 w-full cursor-pointer rounded-lg dark:bg-gray-700"
          />
        </div>
        <div>
          <Input
            bind:value={params.presence_penalty}
            type="number"
            className="max-w-16"
            min="-2"
            max="2"
          />
        </div>
      </div>
    {/if}
  </div>

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t('Enable Mirostat sampling for controlling perplexity.')}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={'mirostat'}
        className={(params?.mirostat ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
          type="button"
          on:click={() => {
            params.mirostat = (params?.mirostat ?? null) === null ? defaultParams.mirostat : null;
          }}
        >
          {#if (params?.mirostat ?? null) === null}
            <span class="ml-2 self-center">{$i18n.t('Default')}</span>
          {:else}
            <span class="ml-2 self-center">{$i18n.t('Custom')}</span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if (params?.mirostat ?? null) !== null}
      <div class="mt-1 mb-4 flex space-x-2">
        <div class=" flex-1">
          <input
            id="steps-range"
            type="range"
            min="0"
            max="2"
            step="1"
            bind:value={params.mirostat}
            class="h-2 w-full cursor-pointer rounded-lg dark:bg-gray-700"
          />
        </div>
        <div>
          <Input
            bind:value={params.mirostat}
            type="number"
            className="max-w-16"
            min="0"
            max="2"
            step="1"
          />
        </div>
      </div>
    {/if}
  </div>

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t(
        'Influences how quickly the algorithm responds to feedback from the generated text. A lower learning rate will result in slower adjustments, while a higher learning rate will make the algorithm more responsive.',
      )}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={'mirostat_eta'}
        className={(params?.mirostat_eta ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
          type="button"
          on:click={() => {
            params.mirostat_eta =
              (params?.mirostat_eta ?? null) === null ? defaultParams.mirostat_eta : null;
          }}
        >
          {#if (params?.mirostat_eta ?? null) === null}
            <span class="ml-2 self-center">{$i18n.t('Default')}</span>
          {:else}
            <span class="ml-2 self-center">{$i18n.t('Custom')}</span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if (params?.mirostat_eta ?? null) !== null}
      <div class="mt-1 mb-4 flex space-x-2">
        <div class=" flex-1">
          <input
            id="steps-range"
            type="range"
            min="0"
            max="1"
            step="0.05"
            bind:value={params.mirostat_eta}
            class="h-2 w-full cursor-pointer rounded-lg dark:bg-gray-700"
          />
        </div>
        <div>
          <Input
            bind:value={params.mirostat_eta}
            type="number"
            className="max-w-16"
            min="0"
            max="1"
          />
        </div>
      </div>
    {/if}
  </div>

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t(
        'Controls the balance between coherence and diversity of the output. A lower value will result in more focused and coherent text.',
      )}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={'mirostat_tau'}
        className={(params?.mirostat_tau ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
          type="button"
          on:click={() => {
            params.mirostat_tau =
              (params?.mirostat_tau ?? null) === null ? defaultParams.mirostat_tau : null;
          }}
        >
          {#if (params?.mirostat_tau ?? null) === null}
            <span class="ml-2 self-center">{$i18n.t('Default')}</span>
          {:else}
            <span class="ml-2 self-center">{$i18n.t('Custom')}</span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if (params?.mirostat_tau ?? null) !== null}
      <div class="mt-1 mb-4 flex space-x-2">
        <div class=" flex-1">
          <input
            id="steps-range"
            type="range"
            min="0"
            max="10"
            step="0.5"
            bind:value={params.mirostat_tau}
            class="h-2 w-full cursor-pointer rounded-lg dark:bg-gray-700"
          />
        </div>
        <div>
          <Input
            bind:value={params.mirostat_tau}
            type="number"
            className="max-w-16"
            min="0"
            max="10"
          />
        </div>
      </div>
    {/if}
  </div>

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t('Sets how far back for the model to look back to prevent repetition.')}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={'repeat_last_n'}
        className={(params?.repeat_last_n ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
          type="button"
          on:click={() => {
            params.repeat_last_n =
              (params?.repeat_last_n ?? null) === null ? defaultParams.repeat_last_n : null;
          }}
        >
          {#if (params?.repeat_last_n ?? null) === null}
            <span class="ml-2 self-center">{$i18n.t('Default')}</span>
          {:else}
            <span class="ml-2 self-center">{$i18n.t('Custom')}</span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if (params?.repeat_last_n ?? null) !== null}
      <div class="mt-1 mb-4 flex space-x-2">
        <div class=" flex-1">
          <input
            id="steps-range"
            type="range"
            min="-1"
            max="128"
            step="1"
            bind:value={params.repeat_last_n}
            class="h-2 w-full cursor-pointer rounded-lg dark:bg-gray-700"
          />
        </div>
        <div>
          <Input
            bind:value={params.repeat_last_n}
            type="number"
            className="max-w-16"
            min="-1"
            max="128"
            step="1"
          />
        </div>
      </div>
    {/if}
  </div>

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t(
        'Tail free sampling is used to reduce the impact of less probable tokens from the output. A higher value (e.g., 2.0) will reduce the impact more, while a value of 1.0 disables this setting.',
      )}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={'tfs_z'}
        className={(params?.tfs_z ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
          type="button"
          on:click={() => {
            params.tfs_z = (params?.tfs_z ?? null) === null ? defaultParams.tfs_z : null;
          }}
        >
          {#if (params?.tfs_z ?? null) === null}
            <span class="ml-2 self-center">{$i18n.t('Default')}</span>
          {:else}
            <span class="ml-2 self-center">{$i18n.t('Custom')}</span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if (params?.tfs_z ?? null) !== null}
      <div class="mt-1 mb-4 flex space-x-2">
        <div class=" flex-1">
          <input
            id="steps-range"
            type="range"
            min="0"
            max="2"
            step="0.05"
            bind:value={params.tfs_z}
            class="h-2 w-full cursor-pointer rounded-lg dark:bg-gray-700"
          />
        </div>
        <div>
          <Input bind:value={params.tfs_z} type="number" className="max-w-16" min="0" max="2" />
        </div>
      </div>
    {/if}
  </div>

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t(
        'Control the repetition of token sequences in the generated text. A higher value (e.g., 1.5) will penalize repetitions more strongly, while a lower value (e.g., 1.1) will be more lenient. At 1, it is disabled.',
      )}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={'repeat_penalty'}
        className={(params?.repeat_penalty ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex flex-shrink-0 rounded p-1 px-3 text-xs transition outline-none"
          type="button"
          on:click={() => {
            params.repeat_penalty =
              (params?.repeat_penalty ?? null) === null ? defaultParams.repeat_penalty : null;
          }}
        >
          {#if (params?.repeat_penalty ?? null) === null}
            <span class="ml-2 self-center">{$i18n.t('Default')}</span>
          {:else}
            <span class="ml-2 self-center">{$i18n.t('Custom')}</span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if (params?.repeat_penalty ?? null) !== null}
      <div class="mt-1 mb-4 flex space-x-2">
        <div class=" flex-1">
          <input
            id="steps-range"
            type="range"
            min="-2"
            max="2"
            step="0.05"
            bind:value={params.repeat_penalty}
            class="h-2 w-full cursor-pointer rounded-lg dark:bg-gray-700"
          />
        </div>
        <div>
          <Input
            bind:value={params.repeat_penalty}
            type="number"
            className="max-w-16"
            min="-2"
            max="2"
          />
        </div>
      </div>
    {/if}
  </div>

  {#if admin}
    <div class=" w-full justify-between py-0.5">
      <Tooltip
        content={$i18n.t(
          'Enable Memory Mapping (mmap) to load model data. This option allows the system to use disk storage as an extension of RAM by treating disk files as if they were in RAM. This can improve model performance by allowing for faster data access. However, it may not work correctly with all systems and can consume a significant amount of disk space.',
        )}
        placement="top-start"
        className="inline-tooltip"
      >
        <SettingItem
          label={'use_mmap'}
          className={(params?.use_mmap ?? null) !== null
            ? 'bg-accent-active/15 hover:bg-accent-active/20 rounded-b-none'
            : ''}
        >
          <button
            class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
            type="button"
            on:click={() => {
              params.use_mmap = (params?.use_mmap ?? null) === null ? defaultParams.use_mmap : null;
            }}
          >
            {#if (params?.use_mmap ?? null) === null}
              <span class="ml-2 self-center">{$i18n.t('Default')}</span>
            {:else}
              <span class="ml-2 self-center">{$i18n.t('Custom')}</span>
            {/if}
          </button>
        </SettingItem>
      </Tooltip>

      {#if (params?.use_mmap ?? null) !== null}
        <ToggleSetting
          bind:value={params.use_mmap}
          label={params.use_mmap ? $i18n.t('Enabled') : $i18n.t('Disabled')}
          className={(params?.use_mmap ?? null) !== null ? 'rounded-t-none' : ''}
        />
      {/if}
    </div>

    <div class=" w-full justify-between py-0.5">
      <Tooltip
        content={$i18n.t(
          "Enable Memory Locking (mlock) to prevent model data from being swapped out of RAM. This option locks the model's working set of pages into RAM, ensuring that they will not be swapped out to disk. This can help maintain performance by avoiding page faults and ensuring fast data access.",
        )}
        placement="top-start"
        className="inline-tooltip"
      >
        <SettingItem
          label={'use_mlock'}
          className={(params?.use_mlock ?? null) !== null
            ? 'bg-accent-active/15 hover:bg-accent-active/20 rounded-b-none'
            : ''}
        >
          <button
            class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
            type="button"
            on:click={() => {
              params.use_mlock =
                (params?.use_mlock ?? null) === null ? defaultParams.use_mlock : null;
            }}
          >
            {#if (params?.use_mlock ?? null) === null}
              <span class="ml-2 self-center">{$i18n.t('Default')}</span>
            {:else}
              <span class="ml-2 self-center">{$i18n.t('Custom')}</span>
            {/if}
          </button>
        </SettingItem>
      </Tooltip>

      {#if (params?.use_mlock ?? null) !== null}
        <ToggleSetting
          bind:value={params.use_mlock}
          label={params.use_mlock ? $i18n.t('Enabled') : $i18n.t('Disabled')}
          className={(params?.use_mlock ?? null) !== null ? 'rounded-t-none' : ''}
        />
      {/if}
    </div>
  {/if}

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t(
        'This option enables or disables the use of the reasoning feature in Ollama, which allows the model to think before generating a response. When enabled, the model can take a moment to process the conversation context and generate a more thoughtful response.',
      )}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={`think (${$i18n.t('Ollama')})`}
        className={(params?.think ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex rounded-sm p-1 px-3 text-xs transition"
          on:click={() => {
            if ((params?.think ?? null) === null) {
              params.think = defaultParams.think;
            } else if (params.think === true) {
              params.think = 'medium';
            } else if (typeof params.think === 'string') {
              params.think = false;
            } else {
              params.think = null;
            }
          }}
          type="button"
        >
          {#if params.think === true}
            <span class="ml-2 self-center">{$i18n.t('On')}</span>
          {:else if params.think === false}
            <span class="ml-2 self-center">{$i18n.t('Off')}</span>
          {:else if typeof params.think === 'string'}
            <span class="ml-2 self-center">{$i18n.t('Custom')}</span>
          {:else}
            <span class="ml-2 self-center">{$i18n.t('Default')}</span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if typeof params.think === 'string'}
      <div class="mt-1 mb-4 flex space-x-2">
        <div class=" flex-1">
          <Input
            type="text"
            placeholder={$i18n.t("e.g. 'low', 'medium', 'high'")}
            bind:value={params.think}
            autocomplete="off"
          />
        </div>
      </div>
    {/if}
  </div>

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t('The format to return a response in. Format can be json or a JSON schema.')}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={`format (${$i18n.t('Ollama')})`}
        className={(params?.format ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex rounded-sm p-1 px-3 text-xs transition"
          on:click={() => {
            params.format = (params?.format ?? null) === null ? defaultParams.format : null;
          }}
          type="button"
        >
          {#if (params?.format ?? null) === null}
            <span class="ml-2 self-center">{$i18n.t('Default')}</span>
          {:else}
            <span class="ml-2 self-center">{$i18n.t('JSON')}</span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if (params?.format ?? null) !== null}
      <div class="mt-1 mb-4 flex space-x-2">
        <Textarea
          placeholder={$i18n.t('e.g. "json" or a JSON schema')}
          bind:value={params.format}
        />
      </div>
    {/if}
  </div>

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t(
        'This option controls how many tokens are preserved when refreshing the context. For example, if set to 2, the last 2 tokens of the conversation context will be retained. Preserving context can help maintain the continuity of a conversation, but it may reduce the ability to respond to new topics.',
      )}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={`num_keep (${$i18n.t('Ollama')})`}
        className={(params?.num_keep ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
          type="button"
          on:click={() => {
            params.num_keep = (params?.num_keep ?? null) === null ? defaultParams.num_keep : null;
          }}
        >
          {#if (params?.num_keep ?? null) === null}
            <span class="ml-2 self-center">{$i18n.t('Default')}</span>
          {:else}
            <span class="ml-2 self-center">{$i18n.t('Custom')}</span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if (params?.num_keep ?? null) !== null}
      <div class="mt-1 mb-4 flex space-x-2">
        <div class=" flex-1">
          <input
            id="steps-range"
            type="range"
            min="-1"
            max="10240000"
            step="1"
            bind:value={params.num_keep}
            class="h-2 w-full cursor-pointer rounded-lg dark:bg-gray-700"
          />
        </div>
        <div class="">
          <Input
            bind:value={params.num_keep}
            type="number"
            className="max-w-16"
            min="-1"
            step="1"
          />
        </div>
      </div>
    {/if}
  </div>

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t('Sets the size of the context window used to generate the next token.')}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={`num_ctx (${$i18n.t('Ollama')})`}
        className={(params?.num_ctx ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
          type="button"
          on:click={() => {
            params.num_ctx = (params?.num_ctx ?? null) === null ? defaultParams.num_ctx : null;
          }}
        >
          {#if (params?.num_ctx ?? null) === null}
            <span class="ml-2 self-center">{$i18n.t('Default')}</span>
          {:else}
            <span class="ml-2 self-center">{$i18n.t('Custom')}</span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if (params?.num_ctx ?? null) !== null}
      <div class="mt-1 mb-4 flex space-x-2">
        <div class=" flex-1">
          <input
            id="steps-range"
            type="range"
            min="-1"
            max="10240000"
            step="1"
            bind:value={params.num_ctx}
            class="h-2 w-full cursor-pointer rounded-lg dark:bg-gray-700"
          />
        </div>
        <div class="">
          <Input bind:value={params.num_ctx} type="number" className="max-w-16" min="-1" step="1" />
        </div>
      </div>
    {/if}
  </div>

  <div class=" w-full justify-between py-0.5">
    <Tooltip
      content={$i18n.t(
        'The batch size determines how many text requests are processed together at once. A higher batch size can increase the performance and speed of the model, but it also requires more memory.',
      )}
      placement="top-start"
      className="inline-tooltip"
    >
      <SettingItem
        label={`num_batch (${$i18n.t('Ollama')})`}
        className={(params?.num_batch ?? null) !== null
          ? 'bg-accent-active/15 hover:bg-accent-active/20'
          : ''}
      >
        <button
          class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
          type="button"
          on:click={() => {
            params.num_batch =
              (params?.num_batch ?? null) === null ? defaultParams.num_batch : null;
          }}
        >
          {#if (params?.num_batch ?? null) === null}
            <span class="ml-2 self-center">{$i18n.t('Default')}</span>
          {:else}
            <span class="ml-2 self-center">{$i18n.t('Custom')}</span>
          {/if}
        </button>
      </SettingItem>
    </Tooltip>

    {#if (params?.num_batch ?? null) !== null}
      <div class="mt-1 mb-4 flex space-x-2">
        <div class=" flex-1">
          <input
            id="steps-range"
            type="range"
            min="256"
            max="8192"
            step="256"
            bind:value={params.num_batch}
            class="h-2 w-full cursor-pointer rounded-lg dark:bg-gray-700"
          />
        </div>
        <div>
          <Input
            bind:value={params.num_batch}
            type="number"
            className="max-w-16"
            min="256"
            step="256"
          />
        </div>
      </div>
    {/if}
  </div>

  {#if admin}
    <div class=" w-full justify-between py-0.5">
      <Tooltip
        content={$i18n.t(
          'Set the number of worker threads used for computation. This option controls how many threads are used to process incoming requests concurrently. Increasing this value can improve performance under high concurrency workloads but may also consume more CPU resources.',
        )}
        placement="top-start"
        className="inline-tooltip"
      >
        <SettingItem
          label={`num_thread (${$i18n.t('Ollama')})`}
          className={(params?.num_thread ?? null) !== null
            ? 'bg-accent-active/15 hover:bg-accent-active/20'
            : ''}
        >
          <button
            class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
            type="button"
            on:click={() => {
              params.num_thread =
                (params?.num_thread ?? null) === null ? defaultParams.num_thread : null;
            }}
          >
            {#if (params?.num_thread ?? null) === null}
              <span class="ml-2 self-center">{$i18n.t('Default')}</span>
            {:else}
              <span class="ml-2 self-center">{$i18n.t('Custom')}</span>
            {/if}
          </button>
        </SettingItem>
      </Tooltip>

      {#if (params?.num_thread ?? null) !== null}
        <div class="mt-1 mb-4 flex space-x-2">
          <div class=" flex-1">
            <input
              id="steps-range"
              type="range"
              min="1"
              max="256"
              step="1"
              bind:value={params.num_thread}
              class="h-2 w-full cursor-pointer rounded-lg dark:bg-gray-700"
            />
          </div>
          <div class="">
            <Input
              bind:value={params.num_thread}
              type="number"
              className="max-w-16"
              min="1"
              max="256"
              step="1"
            />
          </div>
        </div>
      {/if}
    </div>

    <div class=" w-full justify-between py-0.5">
      <Tooltip
        content={$i18n.t(
          'Set the number of layers, which will be off-loaded to GPU. Increasing this value can significantly improve performance for models that are optimized for GPU acceleration but may also consume more power and GPU resources.',
        )}
        placement="top-start"
        className="inline-tooltip"
      >
        <SettingItem
          label={`num_gpu (${$i18n.t('Ollama')})`}
          className={(params?.num_gpu ?? null) !== null
            ? 'bg-accent-active/15 hover:bg-accent-active/20'
            : ''}
        >
          <button
            class="flex shrink-0 rounded-sm p-1 px-3 text-xs outline-hidden transition"
            type="button"
            on:click={() => {
              params.num_gpu = (params?.num_gpu ?? null) === null ? defaultParams.num_gpu : null;
            }}
          >
            {#if (params?.num_gpu ?? null) === null}
              <span class="ml-2 self-center">{$i18n.t('Default')}</span>
            {:else}
              <span class="ml-2 self-center">{$i18n.t('Custom')}</span>
            {/if}
          </button>
        </SettingItem>
      </Tooltip>

      {#if (params?.num_gpu ?? null) !== null}
        <div class="mt-1 mb-4 flex space-x-2">
          <div class=" flex-1">
            <input
              id="steps-range"
              type="range"
              min="0"
              max="256"
              step="1"
              bind:value={params.num_gpu}
              class="h-2 w-full cursor-pointer rounded-lg dark:bg-gray-700"
            />
          </div>
          <div class="">
            <Input
              bind:value={params.num_gpu}
              type="number"
              className="max-w-16"
              min="0"
              max="256"
              step="1"
            />
          </div>
        </div>
      {/if}
    </div>

    <div class=" w-full justify-between py-0.5">
      <Tooltip
        content={$i18n.t(
          'This option controls how long the model will stay loaded into memory following the request (default: 5m)',
        )}
        placement="top-start"
        className="inline-tooltip"
      >
        <SettingItem
          label={`keep_alive (${$i18n.t('Ollama')})`}
          className={(params?.keep_alive ?? null) !== null
            ? 'bg-accent-active/15 hover:bg-accent-active/20'
            : ''}
        >
          <button
            class="flex rounded-sm p-1 px-3 text-xs transition"
            on:click={() => {
              params.keep_alive =
                (params?.keep_alive ?? null) === null ? defaultParams.keep_alive : null;
            }}
            type="button"
          >
            {#if (params?.keep_alive ?? null) === null}
              <span class="ml-2 self-center">{$i18n.t('Default')}</span>
            {:else}
              <span class="ml-2 self-center">{$i18n.t('Custom')}</span>
            {/if}
          </button>
        </SettingItem>
      </Tooltip>

      {#if (params?.keep_alive ?? null) !== null}
        <div class="mt-1 mb-4 flex space-x-2">
          <Input
            type="text"
            placeholder={$i18n.t("e.g. '30s','10m'. Valid time units are 's', 'm', 'h'.")}
            bind:value={params.keep_alive}
          />
        </div>
      {/if}
    </div>

    {#if custom && admin}
      <div class="flex flex-col justify-center gap-2">
        {#each Object.keys(params?.custom_params ?? {}) as key}
          <div class="bg-card border-border mb-1 w-full justify-between rounded-2xl border p-2">
            <div class="flex w-full justify-between gap-2">
              <Input
                type="text"
                placeholder={$i18n.t('Custom Parameter Name')}
                value={key}
                on:change={(e) => {
                  const newKey = e.target.value.trim();
                  if (newKey && newKey !== key) {
                    params.custom_params[newKey] = params.custom_params[key];
                    delete params.custom_params[key];
                    params = {
                      ...params,
                      custom_params: { ...params.custom_params },
                    };
                  }
                }}
              />
              <Button
                size="sm"
                type="button"
                className="shrink-0"
                on:click={() => {
                  delete params.custom_params[key];
                  params = {
                    ...params,
                    custom_params: { ...params.custom_params },
                  };
                }}
              >
                {$i18n.t('Remove')}
              </Button>
            </div>
            <div class="mt-1 flex space-x-2">
              <div class=" flex-1">
                <Input
                  bind:value={params.custom_params[key]}
                  type="text"
                  placeholder={$i18n.t('Custom Parameter Value')}
                />
              </div>
            </div>
          </div>
        {/each}

        <Button
          size="sm"
          variant="ghost"
          type="button"
          radius="lg"
          className="mb-2"
          on:click={() => {
            params.custom_params = (params?.custom_params ?? {}) || {};
            params.custom_params['custom_param_name'] = 'custom_param_value';
          }}
        >
          <Plus />
          <div>{$i18n.t('Add Custom Parameter')}</div>
        </Button>
      </div>
    {/if}
  {/if}
</div>
