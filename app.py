import streamlit as st
from mcp_client import run_tool
from openai import OpenAI
import json
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()


def safe_json(obj):
    try:
        return json.dumps(obj, indent=2)
    except Exception:
        return str(obj)

def is_data_audio_url(text):
    return isinstance(text, str) and text.startswith("data:audio/")

# -- OpenAI config
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="MCP Assistant Playground", layout="centered")
st.markdown("""
    <style>
    .stTextInput input {
        font-size: 16px;
    }
    .stChatInputContainer {
        padding-bottom: 1rem;
    }
    .message {
        background-color: #1e1e1e;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💬 MCP Assistant Playground")
st.caption("Use natural language to call MCP tools via OpenAI GPT-4o.")

# -- Session history
if "messages" not in st.session_state:
    st.session_state.messages = []

# -- Display conversation
with st.container():
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"], unsafe_allow_html=True)
    st.divider()

# -- Input
user_input = st.chat_input("Type your question or command here...")

# -- GPT Router
def select_tool_using_gpt(prompt: str):
    system_prompt = """
You are a tool routing assistant. You receive a natural language user request and determine which MCP tool to use.

Available tools and their signatures:
- chat_gpt4o(prompt: str)
- gen_image_dalle3(prompt: str)
- get_all_members(role?: str, search?: str)
- get_member_by_id(member_id: str)
- create_member(name: str, email: str, role?: str, status?: str)
- update_member(member_id: str, name?: str, email?: str, role?: str, status?: str)
- delete_member(member_id: str)
- text_to_speech_gpt4o(text: str, voice: str = "nova", tone: str = "cheerful")

Respond ONLY in compact JSON like:
{ "tool": "tool_name", "args": { "arg1": "value", ... } }
Do not add explanation or formatting.
""".strip()

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        raw = response.choices[0].message.content

        # ✅ Clean up if needed (optional fallback)
        if not raw.strip().startswith("{"):
            raise ValueError("Invalid JSON structure")

        return json.loads(raw)

    except Exception as e:
        return {
            "tool": "chat_gpt4o",
            "args": {
                "prompt": f"ERROR: {str(e)}"
            }
        }
# -- Process input
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("🔍 GPT is selecting the best MCP tool..."):
            routing = select_tool_using_gpt(user_input)
            tool = routing.get("tool")
            args = routing.get("args", {})

            st.markdown(f"🛠️ **Running `{tool}` with args:**\n```json\n{safe_json(args)}\n```")

            try:
                tool_result = run_tool(tool, args)
                result = tool_result.output if hasattr(tool_result, "output") else tool_result
            except Exception as e:
                result = {"error": str(e)}

            # Render tool response
            if tool == "gen_image_dalle3":
                try:
                    if hasattr(result, "content") and isinstance(result.content, list):
                        text_item = result.content[0]
                        if hasattr(text_item, "text") and isinstance(text_item.text, str):
                            image_url = text_item.text
                            st.image(image_url, caption="🎨 Generated Image", width=300)
                            content = f"🖼️ *DALL·E image for:* `{args.get('prompt', '')}`"
                        else:
                            content = f"⚠️ Unexpected format:\n\n```json\n{safe_json(result)}\n```"
                    else:
                        content = f"⚠️ No image content found:\n\n```json\n{safe_json(result)}\n```"
                except Exception as e:
                    content = f"❌ Error parsing image: {str(e)}"

            elif tool == "text_to_speech_gpt4o":
                try:
                    # Handle TextContent object from OpenAI SDK
                    if hasattr(result, "content") and isinstance(result.content, list):
                        text_item = result.content[0]
                        if hasattr(text_item, "text") and isinstance(text_item.text, str):
                            audio_url = text_item.text

                            if is_data_audio_url(audio_url):
                                st.markdown("🎤 **Speech generated:**")
                                st.audio(audio_url, format="audio/mp3")
                                content = f"🔊 *Speech synthesized for:* `{args.get('prompt', '')}`"
                            else:
                                content = f"❌ Invalid audio data URL:\n\n```json\n{safe_json(audio_url)}\n```"
                        else:
                            content = f"⚠️ Unexpected audio content:\n\n```json\n{safe_json(result)}\n```"
                    else:
                        content = f"⚠️ No audio content returned:\n\n```json\n{safe_json(result)}\n```"
                except Exception as e:
                    content = f"❌ Error handling audio response:\n\n{str(e)}"

            else:
                content = f"**✅ Tool:** `{tool}`\n\n```json\n{safe_json(result)}\n```"

            st.markdown(content)
            st.session_state.messages.append({"role": "assistant", "content": content})
