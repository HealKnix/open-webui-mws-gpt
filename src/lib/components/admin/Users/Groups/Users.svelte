<script lang="ts">
  import { getContext, onDestroy } from 'svelte';
  const i18n = getContext('i18n');

  import dayjs from 'dayjs';
  import relativeTime from 'dayjs/plugin/relativeTime';
  import localizedFormat from 'dayjs/plugin/localizedFormat';
  dayjs.extend(relativeTime);
  dayjs.extend(localizedFormat);

  import { getUsers } from '$lib/apis/users';
  import { toast } from 'svelte-sonner';

  import { addUserToGroup, removeUserFromGroup } from '$lib/apis/groups';
  import { WEBUI_API_BASE_URL } from '$lib/constants';

  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Checkbox from '$lib/components/common/Checkbox.svelte';
  import Badge from '$lib/components/common/Badge.svelte';
  import Search from '$lib/components/icons/Search.svelte';
  import Pagination from '$lib/components/common/Pagination.svelte';
  import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
  import ChevronUp from '$lib/components/icons/ChevronUp.svelte';
  import Spinner from '$lib/components/common/Spinner.svelte';

  export let groupId: string;
  export let userCount = 0;

  let users = null;
  let total = null;

  let query = '';
  let searchDebounceTimer: ReturnType<typeof setTimeout>;
  let orderBy = groupId ? `group_id:${groupId}` : 'last_active_at'; // default sort key
  let direction = 'desc'; // default sort order

  let page = 1;

  const setSortKey = (key) => {
    if (orderBy === key) {
      direction = direction === 'asc' ? 'desc' : 'asc';
    } else {
      orderBy = key;
      direction = 'asc';
    }
    page = 1;
  };

  const getUserList = async () => {
    try {
      const res = await getUsers(localStorage.token, query, orderBy, direction, page).catch(
        (error) => {
          toast.error(`${error}`);
          return null;
        },
      );

      if (res) {
        users = res.users;
        total = res.total;
      }
    } catch (err) {
      console.error(err);
    }
  };

  const toggleMember = async (userId, state) => {
    if (state === 'checked') {
      await addUserToGroup(localStorage.token, groupId, [userId]).catch((error) => {
        toast.error(`${error}`);
        return null;
      });
    } else {
      await removeUserFromGroup(localStorage.token, groupId, [userId]).catch((error) => {
        toast.error(`${error}`);
        return null;
      });
    }

    getUserList();
  };

  $: if (page !== null && orderBy !== null && direction !== null) {
    getUserList();
  }

  $: if (query !== undefined) {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
      page = 1;
      getUserList();
    }, 300);
  }

  onDestroy(() => {
    clearTimeout(searchDebounceTimer);
  });
</script>

