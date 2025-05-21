<script>
    import { page } from '$app/stores';
    import XianWalletUtils from '$lib/xianDappUtils.mjs';
    import { walletAddressElementValue } from "$lib/store";
    import { handleWalletError, handleWalletInfo } from '$lib/walletUtils';
    import { onMount, setContext } from "svelte";
    import '../app.css'; // Import global styles

    let xianBalance = 0; // Keep initial default

    $: activePath = $page.url.pathname;

    let xdu;

    onMount(async ()=>{
        XianWalletUtils.init('https://node.xian.org');

        try {
            // 1. Get Wallet Info FIRST
            const info = await XianWalletUtils.requestWalletInfo();

            // 2. Process the info (this sets the walletAddressElementValue store)
            handleWalletInfo(info);

            // 3. Check if wallet is usable before fetching balance
            if (info && !info.locked) {
                // Wallet info obtained and it's NOT locked, proceed to get balance
                XianWalletUtils.getBalance("currency")
                    .then(balance => {
                        // Add a check to ensure balance is a valid number
                        const numericBalance = parseFloat(balance);
                        xianBalance = isNaN(numericBalance) ? 0 : numericBalance;
                    })
                    .catch(error => {
                        console.error("Error fetching balance:", error);
                        xianBalance = 0; // Reset to 0 on error
                    });
            } else {
                // Wallet is locked or info is missing - set balance to 0
                xianBalance = 0;
            }

        } catch (error) {
             // This catch handles errors from requestWalletInfo (e.g., wallet not installed)
            handleWalletError(error);
            xianBalance = 0; // Ensure balance is 0 if wallet isn't even detected
        }

        // Assign xdu regardless of wallet state, as it might be needed for other things
        xdu = XianWalletUtils;
    });

    setContext('app_functions', {
        xdu: () => {
            return xdu
        }
    })
</script>

<div class="app-container">
    <header class="app-header">
        <div class="logo">OTC</div>
        {#if $walletAddressElementValue}
            <div class="wallet-balance">
                <!-- Display balance. Consider formatting -->
                {$walletAddressElementValue} | {xianBalance.toLocaleString()} <!-- Example formatting -->
            </div>
        {:else}
             <div class="wallet-balance">
                Wallet Not Connected <!-- Default if store is empty/null initially -->
            </div>
        {/if}
    </header>

    <nav class="tabs">
        <a href="/open-offers" class:active={activePath === '/' || activePath === '/open-offers'}>
            Open Offers
        </a>
        <a href="/create-offer" class:active={activePath === '/create-offer'}>
            Create Offer
        </a>
    </nav>

    <main class="main-content">
        <slot />
    </main>

    <footer class="app-footer">
        <!-- Optional footer content -->
        <p>© {new Date().getFullYear()} OTC Platform</p>
    </footer>
</div>

<style>
    /* Styles remain the same */
    .app-container {
        display: flex;
        flex-direction: column;
        min-height: 100vh;
        max-width: 1000px; /* Max width for larger screens */
        margin: 0 auto;    /* Center content */
        padding: 0 1rem;   /* Padding on smaller screens */
        box-sizing: border-box; /* Include padding in width */
    }

    .app-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0;
        border-bottom: 1px solid #eee;
    }

    .logo {
        font-size: 1.8rem;
        font-weight: bold;
    }

    .wallet-balance {
        background-color: #f0f0f0;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-size: 0.9rem;
        color: #333;
    }

    .tabs {
        display: flex;
        margin: 1.5rem 0;
        border-bottom: 2px solid #eee;
    }

    .tabs a {
        padding: 0.8rem 1.5rem;
        text-decoration: none;
        color: #555;
        font-weight: 500;
        border-bottom: 3px solid transparent;
        margin-bottom: -2px; /* Align bottom border with container border */
        transition: color 0.2s ease, border-color 0.2s ease;
        text-align: center;
        flex-grow: 1; /* Make tabs share space */
    }

    .tabs a:hover {
        color: #007bff;
    }

    .tabs a.active {
        color: #007bff;
        border-bottom-color: #007bff;
    }

    .main-content {
        flex-grow: 1; /* Takes up remaining vertical space */
        padding: 1rem 0;
    }

    .app-footer {
        text-align: center;
        padding: 1rem 0;
        margin-top: 2rem;
        font-size: 0.85rem;
        color: #888;
        border-top: 1px solid #eee;
    }

     :global(button) {
        padding: 0.6rem 1.2rem;
        border-radius: 4px;
        border: 1px solid transparent;
        font-size: 1rem;
        cursor: pointer;
        transition: background-color 0.2s ease, border-color 0.2s ease;
        background-color: #007bff;
        color: white;
        border-color: #007bff;
        margin-top: 0.5rem;
    }
    :global(button:hover) {
        background-color: #0056b3;
        border-color: #0056b3;
    }
    :global(button:disabled) {
        background-color: #ccc;
        border-color: #ccc;
        cursor: not-allowed;
    }

    :global(input[type="text"]),
    :global(input[type="number"]) {
        width: 100%;
        padding: 0.75rem;
        border: 1px solid #ccc;
        border-radius: 4px;
        font-size: 1rem;
        box-sizing: border-box;
        margin-bottom: 1rem;
    }
    :global(label) {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 500;
        color: #333;
    }

</style>