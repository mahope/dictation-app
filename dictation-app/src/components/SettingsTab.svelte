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

<div class="p-6 space-y-5 overflow-y-auto max-h-[460px]">
  <!-- Transcription -->
  <section>
    <h3 class="text-xs font-semibold text-fg-muted uppercase tracking-wider mb-3">
      Transcription
    </h3>
    <div class="space-y-3">
      <label class="flex items-center justify-between cursor-pointer group">
        <div>
          <div class="text-sm text-fg group-hover:text-accent transition-colors">
            Smart formatting
          </div>
          <div class="text-xs text-fg-muted">
            Add punctuation & capitalization via AI
          </div>
        </div>
        <button
          class="w-10 h-5 rounded-full transition-colors relative
            {config.smart_format ? 'bg-accent' : 'bg-bg-hover'}"
          onclick={() => toggle("smart_format")}
          role="switch"
          aria-checked={config.smart_format}
        >
          <div
            class="absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform
              {config.smart_format ? 'translate-x-5' : 'translate-x-0.5'}"
          ></div>
        </button>
      </label>

      <label class="flex items-center justify-between cursor-pointer group">
        <div>
          <div class="text-sm text-fg group-hover:text-accent transition-colors">
            Auto-stop on silence
          </div>
          <div class="text-xs text-fg-muted">
            Stop recording after silence
          </div>
        </div>
        <button
          class="w-10 h-5 rounded-full transition-colors relative
            {config.silence_detection ? 'bg-accent' : 'bg-bg-hover'}"
          onclick={() => toggle("silence_detection")}
          role="switch"
          aria-checked={config.silence_detection}
        >
          <div
            class="absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform
              {config.silence_detection ? 'translate-x-5' : 'translate-x-0.5'}"
          ></div>
        </button>
      </label>

      {#if config.silence_detection}
        <div class="pl-1">
          <div class="flex items-center justify-between mb-1">
            <span class="text-xs text-fg-muted">Silence duration</span>
            <span class="text-xs text-accent font-mono">{silenceLabel}</span>
          </div>
          <input
            type="range"
            min="0.5"
            max="5"
            step="0.5"
            value={config.silence_duration}
            oninput={(e) => {
              const v = parseFloat((e.target as HTMLInputElement).value);
              config.silence_duration = v;
            }}
            onchange={(e) => {
              const v = parseFloat((e.target as HTMLInputElement).value);
              setField("silence_duration", v);
            }}
            class="w-full accent-accent"
          />
        </div>
      {/if}

      <label class="flex items-center justify-between cursor-pointer group">
        <div>
          <div class="text-sm text-fg group-hover:text-accent transition-colors">
            Copy only (no paste)
          </div>
          <div class="text-xs text-fg-muted">
            Copy to clipboard without auto-pasting
          </div>
        </div>
        <button
          class="w-10 h-5 rounded-full transition-colors relative
            {config.auto_copy ? 'bg-accent' : 'bg-bg-hover'}"
          onclick={() => toggle("auto_copy")}
          role="switch"
          aria-checked={config.auto_copy}
        >
          <div
            class="absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform
              {config.auto_copy ? 'translate-x-5' : 'translate-x-0.5'}"
          ></div>
        </button>
      </label>
    </div>
  </section>

  <!-- Overlay -->
  <section>
    <h3 class="text-xs font-semibold text-fg-muted uppercase tracking-wider mb-3">
      Overlay
    </h3>
    <div class="space-y-3">
      <label class="flex items-center justify-between cursor-pointer group">
        <div>
          <div class="text-sm text-fg group-hover:text-accent transition-colors">
            Show overlay
          </div>
        </div>
        <button
          class="w-10 h-5 rounded-full transition-colors relative
            {config.visible ? 'bg-accent' : 'bg-bg-hover'}"
          onclick={() => toggle("visible")}
          role="switch"
          aria-checked={config.visible}
        >
          <div
            class="absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform
              {config.visible ? 'translate-x-5' : 'translate-x-0.5'}"
          ></div>
        </button>
      </label>

      <label class="flex items-center justify-between cursor-pointer group">
        <div>
          <div class="text-sm text-fg group-hover:text-accent transition-colors">
            Pin overlay position
          </div>
        </div>
        <button
          class="w-10 h-5 rounded-full transition-colors relative
            {config.pinned ? 'bg-accent' : 'bg-bg-hover'}"
          onclick={() => toggle("pinned")}
          role="switch"
          aria-checked={config.pinned}
        >
          <div
            class="absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform
              {config.pinned ? 'translate-x-5' : 'translate-x-0.5'}"
          ></div>
        </button>
      </label>

      <div class="flex items-center justify-between">
        <span class="text-sm text-fg">Overlay size</span>
        <select
          class="bg-bg-input text-fg text-sm rounded-lg px-3 py-1.5 border border-bg-hover
            focus:border-accent focus:outline-none"
          value={config.overlay_size}
          onchange={(e) => setField("overlay_size", (e.target as HTMLSelectElement).value)}
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
    <h3 class="text-xs font-semibold text-fg-muted uppercase tracking-wider mb-3">
      Behavior
    </h3>
    <div class="space-y-3">
      <label class="flex items-center justify-between cursor-pointer group">
        <div>
          <div class="text-sm text-fg group-hover:text-accent transition-colors">
            Mute sounds
          </div>
        </div>
        <button
          class="w-10 h-5 rounded-full transition-colors relative
            {config.quiet ? 'bg-accent' : 'bg-bg-hover'}"
          onclick={() => toggle("quiet")}
          role="switch"
          aria-checked={config.quiet}
        >
          <div
            class="absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform
              {config.quiet ? 'translate-x-5' : 'translate-x-0.5'}"
          ></div>
        </button>
      </label>
    </div>
  </section>

  <!-- Advanced -->
  <section>
    <h3 class="text-xs font-semibold text-fg-muted uppercase tracking-wider mb-3">
      Advanced
    </h3>
    <div class="space-y-3">
      <label class="flex items-center justify-between cursor-pointer group">
        <div>
          <div class="text-sm text-fg group-hover:text-accent transition-colors">
            Start at Windows startup
          </div>
        </div>
        <button
          class="w-10 h-5 rounded-full transition-colors relative
            {config.start_at_startup ? 'bg-accent' : 'bg-bg-hover'}"
          onclick={() => toggle("start_at_startup")}
          role="switch"
          aria-checked={config.start_at_startup}
        >
          <div
            class="absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform
              {config.start_at_startup ? 'translate-x-5' : 'translate-x-0.5'}"
          ></div>
        </button>
      </label>

      <label class="flex items-center justify-between cursor-pointer group">
        <div>
          <div class="text-sm text-fg group-hover:text-accent transition-colors">
            Log to file
          </div>
        </div>
        <button
          class="w-10 h-5 rounded-full transition-colors relative
            {config.log_to_file ? 'bg-accent' : 'bg-bg-hover'}"
          onclick={() => toggle("log_to_file")}
          role="switch"
          aria-checked={config.log_to_file}
        >
          <div
            class="absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform
              {config.log_to_file ? 'translate-x-5' : 'translate-x-0.5'}"
          ></div>
        </button>
      </label>
    </div>
  </section>
</div>
