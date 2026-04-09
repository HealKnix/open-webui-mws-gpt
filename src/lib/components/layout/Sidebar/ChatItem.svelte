<script lang="ts">
  import { toast } from 'svelte-sonner';
  import { goto, invalidate, invalidateAll } from '$app/navigation';
  import { onMount, getContext, createEventDispatcher, tick, onDestroy } from 'svelte';
  const i18n = getContext('i18n');

  const dispatch = createEventDispatcher();

  import {
    archiveChatById,
    cloneChatById,
    deleteChatById,
    getAllTags,
    getChatById,
    getChatList,
    getChatListByTagName,
    getPinnedChatList,
    updateChatById,
    updateChatFolderIdById,
  } from '$lib/apis/chats';
  import {
    chatId,
    chatTitle as _chatTitle,
    chats,
    mobile,
    pinnedChats,
    showSidebar,
    currentChatPage,
    tags,
    selectedFolder,
    activeChatIds,
  } from '$lib/stores';

  import ChatMenu from './ChatMenu.svelte';
  import DeleteConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
  import ShareChatModal from '$lib/components/chat/ShareChatModal.svelte';
  import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import ArchiveBox from '$lib/components/icons/ArchiveBox.svelte';
  import DragGhost from '$lib/components/common/DragGhost.svelte';
  import Check from '$lib/components/icons/Check.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';
  import Document from '$lib/components/icons/Document.svelte';
  import Sparkles from '$lib/components/icons/Sparkles.svelte';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import { generateTitle } from '$lib/apis';

  export let className = '';

  export let id;
  export let title;
  export let createdAt: number | null = null;

  export let selected = false;
  export let shiftKey = false;

  export let onDragEnd = () => {};

  function formatTimeAgo(timestamp: number): string {
    const now = Date.now();
    const diff = now - timestamp * 1000; // timestamp is in seconds

    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    const weeks = Math.floor(days / 7);
    const years = Math.floor(days / 365);

    if (years > 0) return $i18n.t('{{COUNT}}y', { COUNT: years, context: 'time_ago' });
    if (weeks > 0) return $i18n.t('{{COUNT}}w', { COUNT: weeks, context: 'time_ago' });
    if (days > 0) return $i18n.t('{{COUNT}}d', { COUNT: days, context: 'time_ago' });
    if (hours > 0) return $i18n.t('{{COUNT}}h', { COUNT: hours, context: 'time_ago' });
    if (minutes > 0) return $i18n.t('{{COUNT}}m', { COUNT: minutes, context: 'time_ago' });
    return $i18n.t('1m', { context: 'time_ago' });
  }

  let chat = null;

  let mouseOver = false;

  const loadChat = async () => {
    if (!chat) {
      draggable = false;
      chat = await getChatById(localStorage.token, id);
      draggable = true;
    }
  };

  let showShareChatModal = false;
  let confirmEdit = false;

  let chatTitle = title;

  const editChatTitle = async (id, title) => {
    if (title === '') {
      toast.error($i18n.t('Title cannot be an empty string.'));
    } else {
      await updateChatById(localStorage.token, id, {
        title: title,
      });

      if (id === $chatId) {
        _chatTitle.set(title);
      }

      currentChatPage.set(1);
      await chats.set(await getChatList(localStorage.token, $currentChatPage));
      await pinnedChats.set(await getPinnedChatList(localStorage.token));

      dispatch('change');
    }
  };

  const cloneChatHandler = async (id) => {
    const res = await cloneChatById(
      localStorage.token,
      id,
      $i18n.t('Clone of {{TITLE}}', {
        TITLE: title,
      }),
    ).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    if (res) {
      goto(`/c/${res.id}`);

      currentChatPage.set(1);
      await chats.set(await getChatList(localStorage.token, $currentChatPage));
      await pinnedChats.set(await getPinnedChatList(localStorage.token));
    }
  };

  const deleteChatHandler = async (id) => {
    const res = await deleteChatById(localStorage.token, id).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    if (res) {
      tags.set(await getAllTags(localStorage.token));
      if ($chatId === id) {
        await goto('/');

        await chatId.set('');
        await tick();
      }

      dispatch('change');
    }
  };

  const archiveChatHandler = async (id) => {
    try {
      await archiveChatById(localStorage.token, id);

      if ($chatId === id) {
        await goto('/');
        chatId.set('');
      }

      dispatch('change');
      toast.success($i18n.t('Chat archived.'));
    } catch (error) {
      console.error('Error archiving chat:', error);
      toast.error($i18n.t('Failed to archive chat.'));
    }
  };

  const moveChatHandler = async (chatId, folderId) => {
    if (chatId && folderId) {
      const res = await updateChatFolderIdById(localStorage.token, chatId, folderId).catch(
        (error) => {
          toast.error(`${error}`);
          return null;
        },
      );

      if (res) {
        currentChatPage.set(1);
        await chats.set(await getChatList(localStorage.token, $currentChatPage));
        await pinnedChats.set(await getPinnedChatList(localStorage.token));

        dispatch('change');

        toast.success($i18n.t('Chat moved successfully'));
      }
    } else {
      toast.error($i18n.t('Failed to move chat'));
    }
  };

  let itemElement;

  let generating = false;

  let ignoreBlur = false;
  let doubleClicked = false;

  let dragged = false;
  let x = 0;
  let y = 0;

  const dragImage = new Image();
  dragImage.src =
    'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=';

  const onDragStart = (event) => {
    event.stopPropagation();

    event.dataTransfer.setDragImage(dragImage, 0, 0);

    // Set the data to be transferred
    event.dataTransfer.setData(
      'text/plain',
      JSON.stringify({
        type: 'chat',
        id: id,
      }),
    );

    dragged = true;
    itemElement.style.opacity = '0.5'; // Optional: Visual cue to show it's being dragged
  };

  const onDrag = (event) => {
    event.stopPropagation();

    x = event.clientX;
    y = event.clientY;
  };

  const onDragEndHandler = (event) => {
    event.stopPropagation();

    itemElement.style.opacity = '1'; // Reset visual cue after drag
    dragged = false;

    onDragEnd(event);
  };

  const onClickOutside = (event) => {
    if (!itemElement.contains(event.target)) {
      if (confirmEdit) {
        if (chatTitle !== title) {
          editChatTitle(id, chatTitle);
        }

        confirmEdit = false;
        chatTitle = '';
      }
    }
  };

  onMount(() => {
    if (itemElement) {
      document.addEventListener('click', onClickOutside, true);

      // Event listener for when dragging starts
      itemElement.addEventListener('dragstart', onDragStart);
      // Event listener for when dragging occurs (optional)
      itemElement.addEventListener('drag', onDrag);
      // Event listener for when dragging ends
      itemElement.addEventListener('dragend', onDragEndHandler);
    }
  });

  onDestroy(() => {
    if (itemElement) {
      document.removeEventListener('click', onClickOutside, true);

      itemElement.removeEventListener('dragstart', onDragStart);
      itemElement.removeEventListener('drag', onDrag);
      itemElement.removeEventListener('dragend', onDragEndHandler);
    }
  });

  let showDeleteConfirm = false;

  const chatTitleInputKeydownHandler = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      setTimeout(() => {
        const input = document.getElementById(`chat-title-input-${id}`);
        if (input) input.blur();
      }, 0);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      confirmEdit = false;
      chatTitle = '';
    }
  };

  const renameHandler = async () => {
    chatTitle = title;
    confirmEdit = true;

    await tick();

    setTimeout(() => {
      const input = document.getElementById(`chat-title-input-${id}`);
      if (input) {
        input.focus();
        input.select();
      }
    }, 0);
  };

  const generateTitleHandler = async () => {
    generating = true;
    if (!chat) {
      chat = await getChatById(localStorage.token, id);
    }

    const messages = (chat.chat?.messages ?? []).map((message) => {
      return {
        role: message.role,
        content: message.content,
      };
    });

    const model = chat.chat.models.at(0) ?? chat.models.at(0) ?? '';

    chatTitle = '';

    const generatedTitle = await generateTitle(localStorage.token, model, messages).catch(
      (error) => {
        toast.error(`${error}`);
        return null;
      },
    );

    if (generatedTitle) {
      if (generatedTitle !== title) {
        editChatTitle(id, generatedTitle);
      }

      confirmEdit = false;
    } else {
      chatTitle = title;
    }

    generating = false;
  };
