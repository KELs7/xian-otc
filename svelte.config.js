import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
/** @type {import('@sveltejs/kit').Config} */
const config = {
    preprocess: vitePreprocess(),

    kit: {
        // adapter-auto only supports some environments, see https://kit.svelte.dev/docs/adapter-auto for a list.
        // If your environment is not supported or you settled on a specific environment, switch out the adapter.
        // See https://kit.svelte.dev/docs/adapters for more information about adapters.
        adapter: adapter({
            // default options are shown. On some platforms
            // these options are set automatically — see below
            pages: 'build',
            assets: 'build',
            fallback: 'index.html', // <--- ADD THIS LINE (or '404.html', see note below)
            precompress: false,
            strict: true // Keep strict: true
        }),
        // Optional: Define a base path if deploying to a subdirectory
        // paths: {
        //     base: process.env.NODE_ENV === 'production' ? '/your-repo-name' : ''
        // }
    }
};

export default config;