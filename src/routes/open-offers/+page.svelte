<script>
    import Modal from '$lib/components/Modal.svelte';
    import { transactionInfo } from '$lib/store';
    import { handleTransaction, handleTransactionError } from '$lib/walletUtils';
    import { config } from '$lib/config'; // Import config for fee percentage
    import { onMount, getContext } from 'svelte';
    import { getOpenListedOffers } from '$lib/graphql/queries.js';
    import { fetchOpenOffers } from '$lib/graphql/process.js';

    const { xdu } = getContext('app_functions');

    let paginatedOffers = [];
    let selectedOffer = null;
    let showTakeModal = false;
    let loading = true;
    let errorLoading = null;

    const itemsPerPage = 25;
    let currentPage = 1;
    let hasMorePages = true;

    async function loadOffers(page = 1) {
        loading = true;
        errorLoading = null;

        try {
            const offset = (page - 1) * itemsPerPage;
            const query = getOpenListedOffers(offset, itemsPerPage);
            const offers = await fetchOpenOffers(query);

            if (offers) {
                paginatedOffers = offers;
                hasMorePages = offers.length === itemsPerPage;
            } else {
                paginatedOffers = [];
                hasMorePages = false;
                errorLoading = "Failed to load offers. Check console for details.";
            }

        } catch (err) {
            console.error("Error loading offers:", err);
            errorLoading = `Failed to load offers: ${err.message}`;
            paginatedOffers = [];
            hasMorePages = false;
        } finally {
            loading = false;
        }
    }

    onMount(() => {
        loadOffers(currentPage);
    });

    // handleTakeOfferClick remains the same
    function handleTakeOfferClick(offer) {
        if (!offer || !offer.id || !offer.take_token || offer.take_amount == null) {
            console.error("Invalid offer data selected:", offer);
            handleTransactionError("Cannot take offer: Invalid offer data.");
            return;
        }
        selectedOffer = offer;
        transactionInfo.set({});
        showTakeModal = true;
    }

    function handleCloseModal() {
        showTakeModal = false;
        selectedOffer = null;
        transactionInfo.set({});
    }

    // --- MODIFIED: handleTakeConfirm ---
    // Adds fee calculation to the approval amount
    async function handleTakeConfirm() {
        if (!selectedOffer) {
            console.error("handleTakeConfirm called without a selected offer.");
            handleTransactionError("No offer selected. Please try again.");
            handleCloseModal();
            return;
        }

        console.log(`Confirmed taking offer ${selectedOffer.id}. Initiating approve and take sequence...`);

        try {
            // --- START: Fee Calculation for Taker Approval ---
            const tokenToApprove = selectedOffer.take_token;
            const baseTakeAmount = parseFloat(selectedOffer.take_amount); // Base amount needed

            if (isNaN(baseTakeAmount) || baseTakeAmount <= 0) {
                throw new Error(`Invalid take_amount for approval calculation: ${selectedOffer.take_amount}`);
            }

            // Calculate amount including fee, similar to create-offer
            const feeMultiplier = 1 + config.otcFeePercentage;
            const rawRequiredAmount = baseTakeAmount * feeMultiplier;

            // Round UP to the nearest whole number (or contract's precision unit)
            const amountToApprove = Math.ceil(rawRequiredAmount);

            console.log(`Base take amount: ${baseTakeAmount}`);
            console.log(`Raw required (incl. fee): ${rawRequiredAmount}`);
            console.log(`Amount to approve (Ceiling): ${amountToApprove}`);
            // --- END: Fee Calculation for Taker Approval ---

            // 2. Prepare and Store APPROVE data with CALCULATED amount
            const approveTxData = {
                method: "approve",
                kwargs: {
                    to: config.otcContract,     // Approve the OTC contract
                    amount: amountToApprove     // Approve the calculated amount of take_token
                }
            };
            transactionInfo.set(approveTxData); // Update store for approval

            console.log("Sending Approve Tx:", {
                contract: tokenToApprove,       // Send approve TO THE TOKEN contract
                data: $transactionInfo
            });

            // 3. Send APPROVE transaction
            const approveResponse = await xdu().sendTransaction(
                tokenToApprove,
                $transactionInfo.method,
                $transactionInfo.kwargs
            ).catch(err => {
                 handleTransactionError(err);
                 throw err; // Stop sequence on error
            });

            // Handle immediate errors
             if (approveResponse && approveResponse.errors) {
                 console.error('Approve transaction failed immediately:', approveResponse.errors);
                 handleTransaction(approveResponse);
                 // Consider stopping
                 // throw new Error("Approval transaction failed.");
             } else {
                handleTransaction(approveResponse);
             }

            // 4. Wait briefly
            console.log("Waiting 500 milliseconds before sending take_offer...");
            await new Promise(resolve => setTimeout(resolve, 500));

            // 5. Prepare and Store TAKE_OFFER data
            // Arguments for take_offer itself likely don't change (just needs the ID)
            const takeOfferTxData = {
                method: "take_offer",
                kwargs: {
                    listing_id: selectedOffer.id // Use the ID from the selected offer
                }
            };
            transactionInfo.set(takeOfferTxData); // Update store for take_offer

            console.log("Sending Take Offer Tx:", {
                 contract: config.otcContract, // Send take_offer TO THE OTC contract
                 data: $transactionInfo
            });

            // 6. Send TAKE_OFFER transaction
            const takeOfferResponse = await xdu().sendTransaction(
                config.otcContract,
                $transactionInfo.method,
                $transactionInfo.kwargs
            ).catch(err => {
                 handleTransactionError(err);
                 throw err; // Stop sequence on error
            });

            // Handle immediate errors
             if (takeOfferResponse && takeOfferResponse.errors) {
                 console.error('Take Offer transaction failed immediately:', takeOfferResponse.errors);
             }
            handleTransaction(takeOfferResponse);


        } catch (error) {
            console.error("Error during take offer transaction sequence:", error);
        } finally {
            // 7. Clean up UI
            console.log("Cleaning up after take offer attempt.");
            handleCloseModal(); // Close modal, clear state
            await loadOffers(currentPage); // Reload offers
        }
    }

    // --- Pagination Functions ---
    function goToPage(pageNumber) {
        if (pageNumber >= 1) {
            currentPage = pageNumber;
            // Scroll to top when page changes
            if (typeof window !== 'undefined') {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
            loadOffers(currentPage); // Fetch data for the new page
        }
    }

    // --- Helper Functions (remain the same) ---
    function shortenAddress(address) {
        // Ensure value exists and is a string before shortening
        if (typeof address !== 'string' || address.length < 10) return address || 'N/A';
        return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
    }

    function formatNumber(num) {
        // Add check for undefined/null
        if (num === null || typeof num === 'undefined') return 'N/A';
        if (typeof num !== 'number') {
             // Try converting if it looks like a number string
            const parsedNum = parseFloat(num);
            if (isNaN(parsedNum)) return num; // Return original if not parseable
            num = parsedNum;
        }

        const decimals = num < 1 ? 6 : (num < 100 ? 4 : 2);
        return num.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: decimals
        });
    }

