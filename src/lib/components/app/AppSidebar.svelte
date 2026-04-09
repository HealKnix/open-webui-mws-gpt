<script lang="ts">
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Plus from '$lib/components/icons/Plus.svelte';
  import { WEBUI_BASE_URL } from '$lib/constants';

  let selected = '';
</script>

<nav
  aria-label="App navigation"
  class="flex min-w-[4.5rem] flex-col gap-2.5 bg-gray-50 pt-8 dark:bg-gray-950"
>
  <div class="relative flex justify-center">
    {#if selected === 'home'}
      <div class="absolute top-0 left-0 flex h-full">
        <div class="my-auto h-8 w-1 rounded-r-lg bg-black dark:bg-white"></div>
      </div>
    {/if}

    <Tooltip content="Home" placement="right">
      <button
        aria-label="Home"
        class=" cursor-pointer {selected === 'home' ? 'rounded-2xl' : 'rounded-full'}"
        on:click={() => {
          selected = 'home';

          if (window.electronAPI) {
            window.electronAPI.load('home');
          }
        }}
      >
        <img
          src="{WEBUI_BASE_URL}/static/splash.png"
          class="size-11 p-0.5 dark:invert"
          alt="logo"
          draggable="false"
        />
      </button>
    </Tooltip>
  </div>

  <div class=" mx-4 -mt-1 border-[1.5px] border-gray-100 dark:border-gray-900"></div>

  <div class="group relative flex justify-center">
    {#if selected === ''}
      <div class="absolute top-0 left-0 flex h-full">
        <div class="my-auto h-8 w-1 rounded-r-lg bg-black dark:bg-white"></div>
      </div>
    {/if}
    <button
      aria-label="Chat"
      class=" cursor-pointer bg-transparent"
      on:click={() => {
        selected = '';
      }}
    >
      <img
        src="./favicon.png"
        class="size-10 {selected === '' ? 'rounded-2xl' : 'rounded-full'}"
        alt="logo"
        draggable="false"
      />
    </button>
  </div>

  <!-- <div class="flex justify-center relative group text-gray-400">
		<button class=" cursor-pointer p-2" on:click={() => {}}>
			<Plus className="size-4" strokeWidth="2" />
		</button>
	</div> -->
</nav>
