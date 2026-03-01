<script lang="ts">
  import { getCurrentWindow } from "@tauri-apps/api/window";
  import { listen } from "@tauri-apps/api/event";
  import { readConfig } from "./lib/api";
  import type { Config, SidecarEvent } from "./lib/types";
  import Sidebar from "./components/Sidebar.svelte";
  import HomePage from "./components/HomePage.svelte";
  import SettingsPage from "./components/SettingsPage.svelte";
  import HistoryPage from "./components/HistoryPage.svelte";
  import ApiKeyPage from "./components/ApiKeyPage.svelte";

  let activePage = $state("home");

  let config = $state<Config>({
    smart_format: true,
    device_index: null,
    overlay_x: null,
    overlay_y: null,
    visible: true,
    silence_detection: true,
    silence_duration: 2.0,
    start_at_startup: false,
    quiet: false,
    auto_copy: false,
    pinned: false,
    overlay_size: "normal",
    log_to_file: false,
  });

  let stats = $state({ count: 0, words: 0, history: 0 });
  let engineState = $state("idle");

  $effect(() => {
    readConfig().then((c) => {
      config = c;
    });
  });

  // Listen for sidecar events
  $effect(() => {
    const unlisten = listen<SidecarEvent>("sidecar-event", (event) => {
      const data = event.payload;
      if (data.event === "stats" && data.data) stats = data.data;
      if (data.event === "config" && data.data) config = data.data;
      if (data.event === "state_changed" && data.state)
        engineState = data.state;
    });
    return () => {
      unlisten.then((fn) => fn());
    };
  });

  // Hide window instead of closing (keep app in tray)
  $effect(() => {
    const win = getCurrentWindow();
    const unlisten = win.onCloseRequested(async (event) => {
      event.preventDefault();
      await win.hide();
    });
    return () => {
      unlisten.then((fn) => fn());
    };
  });
</script>

<div class="flex h-screen bg-bg">
  <Sidebar active={activePage} onnavigate={(p) => (activePage = p)} />

  <main class="flex-1 overflow-hidden">
    {#if activePage === "home"}
      <HomePage {stats} {engineState} />
    {:else if activePage === "settings"}
      <SettingsPage bind:config />
    {:else if activePage === "history"}
      <HistoryPage />
    {:else if activePage === "api-key"}
      <ApiKeyPage />
    {/if}
  </main>
</div>
