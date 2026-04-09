<script>
  import { toast } from 'svelte-sonner';

  import { goto } from '$app/navigation';
  import { getContext } from 'svelte';
  const i18n = getContext('i18n');

  import { user } from '$lib/stores';
  import { createNewKnowledge } from '$lib/apis/knowledge';

  import AccessControl from '../common/AccessControl.svelte';
  import Spinner from '$lib/components/common/Spinner.svelte';

  let loading = false;

  let name = '';
  let description = '';
  let accessGrants = [];

  const submitHandler = async () => {
    loading = true;

    if (name.trim() === '' || description.trim() === '') {
      toast.error($i18n.t('Please fill in all fields.'));
      name = '';
      description = '';
      loading = false;
      return;
    }

    const res = await createNewKnowledge(localStorage.token, name, description, accessGrants).catch(
      (e) => {
        toast.error(`${e}`);
      },
    );

    if (res) {
      toast.success($i18n.t('Knowledge created successfully.'));
      goto(`/workspace/knowledge/${res.id}`);
    }

    loading = false;
  };
</script>

<div class="max-h-full w-full">
  <button
    class="flex space-x-1"
    on:click={() => {
      goto('/workspace/knowledge');
    }}
  >
    <div class=" self-center">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 20 20"
        fill="currentColor"
        class="h-4 w-4"
      >
        <path
          fill-rule="evenodd"
          d="M17 10a.75.75 0 01-.75.75H5.612l4.158 3.96a.75.75 0 11-1.04 1.08l-5.5-5.25a.75.75 0 010-1.08l5.5-5.25a.75.75 0 111.04 1.08L5.612 9.25H16.25A.75.75 0 0117 10z"
          clip-rule="evenodd"
        />
      </svg>
    </div>
    <div class=" self-center text-sm font-medium">{$i18n.t('Back')}</div>
  </button>

  <form
    class="mx-auto mt-10 mb-10 flex max-w-lg flex-col"
    on:submit|preventDefault={() => {
      submitHandler();
    }}
  >
    <div class=" flex w-full flex-col justify-center">
      <div class=" font-primary mb-2.5 text-2xl font-medium">
        {$i18n.t('Create a knowledge base')}
      </div>

      <div class="flex w-full flex-col gap-2.5">
        <div class="w-full">
          <div class=" mb-2 text-sm">{$i18n.t('What are you working on?')}</div>

          <div class="mt-1 w-full">
            <input
              class="dark:bg-gray-850 w-full rounded-lg bg-gray-50 px-4 py-2 text-sm outline-hidden dark:text-gray-300"
              type="text"
              bind:value={name}
              placeholder={$i18n.t('Name your knowledge base')}
              required
            />
          </div>
        </div>

        <div>
          <div class="mb-2 text-sm">{$i18n.t('What are you trying to achieve?')}</div>

          <div class=" mt-1 w-full">
            <textarea
              class="dark:bg-gray-850 w-full resize-none rounded-lg bg-gray-50 px-4 py-2 text-sm outline-hidden dark:text-gray-300"
              rows="4"
              bind:value={description}
              placeholder={$i18n.t('Describe your knowledge base and objectives')}
              required
            />
          </div>
        </div>
      </div>
    </div>

    <div class="mt-2">
      <AccessControl
        bind:accessGrants
        accessRoles={['read', 'write']}
        share={$user?.permissions?.sharing?.knowledge || $user?.role === 'admin'}
        sharePublic={$user?.permissions?.sharing?.public_knowledge || $user?.role === 'admin'}
        shareUsers={($user?.permissions?.access_grants?.allow_users ?? true) ||
          $user?.role === 'admin'}
      />
    </div>

    <div class="mt-2 flex justify-end">
      <div>
        <button
          class=" rounded-lg px-4 py-2 text-sm transition {loading
            ? ' cursor-not-allowed bg-gray-100 dark:bg-gray-800'
            : ' dark:bg-gray-850 bg-gray-50 hover:bg-gray-100 dark:hover:bg-gray-800'} flex"
          type="submit"
          disabled={loading}
        >
          <div class=" self-center font-medium">{$i18n.t('Create Knowledge')}</div>

          {#if loading}
            <div class="ml-1.5 self-center">
              <Spinner />
            </div>
          {/if}
        </button>
      </div>
    </div>
  </form>
</div>
