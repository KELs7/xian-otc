<script>
    import Modal from '$lib/components/Modal.svelte';
    import { goto } from '$app/navigation';
    import { transactionInfo } from '$lib/store';
    import { getOtcContract, getOtcFeePercentage } from '$lib/config'; 
    import { handleTransaction, handleTransactionError } from '$lib/walletUtils';
    import { getContext } from 'svelte';

    const { xdu } = getContext('app_functions');

    let offerTokenName = '';
    let offerAmount = null; 
    let takeTokenName = '';
    let takeAmount = null;

    let showListModal = false;
    let formError = '';
    let isListingOffer = false; 

    $: formValid =
        (offerTokenName.trim().startsWith('con_') || offerTokenName.trim() === 'currency') &&
        offerAmount > 0 &&
        (takeTokenName.trim().startsWith('con_') || takeTokenName.trim() === 'currency') &&
        takeAmount > 0 && 
        offerTokenName.trim() !== takeTokenName.trim();

    function validateAndShowModal() {
        formError = ''; 
        if (!offerTokenName.trim().startsWith('con_')) {
            if (offerTokenName.trim() !== 'currency') {
                 formError = 'Offer token name must start with "con_" or be "currency".';
                 return;
            }
        }
        if (!takeTokenName.trim().startsWith('con_')) {
             if (takeTokenName.trim() !== 'currency') {
                 formError = 'Take token name must start with "con_" or be "currency".';
                 return;
            }
        }
        if (!(offerAmount > 0)) {
             formError = 'Offer amount must be positive.';
             return;
        }
        if (!(takeAmount > 0)) {
             formError = 'Take amount must be positive.';
             return;
        }
        if (offerTokenName.trim() === takeTokenName.trim()) {
             formError = 'Offer and Take tokens cannot be the same.';
             return;
         }

        if (formValid) {
            showListModal = true;
        } else {
            formError = 'Please fill all fields correctly.';
        }
    }

    function handleCloseModal() {
        showListModal = false;
        transactionInfo.set({});
    }

    async function handleListConfirm() {
        isListingOffer = true; 
        console.log("Confirmed listing. Initiating approve and list sequence...");

        let approvalSent = false;

        try {
            const baseOfferAmount = parseFloat(offerAmount); 
            if (isNaN(baseOfferAmount) || baseOfferAmount <= 0) {
                throw new Error("Invalid Offer Amount for calculation.");
            }
            const otcFeePercentage = getOtcFeePercentage();
            const feeMultiplier = 1 + otcFeePercentage;
            const rawRequiredAmount = baseOfferAmount * feeMultiplier;
            const amountToApprove = Math.ceil(rawRequiredAmount);

            console.log(`Base amount: ${baseOfferAmount}`);
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

            const tokenContractToApprove = offerTokenName.trim();

            console.log("Sending Approve Tx:", {
                contract: tokenContractToApprove,
                data: $transactionInfo
            });

            const approveResponse = await xdu().sendTransaction(
                tokenContractToApprove,
                $transactionInfo.method,
                $transactionInfo.kwargs
            ).catch(err => {
                 handleTransactionError(err);
                 throw err;
            });
            approvalSent = true;

            if (approveResponse && approveResponse.errors) {
                 console.error('Approve transaction failed immediately:', approveResponse.errors);
                 handleTransaction(approveResponse);
                 throw new Error('Approval transaction failed.'); // Stop if approval fails
            } else {
                handleTransaction(approveResponse);
            }

            console.log("Waiting 500 milliseconds before sending list_offer...");
            await new Promise(resolve => setTimeout(resolve, 500));

            const listOfferTxData = {
                method: "list_offer",
                kwargs: {
                    offer_token: offerTokenName.trim(),
                    offer_amount: baseOfferAmount, 
                    take_token: takeTokenName.trim(),
                    take_amount: takeAmount
                }
            };
            transactionInfo.set(listOfferTxData);

            console.log("Sending List Offer Tx:", {
                 contract: otcContract,
                 data: $transactionInfo
            });

            const listOfferResponse = await xdu().sendTransaction(
                otcContract,
                $transactionInfo.method,
                $transactionInfo.kwargs
            ).catch(err => {
                 handleTransactionError(err);
                 throw err;
            });

             if (listOfferResponse && listOfferResponse.errors) {
                 console.error('List Offer transaction failed immediately:', listOfferResponse.errors);
             }
            handleTransaction(listOfferResponse);

        } catch (error) {
            console.error("Error during transaction sequence:", error);
        } finally {
            isListingOffer = false; 
            console.log("Cleaning up form and closing modal.");
            offerTokenName = '';
            offerAmount = null;
            takeTokenName = '';
            takeAmount = null;
            formError = '';
            handleCloseModal();
            goto('/open-offers');
        }
    }

