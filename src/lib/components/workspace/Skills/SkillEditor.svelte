<script lang="ts">
  import { onMount, tick, getContext } from 'svelte';

  import Textarea from '$lib/components/common/Textarea.svelte';
  import { toast } from 'svelte-sonner';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import LockClosed from '$lib/components/icons/LockClosed.svelte';
  import ChevronLeft from '$lib/components/icons/ChevronLeft.svelte';
  import AccessControlModal from '../common/AccessControlModal.svelte';
  import { user } from '$lib/stores';
  import { slugify, parseFrontmatter, formatSkillName } from '$lib/utils';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import { updateSkillAccessGrants } from '$lib/apis/skills';
  import { goto } from '$app/navigation';

  export let onSubmit: Function;
  export let edit = false;
  export let skill = null;
  export let clone = false;
  export let disabled = false;

  const i18n = getContext('i18n');

  let loading = false;

  let name = '';
  let id = '';
  let description = '';
  let content = '';

  let accessGrants = [];
  let showAccessControlModal = false;
  let hasManualEdit = false;
  let hasManualName = false;
  let hasManualDescription = false;
  let isFrontmatterDetected = false;

  // Auto-detect frontmatter and fill name/description in create mode
  $: if (!edit && content) {
    const fm = parseFrontmatter(content);
    if (fm.name) {
      isFrontmatterDetected = true;
      if (!hasManualName) {
        name = formatSkillName(fm.name);
      }
      if (!hasManualEdit) {
        id = fm.name;
      }
    } else {
      isFrontmatterDetected = false;
    }
    if (fm.description && !hasManualDescription) {
      description = fm.description;
    }
  } else if (!edit && !content) {
    isFrontmatterDetected = false;
  }

  $: if (!edit && !hasManualEdit && !isFrontmatterDetected) {
    id = name !== '' ? slugify(name) : '';
  }

  function handleIdInput(e: Event) {
    hasManualEdit = true;
  }

  function handleNameInput(e: Event) {
    hasManualName = true;
  }

  function handleDescriptionInput(e: Event) {
    hasManualDescription = true;
  }

  const submitHandler = async () => {
    if (disabled) {
      toast.error($i18n.t('You do not have permission to edit this skill.'));
      return;
    }
    loading = true;

    await onSubmit({
      id,
      name,
      description,
      content,
      is_active: true,
      meta: { tags: [] },
      access_grants: accessGrants,
    });

    loading = false;
  };

  onMount(async () => {
    if (skill) {
      name = skill.name || '';
      await tick();
      id = skill.id || '';
      description = skill.description || '';
      content = skill.content || '';
      accessGrants = skill?.access_grants === undefined ? [] : skill?.access_grants;

      if (name) hasManualName = true;
      if (description) hasManualDescription = true;
      if (id) hasManualEdit = true;
    }
  });
</script>

<AccessControlModal
  bind:show={showAccessControlModal}
  bind:accessGrants
  accessRoles={['read', 'write']}
  share={$user?.permissions?.sharing?.skills || $user?.role === 'admin'}
  sharePublic={$user?.permissions?.sharing?.public_skills || $user?.role === 'admin'}
  shareUsers={($user?.permissions?.access_grants?.allow_users ?? true) || $user?.role === 'admin'}
  onChange={async () => {
    if (edit && skill?.id) {
      try {
        await updateSkillAccessGrants(localStorage.token, skill.id, accessGrants);
        toast.success($i18n.t('Saved'));
      } catch (error) {
        toast.error(`${error}`);
      }
    }
  }}
/>

