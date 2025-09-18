#!/usr/bin/env python3
"""
Test script to verify the 0x API fixes
"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_0x_api_connection():
    """Test the 0x API v2 connection and quote endpoint"""
    
    # Configuration
    zerox_base_url = "https://api.0x.org"
    zerox_api_key = "85cbbc10-bb88-45d9-a527-c4f502a06e76"  # Votre clé API 0x
    chain_id = 8453  # Base chain ID
    weth_address = "0x4200000000000000000000000000000000000006"  # WETH on Base
    
    if not zerox_api_key:
        print("❌ ZEROX_API_KEY not configured")
        return False
    
    headers = {
        "0x-api-key": zerox_api_key,
        "0x-version": "v2",
        "Content-Type": "application/json"
    }
    
    # Test parameters - swap 0.001 ETH for USDC
    test_params = {
        "chainId": chain_id,
        "sellToken": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",  # ETH native
        "buyToken": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC on Base
        "sellAmount": "1000000000000000",  # 0.001 ETH in wei
        "taker": "0x6e9df0B4c9E54Bc141c040Fd2f5004d5A0481F52",  # Votre adresse wallet
        "slippageBps": "100"  # 1% slippage
    }
    
    print("🔄 Testing 0x API v2 connection...")
    print(f"📡 Endpoint: {zerox_base_url}/swap/allowance-holder/quote")
    print(f"🔑 API Key: {'*' * (len(zerox_api_key) - 4) + zerox_api_key[-4:]}")
    print(f"⛓️  Chain ID: {chain_id}")
    print(f"💰 Sell: {test_params['sellAmount']} wei ETH")
    print(f"🎯 Buy: USDC")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{zerox_base_url}/swap/allowance-holder/quote",
                headers=headers,
                params=test_params,
                timeout=10.0
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                quote_data = response.json()
                print("✅ 0x API v2 connection successful!")
                
                # Check if quote contains transaction data
                if 'transaction' in quote_data:
                    tx_data = quote_data['transaction']
                    print("✅ Quote contains transaction data")
                    print(f"📍 To address: {tx_data.get('to', 'N/A')}")
                    print(f"⛽ Gas: {tx_data.get('gas', 'N/A')}")
                    print(f"💸 Value: {tx_data.get('value', 'N/A')}")
                    
                    # Validate 'to' address format
                    to_address = tx_data.get('to', '')
                    if to_address.startswith('0x') and len(to_address) == 42:
                        print("✅ 'to' address format is valid")
                    else:
                        print(f"❌ 'to' address format is invalid: {to_address}")
                        return False
                else:
                    print("❌ Quote does not contain transaction data")
                    return False
                
                # Check liquidity availability
                if quote_data.get('liquidityAvailable', False):
                    print("✅ Liquidity is available")
                else:
                    print("❌ No liquidity available")
                    return False
                
                # Check for issues
                issues = quote_data.get('issues', {})
                if issues:
                    print(f"⚠️  Quote has issues: {issues}")
                else:
                    print("✅ No issues found in quote")
                
                return True
                
            else:
                print(f"❌ API request failed: {response.status_code}")
                print(f"📝 Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error testing 0x API: {e}")
        return False

async def main():
    """Main test function"""
    print("🧪 Testing 0x API v2 Integration Fixes")
    print("=" * 50)
    
    success = await test_0x_api_connection()
    
    print("=" * 50)
    if success:
        print("🎉 All tests passed! The 0x API v2 integration should work correctly.")
    else:
        print("💥 Tests failed. Please check your configuration and API key.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
