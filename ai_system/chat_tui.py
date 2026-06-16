from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Header, Footer, ScrollView, Input, Static
import glob, ast
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

class ChatApp(App):
    """Textual TUI for Evil Force JWT with deep-thinking chat panel and function list sidebar."""
    BINDINGS = [("ctrl+f", "toggle_functions", "Listar funções")]

    def __init__(self):
        super().__init__()
        self.engine = AIEngine()
        self.messages = []  # List of tuples (role, message)

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            # Sidebar for functions (hidden by default)
            self.func_panel = ScrollView(Static("\n".join(list_functions()), id="funcs"))
            yield self.func_panel
            # Main chat panel
            self.chat_panel = ScrollView(id="chat")
            yield self.chat_panel
        yield Input(placeholder="Digite sua mensagem e pressione Enter...", id="input")
        yield Footer()

    def on_mount(self):
        # Hide function panel initially
        self.func_panel.visible = False
        self.update_chat()

    def action_toggle_functions(self):
        # Toggle visibility of function list
        self.func_panel.visible = not self.func_panel.visible

    def update_chat(self):
        # Render chat history
        content = "\n".join(f"{role}: {msg}" for role, msg in self.messages)
        self.chat_panel.update(content)

    async def on_input_submitted(self, event):
        # Handle user input
        prompt = event.value
        self.messages.append(("Você", prompt))
        # Check for list functions command
        if "liste as funções" in prompt.lower():
            funcs = list_functions()
            reply = "**Funções encontradas:**\n" + "\n".join(funcs)
        else:
            # Use deep chain-of-thought for other queries
            try:
                reply = self.engine._chain_of_thought({"user_message": prompt}, {"type": "chat"})
                if not reply.strip():
                    reply = "Desculpe, não consegui gerar uma resposta aprofundada no momento."
            except Exception as e:
                reply = f"Erro ao gerar resposta profunda: {e}"
        self.messages.append(("Assistente", reply))
        self.update_chat()
        # Clear input
        self.query_one(Input).value = "" 