<div class=" flex h-full max-h-full w-full flex-col overflow-y-hidden">
  <div class="mb-1.5 h-fit w-full">
    <div class="flex h-fit flex-1">
      <div class=" mr-3 self-center">
        <Search />
      </div>
      <input
        class=" w-full rounded-r-xl bg-transparent pr-4 text-sm outline-hidden"
        bind:value={query}
        placeholder={$i18n.t('Search')}
      />
    </div>
  </div>

  {#if users === null || total === null}
    <div class="my-10">
      <Spinner className="size-5" />
    </div>
  {:else}
    {#if users.length > 0}
      <div class="scrollbar-hidden relative max-w-full overflow-x-auto whitespace-nowrap">
        <table
          class="w-full max-w-full table-auto text-left text-sm text-gray-500 dark:text-gray-400"
        >
          <thead class="bg-transparent text-xs text-gray-800 uppercase dark:text-gray-200">
            <tr class=" border-b-[1.5px] border-gray-50/50 dark:border-gray-800/10">
              <th
                scope="col"
                class="w-8 cursor-pointer px-2.5 py-2 text-left"
                on:click={() => setSortKey(`group_id:${groupId}`)}
              >
                <div class="flex items-center gap-1.5">
                  {$i18n.t('MBR')}

                  {#if orderBy === `group_id:${groupId}`}
                    <span class="font-normal"
                      >{#if direction === 'asc'}
                        <ChevronUp className="size-2" />
                      {:else}
                        <ChevronDown className="size-2" />
                      {/if}
                    </span>
                  {:else}
                    <span class="invisible">
                      <ChevronUp className="size-2" />
                    </span>
                  {/if}
                </div>
              </th>

              <th
                scope="col"
                class="cursor-pointer px-2.5 py-2 select-none"
                on:click={() => setSortKey('role')}
              >
                <div class="flex items-center gap-1.5">
                  {$i18n.t('Role')}

                  {#if orderBy === 'role'}
                    <span class="font-normal"
                      >{#if direction === 'asc'}
                        <ChevronUp className="size-2" />
                      {:else}
                        <ChevronDown className="size-2" />
                      {/if}
                    </span>
                  {:else}
                    <span class="invisible">
                      <ChevronUp className="size-2" />
                    </span>
                  {/if}
                </div>
              </th>
              <th
                scope="col"
                class="cursor-pointer px-2.5 py-2 select-none"
                on:click={() => setSortKey('name')}
              >
                <div class="flex items-center gap-1.5">
                  {$i18n.t('Name')}

                  {#if orderBy === 'name'}
                    <span class="font-normal"
                      >{#if direction === 'asc'}
                        <ChevronUp className="size-2" />
                      {:else}
                        <ChevronDown className="size-2" />
                      {/if}
                    </span>
                  {:else}
                    <span class="invisible">
                      <ChevronUp className="size-2" />
                    </span>
                  {/if}
                </div>
              </th>

              <th
                scope="col"
                class="cursor-pointer px-2.5 py-2 select-none"
                on:click={() => setSortKey('last_active_at')}
              >
                <div class="flex items-center gap-1.5">
                  {$i18n.t('Last Active')}

                  {#if orderBy === 'last_active_at'}
                    <span class="font-normal"
                      >{#if direction === 'asc'}
                        <ChevronUp className="size-2" />
                      {:else}
                        <ChevronDown className="size-2" />
                      {/if}
                    </span>
                  {:else}
                    <span class="invisible">
                      <ChevronUp className="size-2" />
                    </span>
                  {/if}
                </div>
              </th>
            </tr>
          </thead>
          <tbody class="">
            {#each users as user, userIdx (user?.id ?? userIdx)}
              <tr class="dark:border-gray-850 bg-white text-xs dark:bg-gray-900">
                <td class=" w-8 px-3 py-1">
                  <div class="flex w-full justify-center">
                    <Checkbox
                      state={(user?.group_ids ?? []).includes(groupId) ? 'checked' : 'unchecked'}
                      on:change={(e) => {
                        toggleMember(user.id, e.detail);
                      }}
                    />
                  </div>
                </td>
                <td class="w-28 min-w-[7rem] px-3 py-1">
                  <div class=" translate-y-0.5">
                    <Badge
                      type={user.role === 'admin'
                        ? 'info'
                        : user.role === 'user'
                          ? 'success'
                          : 'muted'}
                      content={$i18n.t(user.role)}
                    />
                  </div>
                </td>
                <td class="max-w-48 px-3 py-1 font-medium text-gray-900 dark:text-white">
                  <Tooltip content={user.email} placement="top-start">
                    <div class="flex items-center">
                      <img
                        class="mr-2.5 h-6 w-6 flex-shrink-0 rounded-full object-cover"
                        src={`${WEBUI_API_BASE_URL}/users/${user.id}/profile/image`}
                        alt="user"
                      />

                      <div class="truncate font-medium">{user.name}</div>
                    </div>
                  </Tooltip>
                </td>

                <td class=" px-3 py-1">
                  {dayjs(user.last_active_at * 1000).fromNow()}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {:else}
      <div class="px-10 py-2 text-center text-xs text-gray-500">
        {$i18n.t('No users were found.')}
      </div>
    {/if}

    {#if total > 30}
      <Pagination bind:page count={total} perPage={30} />
    {/if}
  {/if}
</div>
