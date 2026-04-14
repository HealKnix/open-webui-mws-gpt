<script lang="ts">
  import { WEBUI_API_BASE_URL } from '$lib/constants';
  import { Handle, Position, type NodeProps } from '@xyflow/svelte';
  import { getContext } from 'svelte';

  import ProfileImage from '../Messages/ProfileImage.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Heart from '$lib/components/icons/Heart.svelte';

  const i18n = getContext('i18n');

  type $$Props = NodeProps;
  export let data: $$Props['data'];
</script>

<div
  class="group h-20 w-60 rounded-xl border border-gray-100 bg-white px-4 py-3 shadow-md dark:border-gray-900 dark:bg-black"
>
  <Tooltip
    content={data?.message?.error ? data.message.error.content : data.message.content}
    class="w-full"
    allowHTML={false}
  >
    {#if data.message.role === 'user'}
      <div class="flex w-full">
        <ProfileImage
          src={`${WEBUI_API_BASE_URL}/users/${data.user.id}/profile/image`}
          className={'size-5 -translate-y-[1px] flex-shrink-0'}
        />
        <div class="ml-2">
          <div class=" flex items-center justify-between">
            <div class="line-clamp-1 text-xs font-medium text-black dark:text-white">
              {data?.user?.name ?? 'User'}
            </div>
          </div>

          {#if data?.message?.error}
            <div class="mt-0.5 line-clamp-2 text-xs text-red-500">{data.message.error.content}</div>
          {:else}
            <div class="mt-0.5 line-clamp-2 text-xs text-gray-500">{data.message.content}</div>
          {/if}
        </div>
      </div>
    {:else}
      <div class="flex w-full">
        <ProfileImage
          src={`${WEBUI_API_BASE_URL}/models/model/profile/image?id=${data.model?.id ?? data.message.model}&lang=${$i18n.language}`}
          className={'size-5 -translate-y-[1px] flex-shrink-0'}
        />

        <div class="ml-2">
          <div class=" flex items-center justify-between">
            <div class="line-clamp-1 text-xs font-medium text-black dark:text-white">
              {data?.model?.name ?? data?.message?.model ?? 'Assistant'}
            </div>

            <button
              class={data?.message?.favorite ? '' : 'invisible group-hover:visible'}
              aria-label={data?.message?.favorite
                ? $i18n.t('Remove from favorites')
                : $i18n.t('Add to favorites')}
              on:click={() => {
                data.message.favorite = !(data?.message?.favorite ?? false);
              }}
            >
              <Heart
                className="size-3 {data?.message?.favorite
                  ? 'fill-red-500 stroke-red-500'
                  : 'hover:fill-red-500 hover:stroke-red-500'} "
                strokeWidth="2.5"
              />
            </button>
          </div>

          {#if data?.message?.error}
            <div class="mt-0.5 line-clamp-2 text-xs text-red-500">
              {data.message.error.content}
            </div>
          {:else}
            <div class="mt-0.5 line-clamp-2 text-xs text-gray-500">{data.message.content}</div>
          {/if}
        </div>
      </div>
    {/if}
  </Tooltip>
  <Handle type="target" position={Position.Top} class="w-2 rounded-full dark:bg-gray-900" />
  <Handle type="source" position={Position.Bottom} class="w-2 rounded-full dark:bg-gray-900" />
</div>
