<script lang="ts">
  import { cn } from '$lib/utils';
  import Spinner from './Spinner.svelte';

  export let variant: 'solid' | 'flat' | 'ghost' = 'solid';
  export let color: 'primary' | 'secondary' | 'foreground' | string = 'primary';
  export let size: 'xs' | 'sm' | 'md' | 'lg' | 'xl' = 'md';
  export let radius: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full' = 'md';
  export let isIconOnly = false;
  export let loading = false;
  export let disabled = false;
  export let href: string | undefined = undefined;
  export let type: 'button' | 'submit' | 'reset' = 'button';
  export let className = '';

  const isPredefinedColor = ['primary', 'secondary', 'foreground'].includes(color);

  // Size mapping
  const sizes = {
    xs: 'h-7 px-2 text-xs',
    sm: 'h-8 px-3 text-xs',
    md: 'h-10 px-4 text-sm',
    lg: 'h-12 px-6 text-base',
    xl: 'h-14 px-8 text-lg',
  };

  const iconSizes = {
    xs: 'size-7',
    sm: 'size-8',
    md: 'size-10',
    lg: 'size-12',
    xl: 'size-14',
  };

  // Radius mapping
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
        primary: 'bg-primary text-primary-foreground hover:bg-primary-hover',
        secondary: 'bg-border text-secondary-foreground hover:bg-secondary-hover',
        foreground: 'bg-foreground text-background hover:bg-foreground/90',
      },
      flat: {
        primary: 'bg-primary/20 text-primary hover:bg-primary/30',
        secondary: 'bg-border/50 text-secondary-foreground hover:bg-secondary-hover',
        foreground: 'bg-foreground/10 text-foreground hover:bg-foreground/20',
      },
      ghost: {
        primary: 'bg-transparent text-primary hover:bg-primary/10',
        secondary: 'bg-transparent text-secondary hover:bg-secondary-hover',
        foreground: 'bg-transparent text-foreground hover:bg-foreground/10',
      },
    };

    return base[variant][color as keyof (typeof base)['solid']];
  };

  const customStyle = !isPredefinedColor
    ? {
        solid: `background-color: ${color}; color: white;`,
        flat: `background-color: ${color}33; color: ${color};`,
        ghost: `background-color: transparent; color: ${color};`,
      }[variant]
    : '';

  $: buttonClasses = cn(
    'relative inline-flex items-center justify-center font-medium transition-all active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none gap-2 overflow-hidden ring-0 focus-visible:ring-2 ring-primary ring-offset-0 focus-visible:ring-offset-2 ring-offset-background outline-none',
    isIconOnly ? iconSizes[size] : sizes[size],
    radii[radius],
    getVariantClasses(),
    className,
  );

  const Tag = href ? 'a' : 'button';
</script>

<svelte:element
  this={Tag}
  {href}
  {type}
  class={buttonClasses}
  style={customStyle}
  {disabled}
  {...$$restProps}
  on:click
>
  {#if loading}
    <div class="absolute inset-0 flex items-center justify-center bg-inherit">
      <Spinner className="size-4" />
    </div>
    <span class="opacity-0">
      <slot />
    </span>
  {:else}
    <slot />
  {/if}
</svelte:element>
