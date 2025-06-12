<script>
    import { page } from '$app/stores';
    import XianWalletUtils from '$lib/xianDappUtils.mjs';
    import { getMasterNode } from '$lib/config';
    import { walletAddressElementValue, currentUserFullAddress } from "$lib/store"; 
    import { handleWalletError, handleWalletInfo } from '$lib/walletUtils';
    import { onMount, setContext } from "svelte";
    
    // Import Bulma CSS
    import 'bulma/css/bulma.min.css';

    import '../app.css'; // Import global styles

    let xianBalance = "0"; 

    $: activePath = $page.url.pathname;

    let xdu;

    onMount(async ()=>{
        const network = getMasterNode();
        XianWalletUtils.init(network);

        try {
            let info = await XianWalletUtils.requestWalletInfo();
            handleWalletInfo(info);

            //if wallet is locked, wait for a while and request again
            if (info && info.locked){
                await new Promise(resolve => setTimeout(resolve, 10000));
                info = await XianWalletUtils.requestWalletInfo();
                handleWalletInfo(info);
            }

            if (info && info.address) { 
                currentUserFullAddress.set(info.address); 
                if (!info.locked) {
                    XianWalletUtils.getBalance("currency")
                        .then(balance => {
                            xianBalance = balance
                        })
                        .catch(error => {
                            console.error("Error fetching balance:", error);
                            xianBalance = "0"; 
                        });
                } else {
                    xianBalance = "0";
                }
            } else {
                currentUserFullAddress.set(null); 
                xianBalance = "0";
            }

        } catch (error) {
            handleWalletError(error);
            currentUserFullAddress.set(null); 
            xianBalance = "0"; 
        }

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
        <div class="header-left-section"> 
            <div class="logo">OTC</div>
            <nav class="main-nav"> 
                <a href="/open-offers" class:active={activePath === '/' || activePath === '/open-offers'}>
                    <span>Open Offers</span> 
                </a>
                <a href="/create-offer" class:active={activePath === '/create-offer'}>
                    <span>Create Offer</span> 
                </a>
            </nav>
        </div>
        
        {#if $walletAddressElementValue}
            <div class="wallet-balance">
                {$walletAddressElementValue} | {xianBalance} 
            </div>
        {:else}
             <div class="wallet-balance">
                Wallet Not Connected 
            </div>
        {/if}
    </header>

    <main class="main-content">
        <slot />
    </main>

    <footer class="app-footer">
        <p>© {new Date().getFullYear()} OTC Platform</p>
    </footer>
</div>

<style>
    .app-container {
        display: flex;
        flex-direction: column;
        min-height: 100vh;
        max-width: 1000px; 
        margin: 0 auto;    
        padding: 0 1rem;   
        box-sizing: border-box; 
    }

    .app-header {
        display: flex;
        justify-content: space-between; 
        align-items: center;
        padding: 1rem 0;
        border-bottom: 1px solid #d0d9e0; /* Updated */
        gap: 1rem; /* Adds some space between flex items, helps with responsiveness */
    }

    .header-left-section { 
        display: flex;
        align-items: center;
        min-width: 0; /* Allow this section to shrink if nav items are too wide */
        flex-shrink: 1; /* Allow shrinking, higher value means it shrinks more readily */
    }

    .logo {
        font-size: 1.8rem;
        font-weight: bold;
        margin-right: 1rem; /* Slightly reduced margin */
        flex-shrink: 0; /* Logo should not shrink */
    }

    .wallet-balance {
        background-color: #e4eaf0; /* Updated */
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-size: 0.9rem;
        color: #2c3e50; /* Updated */
        /* white-space: nowrap; */ /* Removed to allow wrapping */
        min-width: 0; /* Allow this to shrink */
        flex-shrink: 1; /* Allow shrinking */
        text-align: right; /* Align text to right if it wraps */
        overflow-wrap: break-word; /* Helps break long words/numbers if necessary */
    }

    .main-nav { 
        display: flex;
        min-width: 0; /* Allow nav itself to shrink if its content is too wide */
        flex-shrink: 1; /* Allow nav to shrink */
    }

    .main-nav a { 
        padding: 0.8rem 1rem; /* Slightly reduced horizontal padding */
        text-decoration: none;
        color: #566573; /* Updated */
        font-weight: 500;
        border-bottom: 3px solid transparent; 
        transition: color 0.2s ease; 
        text-align: center;
        white-space: nowrap; 
        position: relative; 
    }

    .main-nav a span {
        position: relative; 
        display: inline-block; 
    }

    .main-nav a:not(:last-child) {
        margin-right: 0.25rem; /* Slightly reduced margin */
    }

    .main-nav a:hover { 
        color: #3498db; /* Updated */
        text-decoration: none; 
    }

    .main-nav a.active { 
        color: #3498db; /* Updated */
    }

    .main-nav a.active span::after {
        content: '';
        position: absolute;
        left: 0;
        width: 100%; 
        height: 3px;
        background-color: #3498db; /* Updated */
        top: calc(100% + 0.8rem); 
    }


    .main-content {
        flex-grow: 1; 
        padding: 1.5rem 0; 
    }

    .app-footer {
        text-align: center;
        padding: 1rem 0;
        margin-top: 2rem;
        font-size: 0.85rem;
        color: #7f8c8d; /* Updated */
        border-top: 1px solid #d0d9e0; /* Updated */
    }

     :global(button) {
        padding: 0.6rem 1.2rem;
        border-radius: 4px;
        border: 1px solid transparent;
        font-size: 1rem;
        cursor: pointer;
        transition: background-color 0.2s ease, border-color 0.2s ease, transform 0.1s ease, filter 0.1s ease; 
        background-color: #3498db; /* Updated */
        color: white;
        border-color: #3498db; /* Updated */
        margin-top: 0.5rem;
    }
    :global(button:hover:not(:disabled)) { 
        background-color: #2980b9; /* Updated */
        border-color: #2980b9; /* Updated */
    }
    :global(button:active:not(:disabled)) { 
        transform: translateY(1px);
        filter: brightness(95%);
    }
    :global(button:disabled) {
        background-color: #e9ecef; /* Updated */
        border-color: #d0d9e0; /* Updated */
        cursor: not-allowed;
        color: #566573; /* Updated */
    }

    :global(input[type="text"]),
    :global(input[type="number"]) {
        width: 100%;
        padding: 0.75rem;
        border: 1px solid #d0d9e0; /* Updated */
        border-radius: 4px;
        font-size: 1rem;
        box-sizing: border-box;
        margin-bottom: 1rem;
    }
    :global(label) {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 500;
        color: #2c3e50; /* Updated */
    }

    /* Responsive adjustments for smaller screens */
    @media (max-width: 600px) {
        .logo {
            font-size: 1.5rem; /* Smaller logo */
            margin-right: 0.5rem;
        }
        .main-nav a {
            padding: 0.8rem 0.5rem; /* Less horizontal padding for nav links */
            font-size: 0.9rem; /* Slightly smaller font for nav links */
        }
        .main-nav a.active span::after {
             top: calc(100% + 0.8rem); /* Ensure underline position is consistent with padding */
        }
        .wallet-balance {
            font-size: 0.8rem; /* Smaller font for wallet info */
            padding: 0.4rem 0.6rem;
        }
        .app-header {
            gap: 0.5rem; /* Reduce gap on smaller screens */
        }
    }

</style>