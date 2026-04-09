<script lang="ts">
  import { toast } from 'svelte-sonner';
  import { getContext } from 'svelte';

  import {
    getChannelWebhooks,
    createChannelWebhook,
    updateChannelWebhook,
    deleteChannelWebhook,
  } from '$lib/apis/channels';

  import Modal from '$lib/components/common/Modal.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import Plus from '$lib/components/icons/Plus.svelte';
  import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
  import WebhookItem from './WebhookItem.svelte';

  const i18n = getContext('i18n');

  export let show = false;
  export let channel = null;

  let webhooks = [];
  let isLoading = false;
  let isSaving = false;

  let showDeleteConfirmDialog = false;
  let selectedWebhookId = null;

  // Track pending changes from child components
  let pendingChanges: { [webhookId: string]: { name: string; profile_image_url: string } } = {};

  const loadWebhooks = async () => {
    isLoading = true;
    try {
      webhooks = await getChannelWebhooks(localStorage.token, channel.id);
    } catch {
      webhooks = [];
    }
    isLoading = false;
  };

  const createHandler = async () => {
    isSaving = true;
    try {
      const newWebhook = await createChannelWebhook(localStorage.token, channel.id, {
        name: 'New Webhook',
      });
      if (newWebhook) {
        webhooks = [...webhooks, newWebhook];
        selectedWebhookId = newWebhook.id;
      }
    } catch (error) {
      toast.error(`${error}`);
    }
    isSaving = false;
  };

  const saveHandler = async () => {
    isSaving = true;
    try {
      for (const [webhookId, changes] of Object.entries(pendingChanges)) {
        await updateChannelWebhook(localStorage.token, channel.id, webhookId, changes);
      }
      pendingChanges = {};
      await loadWebhooks();
      toast.success($i18n.t('Saved'));
    } catch (error) {
      toast.error(`${error}`);
    }
    isSaving = false;
  };

  const deleteHandler = async () => {
    if (!selectedWebhookId) return;

    try {
      await deleteChannelWebhook(localStorage.token, channel.id, selectedWebhookId);
      webhooks = webhooks.filter((webhook) => webhook.id !== selectedWebhookId);
      toast.success($i18n.t('Deleted'));
    } catch (error) {
      toast.error(`${error}`);
    }

    selectedWebhookId = null;
    showDeleteConfirmDialog = false;
  };

  $: if (show && channel) {
    loadWebhooks();
    selectedWebhookId = null;
    pendingChanges = {};
  }
</script>

<ConfirmDialog bind:show={showDeleteConfirmDialog} on:confirm={deleteHandler} />

{#if channel}
  <Modal size="sm" bind:show>
    <div>
      <div class="mb-1.5 flex justify-between px-5 pt-4 dark:text-gray-100">
        <div class="mr-3 flex w-full items-center justify-between">
          <div class="flex items-center gap-1.5 self-center text-base">
            <div>{$i18n.t('Webhooks')}</div>
            <span class="text-sm text-gray-500">{webhooks.length}</span>
          </div>

          <button
            type="button"
            class="dark:bg-gray-850/50 flex items-center justify-center gap-1 rounded-xl bg-gray-100/50 px-3 py-1.5 text-xs font-medium text-black transition dark:text-white"
            on:click={createHandler}
            disabled={isSaving}
          >
            <Plus className="size-3.5" />
            <span>{$i18n.t('New Webhook')}</span>
          </button>
        </div>

        <button class="self-center" on:click={() => (show = false)}>
          <XMark className="size-5" />
        </button>
      </div>

      <div class="flex w-full flex-col px-4 pb-4 dark:text-gray-200">
        <form
          class="flex w-full flex-col"
          on:submit={(e) => {
            e.preventDefault();
            saveHandler();
          }}
        >
          {#if isLoading}
            <div class="flex justify-center py-10">
              <Spinner className="size-5" />
            </div>
          {:else if webhooks.length > 0}
            <div class="w-full py-2">
              {#each webhooks as webhook (webhook.id)}
                <WebhookItem
                  {webhook}
                  expanded={selectedWebhookId === webhook.id}
                  onClick={() => {
                    selectedWebhookId = selectedWebhookId === webhook.id ? null : webhook.id;
                  }}
                  onDelete={() => {
                    showDeleteConfirmDialog = true;
                  }}
                  onUpdate={(changes) => {
                    pendingChanges[webhook.id] = changes;
                  }}
                />
              {/each}
            </div>
          {:else}
            <div class="px-10 py-8 text-center text-xs text-gray-500">
              {$i18n.t('No webhooks yet')}
            </div>
          {/if}

          <div class="flex justify-end gap-1.5 text-sm font-medium">
            <button
              class="flex items-center gap-2 rounded-full bg-black px-3.5 py-1.5 text-sm font-medium whitespace-nowrap text-white transition hover:bg-gray-900 dark:bg-white dark:text-black dark:hover:bg-gray-100 {isSaving
                ? 'cursor-not-allowed'
                : ''}"
              type="submit"
              disabled={isSaving}
            >
              {$i18n.t('Save')}
              {#if isSaving}
                <span class="shrink-0">
                  <Spinner />
                </span>
              {/if}
            </button>
          </div>
        </form>
      </div>
    </div>
  </Modal>
{/if}
