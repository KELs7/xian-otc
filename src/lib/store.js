import { writable } from "svelte/store";

export const networkType = writable("testnet");
export const walletAddressElementValue = writable(null);
export const transactionInfo = writable({});
export const currentUserFullAddress = writable(null);