import ast
import re
from typing import List, Dict, Any, Optional

class CodeChunk:
    def __init__(
        self,
        content: str,
        file_path: str,
        doc_type: str = "code",
        language: str = "python",
        function_name: Optional[str] = None,
        class_name: Optional[str] = None,
        line_start: int = 1,
        line_end: int = 1,
        repository: str = "acme/ecommerce-platform",
        commit_sha: Optional[str] = "main",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.content = content
        self.file_path = file_path
        self.doc_type = doc_type
        self.language = language
        self.function_name = function_name
        self.class_name = class_name
        self.line_start = line_start
        self.line_end = line_end
        self.repository = repository
        self.commit_sha = commit_sha
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "file_path": self.file_path,
            "doc_type": self.doc_type,
            "language": self.language,
            "function_name": self.function_name,
            "class_name": self.class_name,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "repository": self.repository,
            "commit_sha": self.commit_sha,
            "metadata": self.metadata,
        }

class ASTCodeChunker:
    """AST-aware code chunker that extracts complete functions, classes, and top-level definitions."""

    @staticmethod
    def chunk_python_code(code_str: str, file_path: str, repository: str = "acme/ecommerce-platform") -> List[CodeChunk]:
        chunks: List[CodeChunk] = []
        lines = code_str.splitlines()

        try:
            tree = ast.parse(code_str, filename=file_path)
        except SyntaxError:
            # Fallback to line-based chunking if AST parsing fails
            return ASTCodeChunker._line_fallback_chunks(code_str, file_path, repository)

        for node in tree.body:
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                start = node.lineno
                end = getattr(node, "end_lineno", start + len(ast.unparse(node).splitlines()))
                snippet = "\n".join(lines[start - 1:end])
                chunks.append(
                    CodeChunk(
                        content=snippet,
                        file_path=file_path,
                        doc_type="code_function",
                        language="python",
                        function_name=node.name,
                        class_name=None,
                        line_start=start,
                        line_end=end,
                        repository=repository,
                        metadata={"docstring": ast.get_docstring(node)}
                    )
                )
            elif isinstance(node, ast.ClassDef):
                # Chunk class overview and methods
                class_start = node.lineno
                class_end = getattr(node, "end_lineno", class_start + len(lines))
                class_snippet = "\n".join(lines[class_start - 1:class_end])

                chunks.append(
                    CodeChunk(
                        content=class_snippet,
                        file_path=file_path,
                        doc_type="code_class",
                        language="python",
                        class_name=node.name,
                        line_start=class_start,
                        line_end=class_end,
                        repository=repository,
                        metadata={"docstring": ast.get_docstring(node)}
                    )
                )

                # Individual methods inside class
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                        m_start = item.lineno
                        m_end = getattr(item, "end_lineno", m_start)
                        m_snippet = "\n".join(lines[m_start - 1:m_end])
                        chunks.append(
                            CodeChunk(
                                content=m_snippet,
                                file_path=file_path,
                                doc_type="code_method",
                                language="python",
                                function_name=item.name,
                                class_name=node.name,
                                line_start=m_start,
                                line_end=m_end,
                                repository=repository,
                                metadata={"docstring": ast.get_docstring(item)}
                            )
                        )

        # If no functions or classes found (e.g. config or script), chunk whole file
        if not chunks and code_str.strip():
            chunks.append(
                CodeChunk(
                    content=code_str,
                    file_path=file_path,
                    doc_type="code_module",
                    language="python",
                    line_start=1,
                    line_end=len(lines),
                    repository=repository
                )
            )

        return chunks

    @staticmethod
    def _line_fallback_chunks(code_str: str, file_path: str, repository: str) -> List[CodeChunk]:
        lines = code_str.splitlines()
        chunks = []
        chunk_size = 50
        for i in range(0, len(lines), chunk_size):
            end = min(len(lines), i + chunk_size)
            snippet = "\n".join(lines[i:end])
            chunks.append(
                CodeChunk(
                    content=snippet,
                    file_path=file_path,
                    doc_type="code_snippet",
                    language="python",
                    line_start=i + 1,
                    line_end=end,
                    repository=repository
                )
            )
        return chunks

class MarkdownDocumentChunker:
    """Splits markdown and documentation files based on semantic headers."""

    @staticmethod
    def chunk_markdown(doc_str: str, file_path: str, repository: str = "acme/ecommerce-platform") -> List[CodeChunk]:
        chunks: List[CodeChunk] = []
        lines = doc_str.splitlines()
        current_header = "Introduction"
        current_lines: List[str] = []
        start_line = 1

        for idx, line in enumerate(lines, start=1):
            if re.match(r"^#{1,3}\s+", line):
                if current_lines:
                    chunks.append(
                        CodeChunk(
                            content="\n".join(current_lines).strip(),
                            file_path=file_path,
                            doc_type="documentation",
                            language="markdown",
                            function_name=current_header,
                            line_start=start_line,
                            line_end=idx - 1,
                            repository=repository
                        )
                    )
                    current_lines = []
                current_header = line.strip("#").strip()
                start_line = idx

            current_lines.append(line)

        if current_lines:
            chunks.append(
                CodeChunk(
                    content="\n".join(current_lines).strip(),
                    file_path=file_path,
                    doc_type="documentation",
                    language="markdown",
                    function_name=current_header,
                    line_start=start_line,
                    line_end=len(lines),
                    repository=repository
                )
            )

        return chunks

class StackTraceParser:
    """Parses Python stack traces to extract affected files, line numbers, and function calls."""

    @staticmethod
    def parse_stack_trace(stack_trace_str: str) -> List[Dict[str, Any]]:
        frames = []
        pattern = r'File "([^"]+)", line (\d+), in (\w+)'
        matches = re.findall(pattern, stack_trace_str)
        for path, line_no, func in matches:
            frames.append({
                "file_path": path,
                "line_number": int(line_no),
                "function_name": func
            })
        return frames
