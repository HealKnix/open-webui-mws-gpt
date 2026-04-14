<script lang="ts">
  import { onMount, tick, getContext } from 'svelte';
  import { toast } from 'svelte-sonner';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';

  import { user, mcpApps as _mcpApps, widgets as _widgets } from '$lib/stores';
  import { slugify } from '$lib/utils';
  import {
    createMcpApp,
    getMcpAppById,
    getMcpApps,
    updateMcpAppById,
    testMcpAppConnectionDirect,
    updateMcpAppAccessGrants,
  } from '$lib/apis/mcp_apps';
  import { getWidgets } from '$lib/apis/widgets';

  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import Switch from '$lib/components/common/Switch.svelte';
  import Badge from '$lib/components/common/Badge.svelte';
  import ChevronLeft from '$lib/components/icons/ChevronLeft.svelte';
  import ChevronRight from '$lib/components/icons/ChevronRight.svelte';
  import Check from '$lib/components/icons/Check.svelte';
  import AccessControlModal from '../common/AccessControlModal.svelte';
  import LockClosed from '$lib/components/icons/LockClosed.svelte';

  const i18n = getContext('i18n');

  // --- Mode ---
  let edit = false;
  let appId = '';
  let loading = true;
  let saving = false;

  // --- Step navigation ---
  let step = 1; // 1: Connection, 2: Tools, 3: Skill Prompt & Widgets

  // --- Step 1: Connection ---
  let name = '';
  let description = '';
  let icon = '';
  let transport = 'http_streamable';
  let url = '';
  let command = '';
  let args = '';
  let envPairs: { key: string; value: string }[] = [];
  let authType = '';
  let authKey = '';

  // --- Test Connection ---
  let testing = false;
  let testResult: { status: boolean; tools: any[]; tool_count: number } | null = null;
  let testError = '';

  // --- Step 2: Tool Configuration ---
  let discoveredTools: any[] = [];
  let toolConfigs: Record<
    string,
    {
      enabled: boolean;
      display_name: string;
      requires_confirmation: boolean;
      confirmation_widget_id: string;
    }
  > = {};

  // --- Derived: flat list for Step 2 rendering (avoids bind: + dynamic key issues) ---
  $: toolConfigList = Object.entries(toolConfigs).map(([name, cfg]) => ({ name, cfg }));

  // --- Step 3: Skill Prompt & Widgets ---
  let skillPrompt = '';
  let widgetIds: string[] = [];
  let availableWidgets: any[] = [];

  // --- Navigate to Widget Creation (with return flow) ---
  const MCP_APP_RETURN_KEY = 'mcp_app_editor_return_state';
  const MCP_APP_NEW_WIDGET_KEY = 'mcp_app_editor_new_widget_id';

  const captureEditorState = () => ({
    edit,
    appId,
    step,
    name,
    description,
    icon,
    transport,
    url,
    command,
    args,
    envPairs,
    authType,
    authKey,
    discoveredTools,
    toolConfigs,
    testResult,
    skillPrompt,
    widgetIds,
    accessGrants,
  });

  const goToCreateWidget = async () => {
    sessionStorage.setItem(MCP_APP_RETURN_KEY, JSON.stringify(captureEditorState()));
    const returnTo = edit
      ? `/workspace/mcpapps/edit?id=${encodeURIComponent(appId)}`
      : '/workspace/mcpapps/create';
    await goto(`/workspace/widgets/create?returnTo=${encodeURIComponent(returnTo)}`);
  };

  // --- Access Control ---
  let accessGrants: any[] = [];
  let showAccessControlModal = false;

  // --- Helpers ---
  const buildEnvDict = () => {
    const env: Record<string, string> = {};
    for (const pair of envPairs) {
      if (pair.key.trim()) {
        env[pair.key.trim()] = pair.value;
      }
    }
    return Object.keys(env).length > 0 ? env : null;
  };

  const buildAuthConfig = () => {
    if (authType === 'bearer' && authKey) {
      return { key: authKey };
    }
    return null;
  };

  const buildToolConfigsList = () => {
    return Object.entries(toolConfigs).map(([toolName, cfg]) => ({
      name: toolName,
      enabled: cfg.enabled,
      display_name: cfg.display_name || toolName,
      requires_confirmation: cfg.requires_confirmation,
      confirmation_widget_id: cfg.confirmation_widget_id || null,
    }));
  };

  // --- Test Connection ---
  const testConnection = async () => {
    testing = true;
    testResult = null;
    testError = '';

    try {
      const connectionData: any = { transport };

      if (transport === 'http_streamable' || transport === 'sse') {
        connectionData.url = url;
        if (authType) {
          connectionData.auth_type = authType;
          connectionData.auth_config = buildAuthConfig();
        }
      } else if (transport === 'stdio') {
        connectionData.command = command;
        connectionData.args = args.split(/\s+/).filter((a) => a.trim());
        connectionData.env = buildEnvDict();
      }

      const res = await testMcpAppConnectionDirect(localStorage.token, connectionData);
      testResult = res;

      // Populate discovered tools
      if (res?.tools) {
        discoveredTools = res.tools;

        // Initialize tool configs for newly discovered tools
        for (const tool of res.tools) {
          const toolName = tool.name || tool.function?.name;
          if (toolName && !toolConfigs[toolName]) {
            toolConfigs[toolName] = {
              enabled: true,
              display_name: toolName,
              requires_confirmation: false,
              confirmation_widget_id: '',
            };
          }
        }
        toolConfigs = toolConfigs; // trigger reactivity
      }

      toast.success(
        $i18n.t('Connection successful! Found {{count}} tools.', {
          count: res?.tool_count ?? 0,
        }),
      );
    } catch (error) {
      testError = `${error}`;
      toast.error(`${error}`);
    } finally {
      testing = false;
    }
  };

  // --- Save ---
  const submitHandler = async () => {
    if (!name.trim()) {
      toast.error($i18n.t('Name is required'));
      return;
    }

    if ((transport === 'http_streamable' || transport === 'sse') && !url.trim()) {
      toast.error($i18n.t('URL is required'));
      return;
    }

    if (transport === 'stdio' && !command.trim()) {
      toast.error($i18n.t('Command is required'));
      return;
    }

    saving = true;

    const payload: any = {
      name: name.trim(),
      description: description.trim() || null,
      icon: icon.trim() || null,
      is_active: true,
      transport,
      url: transport !== 'stdio' ? url.trim() : null,
      command: transport === 'stdio' ? command.trim() : null,
      args: transport === 'stdio' ? args.split(/\s+/).filter((a) => a.trim()) : null,
      env: buildEnvDict(),
      auth_type: authType || null,
      auth_config: buildAuthConfig(),
      tool_configs: buildToolConfigsList(),
      skill_prompt: skillPrompt.trim() || null,
      widget_ids: widgetIds.length > 0 ? widgetIds : null,
      access_grants: accessGrants,
      meta: { tags: [] },
    };

    try {
      if (edit) {
        const res = await updateMcpAppById(localStorage.token, appId, payload);
        if (res) {
          toast.success($i18n.t('MCP App updated successfully'));
          _mcpApps.set(await getMcpApps(localStorage.token));
        }
      } else {
        const res = await createMcpApp(localStorage.token, payload);
        if (res) {
          toast.success($i18n.t('MCP App created successfully'));
          _mcpApps.set(await getMcpApps(localStorage.token));
          goto('/workspace/mcpapps');
        }
      }
    } catch (error) {
      toast.error(`${error}`);
    } finally {
      saving = false;
    }
  };

  // --- Load Widgets for Step 3 ---
  const loadWidgets = async (forceRefresh = false) => {
    if ($_widgets === null || forceRefresh) {
      _widgets.set(await getWidgets(localStorage.token));
    }
    availableWidgets = $_widgets ?? [];
  };

  const restoreReturnState = () => {
    const raw = sessionStorage.getItem(MCP_APP_RETURN_KEY);
    if (!raw) return false;
    sessionStorage.removeItem(MCP_APP_RETURN_KEY);
    try {
      const s = JSON.parse(raw);
      edit = s.edit;
      appId = s.appId;
      step = s.step ?? 3;
      name = s.name ?? '';
      description = s.description ?? '';
      icon = s.icon ?? '';
      transport = s.transport ?? 'http_streamable';
      url = s.url ?? '';
      command = s.command ?? '';
      args = s.args ?? '';
      envPairs = s.envPairs ?? [];
      authType = s.authType ?? '';
      authKey = s.authKey ?? '';
      discoveredTools = s.discoveredTools ?? [];
      toolConfigs = s.toolConfigs ?? {};
      testResult = s.testResult ?? null;
      skillPrompt = s.skillPrompt ?? '';
      widgetIds = s.widgetIds ?? [];
      accessGrants = s.accessGrants ?? [];
      return true;
    } catch {
      return false;
    }
  };

  // --- Init ---
  onMount(async () => {
    const restored = restoreReturnState();

    if (restored) {
      // Refresh widgets list to pick up newly created widget
      await loadWidgets(true);

      // Auto-select newly created widget
      const newWidgetId = sessionStorage.getItem(MCP_APP_NEW_WIDGET_KEY);
      if (newWidgetId) {
        sessionStorage.removeItem(MCP_APP_NEW_WIDGET_KEY);
        if (!widgetIds.includes(newWidgetId)) {
          widgetIds = [...widgetIds, newWidgetId];
        }
      }
      loading = false;
      return;
    }

    const id = $page.url.searchParams.get('id');
    if (id) {
      edit = true;
      appId = id;

      try {
        const app = await getMcpAppById(localStorage.token, id);
        if (app) {
          name = app.name || '';
          description = app.description || '';
          icon = app.icon || '';
          transport = app.transport || 'http_streamable';
          url = app.url || '';
          command = app.command || '';
          args = (app.args || []).join(' ');
          authType = app.auth_type || '';
          accessGrants = app.access_grants ?? [];

          // Restore tool configs
          if (app.tool_configs) {
            for (const tc of app.tool_configs) {
              const tcName = tc.name || tc.tool_name;
              toolConfigs[tcName] = {
                enabled: tc.enabled ?? true,
                display_name: tc.display_name || tcName,
                requires_confirmation: tc.requires_confirmation ?? false,
                confirmation_widget_id: tc.confirmation_widget_id || '',
              };
            }
            toolConfigs = toolConfigs;
            discoveredTools = app.tool_configs.map((tc) => ({ name: tc.name || tc.tool_name }));
          }

          skillPrompt = app.skill_prompt || '';
          widgetIds = app.widget_ids || [];
        } else {
          goto('/workspace/mcpapps');
          return;
        }
      } catch (error) {
        toast.error(`${error}`);
        goto('/workspace/mcpapps');
        return;
      }
    }

    await loadWidgets();
    loading = false;
  });
