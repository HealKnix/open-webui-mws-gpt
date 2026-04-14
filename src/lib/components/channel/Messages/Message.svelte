<script lang="ts">
  import dayjs from 'dayjs';
  import relativeTime from 'dayjs/plugin/relativeTime';
  import isToday from 'dayjs/plugin/isToday';
  import isYesterday from 'dayjs/plugin/isYesterday';
  import localizedFormat from 'dayjs/plugin/localizedFormat';

  dayjs.extend(relativeTime);
  dayjs.extend(isToday);
  dayjs.extend(isYesterday);
  dayjs.extend(localizedFormat);

  import { getContext, onMount } from 'svelte';
  const i18n = getContext<Writable<i18nType>>('i18n');

  import { formatDate } from '$lib/utils';

  import { settings, user, shortCodesToEmojis } from '$lib/stores';
  import { WEBUI_API_BASE_URL, WEBUI_BASE_URL } from '$lib/constants';
  import { getMessageData } from '$lib/apis/channels';

  import Markdown from '$lib/components/chat/Messages/Markdown.svelte';
  import ProfileImage from '$lib/components/chat/Messages/ProfileImage.svelte';
  import Name from '$lib/components/chat/Messages/Name.svelte';
  import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
  import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
  import Pencil from '$lib/components/icons/Pencil.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Textarea from '$lib/components/common/Textarea.svelte';
  import Image from '$lib/components/common/Image.svelte';
  import FileItem from '$lib/components/common/FileItem.svelte';
  import ProfilePreview from './Message/ProfilePreview.svelte';
  import ChatBubbleOvalEllipsis from '$lib/components/icons/ChatBubble.svelte';
  import FaceSmile from '$lib/components/icons/FaceSmile.svelte';
  import EmojiPicker from '$lib/components/common/EmojiPicker.svelte';
  import ChevronRight from '$lib/components/icons/ChevronRight.svelte';
  import Emoji from '$lib/components/common/Emoji.svelte';
  import Skeleton from '$lib/components/chat/Messages/Skeleton.svelte';
  import ArrowUpLeftAlt from '$lib/components/icons/ArrowUpLeftAlt.svelte';
  import PinSlash from '$lib/components/icons/PinSlash.svelte';
  import Pin from '$lib/components/icons/Pin.svelte';

  export let className = '';

  export let message;
  export let channel;

  export let showUserProfile = true;
  export let thread = false;

  export let replyToMessage = false;
  export let disabled = false;
  export let pending = false;

  export let onDelete: Function = () => {};
  export let onEdit: Function = () => {};
  export let onReply: Function = () => {};
  export let onPin: Function = () => {};
  export let onThread: Function = () => {};
  export let onReaction: Function = () => {};

  let showButtons = false;

  let edit = false;
  let editedContent = null;
  let showDeleteConfirmDialog = false;

  const loadMessageData = async () => {
    if (message && message?.data === true) {
      const res = await getMessageData(localStorage.token, channel?.id, message.id);
      if (res) {
        message.data = res;
      }
    }
  };

  onMount(async () => {
    if (message && message?.data === true) {
      await loadMessageData();
    }
  });
</script>

<ConfirmDialog
  bind:show={showDeleteConfirmDialog}
  title={$i18n.t('Delete Message')}
  message={$i18n.t('Are you sure you want to delete this message?')}
  onConfirm={async () => {
    await onDelete();
  }}
/>

