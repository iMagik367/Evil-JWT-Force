import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import argparse
import sys

def decrypt(ciphertext, key, iv=None, mode="CBC", base64_input=False):
    """Decrypt AES ciphertext with given key and mode (CBC or ECB), optional base64 input."""
    if not ciphertext:
        raise ValueError("Ciphertext is empty")
    # Handle base64-encoded input
    if base64_input:
        try:
            ciphertext = base64.b64decode(ciphertext)
        except Exception as e:
            raise ValueError(f"Invalid base64 input: {e}")
    # Ensure ciphertext is bytes
    if isinstance(ciphertext, str) and not base64_input:
        ciphertext = ciphertext.encode()
    # Prepare key bytes
    if isinstance(key, str):
        # hex string
        key_bytes = bytes.fromhex(key) if all(c in '0123456789abcdefABCDEF' for c in key) else key.encode()
    else:
        key_bytes = key
    mode = mode.upper()
    if mode == "ECB":
        cipher = AES.new(key_bytes, AES.MODE_ECB)
    elif mode == "CBC":
        if iv is None:
            raise ValueError("IV is required for CBC mode")
        iv_bytes = iv if isinstance(iv, (bytes, bytearray)) else bytes.fromhex(iv) if isinstance(iv, str) else iv
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
    else:
        raise ValueError(f"Invalid mode: {mode}")
    try:
        plaintext = cipher.decrypt(ciphertext)
        plaintext = unpad(plaintext, AES.block_size)
        return plaintext
    except Exception as e:
        raise

def decrypt_file(path, key, iv=None, mode="CBC", base64_input=False):
    """Read ciphertext from file and decrypt."""
    data = None
    try:
        with open(path, 'rb') as f:
            data = f.read()
    except Exception as e:
        raise
    return decrypt(data, key, iv=iv, mode=mode, base64_input=base64_input)

def main():
    # Allow invocation with 'aes-decrypt' subcommand
    args_list = sys.argv[1:]
    if args_list and args_list[0] == 'aes-decrypt':
        args_list = args_list[1:]
    parser = argparse.ArgumentParser(prog='aes-decrypt', description="AES Decrypt CLI")
    parser.add_argument("--ciphertext", required=True, help="Ciphertext (bytes or base64 string)")
    parser.add_argument("--key", required=True, help="AES key (hex or string)")
    parser.add_argument("--iv", help="Initialization vector for CBC mode (hex or raw)")
    parser.add_argument("--mode", required=True, choices=["CBC", "ECB"], help="AES mode")
    parser.add_argument("--base64", dest="base64_input", action="store_true", help="Treat ciphertext as base64")
    args = parser.parse_args(args_list)
    try:
        result = decrypt(args.ciphertext, args.key, iv=args.iv, mode=args.mode, base64_input=args.base64_input)
        # Print decoded plaintext
        sys.stdout.write(result.decode(errors='ignore'))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 