</script>

<AccessControlModal
  bind:show={showAccessControlModal}
  bind:accessGrants
  accessRoles={['read']}
  share={$user?.role === 'admin'}
  sharePublic={$user?.role === 'admin'}
  shareUsers={$user?.role === 'admin'}
  onChange={async () => {
    if (edit && appId) {
      try {
        await updateMcpAppAccessGrants(localStorage.token, appId, accessGrants);
        toast.success($i18n.t('Saved'));
      } catch (error) {
        toast.error(`${error}`);
      }
    }
  }}
/>

{#if loading}
  <div class="flex h-full w-full items-center justify-center">
    <Spinner className="size-5" />
  </div>
{:else}
  <div class="flex h-full w-full flex-col overflow-hidden bg-white dark:bg-gray-900">
    <!-- Header -->
    <div class="border-b border-gray-50 p-4 dark:border-gray-800">
      <div class="flex items-center justify-between gap-4">
        <div class="flex items-center gap-2 overflow-hidden">
          <Tooltip content={$i18n.t('Back')}>
            <button
              class="rounded-lg p-1.5 hover:bg-gray-50 dark:hover:bg-gray-800"
              on:click={() => goto('/workspace/mcpapps')}
            >
              <ChevronLeft strokeWidth="2.5" className="size-5" />
            </button>
          </Tooltip>

          <div class="flex flex-col gap-0.5 overflow-hidden">
            <div class="text-lg font-semibold">
              {edit ? $i18n.t('Edit MCP App') : $i18n.t('New MCP App')}
            </div>
            <div class="text-xs text-gray-400">
              {$i18n.t('Step {{step}} of 3', { step })}
              — {step === 1
                ? $i18n.t('Connection')
                : step === 2
                  ? $i18n.t('Tools')
                  : $i18n.t('Skill Prompt & Widgets')}
            </div>
          </div>
        </div>

        <div class="flex shrink-0 items-center gap-2">
          <button
            class="dark:bg-gray-850 flex items-center gap-1.5 rounded-full border border-gray-100 bg-gray-50 px-3 py-1.5 text-sm font-medium transition hover:bg-gray-100 dark:border-gray-800 dark:hover:bg-gray-800"
            on:click={() => (showAccessControlModal = true)}
          >
            <LockClosed strokeWidth="2.5" className="size-3.5" />
            <span>{$i18n.t('Access')}</span>
          </button>

          {#if step > 1}
            <button
              class="dark:bg-gray-850 flex items-center gap-1.5 rounded-full border border-gray-100 bg-gray-50 px-3 py-1.5 text-sm font-medium transition hover:bg-gray-100 dark:border-gray-800 dark:hover:bg-gray-800"
              on:click={() => (step -= 1)}
            >
              <ChevronLeft strokeWidth="2.5" className="size-3.5" />
              <span>{$i18n.t('Back')}</span>
            </button>
          {/if}

          {#if step < 3}
            <button
              class="flex items-center gap-1.5 rounded-full bg-black px-4 py-1.5 text-sm font-medium text-white transition hover:bg-gray-900 dark:bg-white dark:text-black dark:hover:bg-gray-100"
              on:click={() => {
                if (step === 1 && !name.trim()) {
                  toast.error($i18n.t('Name is required'));
                  return;
                }
                step += 1;
              }}
            >
              <span>{$i18n.t('Next')}</span>
              <ChevronRight strokeWidth="2.5" className="size-3.5" />
            </button>
          {:else}
            <button
              class="flex items-center gap-1.5 rounded-full bg-black px-4 py-1.5 text-sm font-medium text-white transition hover:bg-gray-900 dark:bg-white dark:text-black dark:hover:bg-gray-100"
              disabled={saving}
              on:click={submitHandler}
            >
              {#if saving}
                <Spinner className="size-3.5" />
              {:else}
                <Check strokeWidth="2.5" className="size-3.5" />
              {/if}
              <span>{edit ? $i18n.t('Save') : $i18n.t('Create')}</span>
            </button>
          {/if}
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto p-6">
      <div class="mx-auto max-w-2xl">
        <!-- Step 1: Connection Settings -->
        {#if step === 1}
          <div class="flex flex-col gap-5">
            <!-- Name & Icon -->
            <div class="flex gap-3">
              <div class="flex flex-col gap-1">
                <label class="text-xs font-medium text-gray-500" for="app-icon"
                  >{$i18n.t('Icon')}</label
                >
                <input
                  id="app-icon"
                  class="w-16 rounded-xl border border-gray-200 bg-transparent p-2.5 text-center text-lg outline-hidden dark:border-gray-700"
                  placeholder="⚡"
                  bind:value={icon}
                  maxlength="2"
                />
              </div>
              <div class="flex flex-1 flex-col gap-1">
                <label class="text-xs font-medium text-gray-500" for="app-name"
                  >{$i18n.t('Name')} *</label
                >
                <input
                  id="app-name"
                  class="w-full rounded-xl border border-gray-200 bg-transparent p-2.5 text-sm outline-hidden dark:border-gray-700"
                  placeholder={$i18n.t('My MCP App')}
                  bind:value={name}
                  required
                />
              </div>
            </div>

            <!-- Description -->
            <div class="flex flex-col gap-1">
              <label class="text-xs font-medium text-gray-500" for="app-description"
                >{$i18n.t('Description')}</label
              >
              <input
                id="app-description"
                class="w-full rounded-xl border border-gray-200 bg-transparent p-2.5 text-sm outline-hidden dark:border-gray-700"
                placeholder={$i18n.t('What does this app do?')}
                bind:value={description}
              />
            </div>

            <!-- Transport -->
            <div class="flex flex-col gap-1">
              <label class="text-xs font-medium text-gray-500">{$i18n.t('Transport')}</label>
              <div class="flex gap-2">
                {#each [{ value: 'http_streamable', label: 'HTTP Streamable' }, { value: 'sse', label: 'SSE' }, { value: 'stdio', label: 'stdio' }] as opt}
                  <button
                    class="rounded-xl border px-4 py-2 text-sm transition {transport === opt.value
                      ? 'border-black bg-black text-white dark:border-white dark:bg-white dark:text-black'
                      : 'border-gray-200 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800'}"
                    on:click={() => (transport = opt.value)}
                  >
                    {opt.label}
                  </button>
                {/each}
              </div>
            </div>

            <!-- URL (for HTTP/SSE) -->
            {#if transport === 'http_streamable' || transport === 'sse'}
              <div class="flex flex-col gap-1">
                <label class="text-xs font-medium text-gray-500" for="app-url"
                  >{$i18n.t('URL')} *</label
                >
                <input
                  id="app-url"
                  class="w-full rounded-xl border border-gray-200 bg-transparent p-2.5 font-mono text-sm outline-hidden dark:border-gray-700"
                  placeholder="https://mcp-server.example.com/mcp"
                  bind:value={url}
                />
              </div>

              <!-- Auth -->
              <div class="flex flex-col gap-1">
                <label class="text-xs font-medium text-gray-500">{$i18n.t('Authentication')}</label>
                <div class="flex gap-2">
                  {#each [{ value: '', label: 'None' }, { value: 'bearer', label: 'Bearer Token' }] as opt}
                    <button
                      class="rounded-xl border px-4 py-2 text-sm transition {authType === opt.value
                        ? 'border-black bg-black text-white dark:border-white dark:bg-white dark:text-black'
                        : 'border-gray-200 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800'}"
                      on:click={() => (authType = opt.value)}
                    >
                      {opt.label}
                    </button>
                  {/each}
                </div>
              </div>

              {#if authType === 'bearer'}
                <div class="flex flex-col gap-1">
                  <label class="text-xs font-medium text-gray-500" for="app-auth-key"
                    >{$i18n.t('Bearer Token')}</label
                  >
                  <input
                    id="app-auth-key"
                    type="password"
                    class="w-full rounded-xl border border-gray-200 bg-transparent p-2.5 font-mono text-sm outline-hidden dark:border-gray-700"
                    placeholder={edit ? $i18n.t('Leave empty to keep existing') : 'sk-...'}
                    bind:value={authKey}
                  />
                </div>
              {/if}
            {/if}

            <!-- Command / Args / Env (for stdio) -->
            {#if transport === 'stdio'}
              <div class="flex flex-col gap-1">
                <label class="text-xs font-medium text-gray-500" for="app-command"
                  >{$i18n.t('Command')} *</label
                >
                <input
                  id="app-command"
                  class="w-full rounded-xl border border-gray-200 bg-transparent p-2.5 font-mono text-sm outline-hidden dark:border-gray-700"
                  placeholder="npx"
                  bind:value={command}
                />
              </div>

              <div class="flex flex-col gap-1">
                <label class="text-xs font-medium text-gray-500" for="app-args"
                  >{$i18n.t('Arguments')}</label
                >
                <input
                  id="app-args"
                  class="w-full rounded-xl border border-gray-200 bg-transparent p-2.5 font-mono text-sm outline-hidden dark:border-gray-700"
                  placeholder="-y @modelcontextprotocol/server-filesystem /tmp"
                  bind:value={args}
                />
                <div class="text-xs text-gray-400">{$i18n.t('Space-separated arguments')}</div>
              </div>

              <!-- Environment Variables -->
              <div class="flex flex-col gap-1">
                <div class="flex items-center justify-between">
                  <label class="text-xs font-medium text-gray-500"
                    >{$i18n.t('Environment Variables')}</label
                  >
                  <button
                    class="text-xs text-blue-500 hover:text-blue-600"
                    on:click={() => {
                      envPairs = [...envPairs, { key: '', value: '' }];
                    }}
                  >
                    + {$i18n.t('Add')}
                  </button>
                </div>
                {#each envPairs as pair, idx}
                  <div class="flex gap-2">
                    <input
                      class="w-1/3 rounded-xl border border-gray-200 bg-transparent p-2 font-mono text-sm outline-hidden dark:border-gray-700"
                      placeholder="KEY"
                      bind:value={pair.key}
                    />
                    <input
                      class="flex-1 rounded-xl border border-gray-200 bg-transparent p-2 font-mono text-sm outline-hidden dark:border-gray-700"
                      placeholder="value"
                      type="password"
                      bind:value={pair.value}
                    />
                    <button
                      class="px-2 text-gray-400 hover:text-red-500"
                      on:click={() => {
                        envPairs = envPairs.filter((_, i) => i !== idx);
                      }}
                    >
                      ✕
                    </button>
                  </div>
                {/each}
              </div>
            {/if}

            <!-- Test Connection -->
            <div class="flex flex-col gap-2 pt-2">
              <button
                class="flex items-center justify-center gap-2 rounded-xl border border-gray-200 px-4 py-2.5 text-sm font-medium transition hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800"
                disabled={testing}
                on:click={testConnection}
              >
                {#if testing}
                  <Spinner className="size-4" />
                  {$i18n.t('Testing...')}
                {:else}
                  {$i18n.t('Test Connection')}
                {/if}
              </button>

              {#if testResult}
                <div
                  class="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700 dark:border-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-400"
                >
                  {$i18n.t('Connected successfully. Found {{count}} tools.', {
                    count: testResult.tool_count,
                  })}
                </div>
              {/if}

              {#if testError}
                <div
                  class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400"
                >
                  {testError}
                </div>
              {/if}
            </div>
          </div>
        {/if}

        <!-- Step 2: Tool Configuration -->
        {#if step === 2}
          <div class="flex flex-col gap-4">
            <div class="flex items-center justify-between">
              <div>
                <div class="text-sm font-medium">{$i18n.t('Tool Configuration')}</div>
                <div class="text-xs text-gray-500">
                  {$i18n.t('Enable/disable tools and configure confirmation requirements.')}
                </div>
              </div>

              {#if discoveredTools.length === 0}
                <button
                  class="flex items-center gap-2 rounded-xl border border-gray-200 px-3 py-1.5 text-xs font-medium transition hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800"
                  disabled={testing}
                  on:click={testConnection}
                >
                  {#if testing}
                    <Spinner className="size-3" />
                  {/if}
                  {$i18n.t('Discover Tools')}
                </button>
              {/if}
            </div>

            {#if discoveredTools.length === 0}
              <div class="flex flex-col items-center justify-center py-12 text-center">
                <div class="mb-2 text-2xl">🔧</div>
                <div class="text-sm text-gray-500">
                  {$i18n.t(
                    'No tools discovered yet. Test the connection first to discover available tools.',
                  )}
                </div>
              </div>
            {:else}
              <div class="flex flex-col gap-2">
                {#each toolConfigList as tcItem (tcItem.name)}
                  <div
                    class="rounded-xl border border-gray-100 p-3 dark:border-gray-800 {tcItem.cfg
                      .enabled
                      ? ''
                      : 'opacity-50'}"
                  >
                    <div class="flex items-start justify-between gap-3">
                      <div class="min-w-0 flex-1">
                        <div class="flex items-center gap-2">
                          <span class="font-mono text-sm font-medium">{tcItem.name}</span>
                        </div>

                        {#if tcItem.cfg.enabled}
                          <!-- Display name override -->
                          <div class="mt-2 flex items-center gap-2">
                            <label class="shrink-0 text-xs text-gray-400"
                              >{$i18n.t('Display name')}</label
                            >
                            <input
                              class="w-full rounded-lg border border-gray-100 bg-transparent px-2 py-1 text-xs outline-hidden dark:border-gray-800"
                              value={tcItem.cfg.display_name}
                              placeholder={tcItem.name}
                              on:input={(e) => {
                                toolConfigs[tcItem.name].display_name = e.target.value;
                                toolConfigs = toolConfigs;
                              }}
                            />
                          </div>

                          <!-- Confirmation -->
                          <div class="mt-2 flex items-center gap-3">
                            <div class="flex items-center gap-1.5">
                              <Switch
                                state={tcItem.cfg.requires_confirmation}
                                on:change={(e) => {
                                  toolConfigs[tcItem.name].requires_confirmation = e.detail;
                                  toolConfigs = toolConfigs;
                                }}
                              />
                              <span class="text-xs text-gray-500"
                                >{$i18n.t('Requires confirmation')}</span
                              >
                            </div>

                            {#if tcItem.cfg.requires_confirmation}
                              <select
                                class="rounded-lg border border-gray-100 bg-transparent px-2 py-1 text-xs outline-hidden dark:border-gray-800"
                                value={tcItem.cfg.confirmation_widget_id}
                                on:change={(e) => {
                                  toolConfigs[tcItem.name].confirmation_widget_id = e.target.value;
                                  toolConfigs = toolConfigs;
                                }}
                              >
                                <option value="">{$i18n.t('Generic confirmation')}</option>
                                {#each availableWidgets as widget}
                                  <option value={widget.id}>{widget.name}</option>
                                {/each}
                              </select>
                            {/if}
                          </div>
                        {/if}
                      </div>

                      <Switch
                        state={tcItem.cfg.enabled}
                        on:change={(e) => {
                          toolConfigs[tcItem.name].enabled = e.detail;
                          toolConfigs = toolConfigs;
                        }}
                      />
                    </div>
                  </div>
                {/each}
              </div>
            {/if}
          </div>
        {/if}

        <!-- Step 3: Skill Prompt & Widgets -->
        {#if step === 3}
          <div class="flex flex-col gap-5">
            <!-- Skill Prompt -->
            <div class="flex flex-col gap-1">
              <label class="text-xs font-medium text-gray-500" for="skill-prompt"
                >{$i18n.t('Skill Prompt')}</label
              >
              <div class="text-xs text-gray-400">
                {$i18n.t(
                  'Instructions for the agent when this app is active. Tool and widget sections are auto-generated.',
                )}
              </div>
              <textarea
                id="skill-prompt"
                class="mt-1 min-h-[200px] w-full rounded-xl border border-gray-200 bg-transparent p-3 font-mono text-sm outline-hidden dark:border-gray-700"
                placeholder={$i18n.t(
                  'You are a helpful assistant with access to the following tools...',
                )}
                bind:value={skillPrompt}
              />
            </div>

            <!-- Linked Widgets -->
            <div class="flex flex-col gap-2">
              <div class="flex items-center justify-between">
                <div>
                  <label class="text-xs font-medium text-gray-500"
                    >{$i18n.t('Linked Widgets')}</label
                  >
                  <div class="text-xs text-gray-400">
                    {$i18n.t(
                      'Widgets the agent can reference. They will be described in the auto-generated prompt section.',
                    )}
                  </div>
                </div>
                <button
                  class="flex items-center gap-1 text-xs font-medium text-blue-500 hover:text-blue-600"
                  on:click={goToCreateWidget}
                >
                  + {$i18n.t('Create Widget')}
                </button>
              </div>

              {#if availableWidgets.length === 0}
                <div class="py-4 text-center text-xs text-gray-500">
                  {$i18n.t('No widgets available. Click "Create Widget" above to add one.')}
                </div>
              {:else}
                <div class="flex flex-col gap-1.5">
                  {#each availableWidgets as widget (widget.id)}
                    {@const selected = widgetIds.includes(widget.id)}
                    <button
                      class="flex items-center gap-3 rounded-xl border px-3 py-2.5 text-left text-sm transition {selected
                        ? 'border-emerald-300 bg-emerald-50 dark:border-emerald-700 dark:bg-emerald-900/20'
                        : 'border-gray-100 hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-800'}"
                      on:click={() => {
                        if (selected) {
                          widgetIds = widgetIds.filter((id) => id !== widget.id);
                        } else {
                          widgetIds = [...widgetIds, widget.id];
                        }
                      }}
                    >
                      <div
                        class="flex size-5 items-center justify-center rounded border {selected
                          ? 'border-emerald-500 bg-emerald-500 text-white'
                          : 'border-gray-300 dark:border-gray-600'}"
                      >
                        {#if selected}
                          <Check className="size-3" strokeWidth="3" />
                        {/if}
                      </div>
                      <div class="min-w-0 flex-1">
                        <div class="font-medium">{widget.name}</div>
                        {#if widget.description}
                          <div class="truncate text-xs text-gray-500">{widget.description}</div>
                        {/if}
                      </div>
                      <Badge type="muted" content={widget.id} />
                    </button>
                  {/each}
                </div>
              {/if}
            </div>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}
