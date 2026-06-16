"""
EMV Parser - parse EMVCo payload strings for PIX QR codes (copia-e-cola).
"""

def parse_emv(payload_str: str) -> dict:
    """
    Parse EMVCo TLV payload string from PIX copy-paste code.
    Extracts tags:
      01 - chave PIX
      54 - valor
      59 - merchant name
      62 -> nested TLV: tag 05 for txid
    Returns a dict with keys: txid, chave, valor, merchant (if found).
    """
    data = {}
    def _parse_tlv(s: str):
        i = 0
        length_s = len(s)
        while i + 4 <= length_s:
            tag = s[i:i+2]
            try:
                length = int(s[i+2:i+4])
            except ValueError:
                break
            value = s[i+4:i+4+length]
            # top-level tags
            if tag == '01':
                data['chave'] = value
            elif tag == '54':
                data['valor'] = value
            elif tag == '59':
                data['merchant_name'] = value
            elif tag == '62':
                # nested: parse for txid in tag 05
                _parse_tlv(value)
            elif tag == '05':
                data['txid'] = value
            elif tag == '26':
                # nested EMVCo merchant info, may contain subfields
                _parse_tlv(value)
            # skip to next TLV
            i += 4 + length
    _parse_tlv(payload_str)
    return data 