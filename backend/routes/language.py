import requests
import logging

logger = logging.getLogger(__name__)

def translate_text(text, source_lang, target_lang):
    try:
        url = "https://api.lokal-ed.com/translate"
        payload = {
            "source_lang": source_lang,
            "target_lang": target_lang,
            "text": text
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()
        return response_data.get('translated_text', text)  # Fallback to original text if translation is not found
    except Exception as e:
        logger.error(f"Error translating text: {str(e)}")
        return text  # Fallback to original text if translation fails
