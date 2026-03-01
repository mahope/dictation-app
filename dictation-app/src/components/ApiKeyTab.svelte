<script lang="ts">
  import { readApiKey, saveApiKey, validateApiKey } from "../lib/api";

  let apiKey = $state("");
  let showKey = $state(false);
  let status = $state<"idle" | "validating" | "success" | "error">("idle");
  let statusMessage = $state("");

  $effect(() => {
    readApiKey().then((key) => {
      apiKey = key;
    });
  });

  async function handleSave() {
    const key = apiKey.trim();
    if (!key) {
      status = "error";
      statusMessage = "Please enter an API key";
      return;
    }

    status = "validating";
    statusMessage = "Validating...";

    try {
      const valid = await validateApiKey(key);
      if (valid) {
        await saveApiKey(key);
        status = "success";
        statusMessage = "Saved & validated!";
      } else {
        status = "error";
        statusMessage = "Invalid API key";
      }
    } catch (e) {
      status = "error";
      statusMessage = `Error: ${e}`;
    }
  }
</script>

<div class="p-6 space-y-6">
  <div>
    <h2 class="text-lg font-semibold mb-1">OpenAI API Key</h2>
    <p class="text-fg-dim text-sm">
      Required for speech-to-text transcription.
    </p>
  </div>

  <div class="space-y-3">
    <div class="relative">
      <input
        type={showKey ? "text" : "password"}
        bind:value={apiKey}
        placeholder="sk-..."
        class="w-full bg-bg-input text-fg rounded-lg px-4 py-2.5 pr-20
          border border-bg-hover focus:border-accent focus:outline-none
          placeholder:text-fg-muted text-sm"
      />
      <button
        class="absolute right-2 top-1/2 -translate-y-1/2 px-3 py-1
          text-xs text-fg-dim hover:text-fg rounded transition-colors"
        onclick={() => (showKey = !showKey)}
      >
        {showKey ? "Hide" : "Show"}
      </button>
    </div>

    <button
      class="w-full bg-accent text-bg font-medium rounded-lg py-2.5
        hover:brightness-110 transition-all text-sm disabled:opacity-50"
      onclick={handleSave}
      disabled={status === "validating"}
    >
      {status === "validating" ? "Validating..." : "Save & Validate"}
    </button>

    {#if status !== "idle"}
      <p
        class="text-sm {status === 'success'
          ? 'text-accent-green'
          : status === 'error'
            ? 'text-accent-red'
            : 'text-fg-dim'}"
      >
        {statusMessage}
      </p>
    {/if}
  </div>

  <div class="text-xs text-fg-muted space-y-1 pt-2">
    <p>
      Get your key at <span class="text-accent">platform.openai.com/api-keys</span
      >
    </p>
    <p>Stored locally in <span class="text-fg-dim">.env</span> file</p>
  </div>
</div>
