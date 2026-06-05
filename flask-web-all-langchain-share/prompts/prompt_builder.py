from utils.image_lang_chain import image4LangChain


def build_prompt(user_input):
    system_prompt = "你是一個台灣人，請用繁體中文回答，字數不超過20字"
    user_prompt = f"{user_input}"
    return system_prompt, user_prompt


def build_image_prompt(user_input, image_url_list):
    user_messages = []
    system_prompt = "你是一個台灣人也是個專業的圖片鑑定師，請用繁體中文回答"
    user_messages.append({"type": "text", "text": user_input})
    for image_url in image_url_list:
        user_messages.append(
            {
                "type": "image_url",
                "image_url": image4LangChain(image_url),
            }
        )
    return system_prompt, user_messages
