<script lang="ts">
  interface Props {
    stats: { count: number; words: number; history: number };
    engineState: string;
  }
  let { stats, engineState }: Props = $props();

  const shortcuts = [
    ["Ctrl+Shift+D", "Start / stop dictation"],
    ["Ctrl+Shift+Space", "Hold to record"],
    ["Ctrl+Shift+A", "Append mode"],
    ["Ctrl+Shift+Z", "Undo last paste"],
    ["Ctrl+Shift+H", "History popup"],
    ["Ctrl+Shift+Esc", "Cancel recording"],
  ];

  let stateLabel = $derived(
    engineState === "recording"
      ? "Recording..."
      : engineState === "transcribing"
        ? "Transcribing..."
        : "Ready",
  );

  let stateColor = $derived(
    engineState === "recording"
      ? "bg-accent-red"
      : engineState === "transcribing"
        ? "bg-accent"
        : "bg-accent-green",
  );
</script>

<div class="h-full overflow-y-auto">
  <div class="max-w-lg mx-auto px-8 py-8 space-y-8">
    <!-- Welcome header -->
    <div>
      <h1 class="text-2xl font-semibold text-fg">Welcome back</h1>
      <!-- Stats row -->
      <div class="flex items-center gap-4 mt-3">
        <div
          class="flex items-center gap-1.5 text-sm text-fg-dim bg-bg-card rounded-full px-3 py-1"
        >
          <span class="text-base leading-none">&#x1F399;</span>
          <span class="font-medium text-fg">{stats.count}</span> transcriptions
        </div>
        <div
          class="flex items-center gap-1.5 text-sm text-fg-dim bg-bg-card rounded-full px-3 py-1"
        >
          <span class="text-base leading-none">&#x270D;</span>
          <span class="font-medium text-fg"
            >{stats.words.toLocaleString()}</span
          > words
        </div>
      </div>
    </div>

    <!-- Status card -->
    <div class="bg-bg-card rounded-xl p-5 border border-border">
      <div class="flex items-center justify-between">
        <div>
          <div class="text-sm font-medium text-fg">Engine Status</div>
          <div class="text-xs text-fg-muted mt-0.5">
            {engineState === "idle"
              ? "Press Ctrl+Shift+D to start dictating"
              : stateLabel}
          </div>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-2 h-2 rounded-full {stateColor}"></div>
          <span class="text-sm text-fg-dim">{stateLabel}</span>
        </div>
      </div>
    </div>

    <!-- Keyboard shortcuts -->
    <div>
      <h2 class="text-xs font-semibold text-fg-muted uppercase tracking-wider mb-4">
        Keyboard Shortcuts
      </h2>
      <div class="bg-bg-card rounded-xl border border-border divide-y divide-border">
        {#each shortcuts as [key, desc]}
          <div class="flex items-center justify-between px-5 py-3">
            <span class="text-sm text-fg">{desc}</span>
            <kbd
              class="text-xs font-mono text-accent bg-bg px-2.5 py-1 rounded-md border border-border"
            >
              {key}
            </kbd>
          </div>
        {/each}
      </div>
    </div>

    <!-- Version -->
    <div class="text-center text-xs text-fg-muted pt-2">
      Dictation Tool v1.0.0
    </div>
  </div>
</div>
