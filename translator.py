from deep_translator import GoogleTranslator

# A fallback list of languages in case get_supported_languages fails
DEFAULT_LANGUAGES = {
    "english": "en",
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "italian": "it",
    "portuguese": "pt",
    "russian": "ru",
    "japanese": "ja",
    "chinese (simplified)": "zh-CN",
    "chinese (traditional)": "zh-TW",
    "hindi": "hi",
    "arabic": "ar",
    "korean": "ko",
    "turkish": "tr",
    "vietnamese": "vi",
    "dutch": "nl",
    "polish": "pl"
}

def get_languages():
    """
    Returns a dictionary of supported languages mapping language name to its code.
    """
    try:
        langs = GoogleTranslator().get_supported_languages(as_dict=True)
        if langs:
            # Sort the dictionary alphabetically by language name (key)
            return {k.lower(): v for k, v in sorted(langs.items())}
    except Exception:
        pass
    return DEFAULT_LANGUAGES

import requests

def translate(text, target_lang_code, source_lang_code='auto'):
    """
    Translates the text to target_lang_code using Google Translator.
    """
    if not text or not text.strip():
        return ""
        
    try:
        translator = GoogleTranslator(source=source_lang_code, target=target_lang_code)
        translated = translator.translate(text)
        return translated
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        return "No internet connection. Please connect to the internet to translate."
    except Exception as e:
        err_msg = str(e)
        if "Failed to resolve" in err_msg or "Max retries exceeded" in err_msg or "Connection" in err_msg:
            return "No internet connection. Please connect to the internet to translate."
        return f"Translation Error: {err_msg}"

if __name__ == "__main__":
    # Small test
    test_text = "Hello, how are you doing?"
    print(f"Translating: '{test_text}' to Spanish...")
    print(translate(test_text, 'es'))
    print("Languages count:", len(get_languages()))