</script>

<ShareChatModal bind:show={showShareChatModal} chatId={id} />

<DeleteConfirmDialog
  bind:show={showDeleteConfirm}
  title={$i18n.t('Delete chat?')}
  on:confirm={() => {
    deleteChatHandler(id);
  }}
>
  <div class=" line-clamp-3 flex-1 text-sm text-gray-500">
    {$i18n.t('This will delete')} <span class="  font-semibold">{title}</span>.
  </div>
</DeleteConfirmDialog>

{#if dragged && x && y}
  <DragGhost {x} {y}>
    <div class=" w-fit max-w-40 rounded-lg bg-black/80 px-2 py-1 backdrop-blur-2xl">
      <div class="flex items-center gap-1">
        <Document className=" size-[18px]" strokeWidth="2" />
        <div class=" line-clamp-1 text-xs text-white">
          {title}
        </div>
      </div>
    </div>
  </DragGhost>
{/if}

<div
  id="sidebar-chat-group"
  bind:this={itemElement}
  class=" w-full {className} group relative"
  draggable={!confirmEdit}
>
  {#if confirmEdit}
    <div
      id="sidebar-chat-item"
      class=" flex w-full justify-between rounded-xl px-[11px] py-[6px] {id === $chatId ||
      confirmEdit
        ? 'selected bg-gray-100 dark:bg-gray-900'
        : selected
          ? 'selected bg-gray-100 dark:bg-gray-950'
          : 'group-hover:bg-gray-100 dark:group-hover:bg-gray-950'}  relative text-ellipsis whitespace-nowrap {generating
        ? 'cursor-not-allowed'
        : ''}"
    >
      <input
        id="chat-title-input-{id}"
        bind:value={chatTitle}
        class=" mr-10 w-full bg-transparent outline-hidden"
        placeholder={generating ? $i18n.t('Generating...') : ''}
        disabled={generating}
        on:keydown={chatTitleInputKeydownHandler}
        on:blur={async (e) => {
          if (doubleClicked) {
            e.preventDefault();
            e.stopPropagation();

            await tick();
            setTimeout(() => {
              const input = document.getElementById(`chat-title-input-${id}`);
              if (input) input.focus();
            }, 0);

            doubleClicked = false;
            return;
          }
        }}
      />
    </div>
  {:else}
    <a
      id="sidebar-chat-item"
      class=" flex w-full justify-between rounded-xl px-[11px] py-[6px] {id === $chatId ||
      confirmEdit
        ? 'selected bg-gray-100 dark:bg-gray-900'
        : selected
          ? 'selected bg-gray-100 dark:bg-gray-950'
          : ' group-hover:bg-gray-100 dark:group-hover:bg-gray-950'}  text-ellipsis whitespace-nowrap"
      href="/c/{id}"
      on:click={() => {
        dispatch('select');

        if ($selectedFolder) {
          selectedFolder.set(null);
        }

        if ($mobile) {
          showSidebar.set(false);
        }
      }}
      on:dblclick={async (e) => {
        e.preventDefault();
        e.stopPropagation();

        doubleClicked = true;
        renameHandler();
      }}
      on:mouseenter={(e) => {
        mouseOver = true;
      }}
      on:mouseleave={(e) => {
        mouseOver = false;
      }}
      on:focus={(e) => {}}
      draggable="false"
    >
      <!-- Loading spinner for active chat (left side) -->
      {#if $activeChatIds.has(id)}
        <div class="shrink-0 self-center pr-2">
          <Spinner className="size-3" />
        </div>
      {/if}

      <div class="flex w-full min-w-0 flex-1 self-center">
        <div dir="auto" class="h-[20px] w-full self-center truncate overflow-hidden text-left">
          {title}
        </div>
      </div>

      <!-- Time ago indicator -->
      {#if createdAt && !mouseOver}
        <div class="shrink-0 self-center pl-2 text-[10px] text-gray-400 dark:text-gray-500">
          {formatTimeAgo(createdAt)}
        </div>
      {/if}
    </a>
  {/if}

  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div
    id="sidebar-chat-item-menu"
    class="
        {id === $chatId || confirmEdit
      ? 'selected from-gray-100 dark:from-gray-900'
      : selected
        ? 'selected from-gray-100 dark:from-gray-950'
        : 'invisible from-gray-100 group-hover:visible dark:from-gray-950'}
            absolute {className === 'pr-2'
      ? 'right-[8px]'
      : 'right-1'} top-[4px] mr-1.5 bg-linear-to-l from-80% to-transparent py-1 pr-0.5

              pl-5"
    on:mouseenter={(e) => {
      mouseOver = true;
    }}
    on:mouseleave={(e) => {
      mouseOver = false;
    }}
  >
    {#if confirmEdit}
      <div
        class="z-10 flex -translate-x-[0.5px] translate-y-[0.5px] items-center space-x-1.5 self-center"
      >
        <Tooltip content={$i18n.t('Generate')}>
          <button
            class=" self-center transition disabled:cursor-not-allowed dark:hover:text-white"
            id="generate-title-button"
            disabled={generating}
            on:click={() => {
              generateTitleHandler();
            }}
          >
            <Sparkles strokeWidth="2" />
          </button>
        </Tooltip>
      </div>
    {:else if shiftKey && mouseOver}
      <div class=" flex items-center space-x-1.5 self-center">
        <Tooltip content={$i18n.t('Archive')} className="flex items-center">
          <button
            class=" self-center transition dark:hover:text-white"
            on:click={() => {
              archiveChatHandler(id);
            }}
            type="button"
          >
            <ArchiveBox className="size-4  translate-y-[0.5px]" strokeWidth="2" />
          </button>
        </Tooltip>

        <Tooltip content={$i18n.t('Delete')}>
          <button
            class=" self-center transition dark:hover:text-white"
            on:click={() => {
              deleteChatHandler(id);
            }}
            type="button"
          >
            <GarbageBin strokeWidth="2" />
          </button>
        </Tooltip>
      </div>
    {:else}
      <div class="z-10 flex items-end self-center">
        <ChatMenu
          chatId={id}
          cloneChatHandler={() => {
            cloneChatHandler(id);
          }}
          shareHandler={() => {
            showShareChatModal = true;
          }}
          {moveChatHandler}
          archiveChatHandler={() => {
            archiveChatHandler(id);
          }}
          {renameHandler}
          deleteHandler={() => {
            showDeleteConfirm = true;
          }}
          onClose={() => {
            dispatch('unselect');
          }}
          onPinChange={async () => {
            dispatch('change');
          }}
        >
          <button
            aria-label="Chat Menu"
            class=" m-0 self-center transition dark:hover:text-white"
            on:click={() => {
              dispatch('select');
            }}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 16 16"
              fill="currentColor"
              class="h-4 w-4"
            >
              <path
                d="M2 8a1.5 1.5 0 1 1 3 0 1.5 1.5 0 0 1-3 0ZM6.5 8a1.5 1.5 0 1 1 3 0 1.5 1.5 0 0 1-3 0ZM12.5 6.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Z"
              />
            </svg>
          </button>
        </ChatMenu>

        {#if id === $chatId}
          <!-- Shortcut support using "delete-chat-button" id -->
          <button
            id="delete-chat-button"
            class="hidden"
            on:click={() => {
              showDeleteConfirm = true;
            }}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 16 16"
              fill="currentColor"
              class="h-4 w-4"
            >
              <path
                d="M2 8a1.5 1.5 0 1 1 3 0 1.5 1.5 0 0 1-3 0ZM6.5 8a1.5 1.5 0 1 1 3 0 1.5 1.5 0 0 1-3 0ZM12.5 6.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Z"
              />
            </svg>
          </button>
        {/if}
      </div>
    {/if}
  </div>
</div>
