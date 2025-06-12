<script>
    import { createEventDispatcher } from 'svelte';

    export let show = false;
    export let title = "Confirmation";
    export let message = "Are you sure?";
    export let confirmButtonBusy = false; // New prop for loading state of confirm button

    const dispatch = createEventDispatcher();

    function handleConfirm() {
        if (confirmButtonBusy) return; // Prevent action if already busy
        dispatch('confirm');
    }

    function handleClose() {
        // Ensure show is set to false if closed via Escape key or backdrop
        show = false; 
        dispatch('close');
    }

    // Close modal if clicking outside the content area
    function handleBackdropClick(event) {
        if (event.target === event.currentTarget) {
            handleClose();
        }
    }

    // Close modal on Escape key press - NOW CHECKS 'show' internally
    function handleKeydown(event) {
        if (show && event.key === 'Escape') {
            handleClose();
        }
    }
</script>

<svelte:window on:keydown={handleKeydown}/>

{#if show}
<!-- svelte-ignore a11y-click-events-have-key-events -->
<div class="modal-backdrop" on:click={handleBackdropClick}>
    <div class="modal-content" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <h2 id="modal-title">{title}</h2>
        <p>{message}</p>
        <div class="modal-actions">
            <button class="button-secondary" on:click={handleClose} disabled={confirmButtonBusy}>Cancel</button>
            <button class="button-primary" on:click={handleConfirm} disabled={confirmButtonBusy}>
                {#if confirmButtonBusy}
                    Processing...
                {:else}
                    Continue
                {/if}
            </button>
        </div>
        <button class="modal-close-btn" on:click={handleClose} aria-label="Close modal" disabled={confirmButtonBusy}>×</button>
    </div>
</div>
{/if}

<style>
    .modal-backdrop {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.6);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
        padding: 1rem; 
    }

    .modal-content {
        background-color: #ffffff; /* Updated */
        padding: 2rem;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        max-width: 500px;
        width: 100%;
        position: relative;
        color: #2c3e50; /* Updated */
    }

    .modal-close-btn {
        position: absolute;
        top: 10px;
        right: 15px;
        background: none;
        border: none;
        font-size: 1.8rem;
        cursor: pointer;
        color: #7f8c8d; /* Updated */
        line-height: 1;
    }
    .modal-close-btn:hover:not(:disabled) {
        color: #2c3e50; /* Updated */
    }
    .modal-close-btn:disabled {
        cursor: not-allowed;
        color: #566573; /* Updated */
    }


    h2 {
        margin-top: 0;
        margin-bottom: 1rem;
        color: #2c3e50; /* Updated */
    }

    p {
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }

    .modal-actions {
        display: flex;
        justify-content: flex-end;
        gap: 1rem; 
    }

     button {
        padding: 0.6rem 1.2rem;
        border-radius: 4px;
        border: 1px solid transparent;
        font-size: 1rem;
        cursor: pointer;
        transition: background-color 0.2s ease, border-color 0.2s ease, transform 0.1s ease, filter 0.1s ease;
    }

    .button-primary {
        background-color: #3498db; /* Updated */
        color: white;
        border-color: #3498db; /* Updated */
    }
    .button-primary:hover:not(:disabled) {
        background-color: #2980b9; /* Updated */
        border-color: #2980b9; /* Updated */
    }
    .button-primary:active:not(:disabled) {
        transform: translateY(1px);
        filter: brightness(95%);
    }
    .button-primary:disabled {
        background-color: #a9cce3; /* Updated */
        border-color: #a9cce3; /* Updated */
        color: #566573; /* Updated for contrast */
        cursor: not-allowed;
    }


     .button-secondary {
        background-color: #e9ecef; /* Updated */
        color: #2c3e50; /* Updated */
        border: 1px solid #ced4da; /* Updated */
    }
     .button-secondary:hover:not(:disabled) {
        background-color: #d4dae0; /* Updated */
        border-color: #ced4da; /* Updated */
    }
    .button-secondary:active:not(:disabled) {
        transform: translateY(1px);
        filter: brightness(95%);
    }
    .button-secondary:disabled {
        background-color: #e9ecef; /* Consistent with new disabled BG */
        border-color: #d0d9e0; /* Consistent with new disabled border */
        color: #566573; /* Consistent with new disabled text */
        cursor: not-allowed;
    }
</style>