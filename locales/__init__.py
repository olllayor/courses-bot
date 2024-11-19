from typing import Dict
from locales.uzbek import uz_texts
from locales.english import en_texts


class I18n:
    def __init__(self):
        self.languages = {
            'uz': uz_texts,
            'en': en_texts
        }
        self.default_language = 'uz'
        self.user_languages: Dict[int, str] = {}
    
    def set_user_language(self, user_id: int, language: str):
        """Set language preference for a user"""
        if language in self.languages:
            self.user_languages[user_id] = language
    
    def get_text(self, user_id: int, key: str) -> str:
        """Get text in user's preferred language"""
        language = self.user_languages.get(user_id, self.default_language)
        return self.languages[language].get(key, self.languages[self.default_language][key])
