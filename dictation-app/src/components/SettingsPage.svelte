<script lang="ts">
  import type { Config } from "../lib/types";
  import { saveConfigField } from "../lib/api";

  interface Props {
    config: Config;
  }
  let { config = $bindable() }: Props = $props();

  async function toggle(key: keyof Config) {
    const val = !config[key];
    (config as any)[key] = val;
    await saveConfigField(key, val);
  }

  async function setField(key: keyof Config, value: unknown) {
    (config as any)[key] = value;
    await saveConfigField(key, value);
  }

  let silenceLabel = $derived(config.silence_duration.toFixed(1) + "s");
</script>

{#snippet toggle_switch(key: keyof Config)}
  <button
    class="w-10 h-[22px] rounded-full transition-colors relative shrink-0
      {config[key] ? 'bg-accent' : 'bg-bg-hover'}"
    onclick={() => toggle(key)}
    role="switch"
    aria-checked={!!config[key]}
    aria-label="Toggle {key}"
  >
    <div
      class="absolute top-[3px] w-4 h-4 rounded-full bg-white shadow-sm transition-transform
        {config[key] ? 'translate-x-[22px]' : 'translate-x-[3px]'}"
    ></div>
  </button>
{/snippet}

<div class="h-full overflow-y-auto">
  <div class="max-w-lg mx-auto px-8 py-8 space-y-6">
    <h1 class="text-2xl font-semibold text-fg">Settings</h1>

    <!-- Transcription -->
    <section>
      <h2
        class="text-xs font-semibold text-fg-muted uppercase tracking-wider mb-3"
      >
        Transcription
      </h2>
      <div class="bg-bg-card rounded-xl border border-border divide-y divide-border">
        <div class="flex items-center justify-between px-5 py-3.5">
          <div>
            <div class="text-sm text-fg">Smart formatting</div>
            <div class="text-xs text-fg-muted mt-0.5">
              Punctuation & capitalization via AI
            </div>
          </div>
          {@render toggle_switch("smart_format")}
        </div>

        <div class="px-5 py-3.5">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-sm text-fg">Auto-stop on silence</div>
              <div class="text-xs text-fg-muted mt-0.5">
                Stop recording after silence
              </div>
            </div>
            {@render toggle_switch("silence_detection")}
          </div>
          {#if config.silence_detection}
            <div class="mt-3 pt-3 border-t border-border">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs text-fg-muted">Silence duration</span>
                <span class="text-xs text-accent font-mono"
                  >{silenceLabel}</span
                >
              </div>
              <input
                type="range"
                min="0.5"
                max="5"
                step="0.5"
                value={config.silence_duration}
                oninput={(e) => {
                  config.silence_duration = parseFloat(
                    (e.target as HTMLInputElement).value,
                  );
                }}
                onchange={(e) => {
                  setField(
                    "silence_duration",
                    parseFloat((e.target as HTMLInputElement).value),
                  );
                }}
                class="w-full"
              />
            </div>
          {/if}
        </div>

        <div class="flex items-center justify-between px-5 py-3.5">
          <div>
            <div class="text-sm text-fg">Copy only (no paste)</div>
            <div class="text-xs text-fg-muted mt-0.5">
              Copy to clipboard without auto-pasting
            </div>
          </div>
          {@render toggle_switch("auto_copy")}
        </div>
      </div>
    </section>

    <!-- Overlay -->
    <section>
      <h2
        class="text-xs font-semibold text-fg-muted uppercase tracking-wider mb-3"
      >
        Overlay
      </h2>
      <div class="bg-bg-card rounded-xl border border-border divide-y divide-border">
        <div class="flex items-center justify-between px-5 py-3.5">
          <div class="text-sm text-fg">Show overlay</div>
          {@render toggle_switch("visible")}
        </div>
        <div class="flex items-center justify-between px-5 py-3.5">
          <div class="text-sm text-fg">Pin position</div>
          {@render toggle_switch("pinned")}
        </div>
        <div class="flex items-center justify-between px-5 py-3.5">
          <span class="text-sm text-fg">Size</span>
          <select
            class="bg-bg-input text-fg text-sm rounded-lg px-3 py-1.5 border border-border
              focus:border-accent focus:outline-none cursor-pointer"
            value={config.overlay_size}
            onchange={(e) =>
              setField(
                "overlay_size",
                (e.target as HTMLSelectElement).value,
              )}
          >
            <option value="small">Small</option>
            <option value="normal">Normal</option>
            <option value="large">Large</option>
          </select>
        </div>
      </div>
    </section>

    <!-- Behavior -->
    <section>
      <h2
        class="text-xs font-semibold text-fg-muted uppercase tracking-wider mb-3"
      >
        Behavior
      </h2>
      <div class="bg-bg-card rounded-xl border border-border divide-y divide-border">
        <div class="flex items-center justify-between px-5 py-3.5">
          <div class="text-sm text-fg">Mute sounds</div>
          {@render toggle_switch("quiet")}
        </div>
        <div class="flex items-center justify-between px-5 py-3.5">
          <div class="text-sm text-fg">Start at Windows startup</div>
          {@render toggle_switch("start_at_startup")}
        </div>
        <div class="flex items-center justify-between px-5 py-3.5">
          <div class="text-sm text-fg">Log to file</div>
          {@render toggle_switch("log_to_file")}
        </div>
      </div>
    </section>
  </div>
</div>
