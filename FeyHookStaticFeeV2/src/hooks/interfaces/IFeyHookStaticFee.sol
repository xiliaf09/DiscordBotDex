// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {PoolId} from "@uniswap/v4-core/src/types/PoolId.sol";

interface IFeyHookStaticFee {
    error FeyFeeTooHigh();
    error PairedFeeTooHigh();
    error OnlyBootstrapper();
    error InvalidFactory();

    event FactoryUpdated(address indexed oldFactory, address indexed newFactory);
    event BootstrapperReleased(address indexed previousBootstrapper);
    event PoolInitialized(PoolId poolId, uint24 feyFee, uint24 pairedFee);

    struct PoolStaticConfigVars {
        uint24 feyFee;
        uint24 pairedFee;
    }

    function feyFee(PoolId poolId) external view returns (uint24);
    function pairedFee(PoolId poolId) external view returns (uint24);
}
