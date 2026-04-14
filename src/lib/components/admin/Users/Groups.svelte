<script>
  import { toast } from 'svelte-sonner';
  import dayjs from 'dayjs';
  import relativeTime from 'dayjs/plugin/relativeTime';
  dayjs.extend(relativeTime);

  import { onMount, getContext } from 'svelte';
  import { goto } from '$app/navigation';

  import { WEBUI_NAME, config, user, showSidebar, knowledge } from '$lib/stores';
  import { WEBUI_BASE_URL } from '$lib/constants';

  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Plus from '$lib/components/icons/Plus.svelte';
  import UsersSolid from '$lib/components/icons/UsersSolid.svelte';
  import ChevronRight from '$lib/components/icons/ChevronRight.svelte';
  import Search from '$lib/components/icons/Search.svelte';
  import EditGroupModal from './Groups/EditGroupModal.svelte';
  import GroupItem from './Groups/GroupItem.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';
  import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
  import Check from '$lib/components/icons/Check.svelte';
  import Select from '$lib/components/common/Select.svelte';
  import { createNewGroup, getGroups } from '$lib/apis/groups';
  import {
    getUserDefaultPermissions,
    getAllUsers,
    updateUserDefaultPermissions,
  } from '$lib/apis/users';

  const i18n = getContext('i18n');

  let loaded = false;

  let groups = [];

  let query = '';
  let sortBy = 'members';

  const sortItems = [
    { value: 'name', label: $i18n.t('Name') },
    { value: 'members', label: $i18n.t('Members') },
  ];

  $: filteredGroups = groups
    .filter((group) => {
      if (query === '') {
        return true;
      } else {
        let name = group.name.toLowerCase();
        const q = query.toLowerCase();
        return name.includes(q);
      }
    })
    .sort((a, b) => {
      if (sortBy === 'name') {
        return a.name.localeCompare(b.name);
      } else if (sortBy === 'members') {
        return (b.member_count ?? 0) - (a.member_count ?? 0);
      }
      return 0;
    });

  let defaultPermissions = {};

  let showAddGroupModal = false;
  let showDefaultPermissionsModal = false;

  const setGroups = async () => {
    groups = await getGroups(localStorage.token);
  };

  const addGroupHandler = async (group) => {
    const res = await createNewGroup(localStorage.token, group).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    if (res) {
      toast.success($i18n.t('Group created successfully'));
      groups = await getGroups(localStorage.token);
    }
  };

  const updateDefaultPermissionsHandler = async (group) => {
    console.debug(group.permissions);

    const res = await updateUserDefaultPermissions(localStorage.token, group.permissions).catch(
      (error) => {
        toast.error(`${error}`);
        return null;
      },
    );

    if (res) {
      toast.success($i18n.t('Default permissions updated successfully'));
      defaultPermissions = await getUserDefaultPermissions(localStorage.token);
    }
  };

  onMount(async () => {
    if ($user?.role !== 'admin') {
      await goto('/');
      return;
    }

    defaultPermissions = await getUserDefaultPermissions(localStorage.token);
    await setGroups();
    loaded = true;
  });
</script>

