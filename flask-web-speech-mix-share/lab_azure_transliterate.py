from azure.core.exceptions import HttpResponseError
from lab_azure_translate import text_translator


def azure_transliterate(user_input, language):
    """
    呼叫 Azure Translator 將非英文文字轉為拉丁拼音（Romanization）。
    流程：
      1. 英文輸入直接原文回傳，不呼叫 API
      2. 依語言代碼對應來源文字系統（zh-Hant→Hant、ko→Kore、ja→Jpan）
      3. 呼叫 transliterate API，目標文字系統固定為 Latn（拉丁字母）
      4. 回傳拼音字串（例：Pinyin、Romaja、Romaji）
    """
    try:
        if language == "en":
            return user_input

        if language == "zh-Hant":
            from_script = "Hant"
        elif language == "ko":
            from_script = "Kore"
        elif language == "ja":
            from_script = "Jpan"

        to_script = "Latn"
        input_text_elements = [user_input]

        response = text_translator.transliterate(
            body=input_text_elements,
            language=language,
            from_script=from_script,
            to_script=to_script,
        )
        transliteration = response[0] if response else None

        if transliteration:
            print(
                f"Input text was transliterated to '{transliteration.script}' script. Transliterated text: '{transliteration.text}'."
            )
            return transliteration.text

    except HttpResponseError as exception:
        if exception.error is not None:
            print(f"Error Code: {exception.error.code}")
            print(f"Message: {exception.error.message}")
        raise
