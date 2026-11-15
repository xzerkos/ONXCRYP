import sys
from scanner import analyze_address, detect_chain

баннер = r"""
 _____       __  __      __   __      ____       ____        __    __  ____    
/\  __`\    /\ \/\ \    /\ \ /\ \    /\  _`\    /\  _`\     /\ \  /\ \/\  _`\  
\ \ \/\ \   \ \ `\\ \   \ `\`\/'/'   \ \ \/\_\  \ \ \L\ \   \ `\`\\/'/\ \ \L\ \
 \ \ \ \ \   \ \ , ` \   `\/ > <      \ \ \/_/_  \ \ ,  /    `\ `\ /'  \ \ ,__/
  \ \ \_\ \   \ \ \`\ \     \/'/\`\    \ \ \L\ \  \ \ \\ \     `\ \ \   \ \ \/ 
   \ \_____\   \ \_\ \_\    /\_\\ \_\   \ \____/   \ \_\ \_\     \ \_\   \ \_\ 
    \/_____/    \/_/\/_/    \/_/ \/_/    \/___/     \/_/\/ /      \/_/    \/_/ 
"""

def main():
    print(баннер)
    print("owner - @xZerkos | Club - @xZerkosHack | Tool ONXCRYPT - crypto analyzer\n")

    while True:
        try:
            addr = input("> enter address: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[+] Exit.")
            sys.exit(0)
        if not addr:
            continue
        print("\nSearch...")
        chain = detect_chain(addr)
        if chain == "unknown":
            print("[+] Unknown address format. Supported: BTC, ETH, BNB, SOL, LTC, DOGE, TRX (TRC-20), TON, GRAM.")
        else:
            analyze_address(addr, chain)
        print("\n> Press enter to return to the menu...")
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            print("\n[+] Exit.")
            sys.exit(0)

if __name__ == "__main__":
    main()