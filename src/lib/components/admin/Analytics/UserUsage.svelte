<script lang="ts">
  import { onMount, getContext } from 'svelte';
  import { getUserAnalytics } from '$lib/apis/analytics';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import ChevronUp from '$lib/components/icons/ChevronUp.svelte';
  import ChevronDown from '$lib/components/icons/ChevronDown.svelte';

  const i18n = getContext('i18n');

  let userStats: Array<{ user_id: string; count: number }> = [];
  let loading = true;
  let orderBy = 'count';
  let direction: 'asc' | 'desc' = 'desc';

  const toggleSort = (key: string) => {
    if (orderBy === key) {
      direction = direction === 'asc' ? 'desc' : 'asc';
    } else {
      orderBy = key;
      direction = key === 'user_id' ? 'asc' : 'desc';
    }
  };

  const loadAnalytics = async () => {
    loading = true;
    try {
      const result = await getUserAnalytics(localStorage.token, null, null, 100);
      userStats = result?.users ?? [];
    } catch (err) {
      console.error('User analytics load failed:', err);
    }
    loading = false;
  };

  $: sortedUsers = [...userStats].sort((a, b) => {
    if (orderBy === 'user_id') {
      return direction === 'asc'
        ? a.user_id.localeCompare(b.user_id)
        : b.user_id.localeCompare(a.user_id);
    }
    return direction === 'asc' ? a.count - b.count : b.count - a.count;
  });

  $: totalMessages = userStats.reduce((sum, u) => sum + u.count, 0);

  onMount(loadAnalytics);
</script>

<div
  class="sticky top-0 z-10 flex flex-col justify-between gap-1 bg-white pt-0.5 pb-1 md:flex-row dark:bg-gray-900"
>
  <div class="flex shrink-0 items-center gap-2 px-0.5 text-xl font-medium">
    {$i18n.t('User Activity')}
    <span class="text-lg text-gray-500">{userStats.length} {$i18n.t('users')}</span>
  </div>
</div>

<div
  class="scrollbar-hidden relative min-h-[100px] max-w-full overflow-x-auto rounded-sm whitespace-nowrap"
>
  {#if loading}
    <div
      class="absolute inset-0 z-10 flex items-center justify-center bg-white/50 dark:bg-gray-900/50"
    >
      <Spinner className="size-5" />
    </div>
  {/if}

  {#if !userStats.length && !loading}
    <div class="py-1 text-center text-xs text-gray-500">{$i18n.t('No data found')}</div>
  {:else if userStats.length}
    <table
      class="w-full text-left text-sm text-gray-500 dark:text-gray-400 {loading
        ? 'opacity-20'
        : ''}"
    >
      <thead class="bg-transparent text-xs text-gray-800 uppercase dark:text-gray-200">
        <tr class="dark:border-gray-850/30 border-b-[1.5px] border-gray-50">
          <th scope="col" class="w-8 px-2.5 py-2">#</th>
          <th
            scope="col"
            class="cursor-pointer px-2.5 py-2 select-none"
            on:click={() => toggleSort('user_id')}
          >
            <div class="flex items-center gap-1.5">
              {$i18n.t('User')}
              {#if orderBy === 'user_id'}
                {#if direction === 'asc'}<ChevronUp className="size-2" />{:else}<ChevronDown
                    className="size-2"
                  />{/if}
              {:else}
                <span class="invisible"><ChevronUp className="size-2" /></span>
              {/if}
            </div>
          </th>
          <th
            scope="col"
            class="cursor-pointer px-2.5 py-2 text-right select-none"
            on:click={() => toggleSort('count')}
          >
            <div class="flex items-center justify-end gap-1.5">
              {$i18n.t('Messages')}
              {#if orderBy === 'count'}
                {#if direction === 'asc'}<ChevronUp className="size-2" />{:else}<ChevronDown
                    className="size-2"
                  />{/if}
              {:else}
                <span class="invisible"><ChevronUp className="size-2" /></span>
              {/if}
            </div>
          </th>
          <th
            scope="col"
            class="w-24 cursor-pointer px-2.5 py-2 text-right select-none"
            on:click={() => toggleSort('percentage')}
          >
            <div class="flex items-center justify-end gap-1.5">
              {$i18n.t('Share')}
              {#if orderBy === 'percentage'}
                {#if direction === 'asc'}<ChevronUp className="size-2" />{:else}<ChevronDown
                    className="size-2"
                  />{/if}
              {:else}
                <span class="invisible"><ChevronUp className="size-2" /></span>
              {/if}
            </div>
          </th>
        </tr>
      </thead>
      <tbody>
        {#each sortedUsers as user, idx (user.user_id)}
          <tr
            class="dark:hover:bg-gray-850/50 bg-white text-xs transition hover:bg-gray-50 dark:bg-gray-900"
          >
            <td class="px-3 py-1.5 font-medium text-gray-900 dark:text-white">
              {idx + 1}
            </td>
            <td class="px-3 py-1.5">
              <span class="font-mono text-xs font-medium text-gray-800 dark:text-gray-200">
                {user.user_id.substring(0, 8)}...
              </span>
            </td>
            <td class="px-3 py-1.5 text-right font-medium text-gray-900 dark:text-white">
              {user.count.toLocaleString()}
            </td>
            <td class="px-3 py-1.5 text-right font-medium text-blue-500">
              {((user.count / totalMessages) * 100).toFixed(1)}%
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  {/if}
</div>

<div class="mt-1.5 flex w-full justify-end text-xs text-gray-500">
  <div class="text-right">
    ⓘ {$i18n.t('Showing all messages (user + assistant) per user.')}
  </div>
</div>
