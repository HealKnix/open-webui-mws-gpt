<script>
  import { goto } from '$app/navigation';
  import { WEBUI_NAME, config } from '$lib/stores';
  import { onMount, getContext } from 'svelte';

  const i18n = getContext('i18n');

  let loaded = false;

  onMount(async () => {
    if ($config) {
      await goto('/');
    }

    loaded = true;
  });
</script>

{#if loaded}
  <div class="absolute z-50 flex h-full w-full">
    <div class="absolute flex h-full w-full justify-center rounded-xl backdrop-blur-sm">
      <div class="m-auto flex flex-col justify-center pb-44">
        <div class="max-w-md">
          <div class="z-50 text-center text-2xl font-medium">
            {$i18n.t('{{webUIName}} Backend Required', { webUIName: $WEBUI_NAME })}
          </div>

          <div class=" mt-4 w-full text-center text-sm">
            {$i18n.t(
              "Oops! You're using an unsupported method (frontend only). Please serve the WebUI from the backend.",
            )}

            <br class=" " />
            <br class=" " />
            <a
              class=" font-medium underline"
              href="https://github.com/open-webui/open-webui#how-to-install-"
              target="_blank">{$i18n.t('See readme.md for instructions')}</a
            >
            {$i18n.t('or')}
            <a class=" font-medium underline" href="https://discord.gg/5rJgQTnV4s" target="_blank"
              >{$i18n.t('join our Discord for help.')}</a
            >
          </div>

          <div class=" group relative mx-auto mt-6 w-fit">
            <button
              class="relative z-20 flex rounded-full bg-gray-100 px-5 py-2 text-sm font-medium text-black transition hover:bg-gray-200"
              on:click={() => {
                location.href = '/';
              }}
            >
              {$i18n.t('Check Again')}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}
