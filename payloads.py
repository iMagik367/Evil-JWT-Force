import os
import json
import logging
import threading
import random
import string
from typing import Dict, Any, Optional, List, Union

class PayloadsError(Exception):
    pass

class Payloads:
    _instance = None
    _lock = threading.Lock()
    _payloads: Dict[str, Any] = {}
    _env: str = "default"
    _payloads_file: Optional[str] = None

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Payloads, cls).__new__(cls)
        return cls._instance

    def load(self, payloads_file: Optional[str] = None, env: Optional[str] = None):
        """Load payloads from file and environment variables."""
        self._payloads_file = payloads_file or os.getenv("PAYLOADS_FILE", "payloads.json")
        self._env = env or os.getenv("PAYLOADS_ENV", "default")
        try:
            with open(self._payloads_file, "r", encoding="utf-8") as f:
                all_payloads = json.load(f)
            self._payloads = all_payloads.get(self._env, {})
        except Exception as e:
            logging.error(f"Error loading payloads: {e}")
            raise PayloadsError(f"Failed to load payloads: {e}")
        self._apply_env_overrides()
        self._validate()

    def _apply_env_overrides(self):
        """Override payloads with environment variables."""
        for key in self._payloads:
            env_key = f"PAYLOAD_{key.upper()}"
            if env_key in os.environ:
                self._payloads[key] = os.environ[env_key]

    def _validate(self):
        """Validate essential payloads."""
        if not self._payloads or not isinstance(self._payloads, dict):
            raise PayloadsError("No payloads loaded or invalid format.")

    def get(self, key: str, default: Any = None) -> Any:
        return self._payloads.get(key, default)

    def set(self, key: str, value: Any):
        self._payloads[key] = value

    def remove(self, key: str):
        if key in self._payloads:
            del self._payloads[key]

    def as_dict(self) -> Dict[str, Any]:
        return dict(self._payloads)

    def as_list(self) -> List[tuple]:
        return list(self._payloads.items())

    def export(self, path: str, fmt: str = "json"):
        """Export payloads to file."""
        try:
            if fmt == "json":
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self._payloads, f, indent=2)
            elif fmt == "txt":
                with open(path, "w", encoding="utf-8") as f:
                    for k, v in self._payloads.items():
                        f.write(f"{k}: {v}\n")
            else:
                raise PayloadsError("Unsupported export format")
        except Exception as e:
            logging.error(f"Error exporting payloads: {e}")
            raise

    def import_payloads(self, path: str, fmt: str = "json"):
        """Import payloads from file."""
        try:
            if fmt == "json":
                with open(path, "r", encoding="utf-8") as f:
                    self._payloads = json.load(f)
            elif fmt == "txt":
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        if ":" in line:
                            k, v = line.strip().split(":", 1)
                            self._payloads[k.strip()] = v.strip()
            else:
                raise PayloadsError("Unsupported import format")
        except Exception as e:
            logging.error(f"Error importing payloads: {e}")
            raise

    def reload(self):
        """Reload payloads from file."""
        self.load(self._payloads_file, self._env)

    def log_current(self):
        logging.info(f"Current payloads ({self._env}): {self._payloads}")

    def generate(self, length: int = 16, charset: str = "alphanum", prefix: str = "", suffix: str = "") -> str:
        """Generate custom dynamic payload."""
        if charset == "alphanum":
            chars = string.ascii_letters + string.digits
        elif charset == "hex":
            chars = string.hexdigits
        elif charset == "ascii":
            chars = string.printable
        else:
            chars = charset
        payload = ''.join(random.choice(chars) for _ in range(length))
        return f"{prefix}{payload}{suffix}"

    def mutate(self, key: str, mutation: str = "reverse") -> Any:
        """Perform advanced mutation on a payload."""
        value = self._payloads.get(key)
        if not value:
            raise PayloadsError(f"Payload not found: {key}")
        if mutation == "reverse":
            return value[::-1]
        elif mutation == "upper":
            return value.upper()
        elif mutation == "lower":
            return value.lower()
        elif mutation == "xor":
            return ''.join(chr(ord(c) ^ 0xAA) for c in value)
        else:
            raise PayloadsError("Unsupported mutation type")

    def fuzz(self, key: str, count: int = 10) -> List[str]:
        """Generate fuzzing variations of a payload."""
        base = self._payloads.get(key, "")
        fuzzed = []
        for _ in range(count):
            mutated = ''.join(random.choice([c, chr(random.randint(32, 126))]) for c in base)
            fuzzed.append(mutated)
        return fuzzed

    def merge(self, extra: Union[Dict[str, Any], None]):
        """Merge extra payloads."""
        if extra:
            self._payloads.update(extra)

# Global function for quick access
def payloads(key: Optional[str] = None, default: Any = None) -> Any:
    p = Payloads()
    if not p._payloads:
        p.load()
    if key:
        return p.get(key, default)
    return p.as_dict()

# CLI for payload management
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Advanced payload manager for offensive/defensive testing (Kali Linux Only)")
    parser.add_argument("--env", help="Payload environment")
    parser.add_argument("--file", help="Payloads file")
    parser.add_argument("--get", help="Get payload value")
    parser.add_argument("--set", nargs=2, metavar=("KEY", "VALUE"), help="Set payload value")
    parser.add_argument("--remove", help="Remove payload")
    parser.add_argument("--export", nargs=2, metavar=("PATH", "FMT"), help="Export payloads")
    parser.add_argument("--import", dest="import_", nargs=2, metavar=("PATH", "FMT"), help="Import payloads")
    parser.add_argument("--reload", action="store_true", help="Reload payloads")
    parser.add_argument("--generate", nargs="*", metavar=("LEN", "CHARSET", "PREFIX", "SUFFIX"), help="Generate dynamic payload")
    parser.add_argument("--mutate", nargs=2, metavar=("KEY", "MUTATION"), help="Mutate payload")
    parser.add_argument("--fuzz", nargs=2, metavar=("KEY", "COUNT"), help="Fuzz payload")
    parser.add_argument("--merge", help="Merge extra payloads as JSON")
    args = parser.parse_args()

    p = Payloads()
    p.load(payloads_file=args.file, env=args.env)
    if args.get:
        print(p.get(args.get))
    if args.set:
        p.set(args.set[0], args.set[1])
        print(f"{args.set[0]} updated.")
    if args.remove:
        p.remove(args.remove)
        print(f"{args.remove} removed.")
    if args.export:
        p.export(args.export[0], args.export[1])
        print(f"Exported to {args.export[0]} as {args.export[1]}")
    if args.import_:
        p.import_payloads(args.import_[0], args.import_[1])
        print(f"Imported from {args.import_[0]} as {args.import_[1]}")
    if args.reload:
        p.reload()
        print("Payloads reloaded.")
    if args.generate is not None:
        length = int(args.generate[0]) if len(args.generate) > 0 else 16
        charset = args.generate[1] if len(args.generate) > 1 else "alphanum"
        prefix = args.generate[2] if len(args.generate) > 2 else ""
        suffix = args.generate[3] if len(args.generate) > 3 else ""
        print(p.generate(length, charset, prefix, suffix))
    if args.mutate:
        print(p.mutate(args.mutate[0], args.mutate[1]))
    if args.fuzz:
        key = args.fuzz[0]
        count = int(args.fuzz[1])
        print(p.fuzz(key, count))
    if args.merge:
        try:
            extra = json.loads(args.merge)
            p.merge(extra)
            print("Payloads merged.")
        except Exception as e:
            print(f"Error merging payloads: {e}")
    p.log_current()