<script lang="ts">
  import { getContext, onMount, tick } from 'svelte';
  import { toast } from 'svelte-sonner';
  import { chatCompletion } from '$lib/apis/openai';
  import { user, models, settings, config } from '$lib/stores';
  import { WEBUI_BASE_URL } from '$lib/constants';
  import { splitStream } from '$lib/utils';

  import Spinner from '$lib/components/common/Spinner.svelte';
  import XMark from '$lib/components/icons/XMark.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import Messages from './WidgetChatSidebar/Messages.svelte';
  import MessageInput from '$lib/components/channel/MessageInput.svelte';

  const i18n = getContext('i18n');

  export let onApply: (json: string) => void;
  export let onClose: () => void;
  export let currentJson: string = '';

  let loading = false;
  let stopResponseFlag = false;
  let chatInputElement;
  let messagesContainerElement: HTMLDivElement;
  let scrolledToBottom = true;

  let selectedModelId = '';
  let messages: { role: string; content: string; done?: boolean }[] = [];

  $: if ($models.length > 0 && selectedModelId === '') {
    selectedModelId = $settings.models?.[0] || $models[0].id;
  }

  const systemPrompt = `You are an elite UI Designer. Return ONLY a REUSABLE WIDGET TEMPLATE in JSON format.
NO TEXT, NO EXPLANATIONS, NO MARKDOWN BLOCKS. JUST RAW JSON.

## TEMPLATIZATION RULES
- USE {{key}} for all dynamic data (e.g. {{title}}, {{price}}).
- NEVER hardcode final text values.

## SCHEMA
{
  "type": "container" | "flex" | "card" | "card-grid" | "button" | "text" | "badge" | "divider",
  "props": { ... },
  "children": [ ... recursively ... ]
}

## TYPE DETAILS
- container: vertical stack layout (space-y-4). Use as root wrapper.
- flex: horizontal flex layout (flex-wrap, gap-4).
- card: props: { title, subtitle, description, image, badge, price, rating, class }.
- card-grid: responsive grid (1/2/3 columns). Children are cards.
- button: props: { label (display text), action_text (text sent to chat on click), variant ("primary"|"secondary"|"outline"), icon, class }.
- text: props: { value, class }.
- badge: props: { value, class }.
- divider: horizontal line.

## IMPORTANT
- Buttons MUST have "action_text" — this is the message sent to the chat when the user clicks the button.
- "label" is only for display, "action_text" is the payload for the chat action.
- Place buttons inside "children", NOT in a separate "actions" array.
- Always wrap multiple elements in a "container" or "flex" root.

## Brand Style Reference

Its visual language balances **corporate reliability with tech-forward character** — clean, airy layouts punctuated by bold typography and a single vivid accent color. The feel: dependable but not boring, technological but not cold.

### Color System

Use CSS variables for all colors. The palette is deliberately restrained — white dominance, dark contrast sections, and red as the sole vivid accent used sparingly on CTAs.

\`\`\`css
:root {
  /* Backgrounds */
  --mws-bg-primary: #FFFFFF;
  --mws-bg-secondary: #F5F5F7;
  --mws-bg-dark: #1A1A2E;
  --mws-bg-darker: #0D0D1A;

  /* Accent */
  --mws-accent-red: #E30611;
  --mws-accent-red-hover: #FF0032;
  --mws-accent-blue: #0071E3;

  /* Text */
  --mws-text-primary: #1D1D1F;
  --mws-text-secondary: #6E6E73;
  --mws-text-muted: #86868B;
  --mws-text-on-dark: #F5F5F7;

  /* Borders & surfaces */
  --mws-border: #D2D2D7;
  --mws-border-light: #E8E8ED;
  --mws-card-bg-dark: rgba(255, 255, 255, 0.04);
  --mws-card-border-dark: rgba(255, 255, 255, 0.08);

  /* Gradients */
  --mws-gradient-hero: linear-gradient(135deg, #0D0D1A 0%, #1A1A3E 50%, #2D1B4E 100%);
  --mws-gradient-accent: linear-gradient(90deg, #E30611 0%, #FF4D2A 100%);

  /* Radius */
  --mws-radius-sm: 8px;
  --mws-radius-md: 12px;
  --mws-radius-lg: 20px;
  --mws-radius-xl: 24px;
  --mws-radius-full: 9999px;

  /* Shadows */
  --mws-shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.04);
  --mws-shadow-md: 0 8px 30px rgba(0, 0, 0, 0.06);
  --mws-shadow-lg: 0 16px 50px rgba(0, 0, 0, 0.1);
  --mws-shadow-glow-red: 0 4px 20px rgba(227, 6, 17, 0.25);

  /* Spacing (8pt grid) */
  --mws-space-xs: 0.5rem;
  --mws-space-sm: 1rem;
  --mws-space-md: 1.5rem;
  --mws-space-lg: 2.5rem;
  --mws-space-xl: 4rem;
  --mws-space-2xl: 6rem;
  --mws-space-3xl: 8rem;

  /* Typography scale */
  --mws-font-hero: clamp(2.5rem, 5vw, 4.5rem);
  --mws-font-h1: clamp(2rem, 3.5vw, 3rem);
  --mws-font-h2: clamp(1.5rem, 2.5vw, 2.25rem);
  --mws-font-h3: clamp(1.125rem, 1.5vw, 1.5rem);
  --mws-font-body: 1rem;
  --mws-font-small: 0.875rem;
  --mws-font-caption: 0.75rem;

  /* Easing */
  --mws-ease: cubic-bezier(0.25, 0.1, 0.25, 1);
  --mws-ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
}
\`\`\`

### Typography
For reproduction use these substitutes from Google Fonts:

- **Headings**: \`Manrope:wght@700;800\` — geometric, dense, wide grotesque. Alternatively \`Unbounded\` for an even bolder feel.
- **Body text**: \`Onest:wght@400;500;600\` or \`Golos Text\` — clean, modern, excellent Cyrillic support.

Key typographic traits:
- Headings are **large and heavy** (700–800 weight), with tight \`letter-spacing: -0.02em\` and \`line-height: 1.1\`.
- Hero headings reach 48–72px. They dominate the viewport.
- Body text is neutral at 16px, \`line-height: 1.5\`, regular weight.
- Badges and labels use \`text-transform: uppercase; letter-spacing: 0.05em; font-size: 12px; font-weight: 600\`.

### Layout & Spacing

- **Container**: max-width 1280px, padding \`0 clamp(1rem, 4vw, 5rem)\`, centered.
- **Section rhythm**: Alternate backgrounds — dark (\`#1A1A2E\`) → white → light gray (\`#F5F5F7\`) → white → dark. This creates visual rhythm and prevents monotony. Vertical spacing between sections: 80–128px.
- **Card grids**: 3 columns on desktop, 2 on tablet, 1 on mobile. Use \`grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 24px\`.
- **Generous whitespace** between section heading and content: 40–64px.

### Components

**Cards (light background):**
- \`background: #FFF; border: 1px solid #E8E8ED; border-radius: 20px; padding: 32px\`
- Hover: lift \`translateY(-2px)\`, border darkens to \`#D2D2D7\`, shadow grows to \`0 8px 30px rgba(0,0,0,0.06)\`
- Images inside cards use \`overflow: hidden\` with subtle \`scale(1.03)\` on hover
- Product cards often have a soft 3D illustration in purple-blue tones on the right or bottom half

**Cards (dark background — glassmorphism):**
- \`background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; backdrop-filter: blur(10px)\`
- Hover: background brightens to \`rgba(255,255,255,0.08)\`, border to \`rgba(255,255,255,0.15)\`

**Primary button (red CTA):**
- \`background: #E30611; color: #FFF; font-weight: 600; padding: 14px 32px; border-radius: 12px\`
- Hover: \`background: #FF0032; transform: translateY(-1px); box-shadow: 0 4px 16px rgba(227,6,17,0.3)\`
- This is the ONLY element that uses vivid red. Apply sparingly — one or two per viewport.

**Secondary button (outline):**
- \`background: transparent; border: 1.5px solid #D2D2D7; color: #1D1D1F; padding: 14px 32px; border-radius: 12px\`
- Hover: \`border-color: #1D1D1F; background: rgba(0,0,0,0.03)\`

**Badges/Tags:**
- \`font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; padding: 6px 14px; border-radius: 8px; background: rgba(0,113,227,0.08); color: #0071E3\`

### Signature Elements

These are distinctive patterns — include them to make the design feel authentic:

1. **Horizontal ticker / marquee** — a scrolling strip with key metrics (e.g., "20 years experience · 5000+ clients · 7 regions · 24/7 support"). Uses infinite CSS animation. Appears between hero and main content.

2. **Sticky navigation** with \`backdrop-filter: blur(20px); background: rgba(255,255,255,0.8)\` on scroll. Clean, minimal. Red primary CTA button on the right.

3. **Hero section** — full-viewport or near-full, dark background (gradient or video), massive bold heading in white, gray subtitle, single red CTA button. Often features an abstract 3D animation or looping video behind the text.

4. **Horizontal tabs** for content filtering (e.g., "By industry / By task"). Active tab has a bottom underline or filled background. Smooth fade/slide transition on switch.

5. **Scroll-reveal animations** — elements fade in from below (\`translateY(24px) → 0, opacity 0 → 1\`) over 600ms with staggered delays (80ms between siblings).

### Animation

- Default transition: \`all 0.3s cubic-bezier(0.25, 0.1, 0.25, 1)\`
- Scroll reveal: \`opacity 0 → 1, translateY(24px → 0)\` over 600ms
- Staggered children: 80ms delay increment per child
- Card hover: \`translateY(-2px)\` to \`translateY(-4px)\`, shadow expansion, 300ms
- Image hover inside cards: \`scale(1.03)\` with \`overflow: hidden\` on container
- Ticker marquee: \`translateX(0 → -50%)\` linear infinite, 25–35s duration

### Icons

- Line-style (outline), stroke-width 1.5–2px
- Standard size 24×24, card icons 48×48
- White on dark backgrounds, dark gray on light backgrounds
- Geometric, minimal, no fills — consistent with Lucide or similar icon sets

### Forms

- Input fields: minimal, either underline-style or light border (\`1px solid #E8E8ED\`)
- \`border-radius: 8–12px; padding: 14px 16px\`
- Focus state: accent-colored bottom border (red or blue)
- Placeholders in \`#86868B\`, label text in \`#6E6E73\`
- Submit button always uses the red primary style

DO NOT USE PARAMS LIKE mws-bg-primary mws-radius-lg mws-shadow-md. INSTEAD USE COLORS LIKE #FFFFFF OR OTHER STYLES


## EXAMPLE
{
  "type": "container",
  "children": [
    {
      "type": "card",
      "props": { "title": "{{title}}", "image": "{{image}}", "description": "{{desc}}" },
      "children": [
        { "type": "button", "props": { "label": "Book Now", "action_text": "I want to book {{title}}", "variant": "primary" } }
      ]
    }
  ]
}

Current JSON in editor: ${currentJson}`;

  const scrollToBottom = () => {
    if (messagesContainerElement && scrolledToBottom) {
      messagesContainerElement.scrollTop = messagesContainerElement.scrollHeight;
    }
  };

  const onScroll = () => {
    if (messagesContainerElement) {
      scrolledToBottom =
        messagesContainerElement.scrollHeight - messagesContainerElement.scrollTop <=
        messagesContainerElement.clientHeight + 10;
    }
  };

  const chatCompletionHandler = async () => {
    if (selectedModelId === '') {
      toast.error($i18n.t('Please select a model.'));
      return;
    }

    let responseMessage;
    if (messages.at(-1)?.role === 'assistant') {
      responseMessage = messages.at(-1);
    } else {
      responseMessage = { role: 'assistant', content: '', done: false };
      messages = [...messages, responseMessage];
    }

    await tick();
    scrollToBottom();

    stopResponseFlag = false;
    const [res, controller] = await chatCompletion(
      localStorage.token,
      {
        model: selectedModelId,
        messages: [
          { role: 'system', content: systemPrompt },
          ...messages.slice(0, -1).map((m) => ({ role: m.role, content: m.content })),
        ],
        stream: true,
      },
      `${WEBUI_BASE_URL}/api`,
    );

    if (res && res.ok) {
      const reader = res.body
        .pipeThrough(new TextDecoderStream())
        .pipeThrough(splitStream('\n'))
        .getReader();

      let messageContent = '';
      while (true) {
        const { value, done } = await reader.read();
        if (done || stopResponseFlag) {
          if (stopResponseFlag) controller.abort('User: Stop Response');
          responseMessage.done = true;
          messages = messages;
          break;
        }

        try {
          const lines = value.split('\n');
          for (const line of lines) {
            if (line === 'data: [DONE]') {
              responseMessage.done = true;
            } else if (line.startsWith('data: ')) {
              const data = JSON.parse(line.replace(/^data: /, ''));
              const deltaContent = data.choices[0]?.delta?.content ?? '';
              messageContent += deltaContent;
              responseMessage.content = messageContent;

              // Real-time synchronization:
              // Try to extract JSON and apply it to the editor immediately
              const jsonMatch = messageContent.match(/\{[\s\S]*\}/);
              if (jsonMatch) {
                // We send the partial JSON to the editor.
                // CodeMirror and JSON parser in Editor will handle the partial status (e.g. showing error until finished)
                onApply(jsonMatch[0]);
              }

              messages = messages;
            }
          }
        } catch (e) {
          // Ignore partial JSON parse errors for stream extraction
        }
        await tick();
        scrollToBottom();
      }
    }
  };

  const submitHandler = async (e) => {
    const { content } = e;
    if (!content.trim() || loading || !selectedModelId) return;

    messages = [...messages, { role: 'user', content }];
    loading = true;

    await tick();
    scrollToBottom();

    await chatCompletionHandler();
    loading = false;
  };

  const handleApply = (content: string) => {
    const jsonMatch = content.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      onApply(jsonMatch[0]);
      toast.success($i18n.t('Applied to editor'));
    } else {
      toast.error($i18n.t('No valid JSON found'));
    }
  };
