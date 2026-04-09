<script lang="ts">
  import { getContext, onMount } from 'svelte';
  import Checkbox from '$lib/components/common/Checkbox.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';

  const i18n = getContext('i18n');

  export let actions = [];
  export let selectedActionIds = [];

  let _actions = {};

  onMount(() => {
    _actions = actions.reduce((acc, action) => {
      acc[action.id] = {
        ...action,
        selected: selectedActionIds.includes(action.id),
      };

      return acc;
    }, {});
  });
</script>

{#if actions.length > 0}
  <div>
    <div class="mb-1 flex w-full justify-between">
      <div class=" self-center text-xs font-medium text-gray-500">{$i18n.t('Actions')}</div>
    </div>

    <div class="flex flex-col">
      <div class=" flex flex-wrap items-center">
        {#each Object.keys(_actions) as action, actionIdx}
          <div class=" mr-3 flex items-center gap-2">
            <div class="flex items-center self-center">
              <Checkbox
                state={_actions[action].is_global
                  ? 'checked'
                  : _actions[action].selected
                    ? 'checked'
                    : 'unchecked'}
                disabled={_actions[action].is_global}
                on:change={(e) => {
                  if (!_actions[action].is_global) {
                    _actions[action].selected = e.detail === 'checked';
                    selectedActionIds = Object.keys(_actions).filter((t) => _actions[t].selected);
                  }
                }}
              />
            </div>

            <div class=" w-full py-0.5 text-sm font-medium capitalize">
              <Tooltip content={_actions[action].meta.description}>
                {_actions[action].name}
              </Tooltip>
            </div>
          </div>
        {/each}
      </div>
    </div>
  </div>
{/if}
