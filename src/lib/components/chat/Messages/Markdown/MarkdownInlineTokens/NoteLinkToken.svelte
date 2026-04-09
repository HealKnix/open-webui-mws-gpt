<script lang="ts">
  import { onMount, getContext } from 'svelte';
  import { goto } from '$app/navigation';
  import { getNoteById } from '$lib/apis/notes';
  import { getUserInfoById } from '$lib/apis/users';
  import { capitalizeFirstLetter } from '$lib/utils';

  const i18n = getContext('i18n');

  export let noteId: string;
  export let href: string;

  let title = '';
  let author = '';
  let loading = true;

  onMount(async () => {
    try {
      const note = await getNoteById(localStorage.token, noteId);
      if (note) {
        title = note.title || $i18n.t('Untitled');

        if (note.user_id) {
          try {
            const userInfo = await getUserInfoById(localStorage.token, note.user_id);
            if (userInfo) {
              author = capitalizeFirstLetter(userInfo.name ?? userInfo.email ?? '');
            }
          } catch {
            // user lookup failed, skip author
          }
        }
      }
    } catch {
      title = $i18n.t('Note');
    } finally {
      loading = false;
    }
  });
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<!-- svelte-ignore a11y-no-static-element-interactions -->
<button
  class="group dark:bg-gray-850 relative flex w-60 cursor-pointer flex-col rounded-xl border border-gray-50/30 bg-white px-3 py-2 text-left dark:border-gray-800/30"
  type="button"
  on:click|preventDefault|stopPropagation={() => {
    try {
      const url = new URL(href, window.location.origin);
      goto(url.pathname);
    } catch {
      // fallback
    }
  }}
>
  <div class="flex w-full min-w-0 flex-col justify-center">
    <div class="flex items-center justify-between gap-2 text-sm dark:text-gray-100">
      <div class="line-clamp-1 min-w-0 flex-1 font-medium">
        {#if loading}
          <span class="text-gray-400">...</span>
        {:else}
          {title}
        {/if}
      </div>
      <div class="shrink-0 text-xs text-gray-500">{$i18n.t('Note')}</div>
    </div>
    {#if author}
      <div class="mt-0.5 line-clamp-1 text-xs text-gray-500">
        {$i18n.t('By {{name}}', { name: author })}
      </div>
    {/if}
  </div>
</button>
