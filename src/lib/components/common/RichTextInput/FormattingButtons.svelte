<script>
  import { getContext } from 'svelte';
  const i18n = getContext('i18n');

  export let editor = null;

  import Bold from '$lib/components/icons/Bold.svelte';
  import CodeBracket from '$lib/components/icons/CodeBracket.svelte';
  import H1 from '$lib/components/icons/H1.svelte';
  import H2 from '$lib/components/icons/H2.svelte';
  import H3 from '$lib/components/icons/H3.svelte';
  import Italic from '$lib/components/icons/Italic.svelte';
  import ListBullet from '$lib/components/icons/ListBullet.svelte';
  import NumberedList from '$lib/components/icons/NumberedList.svelte';
  import Strikethrough from '$lib/components/icons/Strikethrough.svelte';
  import Underline from '$lib/components/icons/Underline.svelte';

  import Tooltip from '../Tooltip.svelte';
  import CheckBox from '$lib/components/icons/CheckBox.svelte';
  import ArrowLeftTag from '$lib/components/icons/ArrowLeftTag.svelte';
  import ArrowRightTag from '$lib/components/icons/ArrowRightTag.svelte';
</script>

<div
  class="dark:bg-gray-850 flex min-w-fit gap-0.5 rounded-xl border border-gray-100 bg-white p-0.5 text-gray-800 shadow-lg dark:border-gray-800 dark:text-white"
>
  <Tooltip placement="top" content={$i18n.t('H1')}>
    <button
      on:click={() => editor?.chain().focus().toggleHeading({ level: 1 }).run()}
      class="{editor?.isActive('heading', { level: 1 })
        ? 'bg-gray-50 dark:bg-gray-700'
        : ''} rounded-lg p-1.5 transition-all hover:bg-gray-50 dark:hover:bg-gray-700"
      type="button"
    >
      <H1 />
    </button>
  </Tooltip>

  <Tooltip placement="top" content={$i18n.t('H2')}>
    <button
      on:click={() => editor?.chain().focus().toggleHeading({ level: 2 }).run()}
      class="{editor?.isActive('heading', { level: 2 })
        ? 'bg-gray-50 dark:bg-gray-700'
        : ''} rounded-lg p-1.5 transition-all hover:bg-gray-50 dark:hover:bg-gray-700"
      type="button"
    >
      <H2 />
    </button>
  </Tooltip>

  <Tooltip placement="top" content={$i18n.t('H3')}>
    <button
      on:click={() => editor?.chain().focus().toggleHeading({ level: 3 }).run()}
      class="{editor?.isActive('heading', { level: 3 })
        ? 'bg-gray-50 dark:bg-gray-700'
        : ''} rounded-lg p-1.5 transition-all hover:bg-gray-50 dark:hover:bg-gray-700"
      type="button"
    >
      <H3 />
    </button>
  </Tooltip>

  {#if editor?.isActive('bulletList') || editor?.isActive('orderedList') || editor?.isActive('taskList')}
    <Tooltip placement="top" content={$i18n.t('Lift List')}>
      <button
        on:click={() => {
          editor?.commands.liftListItem(editor?.isActive('taskList') ? 'taskItem' : 'listItem');
        }}
        class="rounded-lg p-1.5 transition-all hover:bg-gray-50 dark:hover:bg-gray-700"
        type="button"
      >
        <ArrowLeftTag />
      </button>
    </Tooltip>
    <Tooltip placement="top" content={$i18n.t('Sink List')}>
      <button
        on:click={() =>
          editor?.commands.sinkListItem(editor?.isActive('taskList') ? 'taskItem' : 'listItem')}
        class="rounded-lg p-1.5 transition-all hover:bg-gray-50 dark:hover:bg-gray-700"
        type="button"
      >
        <ArrowRightTag />
      </button>
    </Tooltip>
  {/if}

  <Tooltip placement="top" content={$i18n.t('Bullet List')}>
    <button
      on:click={() => editor?.chain().focus().toggleBulletList().run()}
      class="{editor?.isActive('bulletList')
        ? 'bg-gray-50 dark:bg-gray-700'
        : ''} rounded-lg p-1.5 transition-all hover:bg-gray-50 dark:hover:bg-gray-700"
      type="button"
    >
      <ListBullet />
    </button>
  </Tooltip>

  <Tooltip placement="top" content={$i18n.t('Ordered List')}>
    <button
      on:click={() => editor?.chain().focus().toggleOrderedList().run()}
      class="{editor?.isActive('orderedList')
        ? 'bg-gray-50 dark:bg-gray-700'
        : ''} rounded-lg p-1.5 transition-all hover:bg-gray-50 dark:hover:bg-gray-700"
      type="button"
    >
      <NumberedList />
    </button>
  </Tooltip>

  <Tooltip placement="top" content={$i18n.t('Task List')}>
    <button
      on:click={() => editor?.chain().focus().toggleTaskList().run()}
      class="{editor?.isActive('taskList')
        ? 'bg-gray-50 dark:bg-gray-700'
        : ''} rounded-lg p-1.5 transition-all hover:bg-gray-50 dark:hover:bg-gray-700"
      type="button"
    >
      <CheckBox />
    </button>
  </Tooltip>

  <Tooltip placement="top" content={$i18n.t('Bold')}>
    <button
      on:click={() => editor?.chain().focus().toggleBold().run()}
      class="{editor?.isActive('bold')
        ? 'bg-gray-50 dark:bg-gray-700'
        : ''} rounded-lg p-1.5 transition-all hover:bg-gray-50 dark:hover:bg-gray-700"
      type="button"
    >
      <Bold />
    </button>
  </Tooltip>

  <Tooltip placement="top" content={$i18n.t('Italic')}>
    <button
      on:click={() => editor?.chain().focus().toggleItalic().run()}
      class="{editor?.isActive('italic')
        ? 'bg-gray-50 dark:bg-gray-700'
        : ''} rounded-lg p-1.5 transition-all hover:bg-gray-50 dark:hover:bg-gray-700"
      type="button"
    >
      <Italic />
    </button>
  </Tooltip>

  <Tooltip placement="top" content={$i18n.t('Underline')}>
    <button
      on:click={() => editor?.chain().focus().toggleUnderline().run()}
      class="{editor?.isActive('underline')
        ? 'bg-gray-50 dark:bg-gray-700'
        : ''} rounded-lg p-1.5 transition-all hover:bg-gray-50 dark:hover:bg-gray-700"
      type="button"
    >
      <Underline />
    </button>
  </Tooltip>

  <Tooltip placement="top" content={$i18n.t('Strikethrough')}>
    <button
      on:click={() => editor?.chain().focus().toggleStrike().run()}
      class="{editor?.isActive('strike')
        ? 'bg-gray-50 dark:bg-gray-700'
        : ''} rounded-lg p-1.5 transition-all hover:bg-gray-50 dark:hover:bg-gray-700"
      type="button"
    >
      <Strikethrough />
    </button>
  </Tooltip>

  <Tooltip placement="top" content={$i18n.t('Code Block')}>
    <button
      on:click={() => editor?.chain().focus().toggleCodeBlock().run()}
      class="{editor?.isActive('codeBlock')
        ? 'bg-gray-50 dark:bg-gray-700'
        : ''} rounded-lg p-1.5 transition-all hover:bg-gray-50 dark:hover:bg-gray-700"
      type="button"
    >
      <CodeBracket />
    </button>
  </Tooltip>
</div>
