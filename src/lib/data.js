// Function to generate random hex strings
function generateHex(length) {
    let result = '';
    const characters = '0123456789abcdef';
    for (let i = 0; i < length; i++) {
        result += characters.charAt(Math.floor(Math.random() * characters.length));
    }
    return result;
}

// Function to generate a somewhat realistic token name
function generateTokenName() {
    const prefixes = ['btc', 'eth', 'lamden', 'usdt', 'usdc', 'dai', 'link', 'matic'];
    const suffixes = ['token', 'coin', 'stable', 'wrapped', 'yield'];
    return `con_${prefixes[Math.floor(Math.random() * prefixes.length)]}_${suffixes[Math.floor(Math.random() * suffixes.length)]}`;
}

export function generateMockOffers(count = 100) {
    const offers = [];
    for (let i = 0; i < count; i++) {
        const offer_amount = parseFloat((Math.random() * 1000 + 1).toFixed(Math.random() > 0.5 ? 2 : 6));
        const take_amount = parseFloat((Math.random() * 5000 + 10).toFixed(Math.random() > 0.5 ? 2 : 6));

        offers.push({
            // **** CHANGE ID GENERATION HERE ****
            id: generateHex(64), // Use the hex generator for the ID
            // ***********************************
            maker: generateHex(64),
            offer_token: generateTokenName(),
            offer_amount: offer_amount,
            take_token: generateTokenName(),
            take_amount: take_amount,
            fee: 0.5
        });
    }
    // Ensure offer/take tokens are different in most cases for realism
    offers.forEach(offer => {
        if (offer.offer_token === offer.take_token) {
            offer.take_token = generateTokenName();
            // Retry if still the same (unlikely but possible)
            if (offer.offer_token === offer.take_token) {
                 offer.take_token = generateTokenName();
            }
        }
    });
    return offers;
}

// Export a pre-generated list
export const mockOffers = generateMockOffers(115); // Generate more than needed for pagination testing