<script>
  import { page } from '$app/stores';
</script>

<div class=" min-h-screen bg-white dark:bg-gray-800">
  <div class=" flex h-full">
    <div class="m-auto my-10 text-3xl font-medium dark:text-gray-300">
      {$page.status}: {$page.error?.message}
    </div>
  </div>
</div>
