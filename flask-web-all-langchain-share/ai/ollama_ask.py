from enums.ai_type import AiType
from prompts.prompt_builder import build_prompt, build_image_prompt
from ai.factory import create_ai_langchain


def Ask(user_input: str):
    system_prompt, user_prompt = build_prompt(user_input)

    ollama_ai_client = create_ai_langchain(AiType.OLLAMA)
    ollama_response = ollama_ai_client.chat(system_prompt, user_prompt)
    
    return ollama_response

def AskWithImage(user_input: str, image_url: str):
    system_prompt, human_messages = build_image_prompt(user_input, [image_url])

    ollama_ai_client = create_ai_langchain(AiType.OLLAMA)
    ollama_response = ollama_ai_client.chat_with_images(system_prompt, human_messages)

    return ollama_response
