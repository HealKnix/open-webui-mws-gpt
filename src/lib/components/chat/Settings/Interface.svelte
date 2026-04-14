<script lang="ts">
  import { config, models, settings, user } from '$lib/stores';
  import { createEventDispatcher, onMount, onDestroy, getContext, tick } from 'svelte';
  import { toast } from 'svelte-sonner';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import { updateUserInfo } from '$lib/apis/users';
  import { getUserPosition } from '$lib/utils';
  import { setTextScale } from '$lib/utils/text-scale';

  import Minus from '$lib/components/icons/Minus.svelte';
  import Plus from '$lib/components/icons/Plus.svelte';
  import ToggleSetting from '$lib/components/common/ToggleSetting.svelte';
  import SettingItem from '$lib/components/common/SettingItem.svelte';
  import ManageFloatingActionButtonsModal from './Interface/ManageFloatingActionButtonsModal.svelte';
  import ManageImageCompressionModal from './Interface/ManageImageCompressionModal.svelte';
  import Button from '$lib/components/common/Button.svelte';

  const dispatch = createEventDispatcher();

  const i18n = getContext('i18n');

  export let saveSettings: Function;

  let backgroundImageUrl = null;
  let inputFiles = null;
  let filesInputElement;

  // Addons
  let titleAutoGenerate = true;
  let autoFollowUps = true;
  let autoTags = true;

  let responseAutoCopy = false;
  let widescreenMode = false;
  let splitLargeChunks = false;
  let scrollOnBranchChange = true;
  let userLocation = false;

  // Interface
  let defaultModelId = '';
  let showUsername = false;

  let notificationSound = true;
  let notificationSoundAlways = false;

  let highContrastMode = false;

  let detectArtifacts = true;
  let displayMultiModelResponsesInTabs = false;

  let richTextInput = true;
  let showFormattingToolbar = false;
  let insertPromptAsRichText = false;
  let promptAutocomplete = false;

  let largeTextAsFile = false;

  let insertSuggestionPrompt = false;
  let keepFollowUpPrompts = false;
  let insertFollowUpPrompt = false;

  let regenerateMenu = true;
  let enableMessageQueue = true;

  let landingPageMode = '';
  let chatBubble = true;
  let chatDirection: 'LTR' | 'RTL' | 'auto' = 'auto';
  let ctrlEnterToSend = false;
  let copyFormatted = false;

  let temporaryChatByDefault = false;
  let chatFadeStreamingText = true;
  let collapseCodeBlocks = false;
  let expandDetails = false;
  let renderMarkdownInPreviews = true;
  let showChatTitleInTab = true;

  let showFloatingActionButtons = true;
  let floatingActionButtons = null;

  let imageCompression = false;
  let imageCompressionSize = {
    width: '',
    height: '',
  };
  let imageCompressionInChannels = true;

  // chat export
  let stylizedPdfExport = true;

  // Admin - Show Update Available Toast
  let showUpdateToast = true;
  let showChangelog = true;

  let showEmojiInCall = false;
  let voiceInterruption = false;
  let hapticFeedback = false;

  let webSearch = null;

  let iframeSandboxAllowSameOrigin = false;
  let iframeSandboxAllowForms = false;

  let showManageFloatingActionButtonsModal = false;
  let showManageImageCompressionModal = false;

  let textScale = null;

  const toggleLandingPageMode = async () => {
    landingPageMode = landingPageMode === '' ? 'chat' : '';
    saveSettings({ landingPageMode: landingPageMode });
  };

  const toggleUserLocation = async () => {
    if (userLocation) {
      const position = await getUserPosition().catch((error) => {
        toast.error(error.message);
        return null;
      });

      if (position) {
        await updateUserInfo(localStorage.token, { location: position });
        toast.success($i18n.t('User location successfully retrieved.'));
      } else {
        userLocation = false;
      }
    }

    saveSettings({ userLocation });
  };

  const toggleTitleAutoGenerate = async () => {
    saveSettings({
      title: {
        ...$settings.title,
        auto: titleAutoGenerate,
      },
    });
  };

  const toggleResponseAutoCopy = async () => {
    const permission = await navigator.clipboard
      .readText()
      .then(() => {
        return 'granted';
      })
      .catch(() => {
        return '';
      });

    if (permission === 'granted') {
      saveSettings({ responseAutoCopy: responseAutoCopy });
    } else {
      responseAutoCopy = false;
      toast.error(
        $i18n.t(
          'Clipboard write permission denied. Please check your browser settings to grant the necessary access.',
        ),
      );
    }
  };

  const toggleChangeChatDirection = async () => {
    if (chatDirection === 'auto') {
      chatDirection = 'LTR';
    } else if (chatDirection === 'LTR') {
      chatDirection = 'RTL';
    } else if (chatDirection === 'RTL') {
      chatDirection = 'auto';
    }
    saveSettings({ chatDirection });
  };

  const togglectrlEnterToSend = async () => {
    ctrlEnterToSend = !ctrlEnterToSend;
    saveSettings({ ctrlEnterToSend });
  };

  const updateInterfaceHandler = async () => {
    saveSettings({
      models: [defaultModelId],
      imageCompressionSize: imageCompressionSize,
    });
  };

  const toggleWebSearch = async () => {
    webSearch = webSearch === null ? 'always' : null;
    saveSettings({ webSearch: webSearch });
  };

  const setTextScaleHandler = (scale) => {
    textScale = scale;
    setTextScale(textScale);

    if (textScale === 1) {
      textScale = null;
    }
    saveSettings({ textScale });
  };

  onMount(async () => {
    titleAutoGenerate = $settings?.title?.auto ?? true;
    autoTags = $settings?.autoTags ?? true;
    autoFollowUps = $settings?.autoFollowUps ?? true;

    highContrastMode = $settings?.highContrastMode ?? false;

    detectArtifacts = $settings?.detectArtifacts ?? true;
    responseAutoCopy = $settings?.responseAutoCopy ?? false;

    showUsername = $settings?.showUsername ?? false;
    showUpdateToast = $settings?.showUpdateToast ?? true;
    showChangelog = $settings?.showChangelog ?? true;

    showEmojiInCall = $settings?.showEmojiInCall ?? false;
    voiceInterruption = $settings?.voiceInterruption ?? false;

    displayMultiModelResponsesInTabs = $settings?.displayMultiModelResponsesInTabs ?? false;
    chatFadeStreamingText = $settings?.chatFadeStreamingText ?? true;

    richTextInput = $settings?.richTextInput ?? true;
    showFormattingToolbar = $settings?.showFormattingToolbar ?? false;
    insertPromptAsRichText = $settings?.insertPromptAsRichText ?? false;
    promptAutocomplete = $settings?.promptAutocomplete ?? false;

    insertSuggestionPrompt = $settings?.insertSuggestionPrompt ?? false;
    keepFollowUpPrompts = $settings?.keepFollowUpPrompts ?? false;
    insertFollowUpPrompt = $settings?.insertFollowUpPrompt ?? false;

    regenerateMenu = $settings?.regenerateMenu ?? true;
    enableMessageQueue = $settings?.enableMessageQueue ?? true;

    largeTextAsFile = $settings?.largeTextAsFile ?? false;
    copyFormatted = $settings?.copyFormatted ?? false;

    collapseCodeBlocks = $settings?.collapseCodeBlocks ?? false;
    expandDetails = $settings?.expandDetails ?? false;
    renderMarkdownInPreviews = $settings?.renderMarkdownInPreviews ?? true;

    landingPageMode = $settings?.landingPageMode ?? '';
    chatBubble = $settings?.chatBubble ?? true;
    widescreenMode = $settings?.widescreenMode ?? false;
    splitLargeChunks = $settings?.splitLargeChunks ?? false;
    scrollOnBranchChange = $settings?.scrollOnBranchChange ?? true;

    temporaryChatByDefault = $settings?.temporaryChatByDefault ?? false;
    chatDirection = $settings?.chatDirection ?? 'auto';
    userLocation = $settings?.userLocation ?? false;
    showChatTitleInTab = $settings?.showChatTitleInTab ?? true;

    notificationSound = $settings?.notificationSound ?? true;
    notificationSoundAlways = $settings?.notificationSoundAlways ?? false;

    iframeSandboxAllowSameOrigin = $settings?.iframeSandboxAllowSameOrigin ?? false;
    iframeSandboxAllowForms = $settings?.iframeSandboxAllowForms ?? false;

    stylizedPdfExport = $settings?.stylizedPdfExport ?? true;

    hapticFeedback = $settings?.hapticFeedback ?? false;
    ctrlEnterToSend = $settings?.ctrlEnterToSend ?? false;

    showFloatingActionButtons = $settings?.showFloatingActionButtons ?? true;
    floatingActionButtons = $settings?.floatingActionButtons ?? null;

    imageCompression = $settings?.imageCompression ?? false;
    imageCompressionSize = $settings?.imageCompressionSize ?? { width: '', height: '' };
    imageCompressionInChannels = $settings?.imageCompressionInChannels ?? true;

    defaultModelId = $settings?.models?.at(0) ?? '';
    if ($config?.default_models) {
      defaultModelId = $config.default_models.split(',')[0];
    }

    backgroundImageUrl = $settings?.backgroundImageUrl ?? null;
    webSearch = $settings?.webSearch ?? null;

    textScale = $settings?.textScale ?? null;
  });
