<script>
  import { getContext, tick, onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';

  import Leaderboard from './Evaluations/Leaderboard.svelte';
  import Feedbacks from './Evaluations/Feedbacks.svelte';

  const i18n = getContext('i18n');

  let selectedTab;
  $: {
    const pathParts = $page.url.pathname.split('/');
    const tabFromPath = pathParts[pathParts.length - 1];
    selectedTab = ['leaderboard', 'feedback'].includes(tabFromPath) ? tabFromPath : 'leaderboard';
  }

  $: if (selectedTab) {
    // scroll to selectedTab
    scrollToTab(selectedTab);
  }

  const scrollToTab = (tabId) => {
    const tabElement = document.getElementById(tabId);
    if (tabElement) {
      tabElement.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' });
    }
  };

  let loaded = false;

  onMount(async () => {
    loaded = true;

    const containerElement = document.getElementById('users-tabs-container');

    if (containerElement) {
      containerElement.addEventListener('wheel', function (event) {
        if (event.deltaY !== 0) {
          // Adjust horizontal scroll position based on vertical scroll
          containerElement.scrollLeft += event.deltaY;
        }
      });
    }

    // Scroll to the selected tab on mount
    scrollToTab(selectedTab);
  });
</script>

{#if loaded}
  <div class="flex h-full w-full flex-col pb-2 lg:flex-row lg:space-x-4">
    <div
      id="users-tabs-container"
      class="tabs scrollbar-none mx-[16px] flex max-w-full flex-row gap-2.5 overflow-x-auto text-left text-sm font-medium lg:mx-0 lg:w-50 lg:flex-none lg:flex-col lg:gap-1 lg:px-[16px] dark:text-gray-200"
    >
      <a
        id="leaderboard"
        href="/admin/evaluations/leaderboard"
        draggable="false"
        class="flex min-w-fit rounded-lg px-0.5 py-1 text-right transition select-none lg:flex-none {selectedTab ===
        'leaderboard'
          ? ''
          : ' text-gray-300 hover:text-gray-700 dark:text-gray-600 dark:hover:text-white'}"
      >
        <div class=" mr-2 self-center">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 16 16"
            fill="currentColor"
            class="size-4"
          >
            <path
              fill-rule="evenodd"
              d="M4 2a1.5 1.5 0 0 0-1.5 1.5v9A1.5 1.5 0 0 0 4 14h8a1.5 1.5 0 0 0 1.5-1.5V6.621a1.5 1.5 0 0 0-.44-1.06L9.94 2.439A1.5 1.5 0 0 0 8.878 2H4Zm6 5.75a.75.75 0 0 1 1.5 0v3.5a.75.75 0 0 1-1.5 0v-3.5Zm-2.75 1.5a.75.75 0 0 1 1.5 0v2a.75.75 0 0 1-1.5 0v-2Zm-2 .75a.75.75 0 0 0-.75.75v.5a.75.75 0 0 0 1.5 0v-.5a.75.75 0 0 0-.75-.75Z"
              clip-rule="evenodd"
            />
          </svg>
        </div>
        <div class=" self-center">{$i18n.t('Leaderboard')}</div>
      </a>

      <a
        id="feedback"
        href="/admin/evaluations/feedback"
        draggable="false"
        class="flex min-w-fit rounded-lg px-0.5 py-1 text-right transition select-none lg:flex-none {selectedTab ===
        'feedback'
          ? ''
          : ' text-gray-300 hover:text-gray-700 dark:text-gray-600 dark:hover:text-white'}"
      >
        <div class=" mr-2 self-center">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 16 16"
            fill="currentColor"
            class="size-4"
          >
            <path
              fill-rule="evenodd"
              d="M5.25 2A2.25 2.25 0 0 0 3 4.25v9a.75.75 0 0 0 1.183.613l1.692-1.195 1.692 1.195a.75.75 0 0 0 .866 0l1.692-1.195 1.693 1.195A.75.75 0 0 0 13 13.25v-9A2.25 2.25 0 0 0 10.75 2h-5.5Zm3.03 3.28a.75.75 0 0 0-1.06-1.06L4.97 6.47a.75.75 0 0 0 0 1.06l2.25 2.25a.75.75 0 0 0 1.06-1.06l-.97-.97h1.315c.76 0 1.375.616 1.375 1.375a.75.75 0 0 0 1.5 0A2.875 2.875 0 0 0 8.625 6.25H7.311l.97-.97Z"
              clip-rule="evenodd"
            />
          </svg>
        </div>
        <div class=" self-center">{$i18n.t('Feedback')}</div>
      </a>
    </div>

    <div class="mt-1 flex-1 overflow-y-scroll px-[16px] lg:mt-0 lg:pr-[16px] lg:pl-0">
      {#if selectedTab === 'leaderboard'}
        <Leaderboard />
      {:else if selectedTab === 'feedback'}
        <Feedbacks />
      {/if}
    </div>
  </div>
{/if}
