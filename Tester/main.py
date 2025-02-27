
import truffle

class Tester:
    def __init__(self):
        self.client = truffle.TruffleClient()
    
    # All tool calls must start with a capital letter! 
    @truffle.tool(
        description="Replace this with a description of the tool.",
        icon="brain"
    )
    @truffle.args(user_input="A description of the argument")
    def TesterTool(self, user_input: str) -> str:
        """
        Replace this text with a basic description of what this function does.
        """
        # Implement your tool logic here
        pass

if __name__ == "__main__":
    app = truffle.TruffleApp(Tester())
    app.launch()