{#if loaded}
  <EditGroupModal
    bind:show={showAddGroupModal}
    edit={false}
    tabs={['general', 'permissions']}
    permissions={defaultPermissions}
    onSubmit={addGroupHandler}
  />

  <div class="mt-1.5 mb-3 flex flex-col gap-1 px-1">
    <div class="flex items-center justify-between">
      <div class="flex shrink-0 items-center gap-2 px-0.5 text-xl font-medium md:self-center">
        <div>
          {$i18n.t('Groups')}
        </div>

        <div class="text-lg font-medium text-gray-500 dark:text-gray-500">
          {groups.length}
        </div>
      </div>

      <div class="flex w-full justify-end gap-1.5">
        <button
          class="flex items-center rounded-xl bg-black px-2 py-1.5 text-sm font-medium text-white transition dark:bg-white dark:text-black"
          on:click={() => {
            showAddGroupModal = !showAddGroupModal;
          }}
        >
          <Plus className="size-3" strokeWidth="2.5" />

          <div class="hidden text-xs md:ml-1 md:block">{$i18n.t('New Group')}</div>
        </button>
      </div>
    </div>
  </div>

  <div
    class="dark:border-gray-850/30 rounded-3xl border border-gray-100/30 bg-white py-2 dark:bg-gray-900"
  >
    <div class="flex w-full items-center space-x-2 px-3.5 py-0.5">
      <div class="flex flex-1">
        <div class="mr-3 ml-1 self-center">
          <Search className="size-3.5" />
        </div>
        <input
          class="w-full rounded-r-xl bg-transparent py-1 text-sm outline-hidden"
          bind:value={query}
          aria-label={$i18n.t('Search Groups')}
          placeholder={$i18n.t('Search Groups')}
        />
        {#if query}
          <div class="translate-y-[0.5px] self-center rounded-l-xl bg-transparent pl-1.5">
            <button
              class="hover:bg-card-hover rounded-full p-0.5 transition"
              aria-label={$i18n.t('Clear search')}
              on:click={() => {
                query = '';
              }}
            >
              <XMark className="size-3" strokeWidth="2" />
            </button>
          </div>
        {/if}
      </div>

      <Select
        bind:value={sortBy}
        items={sortItems}
        placeholder={$i18n.t('Sort by')}
        triggerClass="relative flex items-center gap-0.5 px-2.5 py-1.5 text-sm bg-gray-50 dark:bg-gray-850 rounded-xl shrink-0"
        align="end"
      >
        <svelte:fragment slot="trigger" let:selectedLabel>
          <span
            class="h-input inline-flex truncate bg-transparent px-0.5 placeholder-gray-400 outline-hidden focus:outline-hidden"
          >
            {selectedLabel}
          </span>
          <ChevronDown className="size-3.5" strokeWidth="2.5" />
        </svelte:fragment>

        <svelte:fragment slot="item" let:item let:selected>
          {item.label}
          {#if selected}
            <div class="ml-auto">
              <Check />
            </div>
          {/if}
        </svelte:fragment>
      </Select>
    </div>

    {#if filteredGroups.length !== 0}
      <div class="my-2 grid grid-cols-1 gap-1 px-3">
        {#each filteredGroups as group}
          <GroupItem {group} {setGroups} {defaultPermissions} />
        {/each}
      </div>
    {:else}
      <div class="my-16 mb-24 flex h-full w-full flex-col items-center justify-center">
        <div class="max-w-md text-center">
          <div class="mb-3 text-3xl">👥</div>
          <div class="mb-1 text-lg font-medium">{$i18n.t('No groups found')}</div>
          <div class="text-center text-xs text-gray-500">
            {$i18n.t('Use groups to organize your users and assign permissions.')}
          </div>
        </div>
      </div>
    {/if}
  </div>

  <EditGroupModal
    bind:show={showDefaultPermissionsModal}
    tabs={['permissions']}
    bind:permissions={defaultPermissions}
    custom={false}
    onSubmit={updateDefaultPermissionsHandler}
  />

  <button
    class="mt-4 flex w-full items-center justify-between rounded-lg transition"
    aria-haspopup="dialog"
    on:click={() => {
      showDefaultPermissionsModal = true;
    }}
  >
    <div class="flex items-center gap-2.5">
      <div class="rounded-full bg-black/5 p-1.5 dark:bg-white/10">
        <UsersSolid className="size-4" />
      </div>

      <div class="text-left">
        <div class=" text-sm font-medium">{$i18n.t('Default permissions')}</div>

        <div class="mt-0.5 flex text-xs">
          {$i18n.t('applies to all users with the "user" role')}
        </div>
      </div>
    </div>

    <div>
      <ChevronRight strokeWidth="2.5" />
    </div>
  </button>
{/if}
