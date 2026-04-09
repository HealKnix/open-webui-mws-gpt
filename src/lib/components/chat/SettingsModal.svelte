<script lang="ts">
  import { getContext, onMount, tick } from 'svelte';
  import { toast } from 'svelte-sonner';
  import { config, models, settings, user } from '$lib/stores';
  import { updateUserSettings } from '$lib/apis/users';
  import { getModels as _getModels } from '$lib/apis';
  import { goto } from '$app/navigation';

  import Modal from '../common/Modal.svelte';
  import Account from './Settings/Account.svelte';
  import About from './Settings/About.svelte';
  import General from './Settings/General.svelte';
  import Interface from './Settings/Interface.svelte';
  import Audio from './Settings/Audio.svelte';
  import DataControls from './Settings/DataControls.svelte';
  import Personalization from './Settings/Personalization.svelte';
  import Search from '../icons/Search.svelte';
  import XMark from '../icons/XMark.svelte';
  import Connections from './Settings/Connections.svelte';
  import Integrations from './Settings/Integrations.svelte';
  import DatabaseSettings from '../icons/DatabaseSettings.svelte';
  import SettingsAlt from '../icons/SettingsAlt.svelte';
  import Link from '../icons/Link.svelte';
  import UserCircle from '../icons/UserCircle.svelte';
  import SoundHigh from '../icons/SoundHigh.svelte';
  import InfoCircle from '../icons/InfoCircle.svelte';
  import WrenchAlt from '../icons/WrenchAlt.svelte';
  import Face from '../icons/Face.svelte';
  import AppNotification from '../icons/AppNotification.svelte';
  import UserBadgeCheck from '../icons/UserBadgeCheck.svelte';
  import Button from '../common/Button.svelte';
  import { cn } from '$lib/utils';
  import Input from '../common/Input.svelte';

  const i18n = getContext('i18n');

  export let show = false;

  $: if (show) {
    addScrollListener();
  } else {
    removeScrollListener();
  }

  interface SettingsTab {
    id: string;
    title: string;
    keywords: string[];
  }

  const allSettings: SettingsTab[] = [
    {
      id: 'general',
      title: 'General',
      keywords: [
        'advancedparams',
        'advancedparameters',
        'advanced params',
        'advanced parameters',
        'configuration',
        'defaultparameters',
        'default parameters',
        'defaultsettings',
        'default settings',
        'general',
        'keepalive',
        'keep alive',
        'languages',
        'notifications',
        'requestmode',
        'request mode',
        'systemparameters',
        'system parameters',
        'systemprompt',
        'system prompt',
        'systemsettings',
        'system settings',
        'theme',
        'translate',
        'webuisettings',
        'webui settings',
      ],
    },
    {
      id: 'interface',
      title: 'Interface',
      keywords: [
        'allow user location',
        'allow voice interruption in call',
        'allowuserlocation',
        'allowvoiceinterruptionincall',
        'always collapse codeblocks',
        'always collapse code blocks',
        'always expand details',
        'always on web search',
        'always play notification sound',
        'alwayscollapsecodeblocks',
        'alwaysexpanddetails',
        'alwaysonwebsearch',
        'alwaysplaynotificationsound',
        'android',
        'auto chat tags',
        'auto copy response to clipboard',
        'auto title',
        'autochattags',
        'autocopyresponsetoclipboard',
        'autotitle',
        'beta',
        'call',
        'chat background image',
        'chat bubble ui',
        'chat direction',
        'chat tags autogen',
        'chat tags autogeneration',
        'chat ui',
        'chatbackgroundimage',
        'chatbubbleui',
        'chatdirection',
        'chat tags autogeneration',
        'chattagsautogeneration',
        'chatui',
        'copy formatted text',
        'copyformattedtext',
        'default model',
        'defaultmodel',
        'design',
        'detect artifacts automatically',
        'detectartifactsautomatically',
        'display emoji in call',
        'display username',
        'displayemojiincall',
        'displayusername',
        'enter key behavior',
        'enterkeybehavior',
        'expand mode',
        'expandmode',
        'file',
        'followup autogeneration',
        'followupautogeneration',
        'fullscreen',
        'fullwidthmode',
        'full width mode',
        'haptic feedback',
        'hapticfeedback',
        'high contrast mode',
        'highcontrastmode',
        'iframe sandbox allow forms',
        'iframe sandbox allow same origin',
        'iframesandboxallowforms',
        'iframesandboxallowsameorigin',
        'imagecompression',
        'image compression',
        'imagemaxcompressionsize',
        'image max compression size',
        'interface customization',
        'interface options',
        'interfacecustomization',
        'interfaceoptions',
        'landing page mode',
        'landingpagemode',
        'layout',
        'left to right',
        'left-to-right',
        'lefttoright',
        'ltr',
        'paste large text as file',
        'pastelargetextasfile',
        'reset background',
        'resetbackground',
        'response auto copy',
        'responseautocopy',
        'rich text input for chat',
        'richtextinputforchat',
        'right to left',
        'right-to-left',
        'righttoleft',
        'rtl',
        'scroll behavior',
        'scroll on branch change',
        'scrollbehavior',
        'scrollonbranchchange',
        'select model',
        'selectmodel',
        'settings',
        'show username',
        'showusername',
        'stream large chunks',
        'streamlargechunks',
        'stylized pdf export',
        'stylizedpdfexport',
        'title autogeneration',
        'titleautogeneration',
        'toast notifications for new updates',
        'toastnotificationsfornewupdates',
        'upload background',
        'uploadbackground',
        'user interface',
        'user location access',
        'userinterface',
        'userlocationaccess',
        'vibration',
        'voice control',
        'voicecontrol',
        'widescreen mode',
        'widescreenmode',
        'whatsnew',
        'whats new',
        'websearchinchat',
        'web search in chat',
      ],
    },
    {
      id: 'connections',
      title: 'Connections',
      keywords: [
        'addconnection',
        'add connection',
        'manageconnections',
        'manage connections',
        'manage direct connections',
        'managedirectconnections',
        'settings',
      ],
    },
    {
      id: 'tools',
      title: 'Integrations',
      keywords: [
        'addconnection',
        'add connection',
        'integrations',
        'managetools',
        'manage tools',
        'manage tool servers',
        'managetoolservers',
        'open terminal',
        'openterminal',
        'terminal',
        'settings',
      ],
    },

    {
      id: 'personalization',
      title: 'Personalization',
      keywords: [
        'account preferences',
        'account settings',
        'accountpreferences',
        'accountsettings',
        'custom settings',
        'customsettings',
        'experimental',
        'memories',
        'memory',
        'personalization',
        'personalize',
        'personal settings',
        'personalsettings',
        'profile',
        'user preferences',
        'userpreferences',
      ],
    },
    {
      id: 'audio',
      title: 'Audio',
      keywords: [
        'audio config',
        'audio control',
        'audio features',
        'audio input',
        'audio output',
        'audio playback',
        'audio voice',
        'audioconfig',
        'audiocontrol',
        'audiofeatures',
        'audioinput',
        'audiooutput',
        'audioplayback',
        'audiovoice',
        'auto playback response',
        'autoplaybackresponse',
        'auto transcribe',
        'autotranscribe',
        'instant auto send after voice transcription',
        'instantautosendaftervoicetranscription',
        'language',
        'non local voices',
        'nonlocalvoices',
        'save settings',
        'savesettings',
        'set voice',
        'setvoice',
        'sound settings',
        'soundsettings',
        'speech config',
        'speech mode',
        'speech playback speed',
        'speech rate',
        'speech recognition',
        'speech settings',
        'speech speed',
        'speech synthesis',
        'speech to text engine',
        'speechconfig',
        'speechmode',
        'speechplaybackspeed',
        'speechrate',
        'speechrecognition',
        'speechsettings',
        'speechspeed',
        'speechsynthesis',
        'speechtotextengine',
        'speedch playback rate',
        'speedchplaybackrate',
        'stt settings',
        'sttsettings',
        'text to speech engine',
        'text to speech',
        'textospeechengine',
        'texttospeech',
        'texttospeechvoice',
        'text to speech voice',
        'voice control',
        'voice modes',
        'voice options',
        'voice playback',
        'voice recognition',
        'voice speed',
        'voicecontrol',
        'voicemodes',
        'voiceoptions',
        'voiceplayback',
        'voicerecognition',
        'voicespeed',
        'volume',
      ],
    },
    {
      id: 'data_controls',
      title: 'Data Controls',
      keywords: [
        'archive all chats',
        'archive chats',
        'archiveallchats',
        'archivechats',
        'archived chats',
        'archivedchats',
        'chat activity',
        'chat history',
        'chat settings',
        'chatactivity',
        'chathistory',
        'chatsettings',
        'conversation activity',
        'conversation history',
        'conversationactivity',
        'conversationhistory',
        'conversations',
        'convos',
        'delete all chats',
        'delete chats',
        'deleteallchats',
        'deletechats',
        'export chats',
        'exportchats',
        'import chats',
        'importchats',
        'message activity',
        'message archive',
        'message history',
        'messagearchive',
        'messagehistory',
      ],
    },
    {
      id: 'account',
      title: 'Account',
      keywords: [
        'account preferences',
        'account settings',
        'accountpreferences',
        'accountsettings',
        'api keys',
        'apikeys',
        'change password',
        'changepassword',
        'jwt token',
        'jwttoken',
        'login',
        'new password',
        'newpassword',
        'notification webhook url',
        'notificationwebhookurl',
        'personal settings',
        'personalsettings',
        'privacy settings',
        'privacysettings',
        'profileavatar',
        'profile avatar',
        'profile details',
        'profile image',
        'profile picture',
        'profiledetails',
        'profileimage',
        'profilepicture',
        'security settings',
        'securitysettings',
        'update account',
        'update password',
        'updateaccount',
        'updatepassword',
        'user account',
        'user data',
        'user preferences',
        'user profile',
        'useraccount',
        'userdata',
        'username',
        'userpreferences',
        'userprofile',
        'webhook url',
        'webhookurl',
      ],
    },
    {
      id: 'about',
      title: 'About',
      keywords: [
        'about app',
        'about me',
        'about open webui',
        'about page',
        'about us',
        'aboutapp',
        'aboutme',
        'aboutopenwebui',
        'aboutpage',
        'aboutus',
        'check for updates',
        'checkforupdates',
        'contact',
        'copyright',
        'details',
        'discord',
        'documentation',
        'github',
        'help',
        'information',
        'license',
        'redistributions',
        'release',
        'see whats new',
        'seewhatsnew',
        'settings',
        'software info',
        'softwareinfo',
        'support',
        'terms and conditions',
        'terms of use',
        'termsandconditions',
        'termsofuse',
        'timothy jae ryang baek',
        'timothy j baek',
        'timothyjaeryangbaek',
        'timothyjbaek',
        'twitter',
        'update info',
        'updateinfo',
        'version info',
        'versioninfo',
      ],
    },
  ];

  let availableSettings = [];
  let filteredSettings = [];

  let search = '';
  let searchDebounceTimeout;

  const getAvailableSettings = () => {
    return allSettings.filter((tab) => {
      if (tab.id === 'connections') {
        return $config?.features?.enable_direct_connections;
      }

      if (tab.id === 'tools') {
        return (
          $user?.role === 'admin' ||
          ($user?.role === 'user' && $user?.permissions?.features?.direct_tool_servers)
        );
      }

      if (tab.id === 'interface') {
        return $user?.role === 'admin' || ($user?.permissions?.settings?.interface ?? true);
      }

      if (tab.id === 'personalization') {
        return (
          $config?.features?.enable_memories &&
          ($user?.role === 'admin' || ($user?.permissions?.features?.memories ?? true))
        );
      }

      return true;
    });
  };

  const setFilteredSettings = () => {
    filteredSettings = availableSettings
      .filter((tab) => {
        return (
          search === '' ||
          tab.title.toLowerCase().includes(search.toLowerCase().trim()) ||
          tab.keywords.some((keyword) => keyword.includes(search.toLowerCase().trim()))
        );
      })
      .map((tab) => tab.id);

    if (filteredSettings.length > 0 && !filteredSettings.includes(selectedTab)) {
      selectedTab = filteredSettings[0];
    }
  };

  const searchDebounceHandler = () => {
    if (searchDebounceTimeout) {
      clearTimeout(searchDebounceTimeout);
    }

    searchDebounceTimeout = setTimeout(() => {
      setFilteredSettings();
    }, 100);
  };

  const saveSettings = async (updated) => {
    console.log(updated);
    await settings.set({ ...$settings, ...updated });
    await models.set(await getModels());
    await updateUserSettings(localStorage.token, { ui: $settings });
  };

  const getModels = async () => {
    return await _getModels(
      localStorage.token,
      $config?.features?.enable_direct_connections && ($settings?.directConnections ?? null),
    );
  };

  let selectedTab = 'general';

  // Function to handle sideways scrolling
  const scrollHandler = (event) => {
    const settingsTabsContainer = document.getElementById('settings-tabs-container');
    if (settingsTabsContainer) {
      event.preventDefault(); // Prevent default vertical scrolling
      settingsTabsContainer.scrollLeft += event.deltaY; // Scroll sideways
    }
  };

  const addScrollListener = async () => {
    await tick();
    const settingsTabsContainer = document.getElementById('settings-tabs-container');
    if (settingsTabsContainer) {
      settingsTabsContainer.addEventListener('wheel', scrollHandler);
    }
  };

  const removeScrollListener = async () => {
    await tick();
    const settingsTabsContainer = document.getElementById('settings-tabs-container');
    if (settingsTabsContainer) {
      settingsTabsContainer.removeEventListener('wheel', scrollHandler);
    }
  };

  onMount(() => {
    availableSettings = getAvailableSettings();
    setFilteredSettings();

    config.subscribe((configData) => {
      availableSettings = getAvailableSettings();
      setFilteredSettings();
    });
  });
