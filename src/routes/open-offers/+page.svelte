<script>
    import Modal from '$lib/components/Modal.svelte';
    import { transactionInfo } from '$lib/store';
    import { handleTransaction, handleTransactionError } from '$lib/walletUtils';
    import { getOtcContract, getOtcFeePercentage } from '$lib/config'; 
    import { onMount, getContext } from 'svelte';
    import { getOpenListedOffers } from '$lib/graphql/queries.js';
    import { fetchOpenOffers } from '$lib/graphql/process.js';

    const { xdu } = getContext('app_functions');

    let paginatedOffers = [];
    let selectedOffer = null;
    let showTakeModal = false;
    let loading = true; // For loading offers list
    let errorLoading = null;
    let isTakingOffer = false; // New state for "Take Offer" processing

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
        // isTakingOffer should be reset if modal is closed prematurely, 
        // but primarily handled in handleTakeConfirm's finally block.
    }

    async function handleTakeConfirm() {
        if (!selectedOffer) {
            console.error("handleTakeConfirm called without a selected offer.");
            handleTransactionError("No offer selected. Please try again.");
            handleCloseModal();
            return;
        }

        isTakingOffer = true; // Set loading state for modal confirm button
        console.log(`Confirmed taking offer ${selectedOffer.id}. Initiating approve and take sequence...`);

        try {
            const tokenToApprove = selectedOffer.take_token;
            const baseTakeAmount = parseFloat(selectedOffer.take_amount); 

            if (isNaN(baseTakeAmount) || baseTakeAmount <= 0) {
                throw new Error(`Invalid take_amount for approval calculation: ${selectedOffer.take_amount}`);
            }

            const otcFeePercentage = getOtcFeePercentage();
            const feeMultiplier = 1 + otcFeePercentage;
            const rawRequiredAmount = baseTakeAmount * feeMultiplier;
            const amountToApprove = Math.ceil(rawRequiredAmount);

            console.log(`Base take amount: ${baseTakeAmount}`);
            console.log(`Raw required (incl. fee): ${rawRequiredAmount}`);
            console.log(`Amount to approve (Ceiling): ${amountToApprove}`);
            
            const otcContract = getOtcContract();
            const approveTxData = {
                method: "approve",
                kwargs: {
                    to: otcContract,     
                    amount: amountToApprove     
                }
            };
            transactionInfo.set(approveTxData); 

            console.log("Sending Approve Tx:", {
                contract: tokenToApprove,       
                data: $transactionInfo
            });

            const approveResponse = await xdu().sendTransaction(
                tokenToApprove,
                $transactionInfo.method,
                $transactionInfo.kwargs
            ).catch(err => {
                 handleTransactionError(err);
                 throw err; 
            });

             if (approveResponse && approveResponse.errors) {
                 console.error('Approve transaction failed immediately:', approveResponse.errors);
                 handleTransaction(approveResponse);
             } else {
                handleTransaction(approveResponse);
             }

            console.log("Waiting 500 milliseconds before sending take_offer...");
            await new Promise(resolve => setTimeout(resolve, 500));

            const takeOfferTxData = {
                method: "take_offer",
                kwargs: {
                    listing_id: selectedOffer.id 
                }
            };
            transactionInfo.set(takeOfferTxData); 

            console.log("Sending Take Offer Tx:", {
                 contract: otcContract, 
                 data: $transactionInfo
            });

            const takeOfferResponse = await xdu().sendTransaction(
                otcContract,
                $transactionInfo.method,
                $transactionInfo.kwargs
            ).catch(err => {
                 handleTransactionError(err);
                 throw err; 
            });

             if (takeOfferResponse && takeOfferResponse.errors) {
                 console.error('Take Offer transaction failed immediately:', takeOfferResponse.errors);
             }
            handleTransaction(takeOfferResponse);


        } catch (error) {
            console.error("Error during take offer transaction sequence:", error);
            // Error already handled by handleTransactionError or specific toasts
        } finally {
            console.log("Cleaning up after take offer attempt.");
            isTakingOffer = false; // Reset loading state
            handleCloseModal(); 
            await loadOffers(currentPage); 
        }
    }

    function goToPage(pageNumber) {
        if (pageNumber >= 1) {
            currentPage = pageNumber;
            if (typeof window !== 'undefined') {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
            loadOffers(currentPage); 
        }
    }

    function shortenAddress(address) {
        if (typeof address !== 'string' || address.length < 10) return address || 'N/A';
        return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
    }

    function formatNumber(num) {
        if (num === null || typeof num === 'undefined') return 'N/A';
        if (typeof num !== 'number') {
            const parsedNum = parseFloat(num);
            if (isNaN(parsedNum)) return num; 
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

    {#if loading && paginatedOffers.length === 0} <!-- Show loading only if no offers are yet displayed -->
        <p class="loading-message">Loading offers...</p>
    {:else if errorLoading}
        <p class="error-message">{errorLoading}</p>
    {:else if paginatedOffers.length === 0 && !loading} <!-- Ensure loading is false before showing no offers -->
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
                        <button on:click={() => handleTakeOfferClick(offer)} disabled={isTakingOffer || loading}>
                            Take this offer
                        </button>
                    </div>
                </div>
            {/each}
        </div>

        <div class="pagination">
            <button disabled={currentPage <= 1 || loading || isTakingOffer} on:click={() => goToPage(currentPage - 1)}>
                « Previous
            </button>
            <span>Page {currentPage} {#if loading && paginatedOffers.length > 0}(Updating...){/if}</span>
            <button disabled={!hasMorePages || loading || isTakingOffer} on:click={() => goToPage(currentPage + 1)}>
                Next »
            </button>
        </div>
    {/if}
</div>

<Modal
    bind:show={showTakeModal}
    title="Confirm Offer Take"
    message="Two popup windows will show up when you press 'continue'. PATIENTLY WAIT and accept each one: [1] Give OTC contract approval [2] Take the offer."
    on:confirm={handleTakeConfirm}
    on:close={handleCloseModal}
    confirmButtonBusy={isTakingOffer}
/>


<style>
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