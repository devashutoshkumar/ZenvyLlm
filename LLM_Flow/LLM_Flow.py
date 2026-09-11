from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.align import Align
from rich.pretty import Pretty
from rich import box

from Core.Manager import Manager
from Core.Schemas import TaskState
from Core.Policy import PolicyEngine
from Core.Execution import Executor
from Core.Verification import Verifier


console = Console()


# ============================================================
# UI
# ============================================================

def show_banner():
    banner = Text()

    banner.append(
        "ZENVY\n",
        style="bold bright_cyan"
    )

    banner.append(
        "LOCAL AUTONOMOUS AGENT RUNTIME\n",
        style="bold white"
    )

    banner.append(
        "Manager  →  Policy  →  Executor  →  Verifier",
        style="dim"
    )

    console.print(
        Panel(
            Align.center(banner),
            border_style="bright_cyan",
            box=box.DOUBLE,
            padding=(1, 2)
        )
    )


def show_task(task: str):
    console.print(
        Panel(
            task,
            title="[bold white]TASK[/bold white]",
            title_align="left",
            border_style="white",
            padding=(1, 2)
        )
    )


def create_info_table():
    table = Table.grid(
        padding=(0, 2)
    )

    table.add_column(
        style="bold dim",
        no_wrap=True,
        width=14
    )

    table.add_column()

    return table


# ============================================================
# MANAGER
# ============================================================

def show_action(action):

    table = create_info_table()

    table.add_row(
        "Type",
        str(action.action_type)
    )

    table.add_row(
        "Description",
        action.description
    )

    table.add_row(
        "Capabilities",
        Pretty(action.capabilities)
    )

    table.add_row(
        "Tool",
        str(action.tool)
    )

    table.add_row(
        "Risk",
        str(action.risk)
    )

    # Very useful during demos
    if getattr(action, "action_input", None):
        table.add_row(
            "Input",
            Pretty(action.action_input)
        )

    console.print(
        Panel(
            table,
            title="[bold cyan]MANAGER[/bold cyan]",
            subtitle="LLM proposed next action",
            border_style="cyan",
            box=box.ROUNDED
        )
    )


# ============================================================
# POLICY
# ============================================================

def show_policy(decision):

    table = create_info_table()

    effect = str(decision.effect)

    if effect == "ALLOW":
        effect_text = Text("ALLOW", style="bold green")

    elif effect == "DENY":
        effect_text = Text("DENY", style="bold red")

    elif effect == "REQUIRE_APPROVAL":
        effect_text = Text(
            "REQUIRE APPROVAL",
            style="bold yellow"
        )

    else:
        effect_text = Text(effect)

    table.add_row(
        "Decision",
        effect_text
    )

    table.add_row(
        "Reason",
        decision.reason
    )

    table.add_row(
        "Constraints",
        Pretty(decision.constraints)
    )

    console.print(
        Panel(
            table,
            title="[bold yellow]POLICY ENGINE[/bold yellow]",
            subtitle="Capability and safety enforcement",
            border_style="yellow",
            box=box.ROUNDED
        )
    )


# ============================================================
# EXECUTION
# ============================================================

def show_execution(result):

    table = create_info_table()

    success_text = (
        Text("SUCCESS", style="bold green")
        if result.success
        else Text("FAILED", style="bold red")
    )

    table.add_row(
        "Status",
        success_text
    )

    table.add_row(
        "Model",
        str(result.model_used)
    )

    table.add_row(
        "Tool",
        str(result.tool_used)
    )

    table.add_row(
        "Output",
        Pretty(result.output)
    )

    console.print(
        Panel(
            table,
            title="[bold magenta]EXECUTOR[/bold magenta]",
            subtitle="Controlled execution environment",
            border_style="magenta",
            box=box.ROUNDED
        )
    )


# ============================================================
# VERIFICATION
# ============================================================

def show_verification(verification):

    table = create_info_table()

    if verification.passed:

        status = Text(
            "✓ VERIFIED",
            style="bold green"
        )

    else:

        status = Text(
            "✗ FAILED",
            style="bold red"
        )

    table.add_row(
        "Status",
        status
    )

    table.add_row(
        "Reason",
        verification.reason
    )

    console.print(
        Panel(
            table,
            title="[bold blue]VERIFIER[/bold blue]",
            subtitle="Independent result validation",
            border_style="blue",
            box=box.ROUNDED
        )
    )


# ============================================================
# LOADING
# ============================================================

def manager_loading(manager, state):

    with console.status(
        "[bold cyan]◉ Manager is reasoning about the next action...[/bold cyan]",
        spinner="dots"
    ):
        return manager.next_action(state)


