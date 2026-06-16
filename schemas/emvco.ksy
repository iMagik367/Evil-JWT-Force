meta:
  id: emvco_tlv
  endian: be
seq:
  - id: records
    type: record
    repeat: eos

types:
  record:
    seq:
      - id: tag
        size: 2  # ASCII tag
      - id: length
        type: u2
      - id: value
        size: length  # follow by value length 