</script>

<div
  class="flex h-full w-full flex-col border-l border-gray-100 bg-white dark:border-gray-800 dark:bg-gray-950"
>
  <!-- Header -->
  <div
    class="flex items-center justify-between border-b border-gray-50 p-4 dark:border-gray-800 dark:bg-gray-900"
  >
    <div class="flex items-center gap-2">
      <h3 class="text-sm font-semibold">{$i18n.t('Chat')}</h3>
      <Tooltip content={$i18n.t('Experimental features')}>
        <span class="text-[10px] font-bold tracking-widest text-gray-400 uppercase"
          >({$i18n.t('Experimental')})</span
        >
      </Tooltip>
    </div>
    <button
      class="rounded-lg p-1.5 transition hover:bg-gray-50 dark:hover:bg-gray-800"
      on:click={onClose}
    >
      <XMark className="size-4" />
    </button>
  </div>

  <!-- Messages List -->
  <div
    class="flex-1 overflow-y-auto scroll-smooth p-4"
    bind:this={messagesContainerElement}
    on:scroll={onScroll}
  >
    {#if messages.length === 0}
      <div class="flex h-full flex-col items-center justify-center px-10 text-center">
        <div class="mb-4 rounded-full bg-blue-50 p-3 dark:bg-blue-400/10">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="2"
            stroke="currentColor"
            class="size-6 text-blue-500"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M12 18L12 20M12 20L10 18M12 20L14 18M12 18L12 6M12 6L10 8M12 6L14 8M6 12L4 12M4 12L6 10M4 12L6 14M18 12L20 12M20 12L18 10M20 12L18 14"
            />
          </svg>
        </div>
        <h4 class="mb-1 text-sm font-medium">{$i18n.t('Design with AI')}</h4>
        <p class="line-clamp-2 text-xs text-gray-500">
          {$i18n.t(
            'Describe your widget in plain language and let the assistant generate the schema for you.',
          )}
        </p>
      </div>
    {:else}
      <Messages bind:messages onApply={handleApply} />
    {/if}
  </div>

  <!-- Input Area -->
  <div class="border-t border-gray-50 bg-white/50 p-4 dark:border-gray-800 dark:bg-gray-900/50">
    <MessageInput
      bind:chatInputElement
      placeholder={$i18n.t('Ask assistant...')}
      inputLoading={loading}
      onSubmit={submitHandler}
      onStop={() => (stopResponseFlag = true)}
      acceptFiles={false}
      showFormattingToolbar={false}
    >
      <div slot="menu" class="flex w-full items-center justify-end px-2">
        <select
          class="w-full cursor-pointer bg-transparent text-right text-xs font-medium text-gray-500 outline-hidden transition-colors hover:text-gray-900 dark:hover:text-gray-300"
          bind:value={selectedModelId}
        >
          {#each $models.filter((m) => !(m?.info?.meta?.hidden ?? false)) as model}
            <option value={model.id} class="bg-white text-left dark:bg-gray-800"
              >{model.name}</option
            >
          {/each}
        </select>
      </div>
    </MessageInput>
  </div>
</div>
