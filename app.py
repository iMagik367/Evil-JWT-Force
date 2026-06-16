import streamlit as st
import glob, ast, os
from ai_system.engine import AIEngine

# Function to list all Python function definitions in the codebase
def list_functions():
    funcs = []
    for path in glob.glob("**/*.py", recursive=True):
        try:
            with open(path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    funcs.append(f"{path}:{node.name}")
        except Exception:
            continue
    return funcs

# Initialize AI engine
engine = AIEngine()

# Streamlit UI configuration
st.set_page_config(page_title="Evil Force JWT Chat", layout="wide")
st.title("Evil Force JWT - Chat Inteligente")

# Chat history stored in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render chat history
for msg in st.session_state.messages:
    role = msg["role"]
    content = msg["content"]
    if role == "user":
        st.chat_message("Você").write(content)
    else:
        st.chat_message("Assistente").write(content)

# Input box for new messages
if prompt := st.chat_input("Digite sua mensagem aqui..."):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Handle specific commands
    if "liste as funções" in prompt.lower():
        funcs = list_functions()
        reply = "**Funções encontradas no projeto:**\n" + "\n".join(funcs)
    else:
        # Use chain-of-thought for general queries
        try:
            reply = engine._chain_of_thought({"user_message": prompt}, {"type": "chat"})
            if not reply.strip():
                reply = "Desculpe, não consegui gerar uma resposta profunda no momento."
        except Exception as e:
            reply = f"Erro ao gerar resposta profunda: {e}"
    # Append assistant response and rerun
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.experimental_rerun() 