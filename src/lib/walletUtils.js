import { walletAddressElementValue } from "./store";
import * as bulmaToast from "bulma-toast";

const showToast = (message, type) => {
    bulmaToast.toast({
        message,
        type,
        position: "top-center",
        duration: 5000
    });
}

export const handleWalletInfo = (info) => {
    // Add null check for info as well for safety
    if (!info) {
        console.error("handleWalletInfo received null info");
        showToast("Could not retrieve wallet information.", "is-danger");
        return;
    }

    if (info.locked) {
        // walletAddressElementValue.set('Wallet is Locked');
        showToast("Please unlock your wallet to interact with this dapp.", "is-warning");
    }
}


export const handleWalletError = (error) => {
    // Make error message more generic as it catches more than just missing extension now
    console.error("Wallet interaction error:", error); // Log the actual error
    showToast("Ensure the Xian Wallet extension is installed and unlocked", "is-danger");
    walletAddressElementValue.set('Wallet Error'); // More generic error state
}


export const handleTransaction = (response) => {
    // --- START FIX ---
    // Check if response is null or undefined first
    if (!response) {
        console.error('Transaction status check failed: No response received.');
        // Provide feedback that the status couldn't be confirmed
        // showToast("Transaction failed: Could not confirm status.", "is-danger");
        return;
    }
    // --- END FIX ---

    // Now it's safe to access response.errors
    // Line 27 logic:
    if (response.errors) {
        console.error('Transaction failed:', response.errors);
        // Try to make error message slightly more user-friendly if possible
        const errorMsg = typeof response.errors === 'string' ? response.errors : JSON.stringify(response.errors);
        showToast("Transaction failed: " + errorMsg, "is-danger");
        return;
    }

    // If response exists and has no 'errors' property, assume submitted/successful
    console.log('Transaction submitted/succeeded:', response);
    // Maybe adjust wording slightly, as it might just be submitted, not fully confirmed yet
    showToast("Transaction submitted successfully", "is-success");
}


export const handleTransactionError = (error) => {
    // This catches errors *before* a response is received (e.g., network error during send)
    // or errors explicitly thrown.
    console.error('Transaction submission error:', error);
    const errorMsg = error instanceof Error ? error.message : JSON.stringify(error);
    showToast("Transaction error: " + errorMsg, "is-danger");
}