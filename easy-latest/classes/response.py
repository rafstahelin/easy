from rich.console import Console
from rich.table import Table

class Response:

    def __init__(self):
        self.console = Console()

    def input(self, msg="", mode=""):
        if mode == 'i':
            self.console.print(f"[bold blue]{msg}[/bold blue]")
        if mode == 'e':
            self.console.print(f"[bold red]{msg}[/bold red]")
        if mode == 's':
            self.console.print(f"[bold green]{msg}[/bold green]")
        if mode == 'n':
            self.console.print(f"[bold white]{msg}[/bold white]")        
        choice = self.console.input("> ")
        return choice

    def print(self, msg="", mode=""):
        if mode == 'i':
            self.console.print(f"[bold blue]{msg}[/bold blue]")
        if mode == 'e':
            self.console.print(f"[bold red]{msg}[/bold red]")
        if mode == 's':
            self.console.print(f"[bold green]{msg}[/bold green]")
        if mode == 'n':
            self.console.print(f"[bold white]{msg}[/bold white]")

    def edit_table(self, title="Table", columns=[], rows=[]):
        # self.console.clear()

        table = Table(title=title, show_lines=True)

        for i in range(len(columns)): 
            column = columns[i]
            style = "white"
            justify = "left"

            if i == 0:
                style = "bold magenta"
                justify = "right"
            elif i == 1:
                style = "bold yellow"

            table.add_column(column, style=style, justify=justify)

        for row in rows:
            table.add_row(*[str(row[i]) for i in range(len(columns))])

        self.console.print(table)