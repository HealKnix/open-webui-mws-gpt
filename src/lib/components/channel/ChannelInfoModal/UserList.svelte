<script lang="ts">
  import { WEBUI_API_BASE_URL, WEBUI_BASE_URL } from '$lib/constants';
  import { WEBUI_NAME, config, user as _user, showSidebar } from '$lib/stores';
  import { goto } from '$app/navigation';
  import { onMount, getContext } from 'svelte';

  import dayjs from 'dayjs';
  import relativeTime from 'dayjs/plugin/relativeTime';
  import localizedFormat from 'dayjs/plugin/localizedFormat';
  dayjs.extend(relativeTime);
  dayjs.extend(localizedFormat);

  import { toast } from 'svelte-sonner';
  import { getChannelMembersById } from '$lib/apis/channels';

  import Pagination from '$lib/components/common/Pagination.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';

  import Badge from '$lib/components/common/Badge.svelte';
  import Plus from '$lib/components/icons/Plus.svelte';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import ProfilePreview from '../Messages/Message/ProfilePreview.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';

  const i18n = getContext('i18n');

  export let channel = null;

  export let onAdd = null;
  export let onRemove = null;

  export let search = true;
  export let sort = true;

  let page = 1;

  let users = null;
  let total = null;

  let query = '';
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;

  let orderBy = 'name'; // default sort key
  let direction = 'asc'; // default sort order

  const setSortKey = (key) => {
    if (!sort) {
      return;
    }

    if (orderBy === key) {
      direction = direction === 'asc' ? 'desc' : 'asc';
    } else {
      orderBy = key;
      direction = 'asc';
    }
  };

  const getUserList = async () => {
    try {
      const res = await getChannelMembersById(
        localStorage.token,
        channel.id,
        query,
        orderBy,
        direction,
        page,
      ).catch((error) => {
        toast.error(`${error}`);
        return null;
      });

      if (res) {
        users = res.users;
        total = res.total;
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Debounce only query changes
  $: if (query !== undefined && channel !== null) {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      getUserList();
    }, 300);
  }

  // Immediate response to page/sort changes
  $: if (channel !== null && page && orderBy && direction) {
    getUserList();
  }
</script>

<div class="flex flex-col justify-center">
  {#if users === null || total === null}
    <div class="my-10">
      <Spinner className="size-5" />
    </div>
  {:else}
    <div class="mb-1 flex items-center justify-between px-2">
      <div class="flex items-center gap-1">
        <span class="text-sm">
          {$i18n.t('Members')}
        </span>
        <span class="text-sm text-gray-500">{total}</span>
      </div>

      {#if onAdd}
        <div class="">
          <button
            type="button"
            class=" dark:bg-gray-850/50 flex items-center justify-center gap-1 rounded-xl bg-gray-100/50 px-3 py-1.5 text-xs font-medium text-black transition dark:text-white"
            on:click={onAdd}
          >
            <Plus className="size-3.5 " />
            <span>{$i18n.t('Add Member')}</span>
          </button>
        </div>
      {/if}
    </div>
    <!-- <hr class="my-1 border-gray-100/5- dark:border-gray-850/50" /> -->

    {#if search}
      <div class="mb-1 flex gap-1 px-1">
        <div class=" flex w-full space-x-2">
          <div class="flex flex-1 items-center">
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
    {/if}

    {#if users.length > 0}
      <div class="scrollbar-hidden relative w-full max-w-full whitespace-nowrap">
        <div class=" w-full max-w-full text-left text-sm text-gray-500 dark:text-gray-400">
          <!-- <div
						class="text-xs text-gray-800 uppercase bg-transparent dark:text-gray-200 w-full mb-0.5"
					>
						<div
							class=" border-b-[1.5px] border-gray-50/50 dark:border-gray-800/10 flex items-center justify-between"
						>
							<button
								type="button"
								class="px-2.5 py-2 cursor-pointer select-none"
								on:click={() => setSortKey('name')}
							>
								<div class="flex gap-1.5 items-center">
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
							</button>

							<button
								type="button"
								class="px-2.5 py-2 cursor-pointer select-none"
								on:click={() => setSortKey('role')}
							>
								<div class="flex gap-1.5 items-center">
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
							</button>
						</div>
					</div> -->
          <div class="w-full">
            {#each users as user, userIdx (user.id)}
              <div class=" dark:border-gray-850 flex items-center justify-between text-xs">
                <div class="flex-1 px-2 py-1.5 font-medium text-gray-900 dark:text-white">
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
                          <span class="relative inline-flex size-1.5 rounded-full bg-green-500"
                          ></span>
                        </span>
                      </div>
                    {/if}
                  </div>
                </div>

                <div class="flex translate-y-0.5 items-center gap-1 px-2 py-1">
                  <div class=" ">
                    <Badge
                      type={user.role === 'admin'
                        ? 'info'
                        : user.role === 'user'
                          ? 'success'
                          : 'muted'}
                      content={$i18n.t(user.role)}
                    />
                  </div>

                  {#if onRemove}
                    <div>
                      <button
                        class=" dark:hover:bg-gray-850 rounded-full p-1 transition hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
                        type="button"
                        disabled={user.id === $_user?.id}
                        on:click={() => {
                          onRemove(user.id);
                        }}
                      >
                        <XMark />
                      </button>
                    </div>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        </div>
      </div>

      {#if total > 30}
        <Pagination bind:page count={total} perPage={30} />
      {/if}
    {:else}
      <div class="px-10 py-5 text-center text-xs text-gray-500">
        {$i18n.t('No users were found.')}
      </div>
    {/if}
  {/if}
</div>
