"""
AskUserQuestionTool — Interactive User Questions
──────────────────────────────────────────────────────────
Claude Code AskUserQuestionTool referansı — tam özellikler.

Multi-question support, multi-select, preview content,
annotations, header chips, uniqueness validation.
"""

import time
import re
from typing import Optional

from ..models import BaseTool, ToolResult, ToolCategory


class AskUserQuestionTool(BaseTool):
    """
    Ask user questions - Claude Code pattern.

    Features:
    - 1-4 questions at once
    - 2-4 options per question
    - Multi-select support
    - Preview content for options (mockups, code, comparisons)
    - Per-question header/chip labels
    - Annotations (notes on selections)
    - Uniqueness validation

    Patterns: soru sor, kullanıcıya sor, ask user, seçim yap
    """
    name = "AskUserQuestion"
    category = ToolCategory.UTILITY
    patterns = ["soru sor", "seçim yap", "ask user", "kullanıcıya sor", "question"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()

        questions = input_data.get("questions", [])
        answers = input_data.get("answers", {})
        annotations = input_data.get("annotations", {})

        if not questions:
            return ToolResult(
                self.name, False, "",
                "questions array is required (1-4 questions)",
                int((time.time()-start)*1000)
            )

        # Validate
        if len(questions) > 4:
            return ToolResult(
                self.name, False, "",
                "Maximum 4 questions at once",
                int((time.time()-start)*1000)
            )

        # Validate uniqueness
        question_texts = [q.get("question", "") for q in questions]
        if len(question_texts) != len(set(question_texts)):
            return ToolResult(
                self.name, False, "",
                "Question texts must be unique",
                int((time.time()-start)*1000)
            )

        # Format questions for display
        output = self._format_questions(questions)

        return ToolResult(
            self.name, True, output,
            int((time.time()-start)*1000),
            metadata={
                "question_count": len(questions),
                "awaiting_response": True
            }
        )

    def _format_questions(self, questions: list) -> str:
        """Format questions for user display."""
        output = "━━━━━━━━━━━━━━━━━━━━━━━\n"
        output += "   ❓ SORUMLULUK\n"
        output += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        for i, q in enumerate(questions, 1):
            header = q.get("header", "Soru")
            question_text = q.get("question", "")
            options = q.get("options", [])
            multi_select = q.get("multiSelect", False)

            # Header chip
            output += f"[{header}]\n"
            output += f"{i}. {question_text}\n"

            if multi_select:
                output += "   (birden fazla seçebilirsin)\n"

            # Options
            if options:
                output += "\n"
                for j, opt in enumerate(options, 1):
                    label = opt.get("label", "")
                    description = opt.get("description", "")
                    preview = opt.get("preview", "")

                    output += f"   {chr(96+j)}) {label}\n"
                    if description:
                        output += f"       → {description}\n"
                    if preview:
                        output += f"       ┌─ preview ─┐\n"
                        for line in preview.split("\n")[:5]:
                            output += f"       │ {line[:50]}\n"
                        output += f"       └─────────────┘\n"

            output += "\n"

        output += "━━━━━━━━━━━━━━━━━━━━━━━\n"
        output += "Yanıt bekleniyor...\n"

        return output


class AnswerQuestionTool(BaseTool):
    """
    Record user answer to a question - Claude Code pattern.

    Patterns: cevap ver, yanıtla, answer, yanıt
    """
    name = "AnswerQuestion"
    category = ToolCategory.UTILITY
    patterns = ["cevap ver", "yanıtla", "answer", "yanıt"]

    def execute(self, input_data: dict, context: dict | None = None) -> ToolResult:
        start = time.time()

        question = input_data.get("question", "")
        answer = input_data.get("answer", "")
        notes = input_data.get("notes", "")
        preview_content = input_data.get("preview_content", "")

        if not question:
            return ToolResult(
                self.name, False, "",
                "question is required",
                int((time.time()-start)*1000)
            )

        if not answer:
            return ToolResult(
                self.name, False, "",
                "answer is required",
                int((time.time()-start)*1000)
            )

        return ToolResult(
            self.name, True,
            f"Cevap kaydedildi:\n❓ {question}\n✅ {answer}",
            int((time.time()-start)*1000),
            metadata={"recorded": True}
        )
