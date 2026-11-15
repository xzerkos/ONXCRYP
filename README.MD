<div align="center">

# 🕵️‍♂️ ONXCRYPT

**Advanced Crypto Forensics & OSINT Analyzer**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=for-the-badge)](#)
[![License](https://img.shields.io/badge/License-Educational-red?style=for-the-badge)](#)

*Multi-chain cryptocurrency tracker, balance analyzer, and fund flow tracing tool.*

Owner: [@xZerkos](https://t.me/xZerkos) | Club: [@xZerkosHack](https://t.me/xZerkosHack)

</div>

---

## 🚀 Features

- **Multi-Chain Support**: Detects and analyzes BTC, ETH, BSC (BNB), SOL, LTC, DOGE, TRON (TRC-20), TON, and GRAM.
- **Multi-Source Fallback**: Queries multiple public nodes and explorers (Blockstream, Blockchain.com, TronGrid, Blockscout, TON Center, Blockchair) to bypass rate limits and dead APIs.
- **Deep OSINT Tracing**: 
  - UTXO analysis and Peel-Chain tracing for Bitcoin.
  - Common-Input-Ownership clustering for BTC peers.
  - Token balances (ERC-20, BEP-20, TRC-20, SPL, Jetton).
  - NFT holdings for EVM chains.
- **Heuristic Risk Scoring**: Calculates risk based on transaction volume, frequency, and flow.
- **Exchange Identification**: Tags known exchange wallets (Binance, OKX, etc.).
- **Zero-Config**: Works out-of-the-box with public APIs (with randomized User-Agent and auto-retry).

---

## 🛠️ Installation

Выберите вашу операционную систему и следуйте инструкциям ниже.

### 🪟 Установка на Windows

**Шаг 1. Установка Python**
1. Скачайте установщик с официального сайта: [python.org](https://www.python.org/downloads/).
2. Запустите установщик. **ОЧЕНЬ ВАЖНО:** Поставьте галочку **"Add Python to PATH"** (Добавить Python в PATH) в самом низу первого окна установки.
3. Нажмите "Install Now" и дождитесь завершения.

**Шаг 2. Установка Git**
1. Скачайте и установите Git с [git-scm.com](https://git-scm.com/download/win).
2. Во время установки можно везде оставить настройки по умолчанию (жать "Next").

**Шаг 3. Клонирование и запуск**
1. Откройте командную строку (нажмите `Win + R`, введите `cmd` и нажмите `Enter`).
2. Выполните команды по очереди:
```cmd
git clone https://github.com/xzerkos/ONXCRYP.git
cd ONXCRYP
pip install -r requirements.txt
python main.py