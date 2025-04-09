<script>
    import Modal from '$lib/components/Modal.svelte';
    import { goto } from '$app/navigation';
    import { transactionInfo } from '$lib/store';
    import { config } from '$lib/config'; // Ensure config is imported
    import { handleTransaction, handleTransactionError } from '$lib/walletUtils';
    import { getContext } from 'svelte';

    const { xdu } = getContext('app_functions');

    let offerTokenName = '';
    let offerAmount = null; // User input (can be float)
    let takeTokenName = '';
    let takeAmount = null;

    let showListModal = false;
    let formError = '';

    // Basic form validation (remains the same)
    $: formValid =
        offerTokenName.trim().startsWith('con_') &&
        offerAmount > 0 &&
        takeTokenName.trim().startsWith('con_') &&
        takeAmount > 0 &&
        offerTokenName.trim() !== takeTokenName.trim();

    // This function now only validates and shows the modal
    // Transaction data preparation happens in handleListConfirm
    function validateAndShowModal() {
        formError = ''; // Clear previous errors
        if (!offerTokenName.trim().startsWith('con_')) {
             formError = 'Offer token name must start with "con_".';
             return;
        }
        if (!takeTokenName.trim().startsWith('con_')) {
             formError = 'Take token name must start with "con_".';
             return;
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
            // Don't set transactionInfo here anymore
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
        console.log("Confirmed listing. Initiating approve and list sequence...");

        let approvalSent = false;

        try {
            // --- START: Fee Calculation & Rounding ---
            const baseOfferAmount = parseFloat(offerAmount); // Get the numeric value
            if (isNaN(baseOfferAmount) || baseOfferAmount <= 0) {
                throw new Error("Invalid Offer Amount for calculation.");
            }

            const feeMultiplier = 1 + config.otcFeePercentage;
            const rawRequiredAmount = baseOfferAmount * feeMultiplier;

            // Use Math.ceil() to round UP to the nearest whole number,
            // mimicking likely contract integer math requirement.
            const amountToApprove = Math.ceil(rawRequiredAmount);

            console.log(`Base amount: ${baseOfferAmount}`);
            console.log(`Raw required (incl. fee): ${rawRequiredAmount}`);
            console.log(`Amount to approve (Ceiling): ${amountToApprove}`);
            // --- END: Fee Calculation & Rounding ---


            // 1. Prepare and Store APPROVE data with the CEILING amount
            const approveTxData = {
                method: "approve",
                kwargs: {
                    to: config.otcContract,
                    amount: amountToApprove // Use the rounded-up amount
                }
            };
            transactionInfo.set(approveTxData);

            const tokenContractToApprove = offerTokenName.trim();

            console.log("Sending Approve Tx:", {
                contract: tokenContractToApprove,
                data: $transactionInfo
            });

            // 2. Send APPROVE transaction
            const approveResponse = await xdu().sendTransaction(
                tokenContractToApprove,
                $transactionInfo.method,
                $transactionInfo.kwargs
            ).catch(err => {
                 handleTransactionError(err);
                 throw err;
            });
            approvalSent = true;

            // Handle immediate errors
            if (approveResponse && approveResponse.errors) {
                 console.error('Approve transaction failed immediately:', approveResponse.errors);
                 handleTransaction(approveResponse);
                 // Consider stopping if approval fails immediately
                 // throw new Error("Approval transaction failed immediately.");
            } else {
                handleTransaction(approveResponse);
            }


            // 3. Wait 500 millisecond
            console.log("Waiting 1 second before sending list_offer...");
            await new Promise(resolve => setTimeout(resolve, 500));


            // 4. Prepare and Store LIST_OFFER data
            // Pass the ORIGINAL, un-rounded baseOfferAmount here.
            // The contract uses this to calculate the listing details.
            const listOfferTxData = {
                method: "list_offer",
                kwargs: {
                    offer_token: offerTokenName.trim(),
                    offer_amount: baseOfferAmount, // Use original float/decimal amount
                    take_token: takeTokenName.trim(),
                    take_amount: takeAmount
                }
            };
            transactionInfo.set(listOfferTxData);

            console.log("Sending List Offer Tx:", {
                 contract: config.otcContract,
                 data: $transactionInfo
            });

            // 5. Send LIST_OFFER transaction
            const listOfferResponse = await xdu().sendTransaction(
                config.otcContract,
                $transactionInfo.method,
                $transactionInfo.kwargs
            ).catch(err => {
                 handleTransactionError(err);
                 throw err;
            });

            // Handle immediate errors
             if (listOfferResponse && listOfferResponse.errors) {
                 console.error('List Offer transaction failed immediately:', listOfferResponse.errors);
             }
            handleTransaction(listOfferResponse);

        } catch (error) {
            console.error("Error during transaction sequence:", error);
            // Toast already shown? Add specific feedback if needed.
        } finally {
            // 6. Clean up UI
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
    <h1>Create New Offer</h1>

    <form on:submit|preventDefault={validateAndShowModal}>
        <div class="form-group">
            <label for="offer-token">Offering Token Name (e.g., con_rswp_token)</label>
            <input
                id="offer-token"
                type="text"
                bind:value={offerTokenName}
                placeholder="con_..."
                required
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
            />
        </div>

        <hr class="form-divider"/>

        <div class="form-group">
            <label for="take-token">Requesting Token Name (e.g., con_usdt_token)</label>
            <input
                id="take-token"
                type="text"
                bind:value={takeTokenName}
                placeholder="con_..."
                required
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
            />
        </div>

         {#if formError}
             <p class="error-message">{formError}</p>
         {/if}

        <button type="submit" disabled={!formValid}>List Offer</button>
    </form>
</div>

<!-- List Offer Confirmation Modal -->
<Modal
    bind:show={showListModal}
    title="Confirm Offer Listing"
    message="This will initiate two transactions: 1. Approve the contract to spend your tokens. 2. List the offer. Continue?"
    on:confirm={handleListConfirm}
    on:close={handleCloseModal}
/>

<style>
    /* Styles remain the same */
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
        margin-bottom: 2rem;
    }

    .form-group {
        margin-bottom: 1.5rem;
    }

     label { }

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