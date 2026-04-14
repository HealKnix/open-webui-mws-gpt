<script lang="ts">
  import Checkbox from '$lib/components/common/Checkbox.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import { getContext, onMount } from 'svelte';

  import { getSkillItems } from '$lib/apis/skills';

  export let selectedSkillIds: string[] = [];

  let _skills: Record<string, any> = {};

  const i18n = getContext('i18n');

  onMount(async () => {
    const res = await getSkillItems(localStorage.token).catch(() => null);
    const skills = res?.items ?? [];
    _skills = skills.reduce((acc: Record<string, any>, skill: any) => {
      acc[skill.id] = {
        ...skill,
        selected: selectedSkillIds.includes(skill.id),
      };

      return acc;
    }, {});
  });
</script>

<div>
  <div class="mb-1 flex w-full justify-between">
    <div class="mb-1 text-xs font-medium">{$i18n.t('Skills')}</div>
  </div>

  <div class="mb-1 flex flex-col">
    {#if Object.keys(_skills).length > 0}
      <div class="flex flex-wrap items-center gap-2">
        {#each Object.keys(_skills) as skill, skillIdx}
          <Checkbox
            state={_skills[skill].selected ? 'checked' : 'unchecked'}
            on:change={(e) => {
              _skills[skill].selected = e.detail === 'checked';
              selectedSkillIds = Object.keys(_skills).filter((s) => _skills[s].selected);
            }}
            tooltip={{
              label: _skills[skill].name,
              description: _skills[skill].description,
            }}
          />
        {/each}
      </div>
    {/if}
  </div>

  <div class=" text-xs dark:text-gray-700">
    {$i18n.t('To select skills here, add them to the "Skills" workspace first.')}
  </div>
</div>
