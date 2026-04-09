<script lang="ts">
  import { toast } from 'svelte-sonner';
  import { createEventDispatcher, onMount, getContext } from 'svelte';

  import { user, settings, config } from '$lib/stores';
  import { getVoices as _getVoices } from '$lib/apis/audio';

  import Switch from '$lib/components/common/Switch.svelte';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import SettingItem from '$lib/components/common/SettingItem.svelte';
  import ToggleSetting from '$lib/components/common/ToggleSetting.svelte';
  import Button from '$lib/components/common/Button.svelte';
  const dispatch = createEventDispatcher();

  const i18n = getContext('i18n');

  export let saveSettings: Function;

  // Audio
  let conversationMode = false;
  let speechAutoSend = false;
  let responseAutoPlayback = false;
  let nonLocalVoices = false;

  let STTEngine = '';
  let STTLanguage = '';

  let TTSEngine = '';
  let TTSEngineConfig = {};

  let TTSModel = null;
  let TTSModelProgress = null;
  let TTSModelLoading = false;

  let voices = [];
  let voice = '';

  // Audio speed control
  let playbackRate = 1;

  const getVoices = async () => {
    if (TTSEngine === 'browser-kokoro') {
      if (!TTSModel) {
        await loadKokoro();
      }

      voices = Object.entries(TTSModel.voices).map(([key, value]) => {
        return {
          id: key,
          name: value.name,
          localService: false,
        };
      });
    } else {
      if ($config.audio.tts.engine === '') {
        const getVoicesLoop = setInterval(async () => {
          voices = await speechSynthesis.getVoices();

          // do your loop
          if (voices.length > 0) {
            clearInterval(getVoicesLoop);
          }
        }, 100);
      } else {
        const res = await _getVoices(localStorage.token).catch((e) => {
          toast.error(`${e}`);
        });

        if (res) {
          console.log(res);
          voices = res.voices;
        }
      }
    }
  };

  const toggleResponseAutoPlayback = async () => {
    responseAutoPlayback = !responseAutoPlayback;
    saveSettings({ responseAutoPlayback: responseAutoPlayback });
  };

  const toggleSpeechAutoSend = async () => {
    speechAutoSend = !speechAutoSend;
    saveSettings({ speechAutoSend: speechAutoSend });
  };

  onMount(async () => {
    playbackRate = $settings.audio?.tts?.playbackRate ?? 1;
    conversationMode = $settings.conversationMode ?? false;
    speechAutoSend = $settings.speechAutoSend ?? false;
    responseAutoPlayback = $settings.responseAutoPlayback ?? false;

    STTEngine = $settings?.audio?.stt?.engine ?? '';
    STTLanguage = $settings?.audio?.stt?.language ?? '';

    TTSEngine = $settings?.audio?.tts?.engine ?? '';
    TTSEngineConfig = $settings?.audio?.tts?.engineConfig ?? {};

    if ($settings?.audio?.tts?.defaultVoice === $config.audio.tts.voice) {
      voice = $settings?.audio?.tts?.voice ?? $config.audio.tts.voice ?? '';
    } else {
      voice = $config.audio.tts.voice ?? '';
    }

    nonLocalVoices = $settings.audio?.tts?.nonLocalVoices ?? false;

    await getVoices();
  });

  $: if (TTSEngine && TTSEngineConfig) {
    onTTSEngineChange();
  }

  const onTTSEngineChange = async () => {
    if (TTSEngine === 'browser-kokoro') {
      await loadKokoro();
    }
  };

  const loadKokoro = async () => {
    if (TTSEngine === 'browser-kokoro') {
      voices = [];

      if (TTSEngineConfig?.dtype) {
        TTSModel = null;
        TTSModelProgress = null;
        TTSModelLoading = true;

        const model_id = 'onnx-community/Kokoro-82M-v1.0-ONNX';

        const { KokoroTTS } = await import('kokoro-js');
        TTSModel = await KokoroTTS.from_pretrained(model_id, {
          dtype: TTSEngineConfig.dtype, // Options: "fp32", "fp16", "q8", "q4", "q4f16"
          device: !!navigator?.gpu ? 'webgpu' : 'wasm', // Detect WebGPU
          progress_callback: (e) => {
            TTSModelProgress = e;
            console.log(e);
          },
        });

        await getVoices();

        // const rawAudio = await tts.generate(inputText, {
        // 	// Use `tts.list_voices()` to list all available voices
        // 	voice: voice
        // });

        // const blobUrl = URL.createObjectURL(await rawAudio.toBlob());
        // const audio = new Audio(blobUrl);

        // audio.play();
      }
    }
  };
