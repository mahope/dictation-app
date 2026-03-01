<script lang="ts">
  interface Props {
    tabs: string[];
    active: number;
    onselect: (index: number) => void;
  }
  let { tabs, active, onselect }: Props = $props();
</script>

<div class="flex border-b border-bg-hover">
  {#each tabs as tab, i}
    <button
      class="px-5 py-2.5 text-sm font-medium transition-colors relative
        {active === i
        ? 'text-accent'
        : 'text-fg-dim hover:text-fg'}"
      onclick={() => onselect(i)}
    >
      {tab}
      {#if active === i}
        <div
          class="absolute bottom-0 left-0 right-0 h-0.5 bg-accent rounded-full"
        ></div>
      {/if}
    </button>
  {/each}
</div>
