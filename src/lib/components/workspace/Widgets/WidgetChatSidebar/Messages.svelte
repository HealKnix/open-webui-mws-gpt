<script lang="ts">
  import { getContext } from 'svelte';
  import Message from './Message.svelte';

  const i18n = getContext('i18n');

  export let messages = [];
</script>

<div class="space-y-6 px-1 pb-12">
  {#each messages as message, idx}
    <Message
      {message}
      {idx}
      onDelete={() => {
        messages = messages.filter((_, messageIdx) => messageIdx !== idx);
      }}
    />
  {/each}
</div>
