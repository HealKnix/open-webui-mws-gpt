<script lang="ts">
  import AddFilesPlaceholder from '$lib/components/AddFilesPlaceholder.svelte';

  export let show = false;
</script>

{#if show}
  <div
    class="pointer-events-none absolute inset-0 z-[9999] flex h-full w-full touch-none"
    id="dropzone"
    role="region"
    aria-label="Drag and Drop Container"
  >
    <div
      class="absolute flex h-full w-full justify-center bg-gray-100/50 backdrop-blur-sm dark:bg-gray-900/80"
    >
      <div class="m-auto flex flex-col justify-center">
        <div class="max-w-md">
          <AddFilesPlaceholder />
        </div>
      </div>
    </div>
  </div>
{/if}
