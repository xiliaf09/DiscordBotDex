// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {FeyHookV2} from "./FeyHookV2.sol";
import {IFeyHookStaticFee} from "./interfaces/IFeyHookStaticFee.sol";
import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";

import {PoolId} from "@uniswap/v4-core/src/types/PoolId.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";

contract FeyHookStaticFeeV2 is FeyHookV2, IFeyHookStaticFee {
    mapping(PoolId => uint24) public feyFee;
    mapping(PoolId => uint24) public pairedFee;
    address public bs; // factory bootstrapper required for solo deployment

    constructor(
        address _poolManager,
        address _factory,
        address _poolExtensionAllowlist,
        address _weth,
        address _bs
    ) FeyHookV2(_poolManager, _factory, _poolExtensionAllowlist, _weth) {
        bs = _bs;
    }

    function _initializeFeeData(PoolKey memory poolKey, bytes memory feeData) internal override {
        PoolStaticConfigVars memory _poolConfigVars = abi.decode(feeData, (PoolStaticConfigVars));

        if (_poolConfigVars.feyFee > MAX_LP_FEE) {
            revert FeyFeeTooHigh();
        }

        if (_poolConfigVars.pairedFee > MAX_LP_FEE) {
            revert PairedFeeTooHigh();
        }

        feyFee[poolKey.toId()] = _poolConfigVars.feyFee;
        pairedFee[poolKey.toId()] = _poolConfigVars.pairedFee;

        emit PoolInitialized(poolKey.toId(), _poolConfigVars.feyFee, _poolConfigVars.pairedFee);
    }

    // set the LP fee according to the fey/paired fee configuration
    function _setFee(PoolKey calldata poolKey, IPoolManager.SwapParams calldata swapParams)
        internal
        override
    {
        uint24 fee = swapParams.zeroForOne != feyIsToken0[poolKey.toId()]
            ? pairedFee[poolKey.toId()]
            : feyFee[poolKey.toId()];

        _setProtocolFee(fee);
        IPoolManager(poolManager).updateDynamicLPFee(poolKey, fee);
    }

    // set the factory address; required for solo deployment
    function bootstrapFactory(address _factory) external {
        if (msg.sender != bs) revert OnlyBootstrapper();
        if (_factory == address(0)) revert InvalidFactory();

        address oldFactory = factory;
        factory = _factory;
        emit FactoryUpdated(oldFactory, _factory);
    }

    // make factory address immutable
    function releaseBootstrapper() external {
        if (msg.sender != bs) revert OnlyBootstrapper();
        address previousBootstrapper = bs;
        bs = address(0);
        emit BootstrapperReleased(previousBootstrapper);
    }
}
