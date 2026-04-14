<script lang="ts">
  import { getContext } from 'svelte';
  import { toast } from 'svelte-sonner';
  import { updateUserPassword } from '$lib/apis/auths';
  import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
  import Button from '$lib/components/common/Button.svelte';

  const i18n = getContext('i18n');

  let show = false;
  let currentPassword = '';
  let newPassword = '';
  let newPasswordConfirm = '';

  const updatePasswordHandler = async () => {
    if (newPassword === newPasswordConfirm) {
      const res = await updateUserPassword(localStorage.token, currentPassword, newPassword).catch(
        (error) => {
          toast.error(`${error}`);
          return null;
        },
      );

      if (res) {
        toast.success($i18n.t('Successfully updated.'));
      }

      currentPassword = '';
      newPassword = '';
      newPasswordConfirm = '';
    } else {
      toast.error(
        $i18n.t("The passwords you entered don't quite match. Please double-check and try again."),
      );
      newPassword = '';
      newPasswordConfirm = '';
    }
  };
</script>

<form
  class="flex flex-col text-sm"
  on:submit|preventDefault={() => {
    updatePasswordHandler();
  }}
>
  <div class="flex items-center gap-2 text-sm">
    <div class="  font-medium">{$i18n.t('Change Password')}</div>
    <Button
      size="sm"
      variant="flat"
      type="button"
      on:click={() => {
        show = !show;
      }}>{show ? $i18n.t('Hide') : $i18n.t('Show')}</Button
    >
  </div>

  {#if show}
    <div class=" space-y-1.5 py-2.5">
      <div class="flex w-full flex-col">
        <div class=" mb-1 text-xs text-gray-500">{$i18n.t('Current Password')}</div>

        <div class="flex-1">
          <SensitiveInput
            type="password"
            bind:value={currentPassword}
            placeholder={$i18n.t('Enter your current password')}
            autocomplete="current-password"
            required
          />
        </div>
      </div>

      <div class="flex w-full flex-col">
        <div class=" mb-1 text-xs text-gray-500">{$i18n.t('New Password')}</div>

        <div class="flex-1">
          <SensitiveInput
            type="password"
            bind:value={newPassword}
            placeholder={$i18n.t('Enter your new password')}
            autocomplete="new-password"
            required
          />
        </div>
      </div>

      <div class="flex w-full flex-col">
        <div class=" mb-1 text-xs text-gray-500">{$i18n.t('Confirm Password')}</div>

        <div class="flex-1">
          <SensitiveInput
            type="password"
            bind:value={newPasswordConfirm}
            placeholder={$i18n.t('Confirm your new password')}
            autocomplete="off"
            required
          />
        </div>
      </div>
    </div>

    <div class="my-3 flex justify-end">
      <Button size="sm" color="secondary">
        {$i18n.t('Update password')}
      </Button>
    </div>
  {/if}
</form>
