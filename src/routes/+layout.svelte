<script>
    import { page } from '$app/stores';
    import XianWalletUtils from '$lib/xianDappUtils.mjs';
    import { getMasterNode } from '$lib/config';
    import { walletAddressElementValue, currentUserFullAddress } from "$lib/store"; 
    import { handleWalletError, handleWalletInfo } from '$lib/walletUtils';
    import { onMount, setContext, onDestroy } from "svelte"; 
    
    // Import Bulma CSS
    import 'bulma/css/bulma.min.css';

    import '../app.css'; // Import global styles

    let xianBalance = "0"; 
    let connectWalletState = "Connect Wallet";

    $: activePath = $page.url.pathname;

    let xdu;

    // Hamburger menu state and functions
    let isMobileMenuOpen = false;
    const mobileBreakpoint = 767; 
    let windowWidth = 0;

    function toggleMobileMenu() {
        isMobileMenuOpen = !isMobileMenuOpen;
    }

    function closeMobileMenu() {
        if (isMobileMenuOpen) {
            isMobileMenuOpen = false;
        }
    }

    function handleResize() {
        if (typeof window !== 'undefined') {
            windowWidth = window.innerWidth;
            if (windowWidth > mobileBreakpoint && isMobileMenuOpen) {
                closeMobileMenu();
            }
        }
    }


    onMount(async ()=>{
        if (typeof window !== 'undefined') {
            windowWidth = window.innerWidth;
            window.addEventListener('resize', handleResize);
        }

        const network = getMasterNode();
        XianWalletUtils.init(network);

        try {
            let info = await XianWalletUtils.requestWalletInfo();
            handleWalletInfo(info);

        } catch (error) {
            handleWalletError(error);
        }

        xdu = XianWalletUtils;
    });

    onDestroy(() => {
        if (typeof window !== 'undefined') {
            window.removeEventListener('resize', handleResize);
        }
    });

    const connectWallet = async()=>{
        connectWalletState = "Connecting..."
        try {
            let info = await XianWalletUtils.requestWalletInfo();
            handleWalletInfo(info);

            if (info && info.address) {  
                if (!info.locked) {
                    XianWalletUtils.getBalance("currency")
                        .then(async (balance) => {
                            await new Promise((resolve)=>setTimeout(resolve, 500))
                            walletAddressElementValue.set(info.address.slice(0, 4) + '...' + info.address.slice(61, 64));
                            currentUserFullAddress.set(info.address);
                            xianBalance = balance
                        })
                        .catch(error => {
                            console.error("Error fetching balance:", error);
                        });
                }
            }
        } catch (error) {
            handleWalletError(error);
        }
    }

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
            <button 
                class="hamburger-menu" 
                on:click={toggleMobileMenu} 
                aria-label="Toggle menu" 
                aria-expanded={isMobileMenuOpen}
                aria-controls="mobile-navigation"
            >
                <span class="hamburger-icon-bar"></span>
                <span class="hamburger-icon-bar"></span>
                <span class="hamburger-icon-bar"></span>
            </button>
            <nav class="main-nav desktop-nav"> 
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
             <button class="wallet-balance" on:click={connectWallet}>
                {connectWalletState} 
             </button>
        {/if}
    </header>

    {#if isMobileMenuOpen}
    <nav class="mobile-nav" id="mobile-navigation">
        <a href="/open-offers" class:active={activePath === '/' || activePath === '/open-offers'} on:click={closeMobileMenu}>
            Open Offers
        </a>
        <a href="/create-offer" class:active={activePath === '/create-offer'} on:click={closeMobileMenu}>
            Create Offer
        </a>
    </nav>
    {/if}

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
        border-bottom: 1px solid #d0d9e0; 
        gap: 1rem; 
    }

    .header-left-section { 
        display: flex;
        align-items: center;
        min-width: 0; 
        flex-shrink: 1; 
    }

    .logo {
        font-size: 1.8rem;
        font-weight: bold;
        margin-right: 1rem; 
        flex-shrink: 0; 
    }

    .wallet-balance {
        background-color: #e4eaf0; 
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-size: 0.9rem;
        color: #2c3e50; 
        min-width: 0; 
        flex-shrink: 1; 
        text-align: right; 
        overflow-wrap: break-word; 
    }

    .desktop-nav { 
        display: flex; 
        min-width: 0; 
        flex-shrink: 1; 
    }

    .desktop-nav a { 
        padding: 0.8rem 1rem; 
        text-decoration: none;
        color: #566573; 
        font-weight: 500;
        border-bottom: 3px solid transparent; 
        transition: color 0.2s ease; 
        text-align: center;
        white-space: nowrap; 
        position: relative; 
    }

    .desktop-nav a span {
        position: relative; 
        display: inline-block; 
    }

    .desktop-nav a:not(:last-child) {
        margin-right: 0.25rem; 
    }

    .desktop-nav a:hover { 
        color: #3498db; 
        text-decoration: none; 
    }

    .desktop-nav a.active { 
        color: #3498db; 
    }

    .desktop-nav a.active span::after {
        content: '';
        position: absolute;
        left: 0;
        width: 100%; 
        height: 3px;
        background-color: #3498db; 
        top: calc(100% + 0.8rem); 
    }

    /* Hamburger Menu Button Styles */
    .hamburger-menu {
        display: none; 
        background: none;
        border: none;
        cursor: pointer;
        padding: 10px; 
        margin: 0; 
        margin-left: 0.5rem; 
        align-self: center; 
        order: 1; 
        flex-direction: column; /* Ensures bars stack vertically */
        /* Removed justify-content: space-between and min-height */
        box-sizing: border-box; /* Changed from content-box for more predictable padding behavior */
    }

    /* Styles for each bar of the hamburger icon */
    .hamburger-menu .hamburger-icon-bar {
        display: block; 
        width: 22px;
        height: 2px;
        background-color: #2c3e50; 
        margin: 0; 
    }
     .hamburger-menu .hamburger-icon-bar + .hamburger-icon-bar {
        margin-top: 3px; /* Reduced space between bars */
    }


    /* Mobile Navigation Menu Styles */
    .mobile-nav {
        display: flex; 
        flex-direction: column;
        width: 100%;
        background-color: #ffffff; 
        border-bottom: 1px solid #d0d9e0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
    }

    .mobile-nav a {
        padding: 1rem;
        text-decoration: none;
        color: #566573; 
        font-weight: 500;
        text-align: left;
        border-bottom: 1px solid #e9ecef; 
        transition: background-color 0.2s ease, color 0.2s ease;
    }
    .mobile-nav a:last-child {
        border-bottom: none;
    }
    .mobile-nav a:hover,
    .mobile-nav a.active {
        color: #3498db; 
        background-color: #f0f4f8; 
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
        color: #7f8c8d; 
        border-top: 1px solid #d0d9e0; 
    }

     :global(button) {
        padding: 0.6rem 1.2rem;
        border-radius: 4px;
        border: 1px solid transparent;
        font-size: 1rem;
        cursor: pointer;
        transition: background-color 0.2s ease, border-color 0.2s ease, transform 0.1s ease, filter 0.1s ease; 
        background-color: #3498db; 
        color: white;
        border-color: #3498db; 
        margin-top: 0.5rem;
    }
    :global(button:hover:not(:disabled)) { 
        background-color: #2980b9; 
        border-color: #2980b9; 
    }
    :global(button:active:not(:disabled)) { 
        transform: translateY(1px);
        filter: brightness(95%);
    }
    :global(button:disabled) {
        background-color: #e9ecef; 
        border-color: #d0d9e0; 
        cursor: not-allowed;
        color: #566573; 
    }

    :global(input[type="text"]),
    :global(input[type="number"]) {
        width: 100%;
        padding: 0.75rem;
        border: 1px solid #d0d9e0; 
        border-radius: 4px;
        font-size: 1rem;
        box-sizing: border-box;
        margin-bottom: 1rem;
    }
    :global(label) {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 500;
        color: #2c3e50; 
    }

    @media (max-width: 767px) { 
        .desktop-nav {
            display: none; 
        }
        .hamburger-menu {
            display: inline-flex; 
        }
        .header-left-section {
            flex-grow: 1; 
        }
        .wallet-balance {
            flex-shrink: 0; 
        }
    }

    @media (max-width: 600px) {
        .logo {
            font-size: 1.5rem; 
            margin-right: 0.5rem;
        }
        .desktop-nav a.active span::after {
             top: calc(100% + 0.8rem); 
        }
        .wallet-balance {
            font-size: 0.8rem; 
            padding: 0.4rem 0.6rem;
            white-space: normal; 
        }
        .app-header {
            gap: 0.5rem; 
        }
        .hamburger-menu {
            margin-left: 0.25rem; 
        }
    }

</style>