<div class=" flex h-full w-full flex-col justify-between overflow-y-auto">
  <div class="mx-auto h-full w-full md:px-0">
    <form class=" flex h-full max-h-[100dvh] flex-col" on:submit|preventDefault={submitHandler}>
      <div class="flex h-0 flex-1 flex-col overflow-auto rounded-lg">
        <div class="mb-2 flex w-full flex-col gap-0.5">
          <div class="flex w-full items-center">
            <div class=" mr-2 shrink-0">
              <Tooltip content={$i18n.t('Back')}>
                <button
                  class="dark:hover:bg-gray-850 w-full rounded-lg px-1 py-1.5 text-left text-sm hover:bg-black/5 dark:text-gray-300 dark:hover:text-white"
                  aria-label={$i18n.t('Back')}
                  on:click={() => {
                    goto('/workspace/skills');
                  }}
                  type="button"
                >
                  <ChevronLeft strokeWidth="2.5" />
                </button>
              </Tooltip>
            </div>

            <div class="flex-1">
              <Tooltip content={$i18n.t('e.g. Code Review Guidelines')} placement="top-start">
                <input
                  class="w-full bg-transparent text-2xl outline-hidden"
                  type="text"
                  placeholder={$i18n.t('Skill Name')}
                  aria-label={$i18n.t('Skill Name')}
                  bind:value={name}
                  on:input={handleNameInput}
                  required
                  {disabled}
                />
              </Tooltip>
            </div>

            <div class="shrink-0 self-center">
              {#if !disabled}
                <button
                  class="dark:bg-gray-850 flex items-center gap-1 rounded-full bg-gray-50 px-2 py-1 text-black transition hover:bg-gray-100 dark:text-white dark:hover:bg-gray-800"
                  type="button"
                  on:click={() => (showAccessControlModal = true)}
                >
                  <LockClosed strokeWidth="2.5" className="size-3.5" />

                  <div class="shrink-0 text-sm font-medium">
                    {$i18n.t('Access')}
                  </div>
                </button>
              {:else}
                <span
                  class="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-500 dark:bg-gray-800"
                  >{$i18n.t('Read Only')}</span
                >
              {/if}
            </div>
          </div>

          <div class=" flex items-center gap-2 px-1">
            {#if edit}
              <div class="shrink-0 text-sm text-gray-500">
                {id}
              </div>
            {:else}
              <Tooltip
                className="w-full"
                content={$i18n.t('e.g. code-review-guidelines')}
                placement="top-start"
              >
                <input
                  class="w-full bg-transparent text-sm outline-hidden disabled:text-gray-500"
                  type="text"
                  placeholder={$i18n.t('Skill ID')}
                  aria-label={$i18n.t('Skill ID')}
                  bind:value={id}
                  on:input={handleIdInput}
                  required
                  disabled={edit}
                />
              </Tooltip>
            {/if}

            <Tooltip
              className="w-full self-center items-center flex"
              content={$i18n.t('e.g. Step-by-step instructions for code reviews')}
              placement="top-start"
            >
              <input
                class="w-full bg-transparent text-sm outline-hidden"
                type="text"
                placeholder={$i18n.t('Skill Description')}
                aria-label={$i18n.t('Skill Description')}
                bind:value={description}
                on:input={handleDescriptionInput}
                {disabled}
              />
            </Tooltip>
          </div>
        </div>

        <div class="mb-2 h-0 flex-1 overflow-auto rounded-lg">
          <div class="flex h-full flex-col">
            <div
              class="dark:border-gray-850/50 flex min-h-0 flex-1 flex-col overflow-hidden rounded-xl border border-gray-100/50 bg-gray-50 dark:bg-gray-900"
            >
              {#if disabled}
                <div class="flex-1 overflow-y-auto px-4 py-3">
                  <pre class="font-mono text-xs whitespace-pre-wrap">{content}</pre>
                </div>
              {:else}
                <textarea
                  class="w-full flex-1 resize-none bg-transparent px-4 py-3 font-mono text-xs outline-hidden"
                  bind:value={content}
                  placeholder={$i18n.t('Enter skill instructions in markdown...')}
                  aria-label={$i18n.t('Skill Instructions')}
                  required
                />
              {/if}
            </div>
          </div>
        </div>

        <div class="flex justify-end pb-3">
          {#if !disabled}
            <button
              class="flex items-center gap-2 rounded-full bg-black px-3.5 py-1.5 text-sm font-medium whitespace-nowrap text-white transition hover:bg-gray-900 dark:bg-white dark:text-black dark:hover:bg-gray-100"
              type="submit"
              disabled={loading}
            >
              {$i18n.t(edit ? 'Save' : 'Save & Create')}
              {#if loading}
                <span class="shrink-0">
                  <Spinner />
                </span>
              {/if}
            </button>
          {/if}
        </div>
      </div>
    </form>
  </div>
</div>