</script>

<svelte:head>
    <title>Open Offers - OTC</title>
</svelte:head>

<div class="offers-container">
    <h1>Open Offers</h1>

    {#if loading}
        <p class="loading-message">Loading offers...</p>
    {:else if errorLoading}
        <p class="error-message">{errorLoading}</p>
    {:else if paginatedOffers.length === 0}
        <p>No open offers found.</p>
    {:else}
        <div class="offers-list">
            {#each paginatedOffers as offer (offer.id)}
                <div class="offer-item">
                    <div class="offer-details">
                         <p><strong>Offering:</strong> {formatNumber(offer.offer_amount)} <span class="token-name">{offer.offer_token || 'N/A'}</span></p>
                         <p><strong>Requesting:</strong> {formatNumber(offer.take_amount)} <span class="token-name">{offer.take_token || 'N/A'}</span></p>
                         <p class="maker-info"><strong>Maker:</strong> {shortenAddress(offer.maker)}</p>
                         <p class="offer-id"><strong>ID:</strong> {offer.id}</p>
                         <p class="fee-info">Fee: {offer.fee !== undefined ? offer.fee + '%' : 'N/A'}</p>
                    </div>
                    <div class="offer-action">
                        <!-- Pass the whole offer object -->
                        <button on:click={() => handleTakeOfferClick(offer)}>
                            Take this offer
                        </button>
                    </div>
                </div>
            {/each}
        </div>

        <!-- Pagination Controls -->
        <div class="pagination">
            <button disabled={currentPage <= 1 || loading} on:click={() => goToPage(currentPage - 1)}>
                « Previous
            </button>
            <span>Page {currentPage}</span>
            <button disabled={!hasMorePages || loading} on:click={() => goToPage(currentPage + 1)}>
                Next »
            </button>
        </div>
    {/if}
</div>

<!-- Take Offer Confirmation Modal -->
<Modal
    bind:show={showTakeModal}
    title="Confirm Offer Take"
    message="This will initiate two transactions: 1. Approve the contract to spend your tokens required for the offer. 2. Take the offer. Continue?"
    on:confirm={handleTakeConfirm}
    on:close={handleCloseModal}
/>


<style>
    /* Styles remain largely the same */
    .offers-container { }
    h1 { margin-bottom: 1.5rem; text-align: center; }
    .offers-list { display: grid; gap: 1rem; }
    .offer-item { background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 1rem 1.5rem; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: box-shadow 0.2s ease; }
    .offer-item:hover { box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .offer-details p { margin: 0.4rem 0; line-height: 1.5; color: #333; word-break: break-word; }
    .offer-details strong { color: #1a1a1a; }
    .token-name { font-family: monospace; background-color: #f0f0f0; padding: 0.1rem 0.4rem; border-radius: 3px; font-size: 0.9em; }
    .maker-info, .fee-info { font-size: 0.9rem; color: #555; }
    .offer-id { font-size: 0.8em; color: #777; word-break: break-all; margin-top: 0.6rem; }
    .offer-id strong { color: #555; }
    .offer-action { margin-top: 1rem; text-align: right; }
    .offer-action button { padding: 0.5rem 1rem; font-size: 0.95rem; }
    .pagination { display: flex; justify-content: center; align-items: center; margin-top: 2rem; gap: 1rem; }
    .pagination span { font-size: 0.95rem; color: #555; }
    .pagination button { padding: 0.4rem 0.8rem; }

    .loading-message, .error-message {
        text-align: center;
        padding: 2rem;
        font-size: 1.1rem;
        color: #555;
    }
    .error-message {
        color: #dc3545;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 4px;
        margin: 1rem;
    }


    @media (min-width: 600px) {
        .offer-item { flex-direction: row; align-items: center; }
        .offer-details { flex-grow: 1; margin-right: 1rem; }
        .offer-action { margin-top: 0; text-align: right; flex-shrink: 0; }
    }
</style>
