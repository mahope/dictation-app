<script lang="ts">
  import { listen } from "@tauri-apps/api/event";
  import type { HistoryEntry, SidecarEvent } from "../lib/types";

  let history = $state<HistoryEntry[]>([]);
  let search = $state("");
  let copiedIndex = $state<number | null>(null);

  $effect(() => {
    const unlisten = listen<SidecarEvent>("sidecar-event", (event) => {
      const data = event.payload;
      if (data.event === "history" && data.data) {
        history = data.data;
      }
    });
    return () => {
      unlisten.then((fn) => fn());
    };
  });

  let filtered = $derived(
    search.trim()
      ? history.filter(([, text]) =>
          text.toLowerCase().includes(search.toLowerCase()),
        )
      : history,
  );

  function formatTime(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  function formatDate(iso: string): string {
    const d = new Date(iso);
    const today = new Date();
    if (d.toDateString() === today.toDateString()) return "Today";
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    if (d.toDateString() === yesterday.toDateString()) return "Yesterday";
    return d.toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  }

  function groupByDate(
    entries: HistoryEntry[],
  ): [string, HistoryEntry[]][] {
    const groups = new Map<string, HistoryEntry[]>();
    for (const entry of entries) {
      const date = formatDate(entry[0]);
      if (!groups.has(date)) groups.set(date, []);
      groups.get(date)!.push(entry);
    }
    return [...groups.entries()];
  }

  let grouped = $derived(groupByDate(filtered));

  async function copyEntry(text: string, index: number) {
    await navigator.clipboard.writeText(text);
    copiedIndex = index;
    setTimeout(() => {
      copiedIndex = null;
    }, 1500);
  }
</script>

<div class="h-full flex flex-col">
  <!-- Header -->
  <div class="px-8 pt-8 pb-4">
    <h1 class="text-2xl font-semibold text-fg mb-4">History</h1>
    <div class="relative">
      <svg
        class="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-fg-muted"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <circle cx="11" cy="11" r="8" /><line
          x1="21"
          y1="21"
          x2="16.65"
          y2="16.65"
        />
      </svg>
      <input
        type="text"
        bind:value={search}
        placeholder="Search transcriptions..."
        class="w-full bg-bg-card text-fg rounded-xl pl-10 pr-4 py-2.5 text-sm
          border border-border focus:border-accent focus:outline-none
          placeholder:text-fg-muted"
      />
    </div>
  </div>

  <!-- List -->
  <div class="flex-1 overflow-y-auto px-8 pb-8">
    {#if filtered.length === 0}
      <div class="text-center py-16">
        <div class="text-fg-muted text-sm">
          {search ? "No matches found" : "No transcriptions yet"}
        </div>
        {#if !search}
          <div class="text-fg-muted text-xs mt-1">
            Press Ctrl+Shift+D to start dictating
          </div>
        {/if}
      </div>
    {:else}
      {#each grouped as [date, entries]}
        <div class="mb-6">
          <div
            class="text-xs font-semibold text-fg-muted uppercase tracking-wider mb-3"
          >
            {date}
          </div>
          <div class="space-y-1">
            {#each entries as [ts, text], i}
              {@const globalIdx = filtered.indexOf(entries[i] as HistoryEntry)}
              <button
                class="w-full text-left rounded-xl px-5 py-3 transition-colors
                  bg-bg-card border border-border hover:border-accent/30 group"
                onclick={() => copyEntry(text, globalIdx)}
              >
                <div class="flex items-start gap-4">
                  <span
                    class="text-xs text-fg-muted mt-0.5 shrink-0 tabular-nums"
                  >
                    {formatTime(ts)}
                  </span>
                  <span
                    class="text-sm text-fg leading-relaxed flex-1 line-clamp-3"
                  >
                    {text}
                  </span>
                  {#if copiedIndex === globalIdx}
                    <span
                      class="text-xs text-accent-green shrink-0 ml-auto mt-0.5"
                    >
                      Copied
                    </span>
                  {/if}
                </div>
              </button>
            {/each}
          </div>
        </div>
      {/each}
    {/if}
  </div>
</div>
