import { config } from "../config";

export const getOpenListedOffers = (offset = 0, take = 25) => {
  return `
  query MyQuery {
      allStates(
        filter: {
          key: { startsWith: "${config.otcContract}.otc_listing"}
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