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
    statusMessage = "Validating with OpenAI...";
    try {
      const valid = await validateApiKey(key);
      if (valid) {
        await saveApiKey(key);
        status = "success";
        statusMessage = "Key saved and validated!";
      } else {
        status = "error";
        statusMessage = "Invalid API key";
      }
    } catch (e) {
      status = "error";
      statusMessage = `Connection error: ${e}`;
    }
  }
</script>

<div class="h-full overflow-y-auto">
  <div class="max-w-lg mx-auto px-8 py-8 space-y-6">
    <div>
      <h1 class="text-2xl font-semibold text-fg">API Key</h1>
      <p class="text-sm text-fg-dim mt-1">
        Connect your OpenAI account for speech-to-text.
      </p>
    </div>

    <div class="bg-bg-card rounded-xl border border-border p-5 space-y-4">
      <div>
        <label for="api-key-input" class="text-xs font-medium text-fg-dim uppercase tracking-wider"
          >OpenAI API Key</label
        >
        <div class="relative mt-2">
          <input
            id="api-key-input"
            type={showKey ? "text" : "password"}
            bind:value={apiKey}
            placeholder="sk-proj-..."
            class="w-full bg-bg-input text-fg rounded-lg px-4 py-2.5 pr-16
              border border-border focus:border-accent focus:outline-none
              placeholder:text-fg-muted text-sm font-mono"
          />
          <button
            class="absolute right-1.5 top-1/2 -translate-y-1/2 px-3 py-1
              text-xs text-fg-muted hover:text-fg rounded-md hover:bg-bg-hover
              transition-colors"
            onclick={() => (showKey = !showKey)}
          >
            {showKey ? "Hide" : "Show"}
          </button>
        </div>
      </div>

      <button
        class="w-full bg-accent text-bg font-medium rounded-lg py-2.5
          hover:bg-accent-hover transition-colors text-sm disabled:opacity-50"
        onclick={handleSave}
        disabled={status === "validating"}
      >
        {#if status === "validating"}
          <span class="inline-flex items-center gap-2">
            <svg
              class="w-4 h-4 animate-spin"
              viewBox="0 0 24 24"
              fill="none"
            >
              <circle
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="3"
                opacity="0.3"
              />
              <path
                d="M12 2a10 10 0 0 1 10 10"
                stroke="currentColor"
                stroke-width="3"
                stroke-linecap="round"
              />
            </svg>
            Validating...
          </span>
        {:else}
          Save & Validate
        {/if}
      </button>

      {#if status !== "idle"}
        <div
          class="flex items-center gap-2 text-sm
            {status === 'success'
            ? 'text-accent-green'
            : status === 'error'
              ? 'text-accent-red'
              : 'text-fg-dim'}"
        >
          {#if status === "success"}
            <svg
              class="w-4 h-4 shrink-0"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              ><polyline points="20 6 9 17 4 12" /></svg
            >
          {:else if status === "error"}
            <svg
              class="w-4 h-4 shrink-0"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              ><circle cx="12" cy="12" r="10" /><line
                x1="15"
                y1="9"
                x2="9"
                y2="15"
              /><line x1="9" y1="9" x2="15" y2="15" /></svg
            >
          {/if}
          {statusMessage}
        </div>
      {/if}
    </div>

    <div class="text-xs text-fg-muted space-y-1.5">
      <p>
        Get your key at
        <span class="text-accent">platform.openai.com/api-keys</span>
      </p>
      <p>Your key is stored locally in the <code class="text-fg-dim">.env</code> file and never sent anywhere except OpenAI.</p>
    </div>
  </div>
</div>
