<script lang="ts">
  import { toast } from 'svelte-sonner';
  import dayjs from 'dayjs';
  import { createEventDispatcher } from 'svelte';
  import { onMount, getContext } from 'svelte';

  import { goto } from '$app/navigation';

  import { updateUserById, getUserGroupsById } from '$lib/apis/users';

  import Modal from '$lib/components/common/Modal.svelte';
  import localizedFormat from 'dayjs/plugin/localizedFormat';
  import XMark from '$lib/components/icons/XMark.svelte';
  import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
  import UserProfileImage from '$lib/components/chat/Settings/Account/UserProfileImage.svelte';

  const i18n = getContext('i18n');
  const dispatch = createEventDispatcher();
  dayjs.extend(localizedFormat);

  export let show = false;
  export let selectedUser;
  export let sessionUser;

  $: if (show) {
    init();
  }

  const init = () => {
    if (selectedUser) {
      _user = selectedUser;
      _user.password = '';
      loadUserGroups();
    }
  };

  let _user = {
    profile_image_url: '',
    role: 'pending',
    name: '',
    email: '',
    password: '',
  };

  let userGroups: any[] | null = null;

  const submitHandler = async () => {
    const res = await updateUserById(localStorage.token, selectedUser.id, _user).catch((error) => {
      toast.error(`${error}`);
    });

    if (res) {
      dispatch('save');
      show = false;
    }
  };

  const loadUserGroups = async () => {
    if (!selectedUser?.id) return;
    userGroups = null;

    userGroups = await getUserGroupsById(localStorage.token, selectedUser.id).catch((error) => {
      toast.error(`${error}`);
      return null;
    });
  };
</script>

<Modal size="sm" bind:show>
  <div>
    <div class=" flex justify-between px-5 pt-4 pb-2 dark:text-gray-300">
      <div class=" self-center text-lg font-medium">{$i18n.t('Edit User')}</div>
      <button
        class="self-center"
        aria-label={$i18n.t('Close')}
        on:click={() => {
          show = false;
        }}
      >
        <XMark className={'size-5'} />
      </button>
    </div>

    <div class="flex w-full flex-col md:flex-row md:space-x-4 dark:text-gray-200">
      <div class=" flex w-full flex-col sm:flex-row sm:justify-center sm:space-x-6">
        <form
          class="flex w-full flex-col"
          on:submit|preventDefault={() => {
            submitHandler();
          }}
        >
          <div class=" w-full px-5 pt-3 pb-5">
            <div class="flex w-full self-center">
              <div class=" mr-6 h-full self-start">
                <UserProfileImage
                  imageClassName="size-14"
                  bind:profileImageUrl={_user.profile_image_url}
                  user={_user}
                />
              </div>

              <div class=" flex-1">
                <div class="w-ful mb-2 overflow-hidden">
                  <div class=" self-center truncate font-medium capitalize">
                    {selectedUser.name}
                  </div>

                  <div class="text-xs text-gray-500">
                    {$i18n.t('Created at')}
                    {dayjs(selectedUser.created_at * 1000).format('LL')}
                  </div>
                </div>

                <div class=" flex flex-col space-y-1.5">
                  {#if (userGroups ?? []).length > 0}
                    <div class="flex w-full flex-col text-sm">
                      <div class="mb-1 text-xs text-gray-500">{$i18n.t('User Groups')}</div>

                      <div class="-mx-1 my-0.5 flex flex-wrap gap-1">
                        {#each userGroups as userGroup}
                          <span
                            class="dark:bg-gray-850 rounded-xl bg-gray-100 px-1.5 py-0.5 text-xs"
                          >
                            <a
                              href={'/admin/users/groups?id=' + userGroup.id}
                              on:click|preventDefault={() =>
                                goto('/admin/users/groups?id=' + userGroup.id)}
                            >
                              {userGroup.name}
                            </a>
                          </span>
                        {/each}
                      </div>
                    </div>
                  {/if}

                  <div class="flex w-full flex-col">
                    <div class=" mb-1 text-xs text-gray-500">{$i18n.t('Role')}</div>

                    <div class="flex-1">
                      <select
                        class="w-full bg-transparent text-sm outline-hidden disabled:text-gray-500 dark:disabled:text-gray-500"
                        bind:value={_user.role}
                        aria-label={$i18n.t('Role')}
                        disabled={_user.id == sessionUser.id}
                        required
                      >
                        <option value="admin">{$i18n.t('Admin')}</option>
                        <option value="user">{$i18n.t('User')}</option>
                        <option value="pending">{$i18n.t('Pending')}</option>
                      </select>
                    </div>
                  </div>

                  <div class="flex w-full flex-col">
                    <div class=" mb-1 text-xs text-gray-500">{$i18n.t('Name')}</div>

                    <div class="flex-1">
                      <input
                        class="w-full bg-transparent text-sm outline-hidden"
                        type="text"
                        bind:value={_user.name}
                        aria-label={$i18n.t('Name')}
                        placeholder={$i18n.t('Enter Your Name')}
                        autocomplete="off"
                        required
                      />
                    </div>
                  </div>

                  <div class="flex w-full flex-col">
                    <div class=" mb-1 text-xs text-gray-500">{$i18n.t('Email')}</div>

                    <div class="flex-1">
                      <input
                        class="w-full bg-transparent text-sm outline-hidden disabled:text-gray-500 dark:disabled:text-gray-500"
                        type="email"
                        bind:value={_user.email}
                        aria-label={$i18n.t('Email')}
                        placeholder={$i18n.t('Enter Your Email')}
                        autocomplete="off"
                        required
                      />
                    </div>
                  </div>

                  {#if _user?.oauth}
                    <div class="flex w-full flex-col">
                      <div class=" mb-1 text-xs text-gray-500">{$i18n.t('OAuth ID')}</div>

                      <div class="mb-1 flex flex-1 flex-col space-y-1 text-sm break-all">
                        {#each Object.keys(_user.oauth) as key}
                          <div>
                            <span class="text-gray-500">{key}</span>
                            <span class="">{_user.oauth[key]?.sub}</span>
                          </div>
                        {/each}
                      </div>
                    </div>
                  {/if}

                  <div class="flex w-full flex-col">
                    <div class=" mb-1 text-xs text-gray-500">{$i18n.t('New Password')}</div>

                    <div class="flex-1">
                      <SensitiveInput
                        class="w-full bg-transparent text-sm outline-hidden"
                        type="password"
                        aria-label={$i18n.t('New Password')}
                        placeholder={$i18n.t('Enter New Password')}
                        bind:value={_user.password}
                        autocomplete="new-password"
                        required={false}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="flex justify-end pt-3 text-sm font-medium">
              <button
                class="flex flex-row items-center space-x-1 rounded-full bg-black px-3.5 py-1.5 text-sm font-medium text-white transition hover:bg-gray-900 dark:bg-white dark:text-black dark:hover:bg-gray-100"
                type="submit"
              >
                {$i18n.t('Save')}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>
</Modal>

<style>
  input::-webkit-outer-spin-button,
  input::-webkit-inner-spin-button {
    /* display: none; <- Crashes Chrome on hover */
    -webkit-appearance: none;
    margin: 0; /* <-- Apparently some margin are still there even though it's hidden */
  }

  .tabs::-webkit-scrollbar {
    display: none; /* for Chrome, Safari and Opera */
  }

  .tabs {
    -ms-overflow-style: none; /* IE and Edge */
    scrollbar-width: none; /* Firefox */
  }

  input[type='number'] {
    -moz-appearance: textfield; /* Firefox */
  }
</style>
