<script lang="ts">
  import fileSaver from 'file-saver';
  const { saveAs } = fileSaver;

  import {
    chatId,
    chats,
    user,
    settings,
    scrollPaginationEnabled,
    currentChatPage,
    pinnedChats,
  } from '$lib/stores';

  import {
    archiveAllChats,
    deleteAllChats,
    getAllChats,
    getChatList,
    getPinnedChatList,
    importChats,
  } from '$lib/apis/chats';
  import { getImportOrigin, convertOpenAIChats } from '$lib/utils';
  import { onMount, getContext } from 'svelte';
  import { goto } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import ArchivedChatsModal from '$lib/components/layout/ArchivedChatsModal.svelte';
  import SharedChatsModal from '$lib/components/layout/SharedChatsModal.svelte';
  import FilesModal from '$lib/components/layout/FilesModal.svelte';
  import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
  import SettingItem from '$lib/components/common/SettingItem.svelte';

  const i18n = getContext('i18n');

  export let saveSettings: Function;

  // Chats
  let importFiles;

  let showArchiveConfirmDialog = false;
  let showDeleteConfirmDialog = false;
  let showArchivedChatsModal = false;
  let showSharedChatsModal = false;
  let showFilesModal = false;

  let chatImportInputElement: HTMLInputElement;

  $: if (importFiles) {
    console.log(importFiles);

    let reader = new FileReader();
    reader.onload = (event) => {
      let chats = JSON.parse(event.target.result);
      console.log(chats);
      if (getImportOrigin(chats) == 'openai') {
        try {
          chats = convertOpenAIChats(chats);
        } catch (error) {
          console.log('Unable to import chats:', error);
        }
      }
      importChatsHandler(chats);
    };

    if (importFiles.length > 0) {
      reader.readAsText(importFiles[0]);
    }
  }

  const importChatsHandler = async (_chats) => {
    const res = await importChats(
      localStorage.token,
      _chats.map((chat) => {
        if (chat.chat) {
          return {
            chat: chat.chat,
            meta: chat.meta ?? {},
            pinned: false,
            folder_id: chat?.folder_id ?? null,
            created_at: chat?.created_at ?? null,
            updated_at: chat?.updated_at ?? null,
          };
        } else {
          // Legacy format
          return {
            chat: chat,
            meta: {},
            pinned: false,
            folder_id: null,
            created_at: chat?.created_at ?? null,
            updated_at: chat?.updated_at ?? null,
          };
        }
      }),
    );
    if (res) {
      toast.success(`Successfully imported ${res.length} chats.`);
    }

    currentChatPage.set(1);
    await chats.set(await getChatList(localStorage.token, $currentChatPage));
    pinnedChats.set(await getPinnedChatList(localStorage.token));
    scrollPaginationEnabled.set(true);
  };

  const exportChats = async () => {
    let blob = new Blob([JSON.stringify(await getAllChats(localStorage.token))], {
      type: 'application/json',
    });
    saveAs(blob, `chat-export-${Date.now()}.json`);
  };

  const archiveAllChatsHandler = async () => {
    await goto('/');
    await archiveAllChats(localStorage.token).catch((error) => {
      toast.error(`${error}`);
    });

    currentChatPage.set(1);
    await chats.set(await getChatList(localStorage.token, $currentChatPage));
    pinnedChats.set([]);
    scrollPaginationEnabled.set(true);
  };

  const deleteAllChatsHandler = async () => {
    await goto('/');
    await deleteAllChats(localStorage.token).catch((error) => {
      toast.error(`${error}`);
    });

    currentChatPage.set(1);
    await chats.set(await getChatList(localStorage.token, $currentChatPage));
    scrollPaginationEnabled.set(true);
  };

  const handleArchivedChatsChange = async () => {
    currentChatPage.set(1);
    await chats.set(await getChatList(localStorage.token, $currentChatPage));

    scrollPaginationEnabled.set(true);
  };
</script>

<ArchivedChatsModal
  bind:show={showArchivedChatsModal}
  onUpdate={handleArchivedChatsChange}
  onDelete={(id) => {
    if ($chatId === id) {
      goto('/');
      chatId.set('');
    }
  }}
