# ASTROLAB RISK DISCLAIMER
Last Updated: 3 May 2024

At Astrolab DAO (collectively "Astrolab", "the DAO", "we", "us", "our"), we care about risk transparency.
The following risk notice applies to the use of all of Astrolab's product range ("Products", "Services"):
- Monochain Primitive and Composite vaults: cross-asset, multi-protocol strategy vauls
- Cross-chain Composite vaults: cross-chain, auto-compounding, multi-strategy vaults (acUSD, acETH, acBTC)
- Radyal: front-end application allowing end users to deposit to/withdraw from Astrolab products
- Cross-chain Zap: front-end feature allowing users to deposit to/withdraw from Astrolab products cross-chain from/to any asset
- Botnet: distributed, highly available, off-chain automation infrastructure
- CM3: distributed, highly available, off-chain storage solution
- $ASL: Astrolab governance and utility token, used for insurance, revenue sharing, and voting
- Insurances: stake-to-insure $ASL vault
- Stable Mint: asUSDC, asETH, asBTC stablecoin minting contracts accepting strategies and crate tokens as collateral
- asUSDC, asETH, asBTC: over-collateralized stablecoins issued by Astrolab Stable Mint

## 1. DEFINITION
The delegated services with which Astrolab products interacts include:
- holding of cryptoassets
- trading on decentralized exchanges
- liquid staking of platform and protocol tokens
- locked staking of platform and protocol tokens
- liquidity providing
- collateralized and uncollateralized lending
- collateralized and uncollateralized borrowing
- purchase and issuance of insurance products
- purchase and issuance of derivatives such as options and futures
- bridging assets cross-chain
- executing arbitrary operations cross-chain (bridge messaging)
- minting strategy tokens and stablecoins for locked collateral
- distributing of $ASL governance tokens as incentives to product users
- temporarily freezing users' staked assets to follow pre-defined product mechanisms
- liquidating users' locked collateral if to enforce pre-defined product margin requirements

Please note that this list is subject to changes according to the integration of emerging protocols, and future developments.
You should carefully consider whether depositing funds onto any of Astrolabs's products or buying Astrolab's governance token ($ASL) matches your risk profile and loss capacity.

## 2. PROTOCOL RISKS
Market and Financial Risks - As with any asset, all aforementioned Astrolab's products, and their underlying DeFi protocols can increase or decrease in return, and can lead to a substantial loss limited to the amount of funds you deposit. Therefore, you should not invest money that you cannot afford to lose. You should do your own research and/or seek advice from a financial advisor if you are unclear of any matters. Astrolab does not provide any investment, legal or tax advice and does not assume any liability to third parties with respect to the provision of advice or your transactions in and in connection with Astrolab.

Counterparty Risks - Astrolab and its team do not participate in or act as counterparties to its product transactions and do not offer intermediary services like brokerage or custodianship. Transactions are conducted on a peer-to-contract basis using immutable smart contracts, with no regulatory oversight from Astrolab. These activities are not covered by any investor protection or complaint resolution mechanisms. Users are responsible for adhering to local legal requirements and bear all associated risks. Astrolab has no control over user transactions within its protocols
Astrolab does not provide advisory, execution, or clearing services. Users maintain full custody of their funds in Crates and manage their positions independently.

Asynchronous Liquidity Risks - Astrolab products implement [ERC7540 specifications](https://eips.ethereum.org/EIPS/eip-7540) for asynchronous withdrawals from applicable products (vaults) in the case of insufficient liquidity. This allows for the processing of withdrawals of any size but does not guarantee instant, block-time liquidity. Redemption requests shall be honored within a maximum delay of 7 days, but will typically be executed in under 48 hours. ERC7540 solves several issues met with the [plain ERC4626 standard](https://ethereum.org/en/developers/docs/standards/tokens/erc-4626/), and allows for more complex structuring of products.

## 3. THIRD-PARTY RISKS
Regulatory Risks - You should ensure that your activities relating to Astrolab, and its products and services, comply with all applicable legal and regulatory requirements and restrictions you abide by. By carrying out transactions in or in connection with Astrolab products, you warrant that you are authorised to enter into the relevant transactions and that you are acting in compliance with applicable law and regulation. Citizenship amendments are available in [our Terms of Services](https://astrolab.fi/tos).

Oracles Risks - Some of Astrolab's products uses price feeds oracls, namely from Chainlink and Pyth Network. While these services are highly decentralized and fault-tolerant, they carry inherent risks of their own. For more information, please visit:
- Chainlink Terms: https://chain.link/terms
- Pyth Network Disclaimer: https://pyth.network/disclaimer

Cross-Chain Risks - Astrolab cross-chain products and services use relayer networks such as LayerZero and Axelar, and bridge aggregators such as LiFi and Squid Router. These technologies, while proven, decentralized and audited, are still in their early days and carry inherent risks of their own. For more information, please visit:
- LayerZero Terms: https://layerzero.network/terms
- Axelar Terms: https://community.axelar.network/tos
- LiFi Terms: https://li.fi/legal/terms-and-conditions

DeFi Integrations Risks - Astrolab's products involve underlyings that are subject to their own set of operational risks and potential for smart contract technical exploits. These risks, inherent in third-party DeFi protocols, can impact the performance and security of Astrolab's offerings. Users should be aware that interactions with such protocols carry additional layers of risk, including but not limited to vulnerabilities in smart contract code, governance decisions by third-party entities, and varying degrees of decentralization. These factors can lead to scenarios such as loss of funds, reduced returns, or exposure to unforeseen liabilities. It is advisable for users to conduct thorough due diligence and understand the specific risks associated with each underlying protocol involved in Astrolab's strategies.

## 3. MORAL AGREEMENT
By accepting this disclaimer you are acknowledging the risks involved in interacting with advanced DeFi protocols in an early cross-chain environment and are also acknowledging that you, the user, and not Astrolab are solely responsible for any losses, financial or otherwise, as a result of using this service. Astrolab shall under no circumstances be liable for any lost deposits, lost profits, lost opportunities, misstatements, or errors contained within these pages. You also agree that Astrolab will not be held liable for data accuracy, technical issues (client-side, server-side, or blockchain-side), or any special or consequential damages that result from the use of, or the inability to use, any or all of the materials published by Astrolab (eg. on [https://astrolab.fi](https://astrolab.fi) and [https://radyal.xyz](https://radyal.xyz)).

As a reminder of [our Terms of Service](/terms-of-service), you agree to hold Astrolab harmless for any act resulting directly or indirectly from its services, data, content, materials, associated pages and documents. The information in this document and all related Astrolab projects' documents and any and all information on Astrolab is for information purposes only and does not constitute financial or technical advice or an inducement to purchase or sell any service or security (however defined under applicable law). Astrolab makes no warranties of any kind in relation to its content and services, including but not limited to accuracy, security, integrity and (financial or operational) performance of Astrolab's products. Any use of Astrolab and its features and functionalities are solely at your own risk and discretion. You should always conduct your own research, review, analysis and verify the content of Services before relying on or using them.
