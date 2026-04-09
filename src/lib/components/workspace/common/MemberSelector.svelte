<script lang="ts">
  import { toast } from 'svelte-sonner';
  import { getContext, onMount, onDestroy } from 'svelte';

  const i18n = getContext('i18n');

  import { user as _user } from '$lib/stores';
  import { getUserInfoById, searchUsers } from '$lib/apis/users';
  import { WEBUI_API_BASE_URL } from '$lib/constants';

  import XMark from '$lib/components/icons/XMark.svelte';
  import Pagination from '$lib/components/common/Pagination.svelte';
  import ProfilePreview from '$lib/components/channel/Messages/Message/ProfilePreview.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import ChevronUp from '$lib/components/icons/ChevronUp.svelte';
  import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import Checkbox from '$lib/components/common/Checkbox.svelte';
  import { getGroups } from '$lib/apis/groups';

  export let includeGroups = true;
  export let includeUsers = true;
  export let pagination = false;
  export let includeSessionUser = false;

  export let groupIds = [];
  export let userIds = [];

  let groups = null;
  let filteredGroups = [];

  $: filteredGroups = groups
    ? groups.filter((group) => group.name.toLowerCase().includes(query.toLowerCase()))
    : [];

  let selectedGroup = {};
  let selectedUsers = {};

  let page = 1;
  let users = null;
  let total = null;

  let query = '';
  let searchDebounceTimer: ReturnType<typeof setTimeout>;
  let orderBy = 'name'; // default sort key
  let direction = 'asc'; // default sort order

  const getUserList = async () => {
    try {
      const res = await searchUsers(localStorage.token, query, orderBy, direction, page).catch(
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

  $: if (query !== undefined) {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
      getUserList();
    }, 300);
  }

  onDestroy(() => {
    clearTimeout(searchDebounceTimer);
  });

  $: if (page !== null && orderBy !== null && direction !== null) {
    getUserList();
  }

  onMount(async () => {
    groups = await getGroups(localStorage.token, true).catch((error) => {
      console.error(error);
      return [];
    });

    if (userIds.length > 0) {
      userIds.forEach(async (id) => {
        const res = await getUserInfoById(localStorage.token, id).catch((error) => {
          console.error(error);
          return null;
        });
        if (res) {
          selectedUsers[id] = res;
        }
      });
    }
  });
</script>

<div class="">
  {#if users === null || total === null}
    <div class="my-10">
      <Spinner className="size-5" />
    </div>
  {:else}
    {#if groupIds.length > 0}
      <div class="mx-1 mb-1.5">
        <div class="mx-0.5 mb-1 text-xs text-gray-500">
          {groupIds.length}
          {$i18n.t('groups')}
        </div>
        <div class="flex flex-wrap gap-1">
          {#each groupIds as id}
            {#if selectedGroup[id]}
              <button
                type="button"
                class="dark:bg-gray-850 inline-flex items-center space-x-1 rounded-lg bg-gray-100/50 px-2 py-1 text-xs"
                on:click={() => {
                  groupIds = groupIds.filter((gid) => gid !== id);
                  delete selectedGroup[id];
                }}
              >
                <div>
                  {selectedGroup[id].name}
                  <span class="text-xs text-gray-500">{selectedGroup[id].member_count}</span>
                </div>

                <div>
                  <XMark className="size-3" />
                </div>
              </button>
            {/if}
          {/each}
        </div>
      </div>
    {/if}

    {#if userIds.length > 0}
      <div class="mx-1 mb-1.5">
        <div class="mx-0.5 mb-1 text-xs text-gray-500">
          {userIds.length}
          {$i18n.t('users')}
        </div>
        <div class="flex flex-wrap gap-1">
          {#each userIds as id}
            {#if selectedUsers[id]}
              <button
                type="button"
                class="dark:bg-gray-850 inline-flex items-center space-x-1 rounded-lg bg-gray-100/50 px-2 py-1 text-xs"
                on:click={() => {
                  userIds = userIds.filter((uid) => uid !== id);
                  delete selectedUsers[id];
                }}
              >
                <div>
                  {selectedUsers[id].name}
                </div>

                <div>
                  <XMark className="size-3" />
                </div>
              </button>
            {/if}
          {/each}
        </div>
      </div>
    {/if}

    <div class="mb-1 flex gap-1">
      <div class=" flex w-full space-x-2">
        <div class="flex flex-1">
          <div class=" mr-3 ml-1 self-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
              class="h-4 w-4"
            >
              <path
                fill-rule="evenodd"
                d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z"
                clip-rule="evenodd"
              />
            </svg>
          </div>
          <input
            class=" w-full rounded-r-xl bg-transparent py-1 pr-4 text-sm outline-hidden"
            bind:value={query}
            placeholder={$i18n.t('Search')}
          />
        </div>
      </div>
    </div>

    {#if users.length > 0 || filteredGroups.length > 0}
      <div class="scrollbar-hidden relative w-full max-w-full whitespace-nowrap">
        <div class=" w-full max-w-full text-left text-sm text-gray-500 dark:text-gray-400">
          <div class="max-h-96 w-full overflow-y-auto rounded-lg">
            {#if includeGroups && filteredGroups.length > 0}
              <div class="mx-1 mb-1 text-xs text-gray-500">
                {$i18n.t('Groups')}
              </div>

              <div class="mb-3">
                {#each filteredGroups as group, groupIdx (group.id)}
                  <button
                    class=" dark:border-gray-850 flex w-full items-center justify-between text-xs"
                    type="button"
                    on:click={() => {
                      if ((groupIds ?? []).includes(group.id)) {
                        groupIds = groupIds.filter((id) => id !== group.id);
                        delete selectedGroup[group.id];
                      } else {
                        groupIds = [...groupIds, group.id];
                        selectedGroup[group.id] = group;
                      }
                    }}
                  >
                    <div class="flex-1 px-3 py-1.5 font-medium text-gray-900 dark:text-white">
                      <div class="flex items-center gap-2">
                        <Tooltip content={group.name} placement="top-start">
                          <div class="flex items-center gap-1 truncate font-medium">
                            {group.name} <span class="text-gray-500">{group.member_count}</span>
                          </div>
                        </Tooltip>
                      </div>
                    </div>

                    <div class="px-3 py-1">
                      <div class=" translate-y-0.5">
                        <Checkbox
                          state={(groupIds ?? []).includes(group.id) ? 'checked' : 'unchecked'}
                        />
                      </div>
                    </div>
                  </button>
                {/each}
              </div>
            {/if}

            {#if includeUsers}
              <div class="mx-1 mb-1 text-xs text-gray-500">
                {$i18n.t('Users')}
              </div>

              <div>
                {#each users as user, userIdx (user.id)}
                  {#if includeSessionUser || user?.id !== $_user?.id}
                    <button
                      class=" dark:border-gray-850 flex w-full items-center justify-between text-xs"
                      type="button"
                      on:click={() => {
                        if ((userIds ?? []).includes(user.id)) {
                          userIds = userIds.filter((id) => id !== user.id);
                          delete selectedUsers[user.id];
                        } else {
                          userIds = [...userIds, user.id];
                          selectedUsers[user.id] = user;
                        }
                      }}
                    >
                      <div class="flex-1 px-3 py-1.5 font-medium text-gray-900 dark:text-white">
                        <div class="flex items-center gap-2">
                          <ProfilePreview {user} side="right" align="center" sideOffset={6}>
                            <img
                              class="h-6 w-6 flex-shrink-0 rounded-2xl object-cover"
                              src={`${WEBUI_API_BASE_URL}/users/${user.id}/profile/image`}
                              alt="user"
                            />
                          </ProfilePreview>
                          <Tooltip content={user.email} placement="top-start">
                            <div class="truncate font-medium">{user.name}</div>
                          </Tooltip>

                          {#if user?.is_active}
                            <div>
                              <span class="relative flex size-1.5">
                                <span
                                  class="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75"
                                ></span>
                                <span
                                  class="relative inline-flex size-1.5 rounded-full bg-green-500"
                                ></span>
                              </span>
                            </div>
                          {/if}
                        </div>
                      </div>

                      <div class="px-3 py-1">
                        <div class=" translate-y-0.5">
                          <Checkbox
                            state={(userIds ?? []).includes(user.id) ? 'checked' : 'unchecked'}
                          />
                        </div>
                      </div>
                    </button>
                  {/if}
                {/each}
              </div>
            {/if}
          </div>
        </div>
      </div>
    {:else}
      <div class="px-10 py-5 text-center text-xs text-gray-500">
        {$i18n.t('No users were found.')}
      </div>
    {/if}
  {/if}
</div>
