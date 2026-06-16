import base64
from modules.crypto_utils import encrypt_aes as _encrypt_aes, decrypt_aes as _decrypt_aes, hash_sha256, hash_sha512, hash_md5, generate_aes_key, generate_iv
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
import argparse
import sys
import json

def aes_encrypt(plaintext, key, iv=None, mode="CBC", base64_output=False):
    result = _encrypt_aes(plaintext, key, iv=iv, mode=mode)
    if not result or 'ciphertext' not in result:
        raise Exception("Encryption failed")
    ct = result['ciphertext']
    if base64_output:
        return ct
    # return raw bytes decoded from base64
    return base64.b64decode(ct)

def aes_decrypt(ciphertext, key, iv=None, mode="CBC", base64_input=False):
    if base64_input:
        ct = ciphertext
    else:
        # if raw bytes, encode to base64
        ct = base64.b64encode(ciphertext).decode()
    pt = _decrypt_aes(ct, key, iv=iv, mode=mode)
    if pt is None:
        raise Exception("Decryption failed")
    # _decrypt_aes returns string
    return pt.encode() if isinstance(pt, str) else pt

def rsa_encrypt(data, pubkey_pem):
    key = RSA.import_key(pubkey_pem)
    cipher = PKCS1_OAEP.new(key)
    return cipher.encrypt(data)

def rsa_decrypt(data, privkey_pem):
    priv = RSA.import_key(privkey_pem)
    cipher = PKCS1_OAEP.new(priv)
    return cipher.decrypt(data)

def generate_random_key(length):
    return generate_aes_key(length)

def hash_data(data, algorithm="sha256"):
    if algorithm == 'sha256':
        return hash_sha256(data)
    elif algorithm == 'sha512':
        return hash_sha512(data)
    elif algorithm == 'md5':
        return hash_md5(data)
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

def encrypt_file(input_path, output_path, key, iv=None, mode="CBC"):    
    with open(input_path, 'rb') as f:
        data = f.read()
    res = _encrypt_aes(data, key, iv=iv, mode=mode)
    if not res or 'ciphertext' not in res:
        raise Exception("Encryption failed")
    ct_bytes = base64.b64decode(res['ciphertext'])
    with open(output_path, 'wb') as f:
        f.write(ct_bytes)
    return res

def decrypt_file(input_path, output_path, key, iv=None, mode="CBC"):  
    with open(input_path, 'rb') as f:
        ct_bytes = f.read()
    ct_b64 = base64.b64encode(ct_bytes).decode()
    pt_str = _decrypt_aes(ct_b64, key, iv=iv, mode=mode)
    if pt_str is None:
        raise Exception("Decryption failed")
    pt_bytes = pt_str.encode() if isinstance(pt_str, str) else pt_str
    with open(output_path, 'wb') as f:
        f.write(pt_bytes)
    return pt_bytes

# CLI entrypoint
def main():
    args_list = sys.argv[1:]
    # allow subcommand name 'crypto'
    if args_list and args_list[0] == 'crypto':
        args_list = args_list[1:]
    parser = argparse.ArgumentParser(prog='crypto', description='Crypto utilities')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--encrypt', action='store_true')
    group.add_argument('--decrypt', action='store_true')
    parser.add_argument('--ciphertext')
    parser.add_argument('--key', required=True)
    parser.add_argument('--iv')
    parser.add_argument('--mode', choices=['CBC','ECB','CFB','OFB','CTR'], default='CBC')
    parser.add_argument('--base64', dest='base64_flag', action='store_true')
    parser.add_argument('--input')
    parser.add_argument('--output')
    parser.add_argument('--rsa', action='store_true')
    args = parser.parse_args(args_list)
    try:
        if args.rsa:
            if args.encrypt:
                data = None
                if args.input:
                    data = open(args.input,'rb').read()
                else:
                    data = args.ciphertext.encode()
                res = rsa_encrypt(data, args.key)
                sys.stdout.write(base64.b64encode(res).decode())
            else:
                data = None
                if args.input:
                    data = base64.b64decode(open(args.input,'r').read())
                else:
                    data = base64.b64decode(args.ciphertext)
                res = rsa_decrypt(data, args.key)
                sys.stdout.write(res.decode(errors='ignore'))
        else:
            if args.encrypt:
                if args.input and args.output:
                    encrypt_file(args.input, args.output, args.key, iv=args.iv, mode=args.mode)
                    return
                res = aes_encrypt(base64.b64decode(args.ciphertext) if args.base64_flag else args.ciphertext if isinstance(args.ciphertext, bytes) else args.ciphertext, args.key, iv=args.iv, mode=args.mode, base64_output=args.base64_flag)
                sys.stdout.write(res.decode() if isinstance(res, bytes) else res)
            else:
                if args.input and args.output:
                    decrypt_file(args.input, args.output, args.key, iv=args.iv, mode=args.mode)
                    return
                res = aes_decrypt(args.ciphertext, args.key, iv=args.iv, mode=args.mode, base64_input=args.base64_flag)
                sys.stdout.write(res.decode(errors='ignore'))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main() 