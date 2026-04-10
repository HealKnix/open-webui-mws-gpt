<script lang="ts">
  import DOMPurify from 'dompurify';
  import { v4 as uuidv4 } from 'uuid';

  import { getBackendConfig, getVersionUpdates, getWebhookUrl, updateWebhookUrl } from '$lib/apis';
  import {
    getAdminConfig,
    getLdapConfig,
    getLdapServer,
    updateAdminConfig,
    updateLdapConfig,
    updateLdapServer,
  } from '$lib/apis/auths';
  import { getBanners, setBanners } from '$lib/apis/configs';
  import { getGroups } from '$lib/apis/groups';
  import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
  import Switch from '$lib/components/common/Switch.svelte';
  import ToggleSetting from '$lib/components/common/ToggleSetting.svelte';
  import SettingItem from '$lib/components/common/SettingItem.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import { WEBUI_BUILD_HASH, WEBUI_VERSION } from '$lib/constants';
  import { banners as _banners, config, showChangelog } from '$lib/stores';
  import type { Banner } from '$lib/types';
  import { compareVersion } from '$lib/utils';
  import { onMount, getContext } from 'svelte';
  import { toast } from 'svelte-sonner';
  import Textarea from '$lib/components/common/Textarea.svelte';
  import Banners from './Interface/Banners.svelte';
  import Button from '$lib/components/common/Button.svelte';
  import Input from '$lib/components/common/Input.svelte';

  const i18n = getContext('i18n');

  export let saveHandler: Function;

  let updateAvailable = null;
  let version = {
    current: '',
    latest: '',
  };

  let adminConfig = null;
  let webhookUrl = '';
  let groups = [];

  let banners: Banner[] = [];

  // LDAP
  let ENABLE_LDAP = false;
  let LDAP_SERVER = {
    label: '',
    host: '',
    port: '',
    attribute_for_mail: 'mail',
    attribute_for_username: 'uid',
    app_dn: '',
    app_dn_password: '',
    search_base: '',
    search_filters: '',
    use_tls: false,
    certificate_path: '',
    ciphers: '',
  };

  const checkForVersionUpdates = async () => {
    updateAvailable = null;
    version = await getVersionUpdates(localStorage.token).catch((error) => {
      return {
        current: WEBUI_VERSION,
        latest: WEBUI_VERSION,
      };
    });

    console.info(version);

    updateAvailable = compareVersion(version.latest, version.current);
    console.info(updateAvailable);
  };

  const updateLdapServerHandler = async () => {
    if (!ENABLE_LDAP) return;
    const res = await updateLdapServer(localStorage.token, LDAP_SERVER).catch((error) => {
      toast.error(`${error}`);
      return null;
    });
    if (res) {
      toast.success($i18n.t('LDAP server updated'));
    }
  };

  const updateBanners = async () => {
    _banners.set(await setBanners(localStorage.token, banners));
  };

  const updateHandler = async () => {
    webhookUrl = await updateWebhookUrl(localStorage.token, webhookUrl);
    const res = await updateAdminConfig(localStorage.token, adminConfig);
    await updateLdapConfig(localStorage.token, ENABLE_LDAP);
    await updateLdapServerHandler();

    await updateBanners();

    await config.set(await getBackendConfig());

    if (res) {
      saveHandler();
    } else {
      toast.error($i18n.t('Failed to update settings'));
    }
  };

  onMount(async () => {
    if ($config?.features?.enable_version_update_check) {
      checkForVersionUpdates();
    }

    await Promise.all([
      (async () => {
        adminConfig = await getAdminConfig(localStorage.token);
      })(),

      (async () => {
        webhookUrl = await getWebhookUrl(localStorage.token);
      })(),
      (async () => {
        LDAP_SERVER = await getLdapServer(localStorage.token);
      })(),
      (async () => {
        groups = await getGroups(localStorage.token);
      })(),
    ]);

    const ldapConfig = await getLdapConfig(localStorage.token);
    ENABLE_LDAP = ldapConfig.ENABLE_LDAP;

    banners = await getBanners(localStorage.token);
  });
</script>

<form
  class="flex h-full flex-col justify-between space-y-3 text-sm"
  on:submit|preventDefault={async () => {
    updateHandler();
  }}
