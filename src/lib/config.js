import { get } from "svelte/store";
import { networkType } from "./store";

const config = {
    otcContract: {
        "testnet": "con_otc_v3",
        "mainnet": "con_otc_v3"
    },
    otcFeePercentage: {
        "testnet": 0.005,
        "mainnet": 0.005
    }, 
    masternode: {
        "testnet": "https://testnet.xian.org",
        "mainnet": "https://node.xian.org"
    },
    graphqlEndpoint: {
        "testnet": "https://testnet.xian.org/graphql",
        "mainnet": "https://node.xian.org/graphql"
    },
    webSocketUrl: {
        "testnet": "https://testnet.xian.org/websocket",
        "mainnet": "https://node.xian.org/websocket"
    }   
}

export const getOtcContract = ()=>{
    const network = get(networkType);
    if (network === "testnet"){
        return config.otcContract.testnet
    }else{
        return config.otcContract.mainnet
    }
}

export const getOtcFeePercentage = ()=>{
    const network = get(networkType);
    if (network === "testnet"){
        return config.otcFeePercentage.testnet
    }else{
        return config.otcFeePercentage.mainnet
    }
}

export const getMasterNode = ()=>{
    const network = get(networkType);
    if (network === "testnet"){
        return config.masternode.testnet
    }else{
        return config.masternode.mainnet
    }
}

export const getGraphqlEndpoint = ()=>{
    const network = get(networkType);
    if (network === "testnet"){
        return config.graphqlEndpoint.testnet
    }else{
        return config.graphqlEndpoint.mainnet
    }
}

export const getWebSocketUrl = ()=>{
    const network = get(networkType);
    if (network === "testnet"){
        return config.webSocketUrl.testnet
    }else{
        return config.webSocketUrl.mainnet
    }
}