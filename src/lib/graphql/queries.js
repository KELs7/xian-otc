import { getOtcContract } from "../config";

export const getOpenListedOffers = (offset = 0, take = 25) => {
  const otcContract = getOtcContract();
  return `
  query MyQuery {
      allStates(
        filter: {
          key: { startsWith: "${otcContract}.otc_listing"}
          value: {
            contains: { status: "OPEN" }
          }
        }
        offset: ${offset}
        first: ${take}
      ) {
        nodes {
            key
            value
        }
      }
    }
  `;
};