</script>

<form
  id="tab-audio"
  class="flex h-full flex-col justify-between space-y-3 text-sm"
  on:submit|preventDefault={async () => {
    saveSettings({
      audio: {
        stt: {
          engine: STTEngine !== '' ? STTEngine : undefined,
          language: STTLanguage !== '' ? STTLanguage : undefined,
        },
        tts: {
          engine: TTSEngine !== '' ? TTSEngine : undefined,
          engineConfig: TTSEngineConfig,
          playbackRate: playbackRate,
          voice: voice !== '' ? voice : undefined,
          defaultVoice: $config?.audio?.tts?.voice ?? '',
          nonLocalVoices: $config.audio.tts.engine === '' ? nonLocalVoices : undefined,
        },
      },
    });
    dispatch('save');
  }}
>
  <div class=" max-h-[28rem] space-y-3 overflow-y-scroll md:max-h-full">
    <div class="space-y-1 px-1">
      <h1 class="my-2 border-b border-gray-300 pb-2 text-base font-medium dark:border-gray-800">
        {$i18n.t('STT Settings')}
      </h1>

      {#if $config.audio.stt.engine !== 'web'}
        <SettingItem label={$i18n.t('Speech-to-Text Engine')} labelId="stt-engine-label">
          <select
            class="w-fit rounded-sm bg-transparent p-1 px-2 pr-8 text-right text-xs outline-hidden"
            bind:value={STTEngine}
            aria-label={$i18n.t('Speech-to-Text Engine')}
            placeholder={$i18n.t('Select an engine')}
          >
            <option value="">{$i18n.t('Default')}</option>
            <option value="web">{$i18n.t('Web API')}</option>
          </select>
        </SettingItem>

        <SettingItem label={$i18n.t('Language')} labelId="stt-language-label">
          <Tooltip
            content={$i18n.t(
              'The language of the input audio. Supplying the input language in ISO-639-1 (e.g. en) format will improve accuracy and latency. Leave blank to automatically detect the language.',
            )}
            placement="top"
          >
            <input
              type="text"
              bind:value={STTLanguage}
              aria-label={$i18n.t('Speech-to-Text Language')}
              placeholder={$i18n.t('e.g. en')}
              class=" bg-transparent text-right text-sm outline-hidden dark:text-gray-300"
            />
          </Tooltip>
        </SettingItem>
      {/if}

      <SettingItem
        label={$i18n.t('Instant Auto-Send After Voice Transcription')}
        labelId="stt-auto-send-label"
      >
        <button
          class="flex rounded-sm p-1 px-3 text-xs transition"
          on:click={() => {
            toggleSpeechAutoSend();
          }}
          type="button"
          role="switch"
          aria-checked={speechAutoSend}
        >
          {#if speechAutoSend === true}
            <span class="ml-2 self-center">{$i18n.t('On')}</span>
          {:else}
            <span class="ml-2 self-center">{$i18n.t('Off')}</span>
          {/if}
        </button>
      </SettingItem>
    </div>

    <h1 class="my-2 border-b border-gray-300 pb-2 text-base font-medium dark:border-gray-800">
      {$i18n.t('TTS Settings')}
    </h1>

    <SettingItem label={$i18n.t('Text-to-Speech Engine')} labelId="tts-engine-label">
      <select
        class="w-fit rounded-sm bg-transparent p-1 px-2 pr-8 text-right text-xs outline-hidden"
        bind:value={TTSEngine}
        aria-label={$i18n.t('Text-to-Speech Engine')}
        placeholder={$i18n.t('Select an engine')}
      >
        <option value="">{$i18n.t('Default')}</option>
        <option value="browser-kokoro">{$i18n.t('Kokoro.js (Browser)')}</option>
      </select>
    </SettingItem>

    {#if TTSEngine === 'browser-kokoro'}
      <SettingItem label={$i18n.t('Kokoro.js Dtype')} labelId="tts-engine-config-dtype-label">
        <select
          class="w-fit rounded-sm bg-transparent p-1 px-2 pr-8 text-right text-xs outline-hidden"
          bind:value={TTSEngineConfig.dtype}
          aria-label={$i18n.t('Kokoro.js Dtype')}
          placeholder={$i18n.t('Select dtype')}
        >
          <option value="" disabled selected>{$i18n.t('Select dtype')}</option>
          <option value="fp32">fp32</option>
          <option value="fp16">fp16</option>
          <option value="q8">q8</option>
          <option value="q4">q4</option>
        </select>
      </SettingItem>
    {/if}

    <SettingItem label={$i18n.t('Auto-playback response')} labelId="tts-auto-playback-label">
      <button
        class="flex rounded-sm p-1 px-3 text-xs transition"
        on:click={() => {
          toggleResponseAutoPlayback();
        }}
        type="button"
        role="switch"
        aria-checked={responseAutoPlayback}
      >
        {#if responseAutoPlayback === true}
          <span class="ml-2 self-center">{$i18n.t('On')}</span>
        {:else}
          <span class="ml-2 self-center">{$i18n.t('Off')}</span>
        {/if}
      </button>
    </SettingItem>

    <SettingItem label={$i18n.t('Speech Playback Speed')} labelId="tts-playback-speed-label">
      <div class="relative flex items-center px-3 text-xs">
        <input
          type="number"
          min="0"
          step="0.01"
          bind:value={playbackRate}
          aria-label={$i18n.t('Speech Playback Speed')}
          class=" bg-transparent text-right text-sm outline-hidden dark:text-gray-300"
        />
        x
      </div>
    </SettingItem>

    <hr class=" dark:border-gray-850/30 border-gray-100/30" />

    {#if TTSEngine === 'browser-kokoro'}
      {#if TTSModel}
        <SettingItem label={$i18n.t('Set Voice')} labelId="tts-voice-label">
          <div class="w-full">
            <input
              list="voice-list"
              class="w-full bg-transparent text-sm outline-hidden dark:text-gray-300"
              bind:value={voice}
              aria-label={$i18n.t('Voice')}
              placeholder={$i18n.t('Select a voice')}
            />

            <datalist id="voice-list">
              {#each voices as voice}
                <option value={voice.id}>{voice.name}</option>
              {/each}
            </datalist>
          </div>
        </SettingItem>
      {:else}
        <div>
          <div class=" mb-2.5 flex items-center gap-2 text-sm font-medium">
            <Spinner className="size-4" />

            <div class=" shimmer text-sm font-medium">
              {$i18n.t('Loading Kokoro.js...')}
              {TTSModelProgress && TTSModelProgress.status === 'progress'
                ? `(${Math.round(TTSModelProgress.progress * 10) / 10}%)`
                : ''}
            </div>
          </div>

          <div class="text-xs text-gray-500">
            {$i18n.t('Please do not close the settings page while loading the model.')}
          </div>
        </div>
      {/if}
    {:else if $config.audio.tts.engine === ''}
      <SettingItem label={$i18n.t('Set Voice')} labelId="tts-voice-label">
        <select
          class="w-fullp-1 rounded-lg bg-gray-100 px-2 py-1 text-sm outline-hidden dark:bg-gray-950! dark:text-gray-300!"
          bind:value={voice}
          aria-label={$i18n.t('Voice')}
        >
          <option value="" selected={voice !== ''}>{$i18n.t('Default')}</option>
          {#each voices.filter((v) => nonLocalVoices || v.localService === true) as _voice}
            <option
              value={_voice.name}
              class="bg-gray-100 dark:bg-gray-700"
              selected={voice === _voice.name}>{_voice.name}</option
            >
          {/each}
        </select>
      </SettingItem>
      <ToggleSetting
        label={$i18n.t('Allow non-local voices')}
        labelId="tts-allow-non-local-voices-label"
        bind:state={nonLocalVoices}
      />
    {:else if $config.audio.tts.engine !== ''}
      <SettingItem label={$i18n.t('Set Voice')} labelId="tts-voice-label">
        <div class="flex-1">
          <input
            list="voice-list"
            class="w-full bg-gray-100 p-1 px-2 text-sm outline-hidden dark:bg-gray-700 dark:text-gray-300"
            bind:value={voice}
            aria-label={$i18n.t('Voice')}
            placeholder={$i18n.t('Select a voice')}
          />

          <datalist id="voice-list">
            {#each voices as voice}
              <option value={voice.id}>{voice.name}</option>
            {/each}
          </datalist>
        </div>
      </SettingItem>
    {/if}
  </div>

  <div class="flex justify-end p-2">
    <Button type="submit" radius="xl">
      {$i18n.t('Save')}
    </Button>
  </div>
</form>
