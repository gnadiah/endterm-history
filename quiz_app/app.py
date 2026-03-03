"""TUI Quiz App — Ôn tập Lịch Sử Việt Nam."""
from __future__ import annotations

import time

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Label,
    ProgressBar,
    Static,
)

from .data import QuizSession, get_sections, MCQuestion, TFQuestion
from .history import load_history, save_record


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Menu Screen
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class MenuScreen(Screen):
    BINDINGS = [
        Binding("1", "select('mix')", "Mix toàn bộ", show=True),
        Binding("2", "select('part1')", "Phần I", show=True),
        Binding("3", "select('part2')", "Phần II", show=True),
        Binding("4", "select('history')", "Lịch sử", show=True),
        Binding("q", "quit_app", "Thoát", show=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="menu-container"):
            yield Label("📚 ÔN TẬP LỊCH SỬ VIỆT NAM", id="menu-title")
            yield Label("Đề cương ôn thi HK2 — Khối 12", id="menu-subtitle")
            with Center():
                with Vertical(id="menu-buttons"):
                    yield Button("1. 🔀  Mix toàn bộ (Trắc nghiệm → Đúng sai)", id="btn-mix", classes="menu-btn", variant="primary")
                    yield Button("2. 📝  Phần I — Trắc nghiệm nhiều phương án", id="btn-part1", classes="menu-btn", variant="success")
                    yield Button("3. ✅  Phần II — Trắc nghiệm đúng sai", id="btn-part2", classes="menu-btn", variant="warning")
                    yield Button("4. 📊  Xem lịch sử làm bài", id="btn-history", classes="menu-btn", variant="default")
                    yield Button("Q. ❌  Thoát", id="btn-quit", classes="menu-btn", variant="error")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_map = {
            "btn-mix": "mix",
            "btn-part1": "part1",
            "btn-part2": "part2",
            "btn-history": "history",
            "btn-quit": "quit",
        }
        action = btn_map.get(event.button.id, "")
        if action == "quit":
            self.app.exit()
        elif action:
            self.action_select(action)

    def action_select(self, mode: str) -> None:
        if mode == "history":
            self.app.push_screen(HistoryScreen())
        elif mode == "part1":
            self.app.push_screen(SectionSelectScreen())
        elif mode == "part2":
            session = QuizSession(mode="part2", section=None)
            session.setup()
            self.app.push_screen(QuizScreen(session))
        elif mode == "mix":
            session = QuizSession(mode="mix", section=None)
            session.setup()
            self.app.push_screen(QuizScreen(session))

    def action_quit_app(self) -> None:
        self.app.exit()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Section Select Screen (for Part 1)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class SectionSelectScreen(Screen):
    BINDINGS = [
        Binding("0", "select_section('all')", "⓪ Tất cả", show=True),
        Binding("1", "select_section('0')", "① Bài 10", show=True),
        Binding("2", "select_section('1')", "② Bài 11", show=True),
        Binding("3", "select_section('2')", "③ CĐ6", show=True),
        Binding("escape", "go_back", "Quay lại", show=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        from .data import load_part1
        sections = get_sections()
        total_count = len(load_part1())
        with VerticalScroll(id="section-container"):
            yield Label("📖 Chọn bài học", id="section-title")
            with Center():
                with Vertical(id="section-buttons"):
                    yield Button(
                        f"0. 🔀  Tất cả ({total_count} câu)",
                        id="btn-all-sections",
                        classes="section-btn",
                        variant="primary",
                    )
                    for i, sec in enumerate(sections):
                        count = len(load_part1(sec))
                        yield Button(
                            f"{i+1}. {sec} ({count} câu)",
                            id=f"btn-sec-{i}",
                            classes="section-btn",
                            variant="success",
                        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-all-sections":
            self.action_select_section("all")
        elif event.button.id and event.button.id.startswith("btn-sec-"):
            idx = event.button.id.split("-")[-1]
            self.action_select_section(idx)

    def action_select_section(self, key: str) -> None:
        sections = get_sections()
        if key == "all":
            session = QuizSession(mode="part1", section=None)
            session.setup()
            self.app.push_screen(QuizScreen(session))
        else:
            idx = int(key)
            if idx < len(sections):
                session = QuizSession(mode="part1", section=sections[idx])
                session.setup()
                self.app.push_screen(QuizScreen(session))

    def action_go_back(self) -> None:
        self.app.pop_screen()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Quiz Screen
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class QuizScreen(Screen):
    BINDINGS = [
        Binding("1", "choose('1')", "① A/Đúng", show=True),
        Binding("2", "choose('2')", "② B/Sai", show=True),
        Binding("3", "choose('3')", "③ C", show=True),
        Binding("4", "choose('4')", "④ D", show=True),
        Binding("escape", "go_back", "Thoát", show=True),
    ]

    def __init__(self, session: QuizSession) -> None:
        super().__init__()
        self.session = session
        self.start_time = time.time()
        self._waiting_next = False

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="quiz-container"):
            yield Label("", id="quiz-progress-label")
            yield ProgressBar(total=100, show_percentage=False, show_eta=False, id="quiz-progress-bar")
            yield Static("", id="quiz-passage")
            yield Static("", id="quiz-question")
            yield Static("", id="quiz-sub-question")
            with Vertical(id="quiz-options"):
                yield Button("A.", id="opt-A", classes="option-btn")
                yield Button("B.", id="opt-B", classes="option-btn")
                yield Button("C.", id="opt-C", classes="option-btn")
                yield Button("D.", id="opt-D", classes="option-btn")
            with Horizontal(id="tf-options"):
                yield Button("1. ✅ Đúng", id="tf-true", classes="tf-btn", variant="success")
                yield Button("2. ❌ Sai", id="tf-false", classes="tf-btn", variant="error")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#quiz-passage", Static).display = False
        self.query_one("#quiz-sub-question", Static).display = False
        self.query_one("#tf-options", Horizontal).display = False
        self._render_question()

    def _reset_option_styles(self) -> None:
        """Reset all button styles between questions."""
        for letter in ["A", "B", "C", "D"]:
            try:
                btn = self.query_one(f"#opt-{letter}", Button)
                btn.remove_class("correct", "wrong")
                btn.blur()
            except Exception:
                pass
        try:
            true_btn = self.query_one("#tf-true", Button)
            false_btn = self.query_one("#tf-false", Button)
            true_btn.remove_class("correct", "wrong")
            false_btn.remove_class("correct", "wrong")
            true_btn.blur()
            false_btn.blur()
        except Exception:
            pass

    def _render_question(self) -> None:
        session = self.session

        if session.is_finished:
            self._show_results()
            return

        self._reset_option_styles()

        # Progress
        total = session.total_questions
        current = session.current_overall_index + 1
        progress_pct = int((current - 1) / total * 100) if total else 0
        self.query_one("#quiz-progress-label", Label).update(
            f"Câu {current}/{total}"
        )
        self.query_one("#quiz-progress-bar", ProgressBar).update(progress=progress_pct)

        if session.phase == "mc":
            self._render_mc()
        else:
            self._render_tf()

    def _render_mc(self) -> None:
        q = self.session.current_mc()
        if not q:
            return

        self.query_one("#quiz-passage", Static).display = False
        self.query_one("#quiz-sub-question", Static).display = False
        self.query_one("#tf-options", Horizontal).display = False
        self.query_one("#quiz-options", Vertical).display = True

        section_short = q.section.split(":")[-1].strip() if ":" in q.section else q.section
        self.query_one("#quiz-question", Static).update(
            f"[bold]Câu {q.number}[/bold] ({section_short})\n{q.question}"
        )

        # Update existing button labels
        letters = ["A", "B", "C", "D"]
        for i, letter in enumerate(letters):
            btn = self.query_one(f"#opt-{letter}", Button)
            if letter in q.options:
                btn.label = f"  {i+1}. {letter}. {q.options[letter]}"
                btn.display = True
            else:
                btn.display = False

    def _render_tf(self) -> None:
        q = self.session.current_tf()
        if not q:
            return

        self.query_one("#quiz-options", Vertical).display = False
        self.query_one("#tf-options", Horizontal).display = True

        # Show passage
        passage_widget = self.query_one("#quiz-passage", Static)
        passage_widget.display = True
        passage_text = q.passage[:500] + ("..." if len(q.passage) > 500 else "")
        passage_widget.update(f"[italic]{passage_text}[/italic]")

        # Show main question
        self.query_one("#quiz-question", Static).update(
            f"[bold]Câu {q.number}[/bold] — Đúng hay Sai?"
        )

        # Show current sub-question
        letters = ["A", "B", "C", "D"]
        sub_idx = self.session.tf_sub_index
        if sub_idx < len(letters):
            letter = letters[sub_idx]
            sub_q = q.sub_questions.get(letter, "")
            sub_widget = self.query_one("#quiz-sub-question", Static)
            sub_widget.display = True
            sub_widget.update(f"[bold]{letter}.[/bold] {sub_q}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if self._waiting_next:
            return

        btn_id = event.button.id or ""

        if btn_id.startswith("opt-"):
            letter = btn_id.split("-")[1]
            self._handle_mc_answer(letter)
        elif btn_id == "tf-true":
            self._handle_tf_answer(True)
        elif btn_id == "tf-false":
            self._handle_tf_answer(False)

    def action_choose(self, key: str) -> None:
        if self._waiting_next:
            return

        session = self.session
        if session.phase == "mc":
            letter_map = {"1": "A", "2": "B", "3": "C", "4": "D"}
            letter = letter_map.get(key)
            if letter:
                self._handle_mc_answer(letter)
        else:
            if key == "1":
                self._handle_tf_answer(True)
            elif key == "2":
                self._handle_tf_answer(False)

    def _handle_mc_answer(self, letter: str) -> None:
        q = self.session.current_mc()
        if not q:
            return

        correct = self.session.answer_mc(letter)

        # Color feedback
        for opt_letter in ["A", "B", "C", "D"]:
            try:
                btn = self.query_one(f"#opt-{opt_letter}", Button)
                if opt_letter == q.correct_answer:
                    btn.add_class("correct")
                elif opt_letter == letter and not correct:
                    btn.add_class("wrong")
            except Exception:
                pass

        self._waiting_next = True
        self.set_timer(0.8, self._next_mc)

    def _next_mc(self) -> None:
        self._waiting_next = False
        self.session.advance_mc()
        self._render_question()

    def _handle_tf_answer(self, is_true: bool) -> None:
        q = self.session.current_tf()
        if not q:
            return

        letters = ["A", "B", "C", "D"]
        sub_letter = letters[self.session.tf_sub_index]
        correct = self.session.answer_tf_sub(sub_letter, is_true)

        # Color feedback
        try:
            true_btn = self.query_one("#tf-true", Button)
            false_btn = self.query_one("#tf-false", Button)
            expected = q.answers.get(sub_letter, False)
            if expected:
                true_btn.add_class("correct")
                if not correct:
                    false_btn.add_class("wrong")
            else:
                false_btn.add_class("correct")
                if not correct:
                    true_btn.add_class("wrong")
        except Exception:
            pass

        self._waiting_next = True
        self.set_timer(0.8, self._next_tf)

    def _next_tf(self) -> None:
        self._waiting_next = False
        self.session.advance_tf_sub()
        self._render_question()

    def _show_results(self) -> None:
        duration = time.time() - self.start_time
        correct, total = self.session.get_score()
        wrong_ids = [q.id for q in self.session.get_wrong_mc_questions()] + \
                    [q.id for q in self.session.get_wrong_tf_questions()]
        save_record(
            mode=self.session.mode,
            section=self.session.section,
            correct=correct,
            total=total,
            wrong_ids=wrong_ids,
            duration_sec=duration,
        )
        # Switch to results screen
        self.app.switch_screen(ResultsScreen(self.session, duration))

    def action_go_back(self) -> None:
        self.app.pop_screen()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Results Screen
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ResultsScreen(Screen):
    BINDINGS = [
        Binding("r", "retry", "Làm lại câu sai", show=True),
        Binding("m", "go_menu", "Menu chính", show=True),
        Binding("escape", "go_menu", "Menu", show=False),
    ]

    def __init__(self, session: QuizSession, duration: float) -> None:
        super().__init__()
        self.session = session
        self.duration = duration

    def compose(self) -> ComposeResult:
        yield Header()
        correct, total = self.session.get_score()
        wrong_count = total - correct
        pct = int(correct / total * 100) if total else 0
        mins = int(self.duration // 60)
        secs = int(self.duration % 60)

        with VerticalScroll(id="results-container"):
            yield Label("🏆 KẾT QUẢ", id="results-title")

            if pct >= 80:
                emoji = "🎉"
            elif pct >= 60:
                emoji = "👍"
            else:
                emoji = "💪"

            yield Label(
                f"{emoji} Đúng: [bold green]{correct}[/bold green] / {total} "
                f"([bold]{pct}%[/bold])",
                id="results-score",
            )
            yield Label(f"⏱️ Thời gian: {mins}:{secs:02d}", id="results-time")

            if wrong_count > 0:
                yield Label(
                    f"❌ Sai {wrong_count} câu:",
                    id="results-wrong-title",
                )
                wrong_text = self._build_wrong_list()
                yield Static(wrong_text, id="results-wrong-list")

                with Horizontal(id="results-buttons"):
                    yield Button(
                        "🔄 Làm lại câu sai (R)",
                        id="btn-retry",
                        classes="results-btn",
                        variant="warning",
                    )
                    yield Button(
                        "🏠 Menu chính (M)",
                        id="btn-menu",
                        classes="results-btn",
                        variant="primary",
                    )
            else:
                yield Label("🎊 [bold green]Tuyệt vời! Bạn đã trả lời đúng tất cả![/bold green]")
                with Horizontal(id="results-buttons"):
                    yield Button(
                        "🏠 Menu chính (M)",
                        id="btn-menu",
                        classes="results-btn",
                        variant="primary",
                    )
        yield Footer()

    def _build_wrong_list(self) -> str:
        lines = []

        for idx in self.session.mc_wrong:
            q = self.session.mc_questions[idx]
            user_ans = self.session.mc_answers.get(idx, "?")
            lines.append(
                f"[bold red]✗[/bold red] Câu {q.number}: {q.question[:60]}...\n"
                f"   Bạn chọn: [red]{user_ans}[/red] | Đáp án: [green]{q.correct_answer}. "
                f"{q.options.get(q.correct_answer, '')}[/green]\n"
            )

        for idx in self.session.tf_wrong:
            q = self.session.tf_questions[idx]
            user_ans = self.session.tf_answers.get(idx, {})
            wrong_subs = []
            for letter in ["A", "B", "C", "D"]:
                if user_ans.get(letter) != q.answers.get(letter):
                    expected = "Đúng" if q.answers.get(letter) else "Sai"
                    wrong_subs.append(f"{letter}→{expected}")
            lines.append(
                f"[bold red]✗[/bold red] ĐS Câu {q.number}: {q.question[:50]}...\n"
                f"   Sai ở: [red]{', '.join(wrong_subs)}[/red]\n"
            )

        return "\n".join(lines) if lines else ""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-retry":
            self.action_retry()
        elif event.button.id == "btn-menu":
            self.action_go_menu()

    def action_retry(self) -> None:
        wrong_mc = self.session.get_wrong_mc_questions()
        wrong_tf = self.session.get_wrong_tf_questions()
        if not wrong_mc and not wrong_tf:
            self.action_go_menu()
            return

        new_session = QuizSession(mode=self.session.mode, section=self.session.section)
        new_session.setup_retry(wrong_mc, wrong_tf)
        self.app.switch_screen(QuizScreen(new_session))

    def action_go_menu(self) -> None:
        self.app.switch_screen(MenuScreen())


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# History Screen
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class HistoryScreen(Screen):
    BINDINGS = [Binding("escape", "go_back", "Quay lại", show=True)]

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="history-container"):
            yield Label("📊 Lịch sử làm bài", id="history-title")
            yield DataTable(id="history-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#history-table", DataTable)
        table.add_columns("Thời gian", "Chế độ", "Điểm", "Tỉ lệ", "Thời lượng")

        history = load_history()
        for record in reversed(history[-20:]):  # Last 20
            ts = record.get("timestamp", "")[:16].replace("T", " ")
            mode = record.get("mode", "?")
            section = record.get("section", "")
            mode_str = {
                "mix": "Mix toàn bộ",
                "part1": f"Phần I{(' — ' + section[:20]) if section else ''}",
                "part2": "Phần II",
            }.get(mode, mode)
            correct = record.get("correct", 0)
            total = record.get("total", 0)
            pct = f"{int(correct/total*100)}%" if total else "0%"
            dur = record.get("duration_sec", 0)
            dur_str = f"{int(dur//60)}:{int(dur%60):02d}"

            table.add_row(ts, mode_str, f"{correct}/{total}", pct, dur_str)

    def action_go_back(self) -> None:
        self.app.pop_screen()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main App
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class QuizApp(App):
    TITLE = "Ôn tập Lịch Sử"
    SUB_TITLE = "Đề cương HK2 — Khối 12"
    CSS_PATH = "styles.tcss"
    SCREENS = {"menu": MenuScreen}

    def on_mount(self) -> None:
        self.push_screen(MenuScreen())


def main():
    app = QuizApp()
    app.run(mouse=True)


if __name__ == "__main__":
    main()
