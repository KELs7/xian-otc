# Xian OTC Interface (xian-otc)

A simple, mobile-friendly Over-The-Counter (OTC) exchange web interface built with SvelteKit (using Svelte 4). This application allows users to list and take simple token swap offers by interacting with a designated OTC smart contract via the Xian Wallet browser extension.

## Features

*   **Wallet Integration:** Connects to the Xian Wallet browser extension to get user address, balance, and sign transactions.
*   **Two Main Views:**
    *   **Open Offers:** Displays a list of currently available trade offers fetched live from the Xian Testnet via GraphQL.
        *   Shows Offering Token/Amount, Requesting Token/Amount, Maker Address, Fee, and unique Offer ID.
        *   Paginated display (25 offers per page).
        *   "Take this offer" button initiates a two-step transaction process (Approve tokens + Take Offer) with modal confirmation.
    *   **Create Offer:** A form to create and list a new trade offer.
        *   Input fields for Offering Token (contract name), Offering Amount, Requesting Token (contract name), and Requesting Amount.
        *   Input validation (token names must start with `con_`, amounts must be positive, tokens must differ).
        *   "List Offer" button initiates a two-step transaction process (Approve tokens + List Offer) with modal confirmation.
*   **Fee Handling:** Automatically calculates and includes the OTC contract fee (defined in configuration) in the `approve` transaction amount for both creating and taking offers.
*   **Transaction Feedback:** Uses toasts (via `bulma-toast`) to provide user feedback on transaction submission status (success/failure).
*   **Responsive Design:** Basic responsive layout suitable for mobile and desktop use.
*   **Configuration:** Key parameters like contract addresses, network endpoints, and fees are managed in a configuration file.

## Technology Stack

*   [SvelteKit](https://kit.svelte.dev/)
*   [Svelte 4](https://svelte.dev/)
*   JavaScript (ES Modules)
*   CSS (Global styles + Component styles)
*   [Xian Wallet](https://www.xian.org/) (Browser Extension interaction via `xianDappUtils.mjs`)
*   GraphQL (Client-side for fetching offer data)
*   [bulma-toast](https://github.com/rfoel/bulma-toast) (for notifications)

## Prerequisites

*   [Node.js](https://nodejs.org/) (LTS version recommended)
*   npm (or pnpm/yarn)
*   [Xian Wallet Chrome Extension](https://chrome.google.com/webstore/detail/xian-wallet/ajopnjidmegmibopjeloplfojldaojlo) (or compatible browser extension) installed and set up with an account on the Xian **Testnet**.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd xian-otc
    ```

2.  **Install dependencies:**
    ```bash
    pnpm install
    ```

## Configuration

Before running, verify the settings in `src/lib/config.js`. Ensure these match the target environment and deployed smart contracts:

*   `otcContract`: The address of the main OTC smart contract.
*   `masterContract`: (If used by your setup, verify).
*   `networkType`: Should be `"testnet"`.
*   `currencySymbol`: e.g., `"XIAN"`.
*   `blockExplorer`: URL for the Testnet explorer.
*   `masternode`: RPC URL for the Testnet.
*   `graphqlEndpoint`: GraphQL endpoint URL for the Testnet.
*   `otcFeePercentage`: **Crucial.** The fee percentage (e.g., `0.005` for 0.5%) charged by the `otcContract`. This *must* match the contract's fee for approval amounts to be calculated correctly.

## Running the Application

1.  **Start the development server:**
    ```bash
    pnpm dev
    ```

2.  **Open your browser:** Navigate to `http://localhost:5173` (or the port specified in the console).

3.  **Connect Wallet:** The application should attempt to connect to your Xian Wallet automatically. You might need to approve the connection in the extension popup. Ensure the wallet is unlocked and connected to the Testnet.

## Usage

1.  **Wallet Status:** The header displays your connection status, truncated address, and XIAN balance (if connected and unlocked).
2.  **Navigate:** Use the "Open Offers" and "Create Offer" tabs.
3.  **Open Offers:**
    *   Browse the list of available offers.
    *   Use the "Previous" and "Next" buttons for pagination.
    *   Click "Take this offer" on a desired listing.
    *   A confirmation modal will appear explaining the two required transactions (Approve spending your `take_token`, then Take the offer).
    *   Click "Continue" to proceed. Sign the transactions prompted by the Xian Wallet extension.
    *   Observe the toast notifications for transaction status.
4.  **Create Offer:**
    *   Fill in the form with the token contract names (starting with `con_`) and the amounts for the tokens you are offering and requesting.
    *   The "List Offer" button becomes enabled when the form is valid.
    *   Click "List Offer".
    *   A confirmation modal will appear explaining the two required transactions (Approve spending your `offer_token` including fees, then List the offer).
    *   Click "Continue" to proceed. Sign the transactions prompted by the Xian Wallet extension.
    *   Observe the toast notifications. Upon success, you should be redirected to the "Open Offers" page where your new offer might appear.

## Important Notes

*   **Testnet Only:** This application is currently configured for the Xian Testnet. Using it on Mainnet would require configuration changes and careful testing.
*   **Smart Contract Dependency:** The frontend assumes the existence of a compatible OTC smart contract deployed at the address specified in `config.js`. It expects specific methods like `approve` (on token contracts), `list_offer`, and `take_offer` (on the OTC contract) with the argument structures used in the code.
*   **Fee Calculation:** The application calculates the amount needed for `approve` transactions by adding the `otcFeePercentage` (from `config.js`) to the base amount and rounding *up* using `Math.ceil()`. This applies to both creating and taking offers. **Verify this matches your specific contract's requirements.**
*   **Error Handling:** Basic error handling is included, showing toast messages. Check the browser's developer console for more detailed error information.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests. (Add more specific guidelines if desired).

## License

(Specify your license here, e.g., MIT License) or state "This project is unlicensed."