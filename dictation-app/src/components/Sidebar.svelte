<script lang="ts">
  interface Props {
    active: string;
    onnavigate: (page: string) => void;
  }
  let { active, onnavigate }: Props = $props();

  const navItems = [
    { id: "home", label: "Home", icon: "home" },
    { id: "history", label: "History", icon: "history" },
    { id: "settings", label: "Settings", icon: "settings" },
  ];

  const bottomItems = [
    { id: "api-key", label: "API Key", icon: "key" },
  ];
</script>

<nav
  class="w-48 bg-bg-sidebar border-r border-border flex flex-col h-full shrink-0"
>
  <!-- App title -->
  <div class="px-5 pt-5 pb-4">
    <div class="flex items-center gap-2">
      <div class="flex gap-0.5">
        {#each [3, 5, 4, 5, 3] as h}
          <div
            class="w-[3px] rounded-full bg-accent"
            style="height: {h * 3}px"
          ></div>
        {/each}
      </div>
      <span class="text-[15px] font-semibold text-fg">Dictation</span>
    </div>
  </div>

  <!-- Main nav -->
  <div class="flex-1 px-3 space-y-0.5">
    {#each navItems as item}
      <button
        class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors
          {active === item.id
          ? 'bg-bg-hover text-fg font-medium'
          : 'text-fg-dim hover:text-fg hover:bg-bg-card'}"
        onclick={() => onnavigate(item.id)}
      >
        <svg class="w-[18px] h-[18px] shrink-0 opacity-70" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          {#if item.icon === "home"}
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9 22 9 12 15 12 15 22" />
          {:else if item.icon === "history"}
            <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
          {:else if item.icon === "settings"}
            <circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          {/if}
        </svg>
        {item.label}
      </button>
    {/each}
  </div>

  <!-- Bottom nav -->
  <div class="px-3 pb-4 space-y-0.5">
    {#each bottomItems as item}
      <button
        class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors
          {active === item.id
          ? 'bg-bg-hover text-fg font-medium'
          : 'text-fg-dim hover:text-fg hover:bg-bg-card'}"
        onclick={() => onnavigate(item.id)}
      >
        <svg class="w-[18px] h-[18px] shrink-0 opacity-70" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4" />
        </svg>
        {item.label}
      </button>
    {/each}
  </div>
</nav>