</script>

<svelte:head>
    <title>Create Offer - OTC</title>
</svelte:head>

<div class="create-offer-container">
    <p class="page-description">
        Use this form to create a new Over-The-Counter (OTC) offer. You specify which token you are offering,
        how much of it, which token you want in return (take token), and how much of the take token you require.
        Listing an offer involves two transactions: approving the OTC contract to handle your offered tokens,
        and then submitting the offer details to the contract.
    </p>

    <form on:submit|preventDefault={validateAndShowModal}>
        <div class="form-group">
            <label for="offer-token">Offering Token Name (e.g., con_rswp_token or currency)</label>
            <input
                id="offer-token"
                type="text"
                bind:value={offerTokenName}
                placeholder="con_... or currency"
                required
                disabled={isListingOffer}
            />
        </div>

        <div class="form-group">
            <label for="offer-amount">Offering Amount</label>
            <input
                id="offer-amount"
                type="number"
                bind:value={offerAmount}
                placeholder="e.g., 100.5"
                step="any"
                min="0.00000001"
                required
                disabled={isListingOffer}
            />
        </div>

        <hr class="form-divider"/>

        <div class="form-group">
            <label for="take-token">Requesting Token Name (e.g., con_usdt_token or currency)</label>
            <input
                id="take-token"
                type="text"
                bind:value={takeTokenName}
                placeholder="con_... or currency"
                required
                disabled={isListingOffer}
            />
        </div>

        <div class="form-group">
            <label for="take-amount">Requesting Amount</label>
            <input
                id="take-amount"
                type="number"
                bind:value={takeAmount}
                placeholder="e.g., 5500"
                step="any"
                min="0.00000001"
                required
                disabled={isListingOffer}
            />
        </div>

         {#if formError}
             <p class="error-message">{formError}</p>
         {/if}

        <button type="submit" disabled={!formValid || isListingOffer}>
            {#if isListingOffer}
                Processing...
            {:else}
                List Offer
            {/if}
        </button>
    </form>
</div>

<Modal
    bind:show={showListModal}
    title="Confirm Offer Listing"
    message="Two popup windows will show up when you press 'continue'. PATIENTLY WAIT and accept each one: [1] Give OTC contract approval [2] List your offer."
    on:confirm={handleListConfirm}
    on:close={handleCloseModal}
    confirmButtonBusy={isListingOffer}
/>

<style>
    .create-offer-container {
        max-width: 600px;
        margin: 0 auto;
        padding: 1.5rem;
        background-color: #f9f9f9;
        border-radius: 8px;
        border: 1px solid #eee;
    }

    h1 {
        text-align: center;
        margin-bottom: 0.5rem; /* Adjusted margin */
    }

    .page-description {
        text-align: center;
        margin-bottom: 2rem; /* Increased margin to space from form */
        font-size: 0.95rem;
        color: #555;
        max-width: 550px; /* Constrain width for better readability */
        margin-left: auto;
        margin-right: auto;
        line-height: 1.6;
    }

    .form-group {
        margin-bottom: 1.5rem;
    }
    
    .form-divider {
        border: none;
        border-top: 1px dashed #ccc;
        margin: 2rem 0;
    }

    button[type="submit"] {
        width: 100%;
        padding: 0.8rem;
        font-size: 1.1rem;
        margin-top: 1rem;
    }

     .error-message {
         color: #dc3545;
         background-color: #f8d7da;
         border: 1px solid #f5c6cb;
         padding: 0.75rem 1.25rem;
         margin-bottom: 1rem;
         border-radius: 4px;
         font-size: 0.95rem;
     }
</style>