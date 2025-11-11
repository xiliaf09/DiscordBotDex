// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {BalanceDelta} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";

interface IFeyHookV2PoolExtension {
    function initializePreLockerSetup(
        PoolKey calldata poolKey,
        bool feyIsToken0,
        bytes calldata extensionInitData
    ) external;

    function initializePostLockerSetup(PoolKey calldata poolKey, address locker, bool feyIsToken0)
        external;

    function afterSwap(
        PoolKey calldata poolKey,
        IPoolManager.SwapParams calldata swapParams,
        BalanceDelta delta,
        bool feyIsToken0,
        bytes calldata poolExtensionSwapData
    ) external;
}