/>
<SharedChatsModal bind:show={showSharedChatsModal} />
<FilesModal bind:show={showFilesModal} />

<ConfirmDialog
  title={$i18n.t('Archive All Chats')}
  message={$i18n.t('Are you sure you want to archive all chats? This action cannot be undone.')}
  bind:show={showArchiveConfirmDialog}
  on:confirm={archiveAllChatsHandler}
  on:cancel={() => {
    showArchiveConfirmDialog = false;
  }}
/>

<ConfirmDialog
  title={$i18n.t('Delete All Chats')}
  message={$i18n.t('Are you sure you want to delete all chats? This action cannot be undone.')}
  bind:show={showDeleteConfirmDialog}
  on:confirm={deleteAllChatsHandler}
  on:cancel={() => {
    showDeleteConfirmDialog = false;
  }}
/>

<div id="tab-chats" class="flex h-full flex-col justify-between text-sm">
  <div class="max-h-[28rem] space-y-3 overflow-y-scroll md:max-h-full">
    <input
      id="chat-import-input"
      bind:this={chatImportInputElement}
      bind:files={importFiles}
      type="file"
      accept=".json"
      hidden
    />

    <div class="space-y-1 px-1">
      <div
        class="my-2 mb-4 border-b border-gray-300 pb-1 text-base font-medium dark:border-gray-800"
      >
        {$i18n.t('Chats')}
      </div>

      <SettingItem label={$i18n.t('Import Chats')} labelId="chat-import-label">
        <button
          class="flex rounded-sm p-1 px-3 text-xs transition"
          on:click={() => {
            chatImportInputElement.click();
          }}
          type="button"
        >
          <span class="self-center">{$i18n.t('Import')}</span>
        </button>
      </SettingItem>

      {#if $user?.role === 'admin' || ($user.permissions?.chat?.export ?? true)}
        <SettingItem label={$i18n.t('Export Chats')} labelId="chat-export-label">
          <button
            class="flex rounded-sm p-1 px-3 text-xs transition"
            on:click={() => {
              exportChats();
            }}
            type="button"
          >
            <span class="self-center">{$i18n.t('Export')}</span>
          </button>
        </SettingItem>
      {/if}

      <SettingItem label={$i18n.t('Archived Chats')} labelId="chat-archived-label">
        <button
          class="flex rounded-sm p-1 px-3 text-xs transition"
          on:click={() => {
            showArchivedChatsModal = true;
          }}
          type="button"
        >
          <span class="self-center">{$i18n.t('Manage')}</span>
        </button>
      </SettingItem>

      <SettingItem label={$i18n.t('Shared Chats')} labelId="chat-shared-label">
        <button
          class="flex rounded-sm p-1 px-3 text-xs transition"
          on:click={() => {
            showSharedChatsModal = true;
          }}
          type="button"
        >
          <span class="self-center">{$i18n.t('Manage')}</span>
        </button>
      </SettingItem>

      <SettingItem label={$i18n.t('Archive All Chats')} labelId="chat-archive-all-label">
        <button
          class="flex rounded-sm p-1 px-3 text-xs transition"
          on:click={() => {
            showArchiveConfirmDialog = true;
          }}
          type="button"
        >
          <span class="self-center">{$i18n.t('Archive All')}</span>
        </button>
      </SettingItem>

      <SettingItem label={$i18n.t('Delete All Chats')} labelId="chat-delete-all-label">
        <button
          class="flex rounded-sm p-1 px-3 text-xs transition"
          on:click={() => {
            showDeleteConfirmDialog = true;
          }}
          type="button"
        >
          <span class="self-center">{$i18n.t('Delete All')}</span>
        </button>
      </SettingItem>
    </div>

    <div class="my-2 mb-4 border-b border-gray-300 pb-1 text-base font-medium dark:border-gray-800">
      {$i18n.t('Files')}
    </div>

    <SettingItem label={$i18n.t('Manage Files')} labelId="chat-manage-files-label">
      <button
        class="flex rounded-sm p-1 px-3 text-xs transition"
        on:click={() => {
          showFilesModal = true;
        }}
        type="button"
      >
        <span class="self-center">{$i18n.t('Manage')}</span>
      </button>
    </SettingItem>
  </div>
</div>
