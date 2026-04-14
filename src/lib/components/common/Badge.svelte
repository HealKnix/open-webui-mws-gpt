<script lang="ts">
  export let type = 'info';
  export let content = '';

  const classNames: Record<string, string> = {
    info: 'bg-blue-500/20 text-blue-700 dark:text-blue-200 ',
    success: 'bg-green-500/20 text-green-700 dark:text-green-200',
    warning: 'bg-yellow-500/20 text-yellow-700 dark:text-yellow-200',
    error: 'bg-red-500/20 text-red-700 dark:text-red-200',
    muted: 'bg-gray-500/20 text-gray-700 dark:text-gray-200',
  };
</script>

<div
  class=" text-xs font-medium {classNames[type] ??
    classNames['info']} mr-0.5 line-clamp-1 w-fit rounded-lg px-[5px] uppercase"
>
  {content}
</div>
