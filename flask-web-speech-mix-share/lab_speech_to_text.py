import os
import tempfile
import subprocess

import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv()

AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")


def speech_to_text(audio_file):
    """
    接收瀏覽器錄製的 WebM 音訊 FileStorage 物件。
    流程：
      1. 將 WebM 存為暫存檔
      2. 用 ffmpeg 轉為 16kHz mono WAV（Azure Speech SDK 要求格式）
      3. 呼叫 Azure Speech SDK，以 AutoDetectSourceLanguage 辨識英/中/韓/日
      4. 清除暫存檔後回傳辨識文字字串；辨識失敗時回傳錯誤訊息字串
    """
    webm_path = None
    wav_path = None

    speech_config = None
    audio_config = None
    recognizer = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_webm:
            audio_file.save(temp_webm.name)
            webm_path = temp_webm.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
            wav_path = temp_wav.name

        subprocess.run(
            ["ffmpeg", "-y", "-i", webm_path, "-ar", "16000", "-ac", "1", wav_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )

        speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION
        )

        auto_detect_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
            languages=["en-US", "zh-TW", "ko-KR", "ja-JP"]
        )

        audio_config = speechsdk.audio.AudioConfig(filename=wav_path)

        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
            auto_detect_source_language_config=auto_detect_config,
        )

        result = recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            transcript = result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            transcript = "無法辨識語音內容"
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            transcript = f"辨識失敗：{cancellation.reason}"
        else:
            transcript = "未知錯誤"

    except subprocess.CalledProcessError:
        transcript = "ffmpeg 轉檔失敗"

    except Exception as e:
        transcript = f"系統錯誤：{str(e)}"

    finally:
        recognizer = None
        audio_config = None
        speech_config = None

        for path in [webm_path, wav_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except PermissionError:
                    pass

    return transcript
