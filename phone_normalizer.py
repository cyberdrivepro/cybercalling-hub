"""
================================================================================
  🌐 OmniDimension Universal Smart Phone & Country Code Auto-Detector
================================================================================
  Automatically detects country code, cleans raw numbers, and formats to E.164.
  Supports both 3-tuple unpacking (clean_num, country, flag) and Dict indexing.
================================================================================
"""

import re

COUNTRY_FLAGS = {
    "91": ("India", "🇮🇳"),
    "1": ("United States / Canada", "🇺🇸"),
    "44": ("United Kingdom", "🇬🇧"),
    "971": ("United Arab Emirates", "🇦🇪"),
    "61": ("Australia", "🇦🇺"),
    "65": ("Singapore", "🇸🇬"),
    "966": ("Saudi Arabia", "🇸🇦"),
    "49": ("Germany", "🇩🇪"),
    "33": ("France", "🇫🇷"),
    "81": ("Japan", "🇯🇵"),
    "86": ("China", "🇨🇳")
}


class SmartPhoneResult(dict):
    """
    Hybrid return type: behaves simultaneously as a dictionary AND a 3-tuple
    (clean_number, country_name, flag) so unpacking never fails!
    """
    def __init__(self, clean_number, country_name="India", flag="🇮🇳", country_code="91", is_valid=True):
        super().__init__({
            "clean_number": clean_number,
            "country_name": country_name,
            "flag": flag,
            "country_code": country_code,
            "is_valid": is_valid
        })
        self.clean_number = clean_number
        self.country_name = country_name
        self.flag = flag
        self.country_code = country_code
        self.is_valid = is_valid

    def __iter__(self):
        # Enables clean 3-tuple unpacking: clean_num, country, flag = normalize_and_detect_country(...)
        return iter((self.clean_number, self.country_name, self.flag))

    def __getitem__(self, item):
        return super().get(item, getattr(self, item, None))

    def get(self, key, default=None):
        return super().get(key, getattr(self, key, default))


def normalize_and_detect_country(raw_input, default_region="IN"):
    """
    Intelligently normalize any phone number into full E.164 format with country code.
    Examples:
      '9811122233'    -> '+919811122233' (India 🇮🇳)
      '09811122233'   -> '+919811122233' (India 🇮🇳)
      '919811122233'  -> '+919811122233' (India 🇮🇳)
      '+919811122233' -> '+919811122233' (India 🇮🇳)
      '14155552671'   -> '+14155552671' (USA 🇺🇸)
      '447911123456'  -> '+447911123456' (UK 🇬🇧)
    """
    if not raw_input:
        return SmartPhoneResult("", "Unknown", "🌐", "", False)

    raw = str(raw_input).strip()
    digits = re.sub(r'[^\d]', '', raw)

    # 1. Try Google phonenumbers library if available
    try:
        import phonenumbers
        from phonenumbers import geocoder

        # If user passed a number without leading '+', parse with default region (IN)
        if raw.startswith("+"):
            parsed = phonenumbers.parse(raw, None)
        else:
            # If 10 digits starting with 6,7,8,9 -> Definitely India
            if len(digits) == 10 and digits[0] in '6789':
                parsed = phonenumbers.parse(digits, "IN")
            elif len(digits) == 11 and digits.startswith("0") and digits[1] in '6789':
                parsed = phonenumbers.parse(digits[1:], "IN")
            elif len(digits) == 12 and digits.startswith("91"):
                parsed = phonenumbers.parse("+" + digits, None)
            elif len(digits) == 11 and digits.startswith("1"):
                parsed = phonenumbers.parse("+" + digits, None)
            else:
                try:
                    parsed = phonenumbers.parse("+" + digits, None)
                    if not phonenumbers.is_valid_number(parsed):
                        parsed = phonenumbers.parse(digits, default_region)
                except Exception:
                    parsed = phonenumbers.parse(digits, default_region)

        if phonenumbers.is_valid_number(parsed) or phonenumbers.is_possible_number(parsed):
            e164_num = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            c_code = str(parsed.country_code)
            region_name = geocoder.description_for_number(parsed, "en") or COUNTRY_FLAGS.get(c_code, ("International", "🌐"))[0]
            flag = COUNTRY_FLAGS.get(c_code, ("International", "🌐"))[1]
            return SmartPhoneResult(e164_num, region_name, flag, c_code, True)
    except Exception:
        pass

    # 2. Fast Fallback Heuristics
    if raw.startswith("00"):
        digits = digits[2:]

    # 10 digit Indian number
    if len(digits) == 10 and digits[0] in '6789':
        return SmartPhoneResult(f"+91{digits}", "India", "🇮🇳", "91", True)

    # 11 digit Indian number with leading 0
    if len(digits) == 11 and digits.startswith("0") and digits[1] in '6789':
        return SmartPhoneResult(f"+91{digits[1:]}", "India", "🇮🇳", "91", True)

    # 12 digit with 91 prefix
    if len(digits) == 12 and digits.startswith("91"):
        return SmartPhoneResult(f"+{digits}", "India", "🇮🇳", "91", True)

    # 11 digit US/Canada with 1 prefix
    if len(digits) == 11 and digits.startswith("1"):
        return SmartPhoneResult(f"+{digits}", "USA / Canada", "🇺🇸", "1", True)

    # Default
    clean = ("+" + digits) if not raw.startswith("+") else ("+" + digits)
    c_info = COUNTRY_FLAGS.get("91", ("India", "🇮🇳"))
    for code, (cname, flag) in COUNTRY_FLAGS.items():
        if digits.startswith(code):
            c_info = (cname, flag)
            break

    return SmartPhoneResult(clean, c_info[0], c_info[1], "91", len(digits) >= 10)
