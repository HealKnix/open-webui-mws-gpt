<script lang="ts">
  import { cn } from '$lib/utils';
  import type { ComponentType } from 'svelte';

  export let variant: 'solid' | 'flat' | 'ghost' = 'solid';
  export let color: 'primary' | 'secondary' | 'foreground' | string = 'secondary';
  export let size: 'xs' | 'sm' | 'md' | 'lg' | 'xl' = 'sm';
  export let radius: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full' = 'md';
  export let disabled = false;
  export let className = '';
  export let inputClassName = '';

  export let value: string | number | undefined = undefined;
  export let type = 'text';
  export let placeholder = '';
  export let required = false;
  export let autocomplete = 'off';

  export let iconLeft: ComponentType | undefined = undefined;
  export let iconRight: ComponentType | undefined = undefined;

  const isPredefinedColor = ['primary', 'secondary', 'foreground'].includes(color);

  // Size mapping (matching Button)
  const sizes = {
    xs: 'h-7 text-xs',
    sm: 'h-8 text-xs',
    md: 'h-10 text-sm',
    lg: 'h-12 text-base',
    xl: 'h-14 text-lg',
  };

  // Radius mapping (matching Button)
  const radii = {
    xs: 'rounded-xs',
    sm: 'rounded-sm',
    md: 'rounded-md',
    lg: 'rounded-lg',
    xl: 'rounded-xl',
    full: 'rounded-full',
  };

  // Variant & Color logic
  const getVariantClasses = () => {
    if (!isPredefinedColor) return '';

    const base = {
      solid: {
        primary: 'bg-primary/5 border-primary/20 text-foreground',
        secondary: 'bg-border/30 border-border text-foreground',
        foreground: 'bg-foreground/5 border-foreground/10 text-foreground',
      },
      flat: {
        primary: 'bg-primary/10 border-transparent text-foreground',
        secondary: 'bg-border/50 border-transparent text-foreground',
        foreground: 'bg-foreground/10 border-transparent text-foreground',
      },
      ghost: {
        primary: 'bg-transparent border-transparent text-foreground',
        secondary: 'bg-transparent border-transparent text-foreground',
        foreground: 'bg-transparent border-transparent text-foreground',
      },
    };

    return base[variant][color as keyof (typeof base)['solid']];
  };

  $: wrapperClasses = cn(
    'relative flex items-center transition-all duration-200 border ring-primary focus-within:ring-2 ring-offset-0 focus-within:ring-offset-2 ring-offset-background outline-none overflow-hidden w-full',
    radii[radius],
    sizes[size],
    getVariantClasses(),
    disabled && 'opacity-50 pointer-events-none',
    className,
  );

  $: inputClasses = cn(
    'w-full h-full bg-transparent border-none outline-none px-3 py-2',
    iconLeft && 'pl-9',
    iconRight && 'pr-9',
    inputClassName,
  );

  const iconSizeClasses = {
    xs: 'size-3.5',
    sm: 'size-4',
    md: 'size-5',
    lg: 'size-6',
    xl: 'size-7',
  };
</script>

<div class={wrapperClasses}>
  {#if iconLeft}
    <div
      class="text-secondary-foreground/60 pointer-events-none absolute left-3 flex items-center justify-center"
    >
      <svelte:component this={iconLeft} className={iconSizeClasses[size]} />
    </div>
  {/if}

  <input
    bind:value
    {type}
    {placeholder}
    {disabled}
    {required}
    {autocomplete}
    class={inputClasses}
    {...$$restProps}
    on:input
    on:change
    on:keydown
    on:keyup
    on:focus
    on:blur
  />

  {#if iconRight}
    <div
      class="text-secondary-foreground/60 pointer-events-none absolute right-3 flex items-center justify-center"
    >
      <svelte:component this={iconRight} className={iconSizeClasses[size]} />
    </div>
  {/if}
</div>