</script>

<ManageFloatingActionButtonsModal
  bind:show={showManageFloatingActionButtonsModal}
  {floatingActionButtons}
  onSave={(buttons) => {
    floatingActionButtons = buttons;
    saveSettings({ floatingActionButtons });
  }}
/>

<ManageImageCompressionModal
  bind:show={showManageImageCompressionModal}
  size={imageCompressionSize}
  onSave={(size) => {
    saveSettings({ imageCompressionSize: size });
  }}
/>

<form
  id="tab-interface"
  class="flex h-full flex-col justify-between space-y-3 text-sm"
  on:submit|preventDefault={() => {
    updateInterfaceHandler();
    dispatch('save');
  }}
>
  <input
    bind:this={filesInputElement}
    bind:files={inputFiles}
    type="file"
    hidden
    accept="image/*"
    on:change={() => {
      let reader = new FileReader();
      reader.onload = (event) => {
        let originalImageUrl = `${event.target.result}`;

        backgroundImageUrl = originalImageUrl;
        saveSettings({ backgroundImageUrl });
      };

      if (
        inputFiles &&
        inputFiles.length > 0 &&
        ['image/gif', 'image/webp', 'image/jpeg', 'image/png'].includes(inputFiles[0]['type'])
      ) {
        reader.readAsDataURL(inputFiles[0]);
      } else {
        console.log(`Unsupported File Type '${inputFiles[0]['type']}'.`);
        inputFiles = null;
      }
    }}
  />

  <div class=" max-h-[28rem] space-y-4 overflow-y-scroll md:max-h-full">
    <div class="space-y-1 px-1">
      <div
        class="my-2 mb-4 border-b border-gray-300 pb-1 text-base font-medium dark:border-gray-800"
      >
        {$i18n.t('UI')}
      </div>

      <SettingItem label={$i18n.t('UI Scale')} labelId="ui-scale-label">
        <div class="flex items-center gap-2 p-1 text-xs">
          <button
            aria-live="polite"
            type="button"
            on:click={() => {
              if (textScale === null) {
                textScale = 1;
              } else {
                textScale = null;
                setTextScaleHandler(1);
              }
            }}
          >
            {#if textScale === null}
              <span>{$i18n.t('Default')}</span>
            {:else}
              <span>{textScale}x</span>
            {/if}
          </button>
        </div>
      </SettingItem>

      {#if textScale !== null}
        <div class=" flex items-center gap-2 px-1 pb-1">
          <button
            type="button"
            class="rounded-lg p-1 outline-gray-200 transition hover:bg-gray-100 dark:outline-gray-700 dark:hover:bg-gray-800"
            on:click={() => {
              textScale = Math.max(1, parseFloat((textScale - 0.1).toFixed(2)));
              setTextScaleHandler(textScale);
            }}
            aria-labelledby="ui-scale-label"
            aria-label={$i18n.t('Decrease UI Scale')}
          >
            <Minus className="h-3.5 w-3.5" />
          </button>

          <div class="flex flex-1 items-center">
            <input
              id="ui-scale-slider"
              class="w-full"
              type="range"
              min="1"
              max="1.5"
              step={0.01}
              bind:value={textScale}
              on:change={() => {
                setTextScaleHandler(textScale);
              }}
              aria-labelledby="ui-scale-label"
              aria-valuemin="1"
              aria-valuemax="1.5"
              aria-valuenow={textScale}
              aria-valuetext={`${textScale}x`}
            />
          </div>

          <button
            type="button"
            class="rounded-lg p-1 outline-gray-200 transition hover:bg-gray-100 dark:outline-gray-700 dark:hover:bg-gray-800"
            on:click={() => {
              textScale = Math.min(1.5, parseFloat((textScale + 0.1).toFixed(2)));
              setTextScaleHandler(textScale);
            }}
            aria-labelledby="ui-scale-label"
            aria-label={$i18n.t('Increase UI Scale')}
          >
            <Plus className="h-3.5 w-3.5" />
          </button>
        </div>
      {/if}

      <ToggleSetting
        label="{$i18n.t('High Contrast Mode')} ({$i18n.t('Beta')})"
        bind:state={highContrastMode}
        on:change={() => {
          saveSettings({ highContrastMode });
        }}
        tooltip={true}
      />

      <ToggleSetting
        label={$i18n.t('Display chat title in tab')}
        bind:state={showChatTitleInTab}
        on:change={() => {
          saveSettings({ showChatTitleInTab });
        }}
        tooltip={true}
      />

      <ToggleSetting
        label={$i18n.t('Notification Sound')}
        bind:state={notificationSound}
        on:change={() => {
          saveSettings({ notificationSound });
        }}
        tooltip={true}
      />

      {#if notificationSound}
        <ToggleSetting
          label={$i18n.t('Always Play Notification Sound')}
          bind:state={notificationSoundAlways}
          on:change={() => {
            saveSettings({ notificationSoundAlways });
          }}
          tooltip={true}
        />
      {/if}

      <ToggleSetting
        label={$i18n.t('Allow User Location')}
        bind:state={userLocation}
        on:change={() => {
          toggleUserLocation();
        }}
        tooltip={true}
      />

      <ToggleSetting
        label={$i18n.t('Haptic Feedback')}
        bind:state={hapticFeedback}
        on:change={() => {
          saveSettings({ hapticFeedback });
        }}
        tooltip={true}
      >
        <div slot="label" class="ml-1 text-xs text-gray-500">({$i18n.t('Android')})</div>
      </ToggleSetting>

      <ToggleSetting
        label={$i18n.t('Copy Formatted Text')}
        bind:state={copyFormatted}
        on:change={() => {
          saveSettings({ copyFormatted });
        }}
        tooltip={true}
      />

      {#if $user?.role === 'admin'}
        <ToggleSetting
          label={$i18n.t('Toast notifications for new updates')}
          bind:state={showUpdateToast}
          on:change={() => {
            saveSettings({ showUpdateToast });
          }}
          tooltip={true}
        />

        <ToggleSetting
          label={$i18n.t(`Show "What's New" modal on login`)}
          bind:state={showChangelog}
          on:change={() => {
            saveSettings({ showChangelog });
          }}
          tooltip={true}
        />
      {/if}

      <div
        class="my-2 mb-4 border-b border-gray-300 pb-1 text-base font-medium dark:border-gray-800"
      >
        {$i18n.t('Chat')}
      </div>

      <ToggleSetting
        label={$i18n.t('Enable Message Queue')}
        bind:state={enableMessageQueue}
        on:change={() => {
          saveSettings({ enableMessageQueue });
        }}
        tooltip={true}
      />

      <SettingItem label={$i18n.t('Chat direction')}>
        <button on:click={toggleChangeChatDirection} type="button">
          <span class="self-center">
            {chatDirection === 'LTR'
              ? $i18n.t('LTR')
              : chatDirection === 'RTL'
                ? $i18n.t('RTL')
                : $i18n.t('Auto')}
          </span>
        </button>
      </SettingItem>

      <SettingItem label={$i18n.t('Landing Page Mode')}>
        <button
          on:click={() => {
            toggleLandingPageMode();
          }}
          type="button"
        >
          <span class="self-center"
            >{landingPageMode === '' ? $i18n.t('Default') : $i18n.t('Chat')}</span
          >
        </button>
      </SettingItem>

      <SettingItem label={$i18n.t('Chat Background Image')}>
        <button
          on:click={() => {
            if (backgroundImageUrl !== null) {
              backgroundImageUrl = null;
              saveSettings({ backgroundImageUrl });
            } else {
              filesInputElement.click();
            }
          }}
          type="button"
        >
          <span class="self-center"
            >{backgroundImageUrl !== null ? $i18n.t('Reset') : $i18n.t('Upload')}</span
          >
        </button>
      </SettingItem>

      <ToggleSetting
        label={$i18n.t('Chat Bubble UI')}
        bind:state={chatBubble}
        on:change={() => {
          saveSettings({ chatBubble });
        }}
        tooltip={true}
      />

      {#if !$settings.chatBubble}
        <ToggleSetting
          label={$i18n.t('Display the username instead of You in the Chat')}
          bind:state={showUsername}
          on:change={() => {
            saveSettings({ showUsername });
          }}
          tooltip={true}
        />
      {/if}

      <ToggleSetting
        label={$i18n.t('Widescreen Mode')}
        bind:state={widescreenMode}
        on:change={() => {
          saveSettings({ widescreenMode });
        }}
        tooltip={true}
      />

      {#if $user.role === 'admin' || $user?.permissions?.chat?.temporary}
        <ToggleSetting
          label={$i18n.t('Temporary Chat by Default')}
          bind:state={temporaryChatByDefault}
          on:change={() => {
            saveSettings({ temporaryChatByDefault });
          }}
          tooltip={true}
        />
      {/if}

      <ToggleSetting
        label={$i18n.t('Fade Effect for Streaming Text')}
        bind:state={chatFadeStreamingText}
        on:change={() => {
          saveSettings({ chatFadeStreamingText });
        }}
        tooltip={true}
      />

      <ToggleSetting
        label={$i18n.t('Title Auto-Generation')}
        bind:state={titleAutoGenerate}
        on:change={() => {
          toggleTitleAutoGenerate();
        }}
        tooltip={true}
      />

      <ToggleSetting
        label={$i18n.t('Follow-Up Auto-Generation')}
        bind:state={autoFollowUps}
        on:change={() => {
          saveSettings({ autoFollowUps });
        }}
        tooltip={true}
      />

      <ToggleSetting
        label={$i18n.t('Chat Tags Auto-Generation')}
        bind:state={autoTags}
        on:change={() => {
          saveSettings({ autoTags });
        }}
        tooltip={true}
      />

      <ToggleSetting
        label={$i18n.t('Auto-Copy Response to Clipboard')}
        bind:state={responseAutoCopy}
        on:change={() => {
          toggleResponseAutoCopy();
        }}
        tooltip={true}
      />

      <ToggleSetting
        label={$i18n.t('Insert Suggestion Prompt to Input')}
        bind:state={insertSuggestionPrompt}
        on:change={() => {
          saveSettings({ insertSuggestionPrompt });
        }}
        tooltip={true}
      />

      <ToggleSetting
        label={$i18n.t('Keep Follow-Up Prompts in Chat')}
        bind:state={keepFollowUpPrompts}
        on:change={() => {
          saveSettings({ keepFollowUpPrompts });
        }}
        tooltip={true}
      />

      <ToggleSetting
        label={$i18n.t('Insert Follow-Up Prompt to Input')}
        bind:state={insertFollowUpPrompt}
        on:change={() => {
          saveSettings({ insertFollowUpPrompt });
        }}
        tooltip={true}
      />

      <ToggleSetting
        label={$i18n.t('Regenerate Menu')}
        bind:state={regenerateMenu}
        on:change={() => {
          saveSettings({ regenerateMenu });
        }}
        tooltip={true}
      />

      <ToggleSetting
        label={$i18n.t('Always Collapse Code Blocks')}
        bind:state={collapseCodeBlocks}
        on:change={() => {
          saveSettings({ collapseCodeBlocks });
        }}
        tooltip={true}
      />

      <ToggleSetting
        label={$i18n.t('Always Expand Details')}
        bind:state={expandDetails}
        on:change={() => {
          saveSettings({ expandDetails });
        }}
        tooltip={true}
      />

      <ToggleSetting
        label={$i18n.t('Render Markdown in Previews')}
        bind:state={renderMarkdownInPreviews}
        on:change={() => {
          saveSettings({ renderMarkdownInPreviews });
        }}
        tooltip={true}
      />

      <ToggleSetting
        label={$i18n.t('Display Multi-model Responses in Tabs')}
        bind:state={displayMultiModelResponsesInTabs}
        on:change={() => {
          saveSettings({ displayMultiModelResponsesInTabs });
        }}
        tooltip={true}
      />

      <ToggleSetting
        label={$i18n.t('Scroll On Branch Change')}
        bind:state={scrollOnBranchChange}
        on:change={() => {
          saveSettings({ scrollOnBranchChange });
        }}
        tooltip={true}
      />

      <ToggleSetting
        label={$i18n.t('Stylized PDF Export')}
        bind:state={stylizedPdfExport}
        on:change={() => {
          saveSettings({ stylizedPdfExport });
        }}
        tooltip={true}
      />

      <ToggleSetting
        label={$i18n.t('Floating Quick Actions')}
        bind:state={showFloatingActionButtons}
        on:change={() => {
          saveSettings({ showFloatingActionButtons });
        }}
        tooltip={true}
      >
        {#if showFloatingActionButtons}
          <button
            class="text-xs text-gray-700 underline dark:text-gray-400"
            type="button"
            aria-label={$i18n.t('Open Modal To Manage Floating Quick Actions')}
            on:click={() => {
              showManageFloatingActionButtonsModal = true;
            }}
          >
            {$i18n.t('Manage')}
          </button>
        {/if}
      </ToggleSetting>

      <SettingItem label={$i18n.t('Web Search in Chat')}>
        <button
          on:click={() => {
            toggleWebSearch();
          }}
          type="button"
        >
          <span class="self-center"
            >{webSearch === 'always' ? $i18n.t('Always') : $i18n.t('Default')}</span
          >
        </button>
      </SettingItem>

      <div
        class="my-2 mb-4 border-b border-gray-300 pb-1 text-base font-medium dark:border-gray-800"
      >
        {$i18n.t('Input')}
      </div>

      <SettingItem label={$i18n.t('Enter Key Behavior')}>
        <button
          on:click={() => {
            togglectrlEnterToSend();
          }}
          type="button"
        >
          <span class="self-center"
            >{ctrlEnterToSend === true
              ? $i18n.t('Ctrl+Enter to Send')
              : $i18n.t('Enter to Send')}</span
          >
        </button>
      </SettingItem>

      <ToggleSetting
        label={$i18n.t('Rich Text Input for Chat')}
        bind:state={richTextInput}
        on:change={() => {
          saveSettings({ richTextInput });
        }}
        tooltip={true}
      />

      {#if $config?.features?.enable_autocomplete_generation}
        <ToggleSetting
          label={$i18n.t('Prompt Autocompletion')}
          bind:state={promptAutocomplete}
          on:change={() => {
            saveSettings({ promptAutocomplete });
          }}
          tooltip={true}
        />
      {/if}

      {#if richTextInput}
        <ToggleSetting
          label={$i18n.t('Show Formatting Toolbar')}
          bind:state={showFormattingToolbar}
          on:change={() => {
            saveSettings({ showFormattingToolbar });
          }}
          tooltip={true}
        />

        <ToggleSetting
          label={$i18n.t('Insert Prompt as Rich Text')}
          bind:state={insertPromptAsRichText}
          on:change={() => {
            saveSettings({ insertPromptAsRichText });
          }}
          tooltip={true}
        />
      {/if}

      <ToggleSetting
        label={$i18n.t('Paste Large Text as File')}
        bind:state={largeTextAsFile}
        on:change={() => {
          saveSettings({ largeTextAsFile });
        }}
        tooltip={true}
      />

      <div
        class="my-2 mb-4 border-b border-gray-300 pb-1 text-base font-medium dark:border-gray-800"
      >
        {$i18n.t('Artifacts')}
      </div>

      <ToggleSetting
        label={$i18n.t('Detect Artifacts Automatically')}
        bind:state={detectArtifacts}
        on:change={() => {
          saveSettings({ detectArtifacts });
        }}
        tooltip={true}
      />

      <ToggleSetting
        label={$i18n.t('iframe Sandbox Allow Same Origin')}
        bind:state={iframeSandboxAllowSameOrigin}
        on:change={() => {
          saveSettings({ iframeSandboxAllowSameOrigin });
        }}
        tooltip={true}
      />

      <ToggleSetting
        label={$i18n.t('iframe Sandbox Allow Forms')}
        bind:state={iframeSandboxAllowForms}
        on:change={() => {
          saveSettings({ iframeSandboxAllowForms });
        }}
        tooltip={true}
      />

      <div
        class="my-2 mb-4 border-b border-gray-300 pb-1 text-base font-medium dark:border-gray-800"
      >
        {$i18n.t('Voice')}
      </div>

      <ToggleSetting
        label={$i18n.t('Allow Voice Interruption in Call')}
        bind:state={voiceInterruption}
        on:change={() => {
          saveSettings({ voiceInterruption });
        }}
        tooltip={true}
      />

      <ToggleSetting
        label={$i18n.t('Display Emoji in Call')}
        bind:state={showEmojiInCall}
        on:change={() => {
          saveSettings({ showEmojiInCall });
        }}
        tooltip={true}
      />

      <div
        class="my-2 mb-4 border-b border-gray-300 pb-1 text-base font-medium dark:border-gray-800"
      >
        {$i18n.t('File')}
      </div>

      <ToggleSetting
        label={$i18n.t('Image Compression')}
        bind:state={imageCompression}
        on:change={() => {
          saveSettings({ imageCompression });
        }}
        tooltip={true}
      >
        {#if imageCompression}
          <button
            class="text-xs text-gray-700 underline dark:text-gray-400"
            type="button"
            aria-label={$i18n.t('Open Modal To Manage Image Compression')}
            on:click={() => {
              showManageImageCompressionModal = true;
            }}
          >
            {$i18n.t('Manage')}
          </button>
        {/if}
      </ToggleSetting>

      {#if imageCompression}
        <ToggleSetting
          label={$i18n.t('Compress Images in Channels')}
          bind:state={imageCompressionInChannels}
          on:change={() => {
            saveSettings({ imageCompressionInChannels });
          }}
          tooltip={true}
        />
      {/if}
    </div>

    <div class="flex justify-end p-2">
      <Button type="submit" radius="xl">
        {$i18n.t('Save')}
      </Button>
    </div>
  </div>
</form>