def policy_loading(policy, action):

    with console.status(
        "[bold yellow]◉ Policy engine is evaluating the action...[/bold yellow]",
        spinner="dots"
    ):
        return policy.evaluate(action)


def execution_loading(executor, action, decision):

    tool = getattr(action, "tool", None)

    message = (
        f"Executing tool [bold]{tool}[/bold]..."
        if tool
        else "Executing approved action..."
    )

    with console.status(
        f"[bold magenta]◉ {message}[/bold magenta]",
        spinner="dots"
    ):
        return executor.execute(
            action,
            decision
        )


def verification_loading(
    verifier,
    task,
    action,
    result
):

    with console.status(
        "[bold blue]◉ Verifier is checking the result...[/bold blue]",
        spinner="dots"
    ):
        return verifier.verify(
            task,
            action,
            result
        )


# ============================================================
# AGENT
# ============================================================

def run_agent(
    task: str,
    max_attempts: int = 5
):

    manager = Manager()
    policy = PolicyEngine()
    executor = Executor()
    verifier = Verifier()

    state = TaskState(
        task=task
    )

    console.print()

    show_task(task)

    for attempt in range(
        1,
        max_attempts + 1
    ):

        console.print()

        console.print(
            Rule(
                f"[bold white]"
                f"Iteration {attempt}/{max_attempts}"
                f"[/bold white]",
                style="dim"
            )
        )

        # ====================================================
        # 1. MANAGER
        # ====================================================

        console.print(
            "[dim]1/4[/dim] "
            "[cyan]Manager[/cyan]"
        )

        try:

            action = manager_loading(
                manager,
                state
            )

        except Exception as error:

            console.print(
                Panel(
                    str(error),
                    title="[bold red]MANAGER ERROR[/bold red]",
                    border_style="red"
                )
            )

            return state

        console.print(
            "[green]✓[/green] Manager completed"
        )

        show_action(action)

        # ----------------------------------------------------
        # FINISH
        # ----------------------------------------------------

        if action.action_type == "finish":

            console.print(
                Panel(
                    action.description,
                    title="[bold green]✓ TASK COMPLETED[/bold green]",
                    border_style="green",
                    box=box.DOUBLE
                )
            )

            state.completed = True

            return state

        # ====================================================
        # 2. POLICY
        # ====================================================

        console.print(
            "[dim]2/4[/dim] "
            "[yellow]Policy[/yellow]"
        )

        try:

            decision = policy_loading(
                policy,
                action
            )

        except Exception as error:

            console.print(
                Panel(
                    str(error),
                    title="[bold red]POLICY ERROR[/bold red]",
                    border_style="red"
                )
            )

            return state

        console.print(
            "[green]✓[/green] Policy evaluation completed"
        )

        show_policy(decision)

        # ----------------------------------------------------
        # DENY
        # ----------------------------------------------------

        if decision.effect == "DENY":

            state.context.append({
                "action":
                    action.model_dump(),

                "policy":
                    decision.model_dump(),

                "feedback":
                    (
                        "Action denied by policy. "
                        "Find another approach."
                    )
            })

            console.print(
                Panel(
                    "The proposed action was blocked. "
                    "The manager will attempt to find "
                    "an alternative approach.",
                    title="[bold red]ACTION BLOCKED[/bold red]",
                    border_style="red"
                )
            )

            continue

        # ----------------------------------------------------
        # HUMAN APPROVAL
        # ----------------------------------------------------

        if decision.effect == "REQUIRE_APPROVAL":

            console.print(
                Panel(
                    decision.reason,
                    title=(
                        "[bold yellow]"
                        "⚠ HUMAN APPROVAL REQUIRED"
                        "[/bold yellow]"
                    ),
                    border_style="yellow"
                )
            )

            approved = Confirm.ask(
                "[bold yellow]"
                "Approve this action?"
                "[/bold yellow]",
                default=False
            )

            if not approved:

                console.print(
                    "[red]✗ Action rejected by user.[/red]"
                )

                state.context.append({
                    "action":
                        action.model_dump(),

                    "policy":
                        decision.model_dump(),

                    "feedback":
                        (
                            "The human operator rejected "
                            "this action. Find another "
                            "approach."
                        )
                })

                continue

            console.print(
                "[green]✓ Action approved by user.[/green]"
            )

            # Pydantic v2 model
            decision = decision.model_copy(
                update={
                    "effect": "ALLOW"
                }
            )

        # ====================================================
        # 3. EXECUTION
        # ====================================================

        console.print(
            "[dim]3/4[/dim] "
            "[magenta]Execution[/magenta]"
        )

        try:

            result = execution_loading(
                executor,
                action,
                decision
            )

        except Exception as error:

            console.print(
                Panel(
                    str(error),
                    title="[bold red]EXECUTION ERROR[/bold red]",
                    border_style="red"
                )
            )

            state.context.append({
                "previous_action":
                    action.model_dump(),

                "execution_error":
                    str(error),

                "instruction":
                    (
                        "Execution raised an exception. "
                        "Choose another approach."
                    )
            })

            continue

        console.print(
            "[green]✓[/green] Execution completed"
        )

        show_execution(result)

        # ====================================================
        # 4. VERIFICATION
        # ====================================================

        console.print(
            "[dim]4/4[/dim] "
            "[blue]Verification[/blue]"
        )

        try:

            verification = verification_loading(
                verifier,
                state.task,
                action,
                result
            )

        except Exception as error:

            console.print(
                Panel(
                    str(error),
                    title="[bold red]VERIFIER ERROR[/bold red]",
                    border_style="red"
                )
            )

            return state

        console.print(
            "[green]✓[/green] Verification completed"
        )

        show_verification(
            verification
        )

        # ====================================================
        # PASS
        # ====================================================

        if verification.passed:

            console.print()

            console.print(
                Panel(
                    Pretty(result.output),
                    title="[bold green]✓ VERIFIED RESULT[/bold green]",
                    subtitle="Execution satisfied the requested task",
                    border_style="green",
                    box=box.DOUBLE
                )
            )

            state.completed = True

            return state

        # ====================================================
        # FAIL
        # ====================================================

        console.print(
            Panel(
                verification.reason,
                title="[bold red]VERIFICATION FAILED[/bold red]",
                subtitle="Feedback returned to Manager",
                border_style="red"
            )
        )

        state.context.append({
            "previous_action":
                action.model_dump(),

            "execution_result":
                result.model_dump(),

            "verification":
                verification.model_dump(),

            "instruction":
                (
                    "The previous attempt failed "
                    "verification. Use the verifier "
                    "feedback and choose a corrected "
                    "next action."
                )
        })

    console.print(
        Panel(
            (
                f"Agent stopped after "
                f"{max_attempts} iterations."
            ),
            title="[bold red]MAXIMUM RETRIES REACHED[/bold red]",
            border_style="red"
        )
    )

    return state


