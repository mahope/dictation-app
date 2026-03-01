<script lang="ts">
  import { listen } from "@tauri-apps/api/event";
  import type { HistoryEntry, SidecarEvent } from "../lib/types";

  let history = $state<HistoryEntry[]>([]);
  let search = $state("");
  let copiedIndex = $state<number | null>(null);

  // Listen for history events from sidecar
  $effect(() => {
    const unlisten = listen<SidecarEvent>("sidecar-event", (event) => {
      const data = event.payload;
      if (data.event === "history" && data.data) {
        history = data.data;
      }
    });
    // Request history on mount
    requestHistory();
    return () => {
      unlisten.then((fn) => fn());
    };
  });

  async function requestHistory() {
    // Send command to sidecar via invoke or direct IPC
    // For now, history will be populated from sidecar events
  }

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
    return d.toLocaleDateString([], {
      month: "short",
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

<div class="flex flex-col h-full">
  <!-- Search & actions -->
  <div class="p-4 pb-2 space-y-2">
    <input
      type="text"
      bind:value={search}
      placeholder="Search history..."
      class="w-full bg-bg-input text-fg rounded-lg px-4 py-2 text-sm
        border border-bg-hover focus:border-accent focus:outline-none
        placeholder:text-fg-muted"
    />
  </div>

  <!-- History list -->
  <div class="flex-1 overflow-y-auto px-4 pb-4">
    {#if filtered.length === 0}
      <div class="text-center text-fg-muted text-sm py-12">
        {search ? "No matches found" : "No history yet"}
      </div>
    {:else}
      {#each grouped as [date, entries]}
        <div class="mb-4">
          <div class="text-xs font-semibold text-fg-muted uppercase tracking-wider mb-2">
            {date}
          </div>
          {#each entries as [ts, text], i}
            {@const globalIdx = filtered.indexOf(entries[i] as any)}
            <button
              class="w-full text-left px-3 py-2 rounded-lg mb-1 transition-colors
                hover:bg-bg-hover group"
              onclick={() => copyEntry(text, globalIdx)}
            >
              <div class="flex items-start gap-2">
                <span class="text-xs text-fg-muted mt-0.5 shrink-0">
                  {formatTime(ts)}
                </span>
                <span
                  class="text-sm text-fg group-hover:text-accent transition-colors line-clamp-2"
                >
                  {text}
                </span>
                {#if copiedIndex === globalIdx}
                  <span class="text-xs text-accent-green shrink-0 ml-auto">
                    Copied!
                  </span>
                {/if}
              </div>
            </button>
          {/each}
        </div>
      {/each}
    {/if}
  </div>
</div>
