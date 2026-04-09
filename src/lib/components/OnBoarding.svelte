<script>
  import { getContext, onMount } from 'svelte';
  const i18n = getContext('i18n');

  import { WEBUI_BASE_URL } from '$lib/constants';

  import Marquee from './common/Marquee.svelte';
  import SlideShow from './common/SlideShow.svelte';
  import ArrowRightCircle from './icons/ArrowRightCircle.svelte';

  export let show = true;
  export let getStartedHandler = () => {};

  function setLogoImage() {
    const logo = document.getElementById('logo');

    if (logo) {
      const isDarkMode = document.documentElement.classList.contains('dark');

      if (isDarkMode) {
        const darkImage = new Image();
        darkImage.src = `${WEBUI_BASE_URL}/static/favicon-dark.png`;

        darkImage.onload = () => {
          logo.src = `${WEBUI_BASE_URL}/static/favicon-dark.png`;
          logo.style.filter = ''; // Ensure no inversion is applied if splash-dark.png exists
        };

        darkImage.onerror = () => {
          logo.style.filter = 'invert(1)'; // Invert image if splash-dark.png is missing
        };
      }
    }
  }

  $: if (show) {
    setLogoImage();
  }
</script>

{#if show}
  <div class="relative h-screen max-h-[100dvh] w-full text-white">
    <div class="fixed z-50 m-10">
      <div class="flex space-x-2">
        <div class=" self-center">
          <img
            id="logo"
            crossorigin="anonymous"
            src="./favicon.png"
            class=" w-6 rounded-full"
            alt="logo"
          />
        </div>
      </div>
    </div>

    <SlideShow duration={5000} />

    <div
      class="absolute top-0 left-0 h-full w-full bg-linear-to-t from-black from-20% to-transparent"
    ></div>

    <div class="absolute top-0 left-0 h-full w-full bg-black/50 backdrop-blur-xs"></div>

    <div class="relative z-10 flex h-screen max-h-[100dvh] w-full bg-transparent">
      <div class="flex w-full flex-col items-center justify-end pb-10 text-center">
        <div class="font-secondary text-5xl lg:text-7xl">
          <Marquee
            duration={5000}
            words={[
              $i18n.t('Explore the cosmos'),
              $i18n.t('Unlock mysteries'),
              $i18n.t('Chart new frontiers'),
              $i18n.t('Dive into knowledge'),
              $i18n.t('Discover wonders'),
              $i18n.t('Ignite curiosity'),
              $i18n.t('Forge new paths'),
              $i18n.t('Unravel secrets'),
              $i18n.t('Pioneer insights'),
              $i18n.t('Embark on adventures'),
            ]}
          />

          <div class="mt-0.5">{$i18n.t(`wherever you are`)}</div>
        </div>

        <div class="mt-8 flex justify-center">
          <div class="flex flex-col items-center justify-center">
            <button
              aria-label={$i18n.t('Get started')}
              class="relative z-20 flex rounded-full bg-white/5 p-1 text-sm font-medium transition hover:bg-white/10"
              on:click={() => {
                getStartedHandler();
              }}
            >
              <ArrowRightCircle className="size-6" aria-hidden="true" />
            </button>
            <div class="font-primary mt-1.5 text-base font-medium" aria-hidden="true">
              {$i18n.t(`Get started`)}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}
