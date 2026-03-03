"""Data models and quiz session management."""
from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass, field


@dataclass
class MCQuestion:
    """Multiple choice question (Part 1)."""
    section: str
    number: int
    question: str
    options: dict[str, str]  # {'A': '...', 'B': '...', ...}
    correct_answer: str  # 'A', 'B', 'C', or 'D'

    @property
    def id(self) -> str:
        return f"p1_{self.section[:20]}_{self.number}"


@dataclass
class TFQuestion:
    """True/False question (Part 2)."""
    section: str
    number: int
    question: str
    passage: str
    sub_questions: dict[str, str]  # {'A': '...', 'B': '...', ...}
    answers: dict[str, bool]  # {'A': True, 'B': False, ...}

    @property
    def id(self) -> str:
        return f"p2_{self.number}"


def _project_root() -> str:
    """Return path to the project root (parent of quiz_app/)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _data_dir() -> str:
    """Return path to the data/ directory."""
    return os.path.join(_project_root(), "data")


def load_part1(section: str | None = None) -> list[MCQuestion]:
    """Load Part 1 questions, optionally filtered by section."""
    path = os.path.join(_data_dir(), "phan1_trac_nghiem.json")
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    questions = [MCQuestion(**q) for q in raw]
    if section:
        questions = [q for q in questions if q.section == section]
    return questions


def load_part2() -> list[TFQuestion]:
    """Load Part 2 questions."""
    path = os.path.join(_data_dir(), "phan2_dung_sai.json")
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [TFQuestion(**q) for q in raw]


def get_sections() -> list[str]:
    """Get unique section names from Part 1."""
    questions = load_part1()
    seen = []
    for q in questions:
        if q.section not in seen:
            seen.append(q.section)
    return seen


@dataclass
class QuizSession:
    """Tracks state for one quiz attempt."""
    mode: str  # 'part1', 'part2', 'mix'
    section: str | None  # For part1 section filter
    mc_questions: list[MCQuestion] = field(default_factory=list)
    tf_questions: list[TFQuestion] = field(default_factory=list)

    # Current position
    phase: str = "mc"  # 'mc' or 'tf'
    mc_index: int = 0
    tf_index: int = 0
    tf_sub_index: int = 0  # Which sub-question (A/B/C/D) within a TF question

    # User answers
    mc_answers: dict[int, str] = field(default_factory=dict)  # idx -> chosen letter
    tf_answers: dict[int, dict[str, bool]] = field(default_factory=dict)  # idx -> {A: True, ...}

    # Results
    mc_wrong: list[int] = field(default_factory=list)  # indices of wrong MC questions
    tf_wrong: list[int] = field(default_factory=list)  # indices of wrong TF questions

    def setup(self, shuffle: bool = True) -> None:
        """Initialize questions based on mode."""
        if self.mode == "part1":
            self.mc_questions = load_part1(self.section)
            self.tf_questions = []
        elif self.mode == "part2":
            self.mc_questions = []
            self.tf_questions = load_part2()
            self.phase = "tf"
        elif self.mode == "mix":
            self.mc_questions = load_part1()
            self.tf_questions = load_part2()

        if shuffle:
            random.shuffle(self.mc_questions)
            random.shuffle(self.tf_questions)

        self.mc_index = 0
        self.tf_index = 0
        self.tf_sub_index = 0
        self.mc_answers = {}
        self.tf_answers = {}
        self.mc_wrong = []
        self.tf_wrong = []
        self.phase = "mc" if self.mc_questions else "tf"

    def setup_retry(self, wrong_mc: list[MCQuestion], wrong_tf: list[TFQuestion]) -> None:
        """Setup a retry session with only wrong questions."""
        self.mc_questions = list(wrong_mc)
        self.tf_questions = list(wrong_tf)
        random.shuffle(self.mc_questions)
        random.shuffle(self.tf_questions)
        self.mc_index = 0
        self.tf_index = 0
        self.tf_sub_index = 0
        self.mc_answers = {}
        self.tf_answers = {}
        self.mc_wrong = []
        self.tf_wrong = []
        self.phase = "mc" if self.mc_questions else "tf"

    @property
    def total_mc(self) -> int:
        return len(self.mc_questions)

    @property
    def total_tf(self) -> int:
        return len(self.tf_questions)

    @property
    def total_questions(self) -> int:
        return self.total_mc + self.total_tf

    @property
    def current_overall_index(self) -> int:
        if self.phase == "mc":
            return self.mc_index
        return self.total_mc + self.tf_index

    @property
    def is_finished(self) -> bool:
        mc_done = self.mc_index >= self.total_mc
        tf_done = self.tf_index >= self.total_tf
        if self.phase == "mc":
            if mc_done:
                if self.tf_questions:
                    return tf_done
                return True
            return False
        return tf_done

    def current_mc(self) -> MCQuestion | None:
        if self.phase == "mc" and self.mc_index < self.total_mc:
            return self.mc_questions[self.mc_index]
        return None

    def current_tf(self) -> TFQuestion | None:
        if self.phase == "tf" and self.tf_index < self.total_tf:
            return self.tf_questions[self.tf_index]
        return None

    def answer_mc(self, choice: str) -> bool:
        """Answer current MC question. Returns True if correct."""
        q = self.current_mc()
        if not q:
            return False
        self.mc_answers[self.mc_index] = choice
        correct = choice == q.correct_answer
        if not correct:
            self.mc_wrong.append(self.mc_index)
        return correct

    def answer_tf_sub(self, sub_letter: str, is_true: bool) -> bool:
        """Answer one sub-question of current TF question. Returns True if correct."""
        q = self.current_tf()
        if not q:
            return False
        if self.tf_index not in self.tf_answers:
            self.tf_answers[self.tf_index] = {}
        self.tf_answers[self.tf_index][sub_letter] = is_true
        return is_true == q.answers.get(sub_letter, False)

    def advance_mc(self) -> None:
        """Move to next MC question, or switch to TF phase."""
        self.mc_index += 1
        if self.mc_index >= self.total_mc and self.tf_questions:
            self.phase = "tf"

    def advance_tf_sub(self) -> bool:
        """Advance to next sub-question. Returns True if moved to next TF question."""
        letters = ["A", "B", "C", "D"]
        self.tf_sub_index += 1
        if self.tf_sub_index >= len(letters):
            # Check if this TF question has any wrong subs
            q = self.current_tf()
            if q and self.tf_index in self.tf_answers:
                user_ans = self.tf_answers[self.tf_index]
                for letter in letters:
                    if user_ans.get(letter) != q.answers.get(letter):
                        self.tf_wrong.append(self.tf_index)
                        break
            self.tf_sub_index = 0
            self.tf_index += 1
            return True
        return False

    def get_score(self) -> tuple[int, int]:
        """Return (correct, total)."""
        mc_correct = self.total_mc - len(self.mc_wrong)
        tf_correct = self.total_tf - len(self.tf_wrong)
        return mc_correct + tf_correct, self.total_questions

    def get_wrong_mc_questions(self) -> list[MCQuestion]:
        return [self.mc_questions[i] for i in self.mc_wrong]

    def get_wrong_tf_questions(self) -> list[TFQuestion]:
        return [self.tf_questions[i] for i in self.tf_wrong]
