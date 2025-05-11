<script lang="ts">
  import './app.css';

  let character1 = '';
  let character2 = '';
  let resultText = '';
  let battleInProgress = false;
  let errorOccurred = false;

  async function startBattle() {
    if (!character1.trim() || !character2.trim()) {
      return;
    }

    battleInProgress = true;
    errorOccurred = false;
    resultText = '';

    try {
      const response = await fetch('/battle', { // Assuming the backend API is at /battle
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ character1: character1.trim(), character2: character2.trim() }),
      });

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`Battle request failed: ${response.status} ${errorData}`);
      }

      const data = await response.json();
      resultText = `Winner: ${data.winner}\n\nReasoning: ${data.reasoning}`;
    } catch (error: any) {
      errorOccurred = true;
      resultText = `Error: Failed to get battle results. ${error.message}`;
      console.error('Error:', error);
    } finally {
      battleInProgress = false;
    }
  }

  $: battleButtonDisabled = !character1.trim() || !character2.trim() || battleInProgress;
</script>

<main class="h-screen bg-gradient-to-br from-slate-900 to-slate-800 px-4 sm:px-6 lg:px-8 text-white flex flex-col items-center justify-center">
  <div class="max-w-md w-full bg-slate-800 rounded-xl shadow-2xl overflow-hidden p-8 space-y-8">
    <div class="text-center">
      <h1 class="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-500 to-red-500">
        PowerScaler Battle Arena
      </h1>
      <p class="mt-3 text-lg text-slate-400">Who would win in a fight?</p>
    </div>

    <form on:submit|preventDefault={startBattle} class="space-y-6">
      <div>
        <label for="character1" class="block text-sm font-medium text-slate-300 mb-1">Character 1</label>
        <input
          type="text"
          id="character1"
          bind:value={character1}
          class="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-3 placeholder-slate-500"
          placeholder="Enter first challenger"
          disabled={battleInProgress}
        />
      </div>

      <div>
        <label for="character2" class="block text-sm font-medium text-slate-300 mb-1">Character 2</label>
        <input
          type="text"
          id="character2"
          bind:value={character2}
          class="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-3 placeholder-slate-500"
          placeholder="Enter second challenger"
          disabled={battleInProgress}
        />
      </div>

      <button
        type="submit"
        disabled={battleButtonDisabled}
        class="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white 
               bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 
               focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-800 focus:ring-indigo-500 
               disabled:opacity-50 disabled:cursor-not-allowed transition-opacity duration-300"
      >
        {#if battleInProgress}
          Analyzing Battle...
        {:else}
          Start Battle!
        {/if}
      </button>
    </form>

    {#if resultText}
      <div class="mt-6 p-5 bg-slate-700 rounded-md shadow">
        <h2 class="text-xl font-semibold mb-3 text-center {errorOccurred ? 'text-red-400' : 'text-green-400'}">
          {errorOccurred ? 'Battle Error' : 'Battle Result'}
        </h2>
        <pre class="whitespace-pre-wrap text-sm text-slate-300 bg-slate-600 p-4 rounded-md overflow-x-auto">{resultText}</pre>
      </div>
    {/if}
  </div>
</main>

<style>
  /* You can add any additional global styles or overrides here if needed, */
  /* but prefer Tailwind utility classes for most styling. */
  pre {
    /* Ensure preformatted text wraps nicely and is scrollable if too long */
    white-space: pre-wrap;
    word-wrap: break-word;
    max-height: 300px; /* Example max height */
    overflow-y: auto;
  }
</style>
