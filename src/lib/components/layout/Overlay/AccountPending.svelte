<script lang="ts">
  import DOMPurify from 'dompurify';
  import { marked } from 'marked';

  import { getAdminDetails } from '$lib/apis/auths';
  import { onMount, tick, getContext } from 'svelte';
  import { config } from '$lib/stores';

  const i18n = getContext('i18n');

  let adminDetails = null;

  onMount(async () => {
    adminDetails = await getAdminDetails(localStorage.token).catch((err) => {
      console.error(err);
      return null;
    });
  });
</script>

<div class="fixed z-999 flex h-full w-full">
  <div
    class="absolute flex h-full w-full justify-center bg-white/10 backdrop-blur-lg dark:bg-gray-900/50"
  >
    <div class="m-auto flex flex-col justify-center pb-10">
      <div class="max-w-md">
        <div
          class="z-50 text-center text-2xl font-medium dark:text-white"
          style="white-space: pre-wrap;"
        >
          {#if ($config?.ui?.pending_user_overlay_title ?? '').trim() !== ''}
            {$config.ui.pending_user_overlay_title}
          {:else}
            {$i18n.t('Account Activation Pending')}<br />
            {$i18n.t('Contact Admin for WebUI Access')}
          {/if}
        </div>

        <div
          class=" mt-4 w-full text-center text-sm dark:text-gray-200"
          style="white-space: pre-wrap;"
        >
          {#if ($config?.ui?.pending_user_overlay_content ?? '').trim() !== ''}
            {@html marked.parse(
              DOMPurify.sanitize(
                ($config?.ui?.pending_user_overlay_content ?? '').replace(/\n/g, '<br>'),
              ),
            )}
          {:else}
            {$i18n.t('Your account status is currently pending activation.')}{'\n'}{$i18n.t(
              'To access the WebUI, please reach out to the administrator. Admins can manage user statuses from the Admin Panel.',
            )}
          {/if}
        </div>

        {#if adminDetails}
          <div class="mt-4 text-center text-sm font-medium">
            <div>{$i18n.t('Admin')}: {adminDetails.name} ({adminDetails.email})</div>
          </div>
        {/if}

        <div class=" group relative mx-auto mt-6 w-fit">
          <button
            class="relative z-20 flex rounded-full border border-gray-100 bg-white px-5 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-100 dark:border-none"
            on:click={async () => {
              location.href = '/';
            }}
          >
            {$i18n.t('Check Again')}
          </button>

          <button
            class="mt-2 w-full text-center text-xs text-gray-400 underline"
            on:click={async () => {
              localStorage.removeItem('token');
              location.href = '/auth';
            }}>{$i18n.t('Sign Out')}</button
          >
        </div>
      </div>
    </div>
  </div>
</div>
