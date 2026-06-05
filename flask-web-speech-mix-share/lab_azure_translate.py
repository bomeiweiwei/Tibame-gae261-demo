import os

from dotenv import load_dotenv
from azure.ai.translation.text import TextTranslationClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

load_dotenv()

text_translator = TextTranslationClient(
    credential=AzureKeyCredential(os.getenv("AZURE_TRANSLATOR_KEY")),
    endpoint=os.getenv("AZURE_TRANSLATOR_ENDPOINT"),
    region=os.getenv("AZURE_TRANSLATOR_REGION"),
)


def azure_translate(user_input):
    """
    呼叫 Azure Translator 偵測輸入語言，並同時翻譯成 en / zh-Hant / ko / ja。
    流程：
      1. 送出翻譯請求，目標語言為四種
      2. 從回應中取出偵測到的語言代碼（zh-Hans 統一轉為 zh-Hant）
      3. 取出對應語言的翻譯文字與中文翻譯
    回傳 tuple：(偵測語言的翻譯文字, 語言代碼, 中文翻譯文字)
    """
    try:
        target_languages = ["en", "zh-Hant", "ko", "ja"]
        input_text_elements = [user_input]

        response = text_translator.translate(
            body=input_text_elements, to_language=target_languages
        )

        translation = response[0] if response else None
        print(response[0]["translations"])

        trans_datas = response[0]["translations"]
        zh_trans = next(
            (item["text"] for item in trans_datas if item["to"] == "zh-Hant"), None
        )

        if translation:
            detected_language = translation.detected_language.language
            if detected_language in ("zh-Hant", "zh-Hans"):
                detected_language = "zh-Hant"

            index = target_languages.index(detected_language)
            return (
                translation.translations[index].text,
                target_languages[index],
                zh_trans,
            )

    except HttpResponseError as exception:
        print(f"Error Code: {exception.error}")
        print(f"Message: {exception.error.message}")
