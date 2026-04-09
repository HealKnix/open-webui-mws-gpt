<script lang="ts">
  import CodeExecutionModal from './CodeExecutionModal.svelte';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import Check from '$lib/components/icons/Check.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';
  import EllipsisHorizontal from '$lib/components/icons/EllipsisHorizontal.svelte';

  export let codeExecutions = [];

  let selectedCodeExecution = null;
  let showCodeExecutionModal = false;

  $: if (codeExecutions) {
    updateSelectedCodeExecution();
  }

  const updateSelectedCodeExecution = () => {
    if (selectedCodeExecution) {
      selectedCodeExecution = codeExecutions.find(
        (execution) => execution.id === selectedCodeExecution.id,
      );
    }
  };
</script>

<CodeExecutionModal bind:show={showCodeExecutionModal} codeExecution={selectedCodeExecution} />

{#if codeExecutions.length > 0}
  <div class="mt-1 mb-2 flex w-full flex-wrap items-center gap-1">
    {#each codeExecutions as execution (execution.id)}
      <div class="flex gap-1 text-xs font-semibold">
        <button
          class="dark:bg-gray-850 flex max-w-96 rounded-xl bg-gray-50 px-1 py-1 transition hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
          on:click={() => {
            selectedCodeExecution = execution;
            showCodeExecutionModal = true;
          }}
        >
          <div
            class="flex size-4 items-center justify-center rounded-full bg-white dark:bg-gray-700"
          >
            {#if execution?.result}
              {#if execution.result?.error}
                <XMark />
              {:else if execution.result?.output}
                <Check strokeWidth="3" className="size-3" />
              {:else}
                <EllipsisHorizontal />
              {/if}
            {:else}
              <Spinner className="size-4" />
            {/if}
          </div>
          <div
            class="code-execution-name mx-2 line-clamp-1 flex-1 {execution?.result ? '' : 'pulse'}"
          >
            {execution.name}
          </div>
        </button>
      </div>
    {/each}
  </div>
{/if}

<style>
  @keyframes pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.6;
    }
  }

  .pulse {
    opacity: 1;
    animation: pulse 1.5s ease;
  }
</style>
