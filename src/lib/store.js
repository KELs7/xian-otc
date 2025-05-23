import { writable } from "svelte/store";

export const networkType = writable("mainnet");
export const walletAddressElementValue = writable("Connecting...");
export const transactionInfo = writable({});