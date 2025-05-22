import { getGraphqlEndpoint } from "../config";

export async function fetchOpenOffers(query) {
  const url = getGraphqlEndpoint();

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const json = await response.json();
    const openOffers = json.data.allStates.nodes.map((node) => {
        const { key, value } = node;
        return {
            id: key.split(':')[1],
            ...value
        }
    });
    return openOffers;
  } catch (error) {
    console.error('Error with request:', error);
  }
}