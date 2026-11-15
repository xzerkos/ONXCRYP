KNOWN_LABELS = {
    "btc": {
        "1BAuq7Vho2CEkVkUxbfU26LhwQjbCmWQkD": "Binance Hot Wallet",
        "bc1qm34lsc65zpw79lxes69zkqmk6ee3ewf0j77s3h": "Binance Hot Wallet",
        "1NDyJtNTjmwk5xPNhjgAMu4HDHigtobu1s": "Binance Cold Wallet",
        "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy": "Known Exchange / Service",
        "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa": "Genesis Address",
    },
    "trc20": {
        "TDqSquXBgUCLYvYC4XZgrprLK589dkhSCf": "Binance Hot Wallet",
        "TQrY8tryqsYVCYS3MFbtffiPp2ccyn4STm": "Binance Withdrawal Hot Wallet",
        "TV6MuMXfmLbBqPZvBHdwFsDnQeVfnmiuSi": "Binance Deposit",
        "TLa2f6VPqDgRE67v1736s7bJ8Ray5wYjU7": "OKX Hot Wallet",
    },
    "eth": {
        "0x28C6c06298d514Db089934071355E5743bf21d60": "Binance 14",
        "0xDFd5293D8e347dFe59E90eFd55b2956a1343963d": "Binance 16",
        "0x21a31Ee1afC51d94C2eFcCAa2092aD1028285549": "Binance 15",
        "0x564286362092D8e7936f0549571a803B203aAceD": "Binance 20",
        "0x0681d8Db095565FE8A346fA0277bFfdE9C0eDBBF": "Binance 21",
        "0x4E9ce36E442e55EcD9025B9a6E0D88485d628A67": "Binance 22",
    },
    "bnb": {
        "0x8894E0a0c962CB723c1976a4421c95949bE2D4E3": "Binance BSC Hot Wallet",
        "0xE2b1A3B7E7F5A6B4E0c8D9F2A1C3B5D7E9F0A2C4": "Binance BSC Cold Wallet",
    },
    "sol": {
        "5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9": "Binance SOL Hot Wallet",
        "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM": "Binance SOL Cold Wallet",
    },
    "ltc": {
        "LdP8Qox1VAhCzLJNqrr74YovaWYyNBUWvL": "Binance LTC Hot Wallet",
    },
    "doge": {
        "DBXu2kgc3xtvCUWFcxFE3r9hEYgmuaaCyD": "Binance DOGE Hot Wallet",
    },
    "ton": {},
    "gram": {},
}

def get_label(chain: str, address: str) -> str:
    if not address:
        return ""
    chain = chain.lower()
    if chain in KNOWN_LABELS:
        return KNOWN_LABELS[chain].get(address, "")
    return ""