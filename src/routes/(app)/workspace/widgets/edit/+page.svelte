<script lang="ts">
  import { toast } from 'svelte-sonner';
  import { goto } from '$app/navigation';
  import { widgets } from '$lib/stores';
  import { onMount, getContext } from 'svelte';

  const i18n = getContext('i18n');

  import { getWidgetById, getWidgets, updateWidgetById } from '$lib/apis/widgets';
  import { page } from '$app/stores';

  import WidgetEditor from '$lib/components/workspace/Widgets/WidgetEditor.svelte';

  let widget = null;
  let disabled = false;

  $: widgetId = $page.url.searchParams.get('id');

  const onSubmit = async (_widget) => {
    const updatedWidget = await updateWidgetById(localStorage.token, widgetId, _widget).catch(
      (error) => {
        toast.error(`${error}`);
        return null;
      },
    );

    if (updatedWidget) {
      toast.success($i18n.t('Widget updated successfully'));
      await widgets.set(await getWidgets(localStorage.token));
      widget = {
        id: updatedWidget.id,
        name: updatedWidget.name,
        description: updatedWidget.description,
        content: updatedWidget.content,
        is_active: updatedWidget.is_active,
        access_grants:
          updatedWidget?.access_grants === undefined ? [] : updatedWidget?.access_grants,
      };
    }
  };

  onMount(async () => {
    if (widgetId) {
      const _widget = await getWidgetById(localStorage.token, widgetId).catch((error) => {
        toast.error(`${error}`);
        return null;
      });

      if (_widget) {
        disabled = !_widget.write_access ?? true;
        widget = {
          id: _widget.id,
          name: _widget.name,
          description: _widget.description,
          content: _widget.content,
          is_active: _widget.is_active,
          access_grants: _widget?.access_grants === undefined ? [] : _widget?.access_grants,
        };
      } else {
        goto('/workspace/widgets');
      }
    } else {
      goto('/workspace/widgets');
    }
  });
</script>

{#if widget}
  <WidgetEditor {widget} {onSubmit} {disabled} edit />
{/if}
