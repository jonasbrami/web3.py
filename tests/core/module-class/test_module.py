import pytest

from web3 import (
    EthereumTesterProvider,
    Web3,
)
from web3.method import (
    Method,
)


@pytest.fixture
def web3_with_external_modules(module1, module2, module3):
    return Web3(
        EthereumTesterProvider(),
        external_modules={
            'module1': module1,
            'module2': (module2, {
                'submodule1': module3,
            }),
        }
    )


def test_attach_methods_to_module(web3_with_external_modules):
    w3 = web3_with_external_modules

    w3.module1.attach_methods({
        # set `property1` on `module1` with `eth_chainId` RPC endpoint
        'property1': Method('eth_chainId', is_property=True),
        # set `method1` on `module1` with `eth_getBalance` RPC endpoint
        'method1': Method('eth_getBalance'),
    })

    assert w3.eth.chain_id == 61
    assert w3.module1.property1 == 61

    coinbase = w3.eth.coinbase
    assert w3.eth.get_balance(coinbase, 'latest') == 1000000000000000000000000
    assert w3.module1.method1(coinbase, 'latest') == 1000000000000000000000000

    w3.module2.submodule1.attach_methods({
        # set `method2` on `module2.submodule1` with `eth_blockNumber` RPC endpoint
        'method2': Method('eth_blockNumber', is_property=True)
    })

    assert w3.eth.block_number == 0
    assert w3.module2.submodule1.method2 == 0

    w3.eth.attach_methods({'get_block2': Method('eth_getBlockByNumber')})

    assert w3.eth.get_block('latest')['number'] == 0
    assert w3.eth.get_block('pending')['number'] == 1

    assert w3.eth.get_block2('latest')['number'] == 0
    assert w3.eth.get_block2('pending')['number'] == 1


def test_attach_methods_with_mungers(web3_with_external_modules):
    w3 = web3_with_external_modules

    w3.module1.attach_methods({
        'method1': Method('eth_getBlockByNumber', mungers=[
            lambda _method, block_id, f, _z: (block_id, f),
            lambda _m, block_id, _f: (block_id - 1,),
        ]),
    })

    assert w3.eth.get_block(0)['baseFeePerGas'] == 1000000000
    assert w3.eth.get_block(1)['baseFeePerGas'] == 875000000

    # `method1` should take a higher block number than `eth_getBlockByNumber` due to mungers and no
    # other params should matter
    assert w3.module1.method1(1, False, '_is_never_used_')['baseFeePerGas'] == 1000000000
    assert w3.module1.method1(2, '_will_be_overridden_', None)['baseFeePerGas'] == 875000000