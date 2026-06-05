import os

from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

load_dotenv()

speech_config = speechsdk.SpeechConfig(
    subscription=os.getenv("AZURE_SPEECH_KEY"), region=os.getenv("AZURE_SPEECH_REGION")
)


def azure_speech(user_input, language):
    """
    呼叫 Azure TTS 將文字合成為語音，直接回傳 MP3 bytes（不寫入暫存檔）。
    流程：
      1. 設定輸出格式為 Audio16Khz64KBitRateMonoMp3
      2. 依 language 代碼從 voice_map 挑選 Neural 語音角色
      3. 建立不指定 audio_config 的 SpeechSynthesizer，讓音訊存在記憶體
      4. 合成成功時回傳 bytes；取消或失敗時回傳 None
    支援語言：en、zh-Hant、ko、ja
    """
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio16Khz64KBitRateMonoMp3
    )

    voice_map = {
        "en": "en-US-JennyNeural",
        "zh-Hant": "zh-TW-HsiaoChenNeural",
        "ko": "ko-KR-SunHiNeural",
        "ja": "ja-JP-NanamiNeural",
    }

    speech_config.speech_synthesis_voice_name = voice_map.get(
        language, "en-US-JennyNeural"
    )

    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=None
    )

    result = speech_synthesizer.speak_text_async(user_input).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesis success")
        return result.audio_data

    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech synthesis canceled")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(cancellation_details.error_details)
        return None
