import os
import streamlit as st
import google.generativeai as genai
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

    # Get current date in yyyymmdd format
    current_date = datetime.now().strftime("%Y%m%d")

    # Create file handler
    log_file = "./logs/chat_sample_{}.log".format(current_date)
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
    if "chat_model" not in st.session_state:
        st.session_state["chat_model"] = genai.GenerativeModel(
            model_name=st.session_state["gemini_model"],
            system_instruction="You are an excellent AI assistant. Please answer the given question as politely as possible. Please answer in a markdown format. Please answer in the same language as the question."
        )
        logger.info(f"Gemini Model: {st.session_state["gemini_model"]}")

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
        response = st.session_state["chat_model"].generate_content(prompt)
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

    if "document_model" not in st.session_state:
        st.session_state["document_model"] = genai.GenerativeModel(
            model_name=st.session_state["gemini_model"],
            system_instruction="You are an excellent AI assistant. Please answer the given question as politely as possible. Please answer in a markdown format. Please answer in the same language as the question."
        )
        st.session_state["chat_history"] = []
        st.session_state["target_files"] = []
        st.session_state["target_file_names"] = []

    # PDF 파일 업로드
    if uploaded_file := st.sidebar.file_uploader("File Upload", type=["pdf"]):
        if uploaded_file.name not in st.session_state["target_file_names"]:
            file_path = save_uploaded_file(uploaded_file)
            target_file = genai.upload_file(
                path=file_path, display_name=uploaded_file.name
            )
            st.session_state["target_files"].append(target_file)
            st.session_state["target_file_names"].append(uploaded_file.name)
            st.sidebar.success("Upload completed")

    # Chat History
    for message in st.session_state["chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 업로드한 파일이 존재할 경우
    if len(st.session_state["target_files"]) > 0:
        st.sidebar.subheader("Uploaded files")

        # 파일명 표시
        for target_file_name in st.session_state["target_file_names"]:
            st.sidebar.markdown(f"- {target_file_name}")

        # 유저 입력 후
        if prompt := st.chat_input("Message Gemini"):

            # 유저 입력 표시
            with st.chat_message("user"):
                st.markdown(prompt)

            # history 에 유저 입력 추가
            st.session_state["chat_history"].append({"role": "user", "content": prompt})

            # 메시지 송신
            files_and_message = st.session_state["target_files"] + [prompt]
            logger.info(f"files_and_message: {files_and_message}")

            logger.info(f"Gemini Model: {st.session_state["gemini_model"]}")

            response = st.session_state["document_model"].generate_content(
                files_and_message
            )
            logger.info(f"Response: {response}")

            # Response
            with st.chat_message("ai"):
                st.markdown(response.text)

            # Gemini의 Response를 Chat 이력에 추가
            st.session_state["chat_history"].append(
                {"role": "assistant", "content": response.text}
            )
            logger.info(f"History: {st.session_state['chat_history']}")


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
        st.session_state["gemini_model"] = st.sidebar.selectbox(
            "Gemini Model",
            (conf["model_flash"], conf["model_pro"]),
        )
        chat_view()
    elif option == conf["page_document_chat"]:
        st.session_state["gemini_model"] = st.sidebar.selectbox(
            "Gemini Model",
            (conf["model_flash"], conf["model_pro_vision"]),
        )
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
