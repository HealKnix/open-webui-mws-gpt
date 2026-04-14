<script lang="ts">
  import { cn } from '$lib/utils';

  export let variant: 'solid' | 'flat' | 'ghost' = 'solid';
  export let color: 'default' | 'primary' | 'secondary' | 'foreground' | (string & {}) = 'default';
  export let size: 'xs' | 'sm' | 'md' | 'lg' | 'xl' = 'sm';
  export let radius: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full' = 'md';
  export let disabled = false;
  export let readonly = false;
  export let className = '';
  export let textareaClassName = '';

  export let value = '';
  export let placeholder = '';
  export let required = false;
  export let ariaLabel: string | null = null;

  // Radius mapping (matching Button/Input)
  const mappedRadius = {
    xs: 'rounded-xs',
    sm: 'rounded-sm',
    md: 'rounded-md',
    lg: 'rounded-lg',
    xl: 'rounded-xl',
    full: 'rounded-full',
  };

  // Variant & Color logic (matching Input)
  const getVariantClasses = () => {
    const base: Record<typeof variant, Record<typeof color, string>> = {
      solid: {
        default: 'bg-background border-border text-foreground',
        primary: 'bg-primary/5 border-primary/20 text-foreground',
        secondary: 'bg-card border-border text-foreground',
        foreground: 'bg-foreground border-foreground/10 text-background',
      },
      flat: {
        default: 'bg-background border-transparent text-foreground',
        primary: 'bg-primary/10 border-transparent text-foreground',
        secondary: 'bg-card/50 border-transparent text-foreground',
        foreground: 'bg-foreground/10 border-transparent text-background',
      },
      ghost: {
        default: 'bg-transparent border-border text-background',
        primary: 'bg-transparent border-transparent text-foreground',
        secondary: 'bg-transparent border-transparent text-foreground',
        foreground: 'bg-transparent border-transparent text-background',
      },
    };
    return base[variant][color];
  };

  $: wrapperClasses = cn(
    'relative flex flex-col transition-all duration-200 border ring-primary focus-within:ring-2 ring-offset-0 focus-within:ring-offset-2 ring-offset-background outline-none overflow-hidden w-full',
    mappedRadius[radius],
    getVariantClasses(),
    disabled && 'opacity-50 pointer-events-none',
    className,
  );

  $: textareaClasses = cn(
    'w-full bg-transparent border-none outline-none px-3 py-2 resize-none scrollbar-hidden',
    size === 'xs' || size === 'sm' ? 'text-xs' : 'text-sm',
    textareaClassName,
  );
</script>

<div class={wrapperClasses}>
  <textarea
    bind:value
    {placeholder}
    {disabled}
    {readonly}
    {required}
    aria-label={ariaLabel || placeholder}
    class={textareaClasses}
    {...$$restProps}
  ></textarea>
</div>

<style>
  .scrollbar-hidden::-webkit-scrollbar {
    display: none;
  }
  .scrollbar-hidden {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
</style>
