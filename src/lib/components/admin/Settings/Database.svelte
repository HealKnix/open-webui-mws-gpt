<script lang="ts">
  import fileSaver from 'file-saver';
  const { saveAs } = fileSaver;

  import { downloadDatabase } from '$lib/apis/utils';
  import { onMount, getContext } from 'svelte';
  import { config, user } from '$lib/stores';
  import { toast } from 'svelte-sonner';
  import { getAllUserChats } from '$lib/apis/chats';
  import { getAllUsers } from '$lib/apis/users';
  import { exportConfig, importConfig } from '$lib/apis/configs';
  import SettingItem from '$lib/components/common/SettingItem.svelte';

  const i18n = getContext('i18n');

  export let saveHandler: Function;

  const exportAllUserChats = async () => {
    let blob = new Blob([JSON.stringify(await getAllUserChats(localStorage.token))], {
      type: 'application/json',
    });
    saveAs(blob, `all-chats-export-${Date.now()}.json`);
  };

  const exportUsers = async () => {
    const users = await getAllUsers(localStorage.token);

    const headers = ['id', 'name', 'email', 'role'];

    const csv = [
      headers.join(','),
      ...users.users.map((user) => {
        return headers
          .map((header) => {
            if (user[header] === null || user[header] === undefined) {
              return '';
            }
            return `"${String(user[header]).replace(/"/g, '""')}"`;
          })
          .join(',');
      }),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    saveAs(blob, 'users.csv');
  };

  onMount(async () => {
    // permissions = await getUserPermissions(localStorage.token);
  });
</script>

<div class="flex h-full flex-col justify-between text-sm">
  <div class="scrollbar-hidden h-full space-y-3 overflow-y-scroll p-1">
    <input
      id="config-json-input"
      hidden
      type="file"
      accept=".json"
      on:change={(e) => {
        const file = e.target.files[0];
        const reader = new FileReader();

        reader.onload = async (e) => {
          const res = await importConfig(localStorage.token, JSON.parse(e.target.result)).catch(
            (error) => {
              toast.error(`${error}`);
            },
          );

          if (res) {
            toast.success($i18n.t('Config imported successfully'));
          }
          e.target.value = null;
        };

        reader.readAsText(file);
      }}
    />

    <div class="space-y-1">
      <div class="my-2 border-b border-gray-300 pb-2 text-base font-medium dark:border-gray-800">
        {$i18n.t('Config')}
      </div>

      <div>
        <SettingItem label={$i18n.t('Import Config')}>
          <button
            class="flex rounded-sm p-1 px-3 text-xs transition"
            on:click={() => {
              document.getElementById('config-json-input').click();
            }}
            type="button"
          >
            <span class="self-center">{$i18n.t('Import')}</span>
          </button>
        </SettingItem>
      </div>

      <div>
        <SettingItem label={$i18n.t('Export Config')}>
          <button
            class="flex rounded-sm p-1 px-3 text-xs transition"
            on:click={async () => {
              const config = await exportConfig(localStorage.token);
              const blob = new Blob([JSON.stringify(config)], {
                type: 'application/json',
              });
              saveAs(blob, `config-${Date.now()}.json`);
            }}
            type="button"
          >
            <span class="self-center">{$i18n.t('Export')}</span>
          </button>
        </SettingItem>
      </div>
    </div>

    {#if $config?.features.enable_admin_export ?? true}
      <div class="space-y-1">
        <div class="my-2 border-b border-gray-300 pb-2 text-base font-medium dark:border-gray-800">
          {$i18n.t('Database')}
        </div>

        <div>
          <SettingItem label={$i18n.t('Download Database')}>
            <button
              class="flex rounded-sm p-1 px-3 text-xs transition"
              on:click={() => {
                downloadDatabase(localStorage.token).catch((error) => {
                  toast.error(`${error}`);
                });
              }}
              type="button"
            >
              <span class="self-center">{$i18n.t('Download')}</span>
            </button>
          </SettingItem>
        </div>

        <div>
          <SettingItem label={$i18n.t('Export All Chats (All Users)')}>
            <button
              class="flex rounded-sm p-1 px-3 text-xs transition"
              on:click={() => {
                exportAllUserChats();
              }}
              type="button"
            >
              <span class="self-center">{$i18n.t('Export')}</span>
            </button>
          </SettingItem>
        </div>

        <div>
          <SettingItem label={$i18n.t('Export Users')}>
            <button
              class="flex rounded-sm p-1 px-3 text-xs transition"
              on:click={() => {
                exportUsers();
              }}
              type="button"
            >
              <span class="self-center">{$i18n.t('Export')}</span>
            </button>
          </SettingItem>
        </div>
      </div>
    {/if}
  </div>
</div>
