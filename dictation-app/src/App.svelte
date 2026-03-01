<script lang="ts">
  import { getCurrentWindow } from "@tauri-apps/api/window";
  import { readConfig } from "./lib/api";
  import type { Config } from "./lib/types";
  import TabBar from "./components/TabBar.svelte";
  import ApiKeyTab from "./components/ApiKeyTab.svelte";
  import SettingsTab from "./components/SettingsTab.svelte";
  import HistoryTab from "./components/HistoryTab.svelte";
  import AboutTab from "./components/AboutTab.svelte";

  const tabs = ["API Key", "Settings", "History", "About"];
  let activeTab = $state(0);

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

  $effect(() => {
    readConfig().then((c) => {
      config = c;
    });
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

<div class="flex flex-col h-screen bg-bg">
  <TabBar {tabs} active={activeTab} onselect={(i) => (activeTab = i)} />

  <div class="flex-1 overflow-hidden">
    {#if activeTab === 0}
      <ApiKeyTab />
    {:else if activeTab === 1}
      <SettingsTab bind:config />
    {:else if activeTab === 2}
      <HistoryTab />
    {:else}
      <AboutTab />
    {/if}
  </div>
</div>