>
  <div class="scrollbar-hidden h-full space-y-3 overflow-y-scroll p-1">
    {#if adminConfig !== null}
      <div class="space-y-1">
        <div class="my-2 border-b border-gray-300 pb-2 text-base font-medium dark:border-gray-800">
          {$i18n.t('General')}
        </div>

        <div class="mb-2.5">
          <div class=" mb-1 flex items-center space-x-2 text-xs font-medium">
            <div>
              {$i18n.t('Version')}
            </div>
          </div>
          <div class="flex w-full items-center justify-between">
            <div class="flex flex-col text-xs text-gray-700 dark:text-gray-200">
              <div class="flex gap-1">
                <Tooltip content={WEBUI_BUILD_HASH}>
                  v{WEBUI_VERSION}
                </Tooltip>

                {#if $config?.features?.enable_version_update_check}
                  <a
                    href="https://github.com/open-webui/open-webui/releases/tag/v{version.latest}"
                    target="_blank"
                  >
                    {updateAvailable === null
                      ? $i18n.t('Checking for updates...')
                      : updateAvailable
                        ? `(v${version.latest} ${$i18n.t('available!')})`
                        : $i18n.t('(latest)')}
                  </a>
                {/if}
              </div>

              <button
                class=" flex items-center space-x-1 text-xs text-gray-500 underline dark:text-gray-500"
                type="button"
                on:click={() => {
                  showChangelog.set(true);
                }}
              >
                <div>{$i18n.t("See what's new")}</div>
              </button>
            </div>

            {#if $config?.features?.enable_version_update_check}
              <button
                class=" dark:bg-gray-850 rounded-lg bg-gray-50 px-3 py-1.5 text-xs font-medium transition hover:bg-gray-100 dark:hover:bg-gray-800"
                type="button"
                on:click={() => {
                  checkForVersionUpdates();
                }}
              >
                {$i18n.t('Check for updates')}
              </button>
            {/if}
          </div>
        </div>

        <div class="mb-2.5">
          <div class="flex w-full items-center justify-between">
            <div class="pr-2 text-xs">
              <div class="">
                {$i18n.t('Help')}
              </div>
              <div class=" text-xs text-gray-500">
                {$i18n.t('Discover how to use Open WebUI and seek support from the community.')}
              </div>
            </div>

            <a
              class="flex-shrink-0 text-xs font-medium underline"
              href="https://docs.openwebui.com/"
              target="_blank"
            >
              {$i18n.t('Documentation')}
            </a>
          </div>

          <div class="mt-1">
            <div class="flex space-x-1">
              <a href="https://discord.gg/5rJgQTnV4s" target="_blank">
                <img
                  alt="Discord"
                  src="https://img.shields.io/badge/Discord-Open_WebUI-blue?logo=discord&logoColor=white"
                />
              </a>

              <a href="https://twitter.com/OpenWebUI" target="_blank">
                <img
                  alt="X (formerly Twitter) Follow"
                  src="https://img.shields.io/twitter/follow/OpenWebUI"
                />
              </a>

              <a href="https://github.com/open-webui/open-webui" target="_blank">
                <img
                  alt="Github Repo"
                  src="https://img.shields.io/github/stars/open-webui/open-webui?style=social&label=Star us on Github"
                />
              </a>
            </div>
          </div>
        </div>

        <div class="mb-2.5">
          <div class="flex w-full items-center justify-between">
            <div class="pr-2 text-xs">
              <div class="">
                {$i18n.t('License')}
              </div>

              {#if $config?.license_metadata}
                <a
                  href="https://docs.openwebui.com/enterprise"
                  target="_blank"
                  class="mt-0.5 text-gray-500"
                >
                  <span class=" text-black capitalize dark:text-white"
                    >{$config?.license_metadata?.type}
                    license</span
                  >
                  registered to
                  <span class=" text-black capitalize dark:text-white"
                    >{$config?.license_metadata?.organization_name}</span
                  >
                  for
                  <span class=" font-medium text-black dark:text-white"
                    >{$config?.license_metadata?.seats ?? 'Unlimited'} users.</span
                  >
                </a>
                {#if $config?.license_metadata?.html}
                  <div class="mt-0.5">
                    {@html DOMPurify.sanitize($config?.license_metadata?.html)}
                  </div>
                {/if}
              {:else}
                <a
                  class=" text-xs hover:underline"
                  href="https://docs.openwebui.com/enterprise"
                  target="_blank"
                >
                  <span class="text-gray-500">
                    {$i18n.t(
                      'Upgrade to a licensed plan for enhanced capabilities, including custom theming and branding, and dedicated support.',
                    )}
                  </span>
                </a>
              {/if}
            </div>

            <!-- <button
								class="flex-shrink-0 text-xs px-3 py-1.5 bg-gray-50 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-800 transition rounded-lg font-medium"
							>
								{$i18n.t('Activate')}
							</button> -->
          </div>
        </div>
      </div>

      <div class="space-y-1">
        <div class="my-2 border-b border-gray-300 pb-2 text-base font-medium dark:border-gray-800">
          {$i18n.t('Authentication')}
        </div>

        <SettingItem label={$i18n.t('Default User Role')}>
          <select
            class="w-fit rounded-sm bg-transparent px-2 pr-8 text-right text-xs outline-hidden"
            bind:value={adminConfig.DEFAULT_USER_ROLE}
            placeholder={$i18n.t('Select a role')}
          >
            <option value="pending">{$i18n.t('pending')}</option>
            <option value="user">{$i18n.t('user')}</option>
            <option value="admin">{$i18n.t('admin')}</option>
          </select>
        </SettingItem>

        <SettingItem label={$i18n.t('Default Group')}>
          <select
            class="w-fit rounded-sm bg-transparent px-2 pr-8 text-right text-xs outline-hidden"
            bind:value={adminConfig.DEFAULT_GROUP_ID}
            placeholder={$i18n.t('Select a group')}
          >
            <option value={''}>None</option>
            {#each groups as group}
              <option value={group.id}>{group.name}</option>
            {/each}
          </select>
        </SettingItem>

        <ToggleSetting
          label={$i18n.t('Enable New Sign Ups')}
          bind:state={adminConfig.ENABLE_SIGNUP}
        />

        <ToggleSetting
          label={$i18n.t('Show Admin Details in Account Pending Overlay')}
          bind:state={adminConfig.SHOW_ADMIN_DETAILS}
        />

        {#if adminConfig.SHOW_ADMIN_DETAILS}
          <div class="mb-2.5 w-full justify-between">
            <div class="flex w-full justify-between">
              <div class=" self-center text-xs font-medium">{$i18n.t('Admin Contact Email')}</div>
            </div>

            <div class="mt-2 flex space-x-2">
              <Input
                type="email"
                placeholder={$i18n.t('Leave empty to use first admin user')}
                bind:value={adminConfig.ADMIN_EMAIL}
              />
            </div>
          </div>
        {/if}

        <div class="mb-2.5">
          <div class=" mb-2 self-center text-xs font-medium">
            {$i18n.t('Pending User Overlay Title')}
          </div>
          <Textarea
            placeholder={$i18n.t(
              'Enter a title for the pending user info overlay. Leave empty for default.',
            )}
            bind:value={adminConfig.PENDING_USER_OVERLAY_TITLE}
          />
        </div>

        <div class="mb-2.5">
          <div class=" mb-2 self-center text-xs font-medium">
            {$i18n.t('Pending User Overlay Content')}
          </div>
          <Textarea
            placeholder={$i18n.t(
              'Enter content for the pending user info overlay. Leave empty for default.',
            )}
            bind:value={adminConfig.PENDING_USER_OVERLAY_CONTENT}
          />
        </div>

        <ToggleSetting
          label={$i18n.t('Enable API Keys')}
          bind:state={adminConfig.ENABLE_API_KEYS}
        />

        {#if adminConfig?.ENABLE_API_KEYS}
          <ToggleSetting
            label={$i18n.t('API Key Endpoint Restrictions')}
            bind:state={adminConfig.ENABLE_API_KEYS_ENDPOINT_RESTRICTIONS}
          />

          {#if adminConfig?.ENABLE_API_KEYS_ENDPOINT_RESTRICTIONS}
            <div class=" mb-2.5 flex w-full flex-col pr-2">
              <div class=" text-xs font-medium">
                {$i18n.t('Allowed Endpoints')}
              </div>

              <Input
                type="text"
                placeholder={`e.g.) /api/v1/messages, /api/v1/channels`}
                bind:value={adminConfig.API_KEYS_ALLOWED_ENDPOINTS}
              />

              <div class="mt-2 text-xs text-gray-400 dark:text-gray-500">
                <a
                  href="https://docs.openwebui.com/reference/api-endpoints"
                  target="_blank"
                  class=" font-medium text-gray-300 underline"
                >
                  {$i18n.t('To learn more about available endpoints, visit our documentation.')}
                </a>
              </div>
            </div>
          {/if}
        {/if}

        <div class=" mb-2.5 w-full justify-between">
          <div class="flex w-full justify-between">
            <div class=" self-center text-xs font-medium">{$i18n.t('JWT Expiration')}</div>
          </div>

          <div class="mt-2 flex space-x-2">
            <Input
              type="text"
              placeholder={`e.g.) "30m","1h", "10d". `}
              bind:value={adminConfig.JWT_EXPIRES_IN}
            />
          </div>

          <div class="mt-2 text-xs text-gray-400 dark:text-gray-500">
            {$i18n.t('Valid time units:')}
            <span class=" font-medium text-gray-300"
              >{$i18n.t("'s', 'm', 'h', 'd', 'w' or '-1' for no expiration.")}</span
            >
          </div>

          {#if adminConfig.JWT_EXPIRES_IN === '-1'}
            <div class="mt-2 text-xs">
              <div
                class=" rounded-lg bg-yellow-500/20 px-3 py-2 text-yellow-700 dark:text-yellow-200"
              >
                <div>
                  <span class=" font-medium">{$i18n.t('Warning')}:</span>
                  <span
                    ><a
                      href="https://docs.openwebui.com/reference/env-configuration#jwt_expires_in"
                      target="_blank"
                      class=" underline"
                      >{$i18n.t('No expiration can pose security risks.')}
                    </a></span
                  >
                </div>
              </div>
            </div>
          {/if}
        </div>

        <div class=" space-y-3">
          <div class="mt-2 space-y-2 pr-1.5">
            <ToggleSetting label={$i18n.t('LDAP')} bind:state={ENABLE_LDAP} />

            {#if ENABLE_LDAP}
              <div class="flex flex-col gap-1">
                <div class="flex w-full gap-2">
                  <div class="w-full">
                    <div class=" mb-1 min-w-fit self-center text-xs font-medium">
                      {$i18n.t('Label')}
                    </div>
                    <input
                      class="w-full bg-transparent py-0.5 outline-hidden"
                      required
                      placeholder={$i18n.t('Enter server label')}
                      bind:value={LDAP_SERVER.label}
                    />
                  </div>
                  <div class="w-full"></div>
                </div>
                <div class="flex w-full gap-2">
                  <div class="w-full">
                    <div class=" mb-1 min-w-fit self-center text-xs font-medium">
                      {$i18n.t('Host')}
                    </div>
                    <input
                      class="w-full bg-transparent py-0.5 outline-hidden"
                      required
                      placeholder={$i18n.t('Enter server host')}
                      bind:value={LDAP_SERVER.host}
                    />
                  </div>
                  <div class="w-full">
                    <div class=" mb-1 min-w-fit self-center text-xs font-medium">
                      {$i18n.t('Port')}
                    </div>
                    <Tooltip
                      placement="top-start"
                      content={$i18n.t('Default to 389 or 636 if TLS is enabled')}
                      className="w-full"
                    >
                      <input
                        class="w-full bg-transparent py-0.5 outline-hidden"
                        type="number"
                        placeholder={$i18n.t('Enter server port')}
                        bind:value={LDAP_SERVER.port}
                      />
                    </Tooltip>
                  </div>
                </div>
                <div class="flex w-full gap-2">
                  <div class="w-full">
                    <div class=" mb-1 min-w-fit self-center text-xs font-medium">
                      {$i18n.t('Application DN')}
                    </div>
                    <Tooltip
                      content={$i18n.t('The Application Account DN you bind with for search')}
                      placement="top-start"
                    >
                      <input
                        class="w-full bg-transparent py-0.5 outline-hidden"
                        placeholder={$i18n.t('Enter Application DN')}
                        bind:value={LDAP_SERVER.app_dn}
                      />
                    </Tooltip>
                  </div>
                  <div class="w-full">
                    <div class=" mb-1 min-w-fit self-center text-xs font-medium">
                      {$i18n.t('Application DN Password')}
                    </div>
                    <SensitiveInput
                      placeholder={$i18n.t('Enter Application DN Password')}
                      required={false}
                      bind:value={LDAP_SERVER.app_dn_password}
                    />
                  </div>
                </div>
                <div class="flex w-full gap-2">
                  <div class="w-full">
                    <div class=" mb-1 min-w-fit self-center text-xs font-medium">
                      {$i18n.t('Attribute for Mail')}
                    </div>
                    <Tooltip
                      content={$i18n.t(
                        'The LDAP attribute that maps to the mail that users use to sign in.',
                      )}
                      placement="top-start"
                    >
                      <input
                        class="w-full bg-transparent py-0.5 outline-hidden"
                        required
                        placeholder={$i18n.t('Example: mail')}
                        bind:value={LDAP_SERVER.attribute_for_mail}
                      />
                    </Tooltip>
                  </div>
                </div>
                <div class="flex w-full gap-2">
                  <div class="w-full">
                    <div class=" mb-1 min-w-fit self-center text-xs font-medium">
                      {$i18n.t('Attribute for Username')}
                    </div>
                    <Tooltip
                      content={$i18n.t(
                        'The LDAP attribute that maps to the username that users use to sign in.',
                      )}
                      placement="top-start"
                    >
                      <input
                        class="w-full bg-transparent py-0.5 outline-hidden"
                        required
                        placeholder={$i18n.t('Example: sAMAccountName or uid or userPrincipalName')}
                        bind:value={LDAP_SERVER.attribute_for_username}
                      />
                    </Tooltip>
                  </div>
                </div>
                <div class="flex w-full gap-2">
                  <div class="w-full">
                    <div class=" mb-1 min-w-fit self-center text-xs font-medium">
                      {$i18n.t('Search Base')}
                    </div>
                    <Tooltip
                      content={$i18n.t('The base to search for users')}
                      placement="top-start"
                    >
                      <input
                        class="w-full bg-transparent py-0.5 outline-hidden"
                        required
                        placeholder={$i18n.t('Example: ou=users,dc=foo,dc=example')}
                        bind:value={LDAP_SERVER.search_base}
                      />
                    </Tooltip>
                  </div>
                </div>
                <div class="flex w-full gap-2">
                  <div class="w-full">
                    <div class=" mb-1 min-w-fit self-center text-xs font-medium">
                      {$i18n.t('Search Filters')}
                    </div>
                    <input
                      class="w-full bg-transparent py-0.5 outline-hidden"
                      placeholder={$i18n.t('Example: (&(objectClass=inetOrgPerson)(uid=%s))')}
                      bind:value={LDAP_SERVER.search_filters}
                    />
                  </div>
                </div>
                <div class="text-xs text-gray-400 dark:text-gray-500">
                  <a
                    class=" font-medium text-gray-300 underline"
                    href="https://ldap.com/ldap-filters/"
                    target="_blank"
                  >
                    {$i18n.t('Click here for filter guides.')}
                  </a>
                </div>
                <div>
                  <ToggleSetting label={$i18n.t('TLS')} bind:state={LDAP_SERVER.use_tls} />
                  {#if LDAP_SERVER.use_tls}
                    <div class="flex w-full gap-2">
                      <div class="w-full">
                        <div class=" mt-1 mb-1 min-w-fit self-center text-xs font-medium">
                          {$i18n.t('Certificate Path')}
                        </div>
                        <input
                          class="w-full bg-transparent py-0.5 outline-hidden"
                          placeholder={$i18n.t('Enter certificate path')}
                          bind:value={LDAP_SERVER.certificate_path}
                        />
                      </div>
                    </div>
                    <ToggleSetting
                      label={$i18n.t('Validate certificate')}
                      bind:state={LDAP_SERVER.validate_cert}
                    />
                    <div class="flex w-full gap-2">
                      <div class="w-full">
                        <div class=" mb-1 min-w-fit self-center text-xs font-medium">
                          {$i18n.t('Ciphers')}
                        </div>
                        <Tooltip content={$i18n.t('Default to ALL')} placement="top-start">
                          <input
                            class="w-full bg-transparent py-0.5 outline-hidden"
                            placeholder={$i18n.t('Example: ALL')}
                            bind:value={LDAP_SERVER.ciphers}
                          />
                        </Tooltip>
                      </div>
                      <div class="w-full"></div>
                    </div>
                  {/if}
                </div>
              </div>
            {/if}
          </div>
        </div>
      </div>

      <div class="space-y-1">
        <div class="my-2 border-b border-gray-300 pb-2 text-base font-medium dark:border-gray-800">
          {$i18n.t('Features')}
        </div>

        <ToggleSetting
          label={$i18n.t('Enable Community Sharing')}
          bind:state={adminConfig.ENABLE_COMMUNITY_SHARING}
        />

        <ToggleSetting
          label={$i18n.t('Enable Message Rating')}
          bind:state={adminConfig.ENABLE_MESSAGE_RATING}
        />

        <ToggleSetting label={$i18n.t('Folders')} bind:state={adminConfig.ENABLE_FOLDERS} />

        {#if adminConfig.ENABLE_FOLDERS}
          <div class="mb-2.5 w-full justify-between">
            <div class="flex w-full justify-between">
              <div class=" self-center text-xs font-medium">
                {$i18n.t('Folder Max File Count')}
              </div>
            </div>

            <div class="mt-2 flex space-x-2">
              <Input
                type="number"
                min="0"
                placeholder={$i18n.t('Leave empty for unlimited')}
                bind:value={adminConfig.FOLDER_MAX_FILE_COUNT}
              />
            </div>

            <div class="mt-2 text-xs text-gray-400 dark:text-gray-500">
              {$i18n.t('Maximum number of files allowed per folder.')}
            </div>
          </div>
        {/if}

        <ToggleSetting
          label={`${$i18n.t('Notes')} (${$i18n.t('Beta')})`}
          bind:state={adminConfig.ENABLE_NOTES}
        />

        <ToggleSetting
          label={`${$i18n.t('Channels')} (${$i18n.t('Beta')})`}
          bind:state={adminConfig.ENABLE_CHANNELS}
        />

        <ToggleSetting
          label={`${$i18n.t('Memories')} (${$i18n.t('Beta')})`}
          bind:state={adminConfig.ENABLE_MEMORIES}
        />

        <ToggleSetting
          label={$i18n.t('User Webhooks')}
          bind:state={adminConfig.ENABLE_USER_WEBHOOKS}
        />

        <ToggleSetting label={$i18n.t('User Status')} bind:state={adminConfig.ENABLE_USER_STATUS} />

        <div class="mb-2.5">
          <div class=" mb-2 self-center text-xs font-medium">
            {$i18n.t('Response Watermark')}
          </div>
          <Textarea
            placeholder={$i18n.t('Enter a watermark for the response. Leave empty for none.')}
            bind:value={adminConfig.RESPONSE_WATERMARK}
          />
        </div>

        <div class="mb-2.5 w-full justify-between">
          <div class="flex w-full justify-between">
            <div class=" self-center text-xs font-medium">{$i18n.t('WebUI URL')}</div>
          </div>

          <div class="mt-2 flex space-x-2">
            <Input
              type="text"
              placeholder={`e.g.) "http://localhost:3000"`}
              bind:value={adminConfig.WEBUI_URL}
            />
          </div>

          <div class="mt-2 text-xs text-gray-400 dark:text-gray-500">
            {$i18n.t(
              'Enter the public URL of your WebUI. This URL will be used to generate links in the notifications.',
            )}
          </div>
        </div>

        <div class=" w-full justify-between">
          <div class="flex w-full justify-between">
            <div class=" self-center text-xs font-medium">{$i18n.t('Webhook URL')}</div>
          </div>

          <div class="mt-2 flex space-x-2">
            <Input
              type="text"
              placeholder={`https://example.com/webhook`}
              bind:value={webhookUrl}
            />
          </div>
        </div>
      </div>

      <div class="space-y-1">
        <div class="my-2 border-b border-gray-300 pb-2 text-base font-medium dark:border-gray-800">
          {$i18n.t('UI')}
        </div>

        <SettingItem label={$i18n.t('Banners')}>
          <button
            class="flex rounded-sm p-1 px-3 text-xs transition"
            type="button"
            on:click={() => {
              if (banners.length === 0 || banners.at(-1).content !== '') {
                banners = [
                  ...banners,
                  {
                    id: uuidv4(),
                    type: '',
                    title: '',
                    content: '',
                    dismissible: true,
                    timestamp: Math.floor(Date.now() / 1000),
                  },
                ];
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
                d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z"
              />
            </svg>
          </button>
        </SettingItem>

        <Banners bind:banners />
      </div>
    {/if}
  </div>

  <div class="flex justify-end p-1">
    <Button type="submit" radius="xl">
      {$i18n.t('Save')}
    </Button>
  </div>
</form>
