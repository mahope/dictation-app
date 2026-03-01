<script lang="ts">
  import { listen } from "@tauri-apps/api/event";
  import type { SidecarEvent } from "../lib/types";

  let stats = $state({ count: 0, words: 0, history: 0 });

  $effect(() => {
    const unlisten = listen<SidecarEvent>("sidecar-event", (event) => {
      const data = event.payload;
      if (data.event === "stats" && data.data) {
        stats = data.data;
      }
    });
    return () => {
      unlisten.then((fn) => fn());
    };
  });

  const shortcuts = [
    ["Ctrl+Shift+D", "Start / stop dictation"],
    ["Ctrl+Shift+Space", "Hold to record, release to stop"],
    ["Ctrl+Shift+A", "Append to last transcription"],
    ["Ctrl+Shift+Z", "Undo last paste"],
    ["Ctrl+Shift+H", "Show history popup"],
    ["Ctrl+Shift+Esc", "Cancel recording"],
  ];
</script>

<div class="p-6 space-y-6">
  <!-- Header -->
  <div class="text-center space-y-1">
    <h2 class="text-xl font-bold text-accent">Dictation Tool</h2>
    <p class="text-sm text-fg-dim">Voice-to-text with OpenAI Whisper</p>
  </div>

  <!-- Shortcuts -->
  <section>
    <h3 class="text-xs font-semibold text-fg-muted uppercase tracking-wider mb-3">
      Keyboard Shortcuts
    </h3>
    <div class="space-y-1.5">
      {#each shortcuts as [key, desc]}
        <div class="flex items-center justify-between py-1">
          <span class="text-sm text-fg-dim">{desc}</span>
          <kbd
            class="text-xs font-mono bg-bg-input text-accent px-2 py-0.5 rounded border border-bg-hover"
          >
            {key}
          </kbd>
        </div>
      {/each}
    </div>
  </section>

  <!-- Stats -->
  <section>
    <h3 class="text-xs font-semibold text-fg-muted uppercase tracking-wider mb-3">
      Session Statistics
    </h3>
    <div class="grid grid-cols-3 gap-3">
      <div class="bg-bg-card rounded-lg p-3 text-center">
        <div class="text-lg font-bold text-accent">{stats.count}</div>
        <div class="text-xs text-fg-muted">Transcriptions</div>
      </div>
      <div class="bg-bg-card rounded-lg p-3 text-center">
        <div class="text-lg font-bold text-accent">{stats.words}</div>
        <div class="text-xs text-fg-muted">Words</div>
      </div>
      <div class="bg-bg-card rounded-lg p-3 text-center">
        <div class="text-lg font-bold text-accent">{stats.history}</div>
        <div class="text-xs text-fg-muted">History</div>
      </div>
    </div>
  </section>

  <!-- Version -->
  <div class="text-center text-xs text-fg-muted">v1.0.0</div>
</div>
