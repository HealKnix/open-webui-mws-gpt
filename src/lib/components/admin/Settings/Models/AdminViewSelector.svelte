<script lang="ts">
  import { getContext } from 'svelte';
  import RichSelector from '$lib/components/common/RichSelector.svelte';

  import Grid from '$lib/components/icons/Grid.svelte';
  import CheckCircle from '$lib/components/icons/CheckCircle.svelte';
  import Minus from '$lib/components/icons/Minus.svelte';
  import Eye from '$lib/components/icons/Eye.svelte';
  import EyeSlash from '$lib/components/icons/EyeSlash.svelte';
  import GlobeAlt from '$lib/components/icons/GlobeAlt.svelte';
  import LockClosed from '$lib/components/icons/LockClosed.svelte';

  const i18n = getContext('i18n');

  export let value = '';
  export let placeholder = $i18n.t('Select view');
  export let onChange: (value: string) => void = () => {};

  const items = [
    { value: '', label: $i18n.t('All'), icon: Grid, description: $i18n.t('Show all models') },
    {
      value: 'enabled',
      label: $i18n.t('Enabled'),
      icon: CheckCircle,
      description: $i18n.t('Show only active models'),
    },
    {
      value: 'disabled',
      label: $i18n.t('Disabled'),
      icon: Minus,
      description: $i18n.t('Show only inactive models'),
    },
    {
      value: 'visible',
      label: $i18n.t('Visible'),
      icon: Eye,
      description: $i18n.t('Show only visible models'),
    },
    {
      value: 'hidden',
      label: $i18n.t('Hidden'),
      icon: EyeSlash,
      description: $i18n.t('Show only hidden models'),
    },
    {
      value: 'public',
      label: $i18n.t('Public'),
      icon: GlobeAlt,
      description: $i18n.t('Show only public models'),
    },
    {
      value: 'private',
      label: $i18n.t('Private'),
      icon: LockClosed,
      description: $i18n.t('Show only private models'),
    },
  ];
</script>

<RichSelector bind:value {items} {placeholder} {onChange} triggerClass="px-2.5 py-1.5" />