</script>

<Modal size="2xl" bind:show>
  <div class="mx-1 text-gray-700 dark:text-gray-100">
    <div class=" flex justify-between px-4 pt-4.5 pb-0.5 md:px-4.5 md:pb-2.5 dark:text-gray-300">
      <div class=" self-center text-lg font-medium">{$i18n.t('Settings')}</div>
      <Button
        aria-label={$i18n.t('Close settings modal')}
        on:click={() => {
          show = false;
        }}
        variant="ghost"
        color="foreground"
        size="xs"
        radius="lg"
        isIconOnly
      >
        <XMark className="w-5 h-5"></XMark>
      </Button>
    </div>

    <div class="flex w-full flex-col pt-1 pb-4 md:flex-row">
      <div
        role="tablist"
        id="settings-tabs-container"
        class="tabs bg-card mx-3 mb-1 flex flex-1 -translate-y-1 flex-row gap-2.5 overflow-x-auto rounded-2xl p-2 text-left text-sm md:mb-0 md:max-h-[42rem] md:min-h-[42rem] md:w-50 md:flex-none md:flex-col md:gap-1"
      >
        <Input
          bind:value={search}
          id="search-input-settings-modal"
          on:input={searchDebounceHandler}
          placeholder={$i18n.t('Search')}
          iconLeft={Search}
          radius="lg"
          className="mb-2 md:flex hidden"
          inputClassName="bg-background"
        />
        {#if filteredSettings.length > 0}
          {#each filteredSettings as tabId (tabId)}
            {#if tabId === 'general'}
              <Button
                role="tab"
                aria-controls="tab-general"
                aria-selected={selectedTab === 'general'}
                variant="ghost"
                color="foreground"
                className={cn(
                  'flex min-w-fit flex-1 justify-start rounded-xl py-1 text-left transition md:flex-none',
                  selectedTab === 'general' && 'text-primary bg-primary/15! font-medium',
                )}
                on:click={() => {
                  selectedTab = 'general';
                }}
              >
                <div class=" mr-2 self-center">
                  <SettingsAlt strokeWidth="2" />
                </div>
                <div class=" self-center">{$i18n.t('General')}</div>
              </Button>
            {:else if tabId === 'interface'}
              <Button
                role="tab"
                aria-controls="tab-interface"
                aria-selected={selectedTab === 'interface'}
                variant="ghost"
                color="foreground"
                className={cn(
                  'flex min-w-fit flex-1 justify-start rounded-xl py-1 text-left transition md:flex-none',
                  selectedTab === 'interface' && 'text-primary bg-primary/15! font-medium',
                )}
                on:click={() => {
                  selectedTab = 'interface';
                }}
              >
                <div class=" mr-2 self-center">
                  <AppNotification strokeWidth="2" />
                </div>
                <div class=" self-center">{$i18n.t('Interface')}</div>
              </Button>
            {:else if tabId === 'connections'}
              {#if $user?.role === 'admin' || ($user?.role === 'user' && $config?.features?.enable_direct_connections)}
                <Button
                  role="tab"
                  aria-controls="tab-connections"
                  aria-selected={selectedTab === 'connections'}
                  variant="ghost"
                  color="foreground"
                  className={cn(
                    'flex min-w-fit flex-1 justify-start rounded-xl py-1 text-left transition md:flex-none',
                    selectedTab === 'connections' && 'text-primary bg-primary/15! font-medium',
                  )}
                  on:click={() => {
                    selectedTab = 'connections';
                  }}
                >
                  <div class=" mr-2 self-center">
                    <Link strokeWidth="2" />
                  </div>
                  <div class=" self-center">{$i18n.t('Connections')}</div>
                </Button>
              {/if}
            {:else if tabId === 'tools'}
              {#if $user?.role === 'admin' || ($user?.role === 'user' && $user?.permissions?.features?.direct_tool_servers)}
                <Button
                  role="tab"
                  aria-controls="tab-tools"
                  aria-selected={selectedTab === 'tools'}
                  variant="ghost"
                  color="foreground"
                  className={cn(
                    'flex min-w-fit flex-1 justify-start rounded-xl py-1 text-left transition md:flex-none',
                    selectedTab === 'tools' && 'text-primary bg-primary/15! font-medium',
                  )}
                  on:click={() => {
                    selectedTab = 'tools';
                  }}
                >
                  <div class=" mr-2 self-center">
                    <WrenchAlt strokeWidth="2" />
                  </div>
                  <div class=" self-center">{$i18n.t('Integrations')}</div>
                </Button>
              {/if}
            {:else if tabId === 'personalization'}
              <Button
                role="tab"
                aria-controls="tab-personalization"
                aria-selected={selectedTab === 'personalization'}
                variant="ghost"
                color="foreground"
                className={cn(
                  'flex min-w-fit flex-1 justify-start rounded-xl py-1 text-left transition md:flex-none',
                  selectedTab === 'personalization' && 'text-primary bg-primary/15! font-medium',
                )}
                on:click={() => {
                  selectedTab = 'personalization';
                }}
              >
                <div class=" mr-2 self-center">
                  <Face strokeWidth="2" />
                </div>
                <div class=" self-center">{$i18n.t('Personalization')}</div>
              </Button>
            {:else if tabId === 'audio'}
              <Button
                role="tab"
                aria-controls="tab-audio"
                aria-selected={selectedTab === 'audio'}
                variant="ghost"
                color="foreground"
                className={cn(
                  'flex min-w-fit flex-1 justify-start rounded-xl py-1 text-left transition md:flex-none',
                  selectedTab === 'audio' && 'text-primary bg-primary/15! font-medium',
                )}
                on:click={() => {
                  selectedTab = 'audio';
                }}
              >
                <div class=" mr-2 self-center">
                  <SoundHigh strokeWidth="2" />
                </div>
                <div class=" self-center">{$i18n.t('Audio')}</div>
              </Button>
            {:else if tabId === 'data_controls'}
              <Button
                role="tab"
                aria-controls="tab-data-controls"
                aria-selected={selectedTab === 'data_controls'}
                variant="ghost"
                color="foreground"
                className={cn(
                  'flex min-w-fit flex-1 justify-start rounded-xl py-1 text-left transition md:flex-none',
                  selectedTab === 'data_controls' && 'text-primary bg-primary/15! font-medium',
                )}
                on:click={() => {
                  selectedTab = 'data_controls';
                }}
              >
                <div class=" mr-2 self-center">
                  <DatabaseSettings strokeWidth="2" />
                </div>
                <div class=" self-center">{$i18n.t('Data Controls')}</div>
              </Button>
            {:else if tabId === 'account'}
              <Button
                role="tab"
                aria-controls="tab-account"
                aria-selected={selectedTab === 'account'}
                variant="ghost"
                color="foreground"
                className={cn(
                  'flex min-w-fit flex-1 justify-start rounded-xl py-1 text-left transition md:flex-none',
                  selectedTab === 'account' && 'text-primary bg-primary/15! font-medium',
                )}
                on:click={() => {
                  selectedTab = 'account';
                }}
              >
                <div class=" mr-2 self-center">
                  <UserCircle strokeWidth="2" />
                </div>
                <div class=" self-center">{$i18n.t('Account')}</div>
              </Button>
            {:else if tabId === 'about'}
              <Button
                role="tab"
                aria-controls="tab-about"
                aria-selected={selectedTab === 'about'}
                variant="ghost"
                color="foreground"
                className={cn(
                  'flex min-w-fit flex-1 justify-start rounded-xl py-1 text-left transition md:flex-none',
                  selectedTab === 'about' && 'text-primary bg-primary/15! font-medium',
                )}
                on:click={() => {
                  selectedTab = 'about';
                }}
              >
                <div class=" mr-2 self-center">
                  <InfoCircle strokeWidth="2" />
                </div>
                <div class=" self-center">{$i18n.t('About')}</div>
              </Button>
            {/if}
          {/each}
        {:else}
          <div class="mt-4 text-center text-gray-500">
            {$i18n.t('No results found')}
          </div>
        {/if}
        {#if $user?.role === 'admin'}
          <Button
            href="/admin/settings"
            variant="ghost"
            className="flex flex-none rounded-xl justify-start text-left transition select-none md:mt-auto md:flex-none"
            on:click={async (e) => {
              e.preventDefault();
              await goto('/admin/settings');
              show = false;
            }}
          >
            <div class=" mr-2 self-center">
              <UserBadgeCheck strokeWidth="2" />
            </div>
            <div class=" self-center">{$i18n.t('Admin Settings')}</div>
          </Button>
        {/if}
      </div>
      <div class="max-h-[42rem] flex-1 md:min-h-[42rem]">
        {#if selectedTab === 'general'}
          <General
            {getModels}
            {saveSettings}
            on:save={() => {
              toast.success($i18n.t('Settings saved successfully!'));
            }}
          />
        {:else if selectedTab === 'interface'}
          <Interface
            {saveSettings}
            on:save={() => {
              toast.success($i18n.t('Settings saved successfully!'));
            }}
          />
        {:else if selectedTab === 'connections'}
          <Connections
            saveSettings={async (updated) => {
              await saveSettings(updated);
              toast.success($i18n.t('Settings saved successfully!'));
            }}
          />
        {:else if selectedTab === 'tools'}
          <Integrations
            saveSettings={async (updated) => {
              await saveSettings(updated);
              toast.success($i18n.t('Settings saved successfully!'));
            }}
          />
        {:else if selectedTab === 'personalization'}
          <Personalization
            {saveSettings}
            on:save={() => {
              toast.success($i18n.t('Settings saved successfully!'));
            }}
          />
        {:else if selectedTab === 'audio'}
          <Audio
            {saveSettings}
            on:save={() => {
              toast.success($i18n.t('Settings saved successfully!'));
            }}
          />
        {:else if selectedTab === 'data_controls'}
          <DataControls {saveSettings} />
        {:else if selectedTab === 'account'}
          <Account
            {saveSettings}
            saveHandler={() => {
              toast.success($i18n.t('Settings saved successfully!'));
            }}
          />
        {:else if selectedTab === 'about'}
          <About />
        {/if}
      </div>
    </div>
  </div>
</Modal>

<style>
  input::-webkit-outer-spin-button,
  input::-webkit-inner-spin-button {
    /* display: none; <- Crashes Chrome on hover */
    -webkit-appearance: none;
    margin: 0; /* <-- Apparently some margin are still there even though it's hidden */
  }

  .tabs::-webkit-scrollbar {
    display: none; /* for Chrome, Safari and Opera */
  }

  .tabs {
    -ms-overflow-style: none; /* IE and Edge */
    scrollbar-width: none; /* Firefox */
  }

  input[type='number'] {
    appearance: textfield;
    -moz-appearance: textfield; /* Firefox */
  }
</style>
