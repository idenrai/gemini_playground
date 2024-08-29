import os
import streamlit as st
import google.generativeai as genai
import google.ai.generativelanguage as glm
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from utils.common_utils import get_env, load_config


def setup_logger():
    """
    Logger
    :return:
    """
    # Create logger
    _logger = logging.getLogger("Logger")
    _logger.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Create file handler
    log_file = "./logs/chat_sample_{}.log".format(timestamp)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    _logger.addHandler(file_handler)

    # Create console_handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)

    return _logger


def save_uploaded_file(uploaded_file):
    """
    Save the uploaded file to the specified directory and return the file path.
    """
    if not os.path.exists(conf["upload_path"]):
        os.makedirs(conf["upload_path"])

    file_path = os.path.join(conf["upload_path"], uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def chat_view():
    """
    View for Gemini Chat.
    """
    st.title(conf["page_chat"])
    if "chat" not in st.session_state:
        model = genai.GenerativeModel(conf["model_flash"])
        st.session_state["chat"] = model.start_chat(
            history=[
                glm.Content(
                    role="user",
                    parts=[
                        glm.Part(
                            text="You are an excellent AI assistant. Please answer the given question as politely as possible. Please answer in a markdown format. Please answer in Korean."
                        )
                    ],
                ),
                glm.Content(role="model", parts=[glm.Part(text="Okay.")]),
            ]
        )
        st.session_state["chat_history"] = []

    # Chat History
    for message in st.session_state["chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 유저 입력 후
    if prompt := st.chat_input("Message Gemini"):
        logger.info(f"User prompt: {prompt}")

        # 유저 입력 표시
        with st.chat_message("user"):
            st.markdown(prompt)

        # history 에 유저 입력 추가
        st.session_state["chat_history"].append({"role": "user", "content": prompt})

        # 메시지 송신
        response = st.session_state["chat"].send_message(prompt)
        logger.info(f"Response: {response}")

        # Response
        with st.chat_message("ai"):
            st.markdown(response.text)

        # Gemini의 Response를 Chat 이력에 추가
        st.session_state["chat_history"].append(
            {"role": "assistant", "content": response.text}
        )
        logger.info(f"History: {st.session_state['chat_history']}")


def document_chat_view():
    """
    View for uploading files.
    """
    st.title(conf["page_document_chat"])
    uploaded_file = st.file_uploader(
        "파일을 업로드하세요", type=["txt", "pdf", "png", "jpg"]
    )
    if uploaded_file:
        file_path = save_uploaded_file(uploaded_file)
        st.session_state["uploaded_file_path"] = file_path
        st.success(f"파일이 성공적으로 업로드 되었습니다: {file_path}")


def execute():
    """
    Execute
    :return:
    """
    # API 키 설정
    genai.configure(api_key=get_env("GOOGLE_API_KEY"))

    st.set_page_config(page_title="Gemini Playground", page_icon=None)

    option = st.sidebar.selectbox(
        "Navigation",
        (conf["page_chat"], conf["page_document_chat"]),
    )

    # 선택된 옵션에 따라 메인 화면 변경
    if option == conf["page_chat"]:
        chat_view()
    elif option == conf["page_document_chat"]:
        document_chat_view()


if __name__ == "__main__":
    # 환경변수 로드
    load_dotenv(verbose=True)
    load_dotenv("envs/.dev.env", override=True)

    # Config
    conf = load_config()

    # 글로벌 변수로 Logger 를 만들어 두기
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    timestamp = now.strftime("%Y%m%d%H%M%S")
    logger = setup_logger()
    logger.info("Processing dev environment")

    execute()
