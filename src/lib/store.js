import { writable } from "svelte/store";

export const walletAddressElementValue = writable("Connecting...");
export const transactionInfo = writable({});