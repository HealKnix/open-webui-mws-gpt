<script lang="ts">
  import Input from './Input.svelte';
  import TagList from './Tags/TagList.svelte';
  import { getContext, createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  const i18n = getContext('i18n');

  export let tags = [];
  export let suggestionTags = [];
  export let disabled = false;

  let inputValue = '';

  const addTag = () => {
    const value = inputValue.trim();
    if (value !== '') {
      dispatch('add', value);
      inputValue = '';
    }
  };
</script>

<div class="flex w-full flex-wrap items-center gap-1">
  <TagList
    {tags}
    {disabled}
    on:delete={(e) => {
      dispatch('delete', e.detail);
    }}
  />

  {#if !disabled}
    <Input
      size="xs"
      variant="flat"
      color="secondary"
      bind:value={inputValue}
      placeholder={$i18n.t('Add a tag...')}
      on:keydown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          addTag();
        }
      }}
    />
  {/if}
</div>
