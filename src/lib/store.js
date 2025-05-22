import { writable } from "svelte/store";

export const networkType = writable("testnet");
export const walletAddressElementValue = writable("Connecting...");
export const transactionInfo = writable({});