# ============================================================
# COMMANDS
# ============================================================

def show_help():

    table = Table(
        title="Available Commands",
        box=box.SIMPLE,
        header_style="bold cyan"
    )

    table.add_column(
        "Command",
        style="cyan"
    )

    table.add_column(
        "Description"
    )

    table.add_row(
        "/help",
        "Show this menu"
    )

    table.add_row(
        "/clear",
        "Clear the terminal"
    )

    table.add_row(
        "/exit",
        "Exit Sovereign"
    )

    console.print(table)


# ============================================================
# INTERACTIVE CLI
# ============================================================

def run_cli():

    console.clear()

    show_banner()

    console.print(
        "\n[dim]"
        "Enter a task for the agent."
        "\n"
        "Commands: /help  /clear  /exit"
        "[/dim]"
    )

    while True:

        console.print()

        try:

            task = Prompt.ask(
                "[bold bright_cyan]"
                "Zenvy"
                "[/bold bright_cyan]"
                " [bold white]›[/bold white]"
            ).strip()

        except (KeyboardInterrupt, EOFError):

            console.print(
                "\n[dim]Session terminated.[/dim]"
            )

            break

        if not task:
            continue

        command = task.lower()

        # EXIT
        if command in {
            "/exit",
            "/quit",
            "exit",
            "quit"
        }:

            console.print(
                "\n[bright_cyan]"
                "Zenvy runtime terminated."
                "[/bright_cyan]"
            )

            break

        # CLEAR
        if command == "/clear":

            console.clear()

            show_banner()

            continue

        # HELP
        if command == "/help":

            show_help()

            continue

        # RUN TASK
        try:

            run_agent(task)

        except KeyboardInterrupt:

            console.print(
                "\n[yellow]"
                "! Current task interrupted."
                "[/yellow]"
            )

        except Exception:

            console.print(
                Panel(
                    (
                        "An unexpected runtime error "
                        "occurred."
                    ),
                    title="[bold red]RUNTIME ERROR[/bold red]",
                    border_style="red"
                )
            )

            console.print_exception(
                show_locals=False
            )


# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":
    run_cli()