{#if message}
  <div
    id="message-{message.id}"
    class="group relative mx-auto flex w-full max-w-full flex-col justify-between transition hover:bg-gray-300/5 dark:hover:bg-gray-700/5 {className
      ? className
      : `px-5 ${
          replyToMessage ? 'border-l-4 border-blue-500 bg-blue-100/10 pl-4 dark:bg-blue-100/5' : ''
        } ${
          (message?.reply_to_message?.meta?.model_id ?? message?.reply_to_message?.user_id) ===
          $user?.id
            ? 'border-l-4 border-orange-500 bg-orange-100/10 pl-4 dark:bg-orange-100/5'
            : ''
        } ${message?.is_pinned ? 'bg-yellow-100/20 dark:bg-yellow-100/5' : ''}`} {showUserProfile
      ? 'pt-1.5 pb-0.5'
      : ''}"
  >
    {#if !edit && !disabled}
      <div
        class=" absolute {showButtons ? '' : 'invisible group-hover:visible'} -top-2 right-1 z-10"
      >
        <div
          class="dark:bg-gray-850 dark:border-gray-850/30 flex gap-1 rounded-lg border border-gray-100/30 bg-white p-0.5 shadow-md"
        >
          {#if onReaction}
            <EmojiPicker
              onClose={() => (showButtons = false)}
              onSubmit={(name) => {
                showButtons = false;
                onReaction(name);
              }}
            >
              <Tooltip content={$i18n.t('Add Reaction')}>
                <button
                  class="rounded-lg p-1 transition hover:bg-gray-100 dark:hover:bg-gray-800"
                  on:click={() => {
                    showButtons = true;
                  }}
                >
                  <FaceSmile />
                </button>
              </Tooltip>
            </EmojiPicker>
          {/if}

          {#if onReply}
            <Tooltip content={$i18n.t('Reply')}>
              <button
                class="rounded-lg p-0.5 transition hover:bg-gray-100 dark:hover:bg-gray-800"
                on:click={() => {
                  onReply(message);
                }}
              >
                <ArrowUpLeftAlt className="size-5" />
              </button>
            </Tooltip>
          {/if}

          <Tooltip content={message?.is_pinned ? $i18n.t('Unpin') : $i18n.t('Pin')}>
            <button
              class="rounded-lg p-1 transition hover:bg-gray-100 dark:hover:bg-gray-800"
              on:click={() => {
                onPin(message);
              }}
            >
              {#if message?.is_pinned}
                <PinSlash className="size-4" />
              {:else}
                <Pin className="size-4" />
              {/if}
            </button>
          </Tooltip>

          {#if !thread && onThread}
            <Tooltip content={$i18n.t('Reply in Thread')}>
              <button
                class="rounded-lg p-1 transition hover:bg-gray-100 dark:hover:bg-gray-800"
                on:click={() => {
                  onThread(message.id);
                }}
              >
                <ChatBubbleOvalEllipsis />
              </button>
            </Tooltip>
          {/if}

          {#if message.user_id === $user?.id || $user?.role === 'admin'}
            {#if onEdit}
              <Tooltip content={$i18n.t('Edit')}>
                <button
                  class="rounded-lg p-1 transition hover:bg-gray-100 dark:hover:bg-gray-800"
                  on:click={() => {
                    edit = true;
                    editedContent = message.content;
                  }}
                >
                  <Pencil />
                </button>
              </Tooltip>
            {/if}

            {#if onDelete}
              <Tooltip content={$i18n.t('Delete')}>
                <button
                  class="rounded-lg p-1 transition hover:bg-gray-100 dark:hover:bg-gray-800"
                  on:click={() => (showDeleteConfirmDialog = true)}
                >
                  <GarbageBin />
                </button>
              </Tooltip>
            {/if}
          {/if}
        </div>
      </div>
    {/if}

    {#if message?.is_pinned}
      <div class="flex {showUserProfile ? 'mb-0.5' : 'mt-0.5'}">
        <div class="ml-8.5 flex items-center gap-1 rounded-full px-1 text-xs">
          <Pin className="size-3 text-yellow-500 dark:text-yellow-300" />
          <span class="text-gray-500">{$i18n.t('Pinned')}</span>
        </div>
      </div>
    {/if}

    {#if message?.reply_to_message?.user}
      <div class="relative mb-1 text-xs">
        <div
          class="absolute top-2 left-[18px] z-0 h-3 w-7 rounded-tl-lg border-t-[1.5px] border-l-[1.5px] border-gray-200 dark:border-gray-700"
        ></div>

        <button
          class="relative z-0 ml-12 flex items-center space-x-2"
          on:click={() => {
            const messageElement = document.getElementById(
              `message-${message.reply_to_message.id}`,
            );
            if (messageElement) {
              messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
              messageElement.classList.add('highlight');
              setTimeout(() => {
                messageElement.classList.remove('highlight');
              }, 2000);
              return;
            }
          }}
        >
          {#if message?.reply_to_message?.meta?.model_id}
            <img
              src={`${WEBUI_API_BASE_URL}/models/model/profile/image?id=${message.reply_to_message.meta.model_id}`}
              alt={message.reply_to_message.meta.model_name ??
                message.reply_to_message.meta.model_id}
              class="ml-0.5 size-4 rounded-full object-cover"
              on:error={(e) => {
                e.currentTarget.src = '/favicon.png';
              }}
            />
          {:else}
            <img
              src={message.reply_to_message.user?.role === 'webhook'
                ? `${WEBUI_API_BASE_URL}/channels/webhooks/${message.reply_to_message.user?.id}/profile/image`
                : `${WEBUI_API_BASE_URL}/users/${message.reply_to_message.user?.id}/profile/image`}
              alt={message.reply_to_message.user?.name ?? $i18n.t('Unknown User')}
              class="ml-0.5 size-4 rounded-full object-cover"
            />
          {/if}

          <div class="shrink-0">
            {message?.reply_to_message.meta?.model_name ??
              message?.reply_to_message.user?.name ??
              $i18n.t('Unknown User')}
          </div>

          <div class="line-clamp-1 w-full flex-1 text-sm text-gray-500 italic dark:text-gray-400">
            <Markdown id={`${message.id}-reply-to`} content={message?.reply_to_message?.content} />
          </div>
        </button>
      </div>
    {/if}

    <div
      class=" flex w-full message-{message.id} "
      id="message-{message.id}"
      dir={$settings.chatDirection}
    >
      <div class={`mr-1 w-9 shrink-0`}>
        {#if showUserProfile}
          {#if message?.meta?.model_id}
            <img
              src={`${WEBUI_API_BASE_URL}/models/model/profile/image?id=${message.meta.model_id}`}
              alt={message.meta.model_name ?? message.meta.model_id}
              class="ml-0.5 size-8 translate-y-1 rounded-full object-cover"
              on:error={(e) => {
                e.currentTarget.src = '/favicon.png';
              }}
            />
          {:else if message.user?.role === 'webhook'}
            <ProfileImage
              src={`${WEBUI_API_BASE_URL}/channels/webhooks/${message.user?.id}/profile/image`}
              className={'size-8 ml-0.5'}
            />
          {:else}
            <ProfilePreview user={message.user}>
              <ProfileImage
                src={`${WEBUI_API_BASE_URL}/users/${message.user?.id}/profile/image`}
                className={'size-8 ml-0.5'}
              />
            </ProfilePreview>
          {/if}
        {:else}
          <!-- <div class="w-7 h-7 rounded-full bg-transparent" /> -->

          {#if message.created_at}
            <div
              class="invisible mt-1.5 flex shrink-0 items-center self-center text-xs font-medium text-gray-500 group-hover:visible first-letter:capitalize"
            >
              <Tooltip content={dayjs(message.created_at / 1000000).format('LLLL')}>
                {dayjs(message.created_at / 1000000).format('HH:mm')}
              </Tooltip>
            </div>
          {/if}
        {/if}
      </div>

      <div class="w-0 flex-auto pl-2">
        {#if showUserProfile}
          <Name>
            <div class=" shrink-0 self-end truncate text-base font-medium">
              {#if message?.meta?.model_id}
                {message?.meta?.model_name ?? message?.meta?.model_id}
              {:else}
                {message?.user?.name}
              {/if}
            </div>

            {#if message.created_at}
              <div
                class=" ml-0.5 translate-y-[1px] self-center text-xs font-medium text-gray-400 first-letter:capitalize"
              >
                <Tooltip content={dayjs(message.created_at / 1000000).format('LLLL')}>
                  <span class="line-clamp-1">
                    {#if dayjs(message.created_at / 1000000).isToday()}
                      {dayjs(message.created_at / 1000000).format('LT')}
                    {:else}
                      {$i18n.t(formatDate(message.created_at / 1000000), {
                        LOCALIZED_TIME: dayjs(message.created_at / 1000000).format('LT'),
                        LOCALIZED_DATE: dayjs(message.created_at / 1000000).format('L'),
                      })}
                    {/if}
                  </span>
                </Tooltip>
              </div>
            {/if}
          </Name>
        {/if}

        {#if message?.data === true}
          <!-- loading indicator -->
          <div class=" my-2">
            <Skeleton />
          </div>
        {:else if (message?.data?.files ?? []).length > 0}
          <div
            class="my-2.5 flex w-full flex-wrap gap-2 overflow-x-auto"
            dir={$settings?.chatDirection ?? 'auto'}
          >
            {#each message?.data?.files as file}
              {@const fileUrl =
                file.url.startsWith('data') || file.url.startsWith('http')
                  ? file.url
                  : `${WEBUI_API_BASE_URL}/files/${file.url}${file?.content_type ? '/content' : ''}`}
              <div>
                {#if file.type === 'image' || (file?.content_type ?? '').startsWith('image/')}
                  <Image src={fileUrl} alt={file.name} imageClassName=" max-h-96 rounded-lg" />
                {:else if file.type === 'video' || (file?.content_type ?? '').startsWith('video/')}
                  <video src={fileUrl} controls class=" max-h-96 rounded-lg"></video>
                {:else}
                  <FileItem
                    item={file}
                    url={file.url}
                    name={file.name}
                    type={file.type}
                    size={file?.size}
                    small={true}
                  />
                {/if}
              </div>
            {/each}
          </div>
        {/if}

        {#if edit}
          <div class="py-2">
            <Textarea
              className=" bg-transparent outline-hidden w-full resize-none"
              bind:value={editedContent}
              onKeydown={(e) => {
                if (e.key === 'Escape') {
                  document.getElementById('close-edit-message-button')?.click();
                }

                const isCmdOrCtrlPressed = e.metaKey || e.ctrlKey;
                const isEnterPressed = e.key === 'Enter';

                if (isCmdOrCtrlPressed && isEnterPressed) {
                  document.getElementById('confirm-edit-message-button')?.click();
                }
              }}
            />
            <div class=" mt-2 mb-1 flex justify-end text-sm font-medium">
              <div class="flex space-x-1.5">
                <button
                  id="close-edit-message-button"
                  class="rounded-3xl bg-white px-3.5 py-1.5 text-gray-800 transition hover:bg-gray-100 dark:bg-gray-900 dark:text-gray-100"
                  on:click={() => {
                    edit = false;
                    editedContent = null;
                  }}
                >
                  {$i18n.t('Cancel')}
                </button>

                <button
                  id="confirm-edit-message-button"
                  class="hover:bg-gray-850 rounded-3xl bg-gray-900 px-3.5 py-1.5 text-gray-100 transition dark:bg-white dark:text-gray-800"
                  on:click={async () => {
                    onEdit(editedContent);
                    edit = false;
                    editedContent = null;
                  }}
                >
                  {$i18n.t('Save')}
                </button>
              </div>
            </div>
          </div>
        {:else}
          <div class=" markdown-prose min-w-full {pending ? 'opacity-50' : ''}">
            {#if (message?.content ?? '').trim() === '' && message?.meta?.model_id}
              <Skeleton />
            {:else}
              <Markdown
                id={message.id}
                content={message.content}
                paragraphTag="span"
              />{#if message.created_at !== message.updated_at && (message?.meta?.model_id ?? null) === null}<span
                  class="self-center pl-1 text-[10px] text-gray-500">({$i18n.t('edited')})</span
                >{/if}
            {/if}
          </div>

          {#if (message?.reactions ?? []).length > 0}
            <div>
              <div class="mt-1 mb-2 flex flex-wrap items-center gap-1 gap-y-1.5">
                {#each message.reactions as reaction}
                  <Tooltip
                    content={$i18n.t('{{NAMES}} reacted with {{REACTION}}', {
                      NAMES: reaction.users
                        .reduce((acc, u, idx) => {
                          const name = u.id === $user?.id ? $i18n.t('You') : u.name;
                          const total = reaction.users.length;

                          // First three names always added normally
                          if (idx < 3) {
                            const separator =
                              idx === 0
                                ? ''
                                : idx === Math.min(2, total - 1)
                                  ? ` ${$i18n.t('and')} `
                                  : ', ';
                            return `${acc}${separator}${name}`;
                          }

                          // More than 4 → "and X others"
                          if (idx === 3 && total > 4) {
                            return (
                              acc +
                              ` ${$i18n.t('and {{COUNT}} others', {
                                COUNT: total - 3,
                              })}`
                            );
                          }

                          return acc;
                        }, '')
                        .trim(),
                      REACTION: `:${reaction.name}:`,
                    })}
                  >
                    <button
                      class="flex cursor-pointer items-center gap-1.5 rounded-xl px-2 py-1 transition {reaction.users
                        .map((u) => u.id)
                        .includes($user?.id)
                        ? ' bg-blue-300/10 outline outline-1 outline-blue-500/50'
                        : 'bg-gray-300/10 hover:outline hover:outline-1 hover:outline-gray-700/30 dark:bg-gray-500/10 dark:hover:outline-gray-300/30'}"
                      on:click={() => {
                        if (onReaction) {
                          onReaction(reaction.name);
                        }
                      }}
                    >
                      <Emoji shortCode={reaction.name} />

                      {#if reaction.users.length > 0}
                        <div class="text-xs font-medium text-gray-500 dark:text-gray-400">
                          {reaction.users?.length}
                        </div>
                      {/if}
                    </button>
                  </Tooltip>
                {/each}

                {#if onReaction}
                  <EmojiPicker
                    onSubmit={(name) => {
                      onReaction(name);
                    }}
                  >
                    <Tooltip content={$i18n.t('Add Reaction')}>
                      <div
                        class="flex cursor-pointer items-center gap-1.5 rounded-xl bg-gray-500/10 px-1 py-1 text-gray-500 transition hover:outline hover:outline-1 hover:outline-gray-700/30 dark:text-gray-400 dark:hover:outline-gray-300/30"
                      >
                        <FaceSmile />
                      </div>
                    </Tooltip>
                  </EmojiPicker>
                {/if}
              </div>
            </div>
          {/if}

          {#if !thread && message.reply_count > 0}
            <div class="-mt-0.5 mb-1.5 flex items-center gap-1.5">
              <button
                class="flex items-center py-1 text-xs text-gray-500 transition hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                on:click={() => {
                  onThread(message.id);
                }}
              >
                <span class="mr-1 font-medium">
                  {$i18n.t('{{COUNT}} Replies', { COUNT: message.reply_count })}</span
                ><span>
                  {' - '}{$i18n.t('Last reply')}
                  {dayjs.unix(message.latest_reply_at / 1000000000).fromNow()}</span
                >

                <span class="ml-1">
                  <ChevronRight className="size-2.5" strokeWidth="3" />
                </span>
                <!-- {$i18n.t('View Replies')} -->
              </button>
            </div>
          {/if}
        {/if}
      </div>
    </div>
  </div>
{/if}

<style>
  .highlight {
    animation: highlightAnimation 2s ease-in-out;
  }

  @keyframes highlightAnimation {
    0% {
      background-color: rgba(0, 60, 255, 0.1);
    }
    100% {
      background-color: transparent;
    }
  }
</style>
