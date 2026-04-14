<script lang="ts">
  import { toast } from 'svelte-sonner';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { widgets } from '$lib/stores';
  import { onMount, getContext } from 'svelte';

  const i18n = getContext('i18n');

  import { createNewWidget, getWidgets } from '$lib/apis/widgets';
  import WidgetEditor from '$lib/components/workspace/Widgets/WidgetEditor.svelte';

  let widget: {
    name: string;
    id: string;
    description: string;
    content: string;
    is_active: boolean;
    access_grants: any[];
  } | null = null;

  let clone = false;

  const onSubmit = async (_widget) => {
    const res = await createNewWidget(localStorage.token, _widget).catch((error) => {
      toast.error(`${error}`);
      return null;
    });

    if (res) {
      toast.success($i18n.t('Widget created successfully'));
      await widgets.set(await getWidgets(localStorage.token));

      const returnTo = $page.url.searchParams.get('returnTo');
      if (returnTo) {
        sessionStorage.setItem('mcp_app_editor_new_widget_id', res.id || _widget.id);
        await goto(returnTo);
      } else {
        await goto('/workspace/widgets');
      }
    }
  };

  onMount(async () => {
    if (sessionStorage.widget) {
      const _widget = JSON.parse(sessionStorage.widget);
      sessionStorage.removeItem('widget');

      clone = true;
      widget = {
        name: _widget.name || 'Widget',
        id: _widget.id || '',
        description: _widget.description || '',
        content: _widget.content || '{}',
        is_active: _widget.is_active ?? true,
        access_grants: _widget.access_grants !== undefined ? _widget.access_grants : [],
      };
    }
  });
</script>

{#key widget}
  <WidgetEditor {widget} {onSubmit} {clone} />
{/key}
