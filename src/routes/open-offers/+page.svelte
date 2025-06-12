<script>
    import Modal from '$lib/components/Modal.svelte';
    import { transactionInfo, currentUserFullAddress } from '$lib/store'; 
    import { handleTransaction, handleTransactionError } from '$lib/walletUtils';
    import { getOtcContract, getOtcFeePercentage } from '$lib/config'; 
    import { onMount, getContext } from 'svelte';
    import { getOpenListedOffers } from '$lib/graphql/queries.js';
    import { fetchOpenOffers } from '$lib/graphql/process.js';
    import { getTimeTo } from '$lib/utils';

    const { xdu } = getContext('app_functions');

    let paginatedOffers = [];
    let selectedOffer = null;
    let loading = true; 
    let errorLoading = null;
    
    let showModal = false;
    let modalTitle = "";
    let modalMessage = "";
    let modalConfirmHandler = () => {};
    let modalConfirmButtonBusy = false;

    let isTakingOffer = false; 
    let isCancellingOffer = false;

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
            console.error("Invalid offer data selected for taking:", offer);
            handleTransactionError("Cannot take offer: Invalid offer data.");
            return;
        }
        selectedOffer = offer;
        transactionInfo.set({}); 

        modalTitle = "Confirm Offer Take";
        modalMessage = "Two popup windows will show up when you press 'continue'. PATIENTLY WAIT and accept each one: [1] Give OTC contract approval [2] Take the offer.";
        modalConfirmHandler = handleTakeConfirm;
        showModal = true;
    }

    function handleCancelOfferClick(offer) {
        if (!offer || !offer.id) {
            console.error("Invalid offer data selected for cancelling:", offer);
            handleTransactionError("Cannot cancel offer: Invalid offer data.");
            return;
        }
        selectedOffer = offer;
        transactionInfo.set({}); 

        modalTitle = "Confirm Offer Cancellation";
        modalMessage = "Are you sure you want to cancel this offer? This action is irreversible. A single popup will appear for confirmation.";
        modalConfirmHandler = handleCancelConfirm;
        showModal = true;
    }


    function handleCloseModal() {
        showModal = false;
        selectedOffer = null;
        transactionInfo.set({});
    }

    async function handleTakeConfirm() {
        if (!selectedOffer) {
            console.error("handleTakeConfirm called without a selected offer.");
            handleTransactionError("No offer selected. Please try again.");
            handleCloseModal();
            return;
        }

        isTakingOffer = true; 
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
                 throw new Error('Approval transaction failed.'); 
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
        } finally {
            console.log("Cleaning up after take offer attempt.");
            isTakingOffer = false; 
            handleCloseModal(); 
            await loadOffers(currentPage); 
        }
    }

    async function handleCancelConfirm() {
        if (!selectedOffer) {
            console.error("handleCancelConfirm called without a selected offer.");
            handleTransactionError("No offer selected for cancellation. Please try again.");
            handleCloseModal();
            return;
        }

        isCancellingOffer = true;
        console.log(`Confirmed cancelling offer ${selectedOffer.id}. Initiating cancel transaction...`);

        try {
            const otcContract = getOtcContract();
            const cancelOfferTxData = {
                method: "cancel_offer",
                kwargs: {
                    listing_id: selectedOffer.id
                }
            };
            transactionInfo.set(cancelOfferTxData);

            console.log("Sending Cancel Offer Tx:", {
                contract: otcContract,
                data: $transactionInfo
            });

            const cancelOfferResponse = await xdu().sendTransaction(
                otcContract,
                $transactionInfo.method,
                $transactionInfo.kwargs
            ).catch(err => {
                handleTransactionError(err);
                throw err; 
            });
            
            if (cancelOfferResponse && cancelOfferResponse.errors) {
                console.error('Cancel Offer transaction failed immediately:', cancelOfferResponse.errors);
            }
            handleTransaction(cancelOfferResponse); 

        } catch (error) {
            console.error("Error during cancel offer transaction:", error);
        } finally {
            console.log("Cleaning up after cancel offer attempt.");
            isCancellingOffer = false;
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

    $: modalConfirmButtonBusy = isTakingOffer || isCancellingOffer;

</script>

<svelte:head>
    <title>Open Offers - OTC</title>
</svelte:head>

<div class="offers-container">
    <p class="page-description">
        Browse all currently available Over-The-Counter (OTC) offers. You can take an offer if you agree with the terms,
        or cancel an offer if you are the original creator (maker) of that offer.
        Taking an offer involves approving the token you will send and then executing the exchange.
    </p>

    {#if loading && paginatedOffers.length === 0} 
        <p class="loading-message">Loading offers...</p>
    {:else if errorLoading}
        <p class="error-message">{errorLoading}</p>
    {:else if paginatedOffers.length === 0 && !loading} 
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
                         <p class="date-listed"><strong>date-listed:</strong> {new Date(offer.date_listed).toLocaleString()} ({getTimeTo(new Date(offer.date_listed))})</p>
                         <p class="fee-info">Fee: {offer.fee !== undefined ? offer.fee + '%' : 'N/A'}</p>
                    </div>
                    <div class="offer-action">
                        {#if $currentUserFullAddress && offer.maker === $currentUserFullAddress}
                            <button 
                                on:click={() => handleCancelOfferClick(offer)} 
                                disabled={isCancellingOffer || isTakingOffer || loading}
                                class="button-cancel">
                                {#if isCancellingOffer}
                                    Processing...
                                {:else}
                                    Cancel Offer
                                {/if}
                            </button>
                        {:else}
                            <button 
                                on:click={() => handleTakeOfferClick(offer)} 
                                disabled={isTakingOffer || isCancellingOffer || loading}>
                                {#if isTakingOffer}
                                    Processing...
                                {:else}
                                    Take this offer
                                {/if}
                            </button>
                        {/if}
                    </div>
                </div>
            {/each}
        </div>

        <div class="pagination">
            <button disabled={currentPage <= 1 || loading || isTakingOffer || isCancellingOffer} on:click={() => goToPage(currentPage - 1)}>
                « Previous
            </button>
            <span>Page {currentPage} {#if loading && paginatedOffers.length > 0}(Updating...){/if}</span>
            <button disabled={!hasMorePages || loading || isTakingOffer || isCancellingOffer} on:click={() => goToPage(currentPage + 1)}>
                Next »
            </button>
        </div>
    {/if}
</div>

<Modal
    bind:show={showModal}
    title={modalTitle}
    message={modalMessage}
    on:confirm={modalConfirmHandler}
    on:close={handleCloseModal}
    confirmButtonBusy={modalConfirmButtonBusy}
/>


<style>
    .offers-container { }
    h1 { margin-bottom: 0.5rem; text-align: center; } /* Adjusted margin */
    .page-description {
        text-align: center;
        margin-bottom: 1.5rem;
        font-size: 0.95rem;
        color: #566573; /* Updated */
        max-width: 800px;
        margin-left: auto;
        margin-right: auto;
        padding: 0 1rem;
        line-height: 1.6;
    }
    .offers-list { display: grid; gap: 1rem; }
    .offer-item { background-color: #ffffff; border: 1px solid #d0d9e0; border-radius: 8px; padding: 1rem 1.5rem; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: box-shadow 0.2s ease; } /* Updated border */
    .offer-item:hover { box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .offer-details p { margin: 0.4rem 0; line-height: 1.5; color: #2c3e50; word-break: break-word; } /* Updated */
    .offer-details strong { color: #2c3e50; } /* Updated */
    .token-name { font-family: monospace; background-color: #e4eaf0; padding: 0.1rem 0.4rem; border-radius: 3px; font-size: 0.9em; } /* Updated */
    .maker-info, .fee-info { font-size: 0.9rem; color: #566573; } /* Updated */
    .offer-id { font-size: 0.8em; color: #7f8c8d; word-break: break-all; margin-top: 0.6rem; } /* Updated */
    .offer-id strong { color: #566573; } /* Updated */
    .date-listed { font-size: 0.8em; color: #7f8c8d; word-break: break-all; margin-top: 0.6rem; } /* Updated */
    .date-listed strong { color: #566573; } /* Updated */
    .offer-action { margin-top: 1rem; text-align: right; }
    .offer-action button { padding: 0.5rem 1rem; font-size: 0.95rem; }
    .offer-action button.button-cancel {
        background-color: #e74c3c;  /* Updated */
        border-color: #e74c3c; /* Updated */
        color: white; /* Ensure text is white on danger button */
    }
    .offer-action button.button-cancel:hover:not(:disabled) {
        background-color: #c0392b; /* Updated */
        border-color: #c0392b; /* Updated */
    }
     .offer-action button.button-cancel:disabled {
        background-color: #f5b7b1;  /* Updated */
        border-color: #f5b7b1; /* Updated */
        color: #943126; /* Updated */
    }

    .pagination { display: flex; justify-content: center; align-items: center; margin-top: 2rem; gap: 1rem; }
    .pagination span { font-size: 0.95rem; color: #566573; } /* Updated */
    .pagination button { padding: 0.4rem 0.8rem; }

    .loading-message, .error-message {
        text-align: center;
        padding: 2rem;
        font-size: 1.1rem;
        color: #566573; /* Updated */
    }
    .error-message {
        color: #c0392b; /* Updated text color */
        background-color: #fadbd8; /* Updated background */
        border: 1px solid #f1948a; /* Updated border */
        border-radius: 4px;
        margin: 1rem;
    }


    @media (min-width: 600px) {
        .offer-item { flex-direction: row; align-items: center; }
        .offer-details { flex-grow: 1; margin-right: 1rem; }
        .offer-action { margin-top: 0; text-align: right; flex-shrink: 0; }
    }
</style>