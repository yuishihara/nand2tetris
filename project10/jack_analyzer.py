import pathlib

from enum import Enum

import argparse


class TokenType(Enum):
    KEYWORD = 1
    SYMBOL = 2
    IDENTIFIER = 3
    INT_CONST = 4
    STRING_CONST = 5


class KeyWord(Enum):
    CLASS = 1
    METHOD = 2
    FUNCTION = 3
    CONSTRUCTOR = 4
    INT = 5
    BOOLEAN = 6
    CHAR = 7
    VOID = 8
    VAR = 9
    STATIC = 10
    FIELD = 11
    LET = 12
    DO = 13
    IF = 14
    ELSE = 15
    WHILE = 16
    RETURN = 17
    TRUE = 18
    FALSE = 19
    NULL = 20
    THIS = 21


class JackTokenizer:
    KEYWORD_MAP = {
        "class": KeyWord.CLASS,
        "constructor": KeyWord.CONSTRUCTOR,
        "function": KeyWord.FUNCTION,
        "method": KeyWord.METHOD,
        "field": KeyWord.FIELD,
        "static": KeyWord.STATIC,
        "var": KeyWord.VAR,
        "int": KeyWord.INT,
        "char": KeyWord.CHAR,
        "boolean": KeyWord.BOOLEAN,
        "void": KeyWord.VOID,
        "true": KeyWord.TRUE,
        "false": KeyWord.FALSE,
        "null": KeyWord.NULL,
        "this": KeyWord.THIS,
        "let": KeyWord.LET,
        "do": KeyWord.DO,
        "if": KeyWord.IF,
        "else": KeyWord.ELSE,
        "while": KeyWord.WHILE,
        "return": KeyWord.RETURN,
    }

    def __init__(self, source):
        self._source_path = source
        self._source_list = None
        self._current_line = 0
        self._current_pos = 0
        self._next_token = None
        self._next_token_type = None
        self._current_token = None
        self._current_token_type = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def open(self):
        self._file = open(self._source_path, "r", encoding="UTF-8")
        self._source_list = self._remove_all_comments_and_new_line(self._file)
        self._next_token, self._next_token_type = self._retrieve_next_token()

    def close(self):
        if not self._file.closed:
            self._file.close()

    def write_token(self, outfile):
        token_type = self.token_type()
        if token_type == TokenType.IDENTIFIER:
            outfile.write(f"<identifier> {self._current_token} </identifier>\n")
            return
        if token_type == TokenType.INT_CONST:
            outfile.write(
                f"<integerConstant> {self._current_token} </integerConstant>\n"
            )
            return
        if token_type == TokenType.KEYWORD:
            outfile.write(f"<keyword> {self._current_token} </keyword>\n")
            return
        if token_type == TokenType.STRING_CONST:
            outfile.write(f"<stringConstant> {self._current_token} </stringConstant>\n")
            return
        if token_type == TokenType.SYMBOL:
            replace_symbols = {"<": "&lt;", ">": "&gt;", "&": "&amp;"}
            symbol = replace_symbols.get(self._current_token, self._current_token)
            outfile.write(f"<symbol> {symbol} </symbol>\n")
            return
        raise NotImplementedError(f"Unknown token: {token_type}")

    def has_more_tokens(self) -> bool:
        return self._next_token is not None

    def advance(self):
        self._current_token = self._next_token
        self._current_token_type = self._next_token_type
        self._next_token, self._next_token_type = self._retrieve_next_token()

    def token_type(self) -> TokenType:
        return self._current_token_type

    def keyword(self) -> KeyWord:
        return JackTokenizer.KEYWORD_MAP[self._current_token]

    def symbol(self) -> str:
        return self._current_token

    def identifier(self) -> str:
        return self._current_token

    def int_val(self) -> int:
        return self._current_token

    def string_val(self) -> str:
        return self._current_token

    def current_token(self) -> str:
        return self._current_token

    def _retrieve_next_token(self):
        new_token = ""
        while True:
            if len(self._source_list) == self._current_line:
                return None, None

            line = self._source_list[self._current_line]
            if len(line) <= self._current_pos:
                self._current_line += 1
                self._current_pos = 0
                continue

            new_char = line[self._current_pos]
            self._current_pos += 1
            if new_char == " " or new_char == "\t":
                if len(new_token) != 0:
                    try:
                        new_token = int(new_token)
                        return new_token, TokenType.INT_CONST
                    except:
                        return new_token, TokenType.IDENTIFIER
                else:
                    continue
            if new_char == '"':
                if len(new_token) != 0:
                    raise ValueError("token length should not be 0")
                string_const_end = line[self._current_pos :].find('"')
                new_token = line[
                    self._current_pos : self._current_pos + string_const_end
                ]
                self._current_pos = self._current_pos + string_const_end + 1
                return new_token, TokenType.STRING_CONST

            if self._is_symbol(new_char):
                if len(new_token) != 0:
                    self._current_pos -= 1
                    try:
                        new_token = int(new_token)
                        return new_token, TokenType.INT_CONST
                    except:
                        return new_token, TokenType.IDENTIFIER
                else:
                    return new_char, TokenType.SYMBOL
            new_token += new_char
            if self._is_keyword(new_token):
                return new_token, TokenType.KEYWORD

    def _is_symbol(self, value: str):
        if len(value) != 1:
            return False
        defined_symbols = [
            "{",
            "}",
            "(",
            ")",
            "[",
            "]",
            ".",
            ",",
            ";",
            "+",
            "-",
            "*",
            "/",
            "&",
            "|",
            "<",
            ">",
            "=",
            "~",
        ]
        return value in defined_symbols

    def _is_keyword(self, value: str):
        return value in JackTokenizer.KEYWORD_MAP.keys()

    def _remove_all_comments_and_new_line(self, f):
        source_lines = []
        multirow_comment_active = False
        for line in f.readlines():
            line = line[:-1]

            single_comment_index = line.find("//")
            if single_comment_index != -1:
                line = line[:single_comment_index]

            multi_comment_start_index = line.find("/*")
            multi_comment_end_index = line.find("*/")
            if multi_comment_start_index != -1 and multi_comment_end_index != -1:
                line = line[:multi_comment_start_index]
                line += line[multi_comment_end_index + 2 :]
            elif multi_comment_start_index != -1 and not multirow_comment_active:
                line = line[:multi_comment_start_index]
                multirow_comment_active = True
            elif multi_comment_end_index != -1 and multirow_comment_active:
                line = line[multi_comment_end_index + 2 :]
                multirow_comment_active = False
            elif multirow_comment_active:
                line = ""
            source_lines.append(line)

        return source_lines


class CompilationEngine:
    _tokenizer: JackTokenizer

    def __init__(self, tokenizer: JackTokenizer, outfile):
        self._tokenizer = tokenizer
        self._outfile = outfile

    def compile(self):
        self.compile_class()

    def compile_class(self):
        self._outfile.write("<class>\n")

        token_type = self._tokenizer.token_type()
        print(f"token type: {str(token_type)}")
        if token_type != TokenType.KEYWORD:
            raise ValueError(f"trying to compile class but keyword not found")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        token_type = self._tokenizer.token_type()
        if token_type != TokenType.IDENTIFIER:
            raise ValueError("trying to compile class but could not find an identifier")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        token_type = self._tokenizer.token_type()
        if token_type != TokenType.SYMBOL:
            raise ValueError("trying to compile class but could not find symbol '{'")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        while self._tokenizer.token_type() == TokenType.KEYWORD:
            keyword = self._tokenizer.keyword()
            SUBROUTINE_KEYS = [KeyWord.CONSTRUCTOR, KeyWord.FUNCTION, KeyWord.METHOD]
            CLASS_VAR_KEYS = [KeyWord.FIELD, KeyWord.STATIC]
            if keyword not in SUBROUTINE_KEYS + CLASS_VAR_KEYS:
                raise ValueError(
                    f"trying to compile class but found unexpected keyword: {keyword}"
                )
            if keyword in SUBROUTINE_KEYS:
                self.compile_subroutine()
            if keyword in CLASS_VAR_KEYS:
                self.compile_class_var_dec()

        token_type = self._tokenizer.token_type()
        if token_type != TokenType.SYMBOL:
            raise ValueError("trying to compile class but could not find symbol '}'")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        self._outfile.write("</class>\n")

    def compile_class_var_dec(self):
        self._outfile.write("<classVarDec>\n")

        token_type = self._tokenizer.token_type()
        if token_type != TokenType.KEYWORD:
            raise ValueError(f"trying to compile class but keyword not found")
        if self._tokenizer.keyword() not in [KeyWord.STATIC, KeyWord.FIELD]:
            raise ValueError(f"keyword for class var should be either static or field")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        token_type = self._tokenizer.token_type()
        if token_type == TokenType.KEYWORD and self._tokenizer.keyword() not in [
            KeyWord.INT,
            KeyWord.BOOLEAN,
            KeyWord.CHAR,
        ]:
            raise ValueError(
                f"type for class var should be one of [int, boolean, char]"
            )
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        token_type = self._tokenizer.token_type()
        if token_type != TokenType.IDENTIFIER:
            raise ValueError(
                "trying to compile a class var but could not find an identifier"
            )
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        while not (
            self._tokenizer.token_type() == TokenType.SYMBOL
            and self._tokenizer.symbol() == ";"
        ):
            token_type = self._tokenizer.token_type()
            if token_type != TokenType.SYMBOL or self._tokenizer.symbol() != ",":
                raise ValueError(
                    "trying to compile class but could not find symbol ','"
                )
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

            token_type = self._tokenizer.token_type()
            if token_type != TokenType.IDENTIFIER:
                raise ValueError(
                    "trying to compile a class var but could not find an identifier"
                )
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

        token_type = self._tokenizer.token_type()
        if token_type != TokenType.SYMBOL:
            raise ValueError("trying to compile class but could not find symbol ';'")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        self._outfile.write("</classVarDec>\n")

    def compile_subroutine(self):
        self._outfile.write("<subroutineDec>\n")

        token_type = self._tokenizer.token_type()
        if token_type != TokenType.KEYWORD:
            raise ValueError(
                "trying to compile class subroutine but could not find a keyword"
            )
        if self._tokenizer.keyword() not in [
            KeyWord.CONSTRUCTOR,
            KeyWord.FUNCTION,
            KeyWord.METHOD,
        ]:
            raise ValueError(
                f"type for class subroutine should be one of [constructor, function, method]"
            )
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        token_type = self._tokenizer.token_type()
        if token_type == TokenType.KEYWORD:
            if self._tokenizer.keyword() not in [
                KeyWord.VOID,
                KeyWord.INT,
                KeyWord.BOOLEAN,
                KeyWord.CHAR,
            ]:
                raise ValueError(
                    f"type for class subroutine should be one of [void, int, boolean, char]"
                )
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        token_type = self._tokenizer.token_type()
        if token_type != TokenType.IDENTIFIER:
            raise ValueError(
                "trying to compile a class subroutine but could not find an identifier"
            )
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        token_type = self._tokenizer.token_type()
        if token_type != TokenType.SYMBOL:
            raise ValueError("trying to compile class but could not find symbol '('")
        if self._tokenizer.symbol() != "(":
            raise ValueError("trying to compile class but could not find symbol '('")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        self.compile_parameter_list()

        token_type = self._tokenizer.token_type()
        if token_type != TokenType.SYMBOL:
            raise ValueError("trying to compile class but could not find symbol ')'")
        if self._tokenizer.symbol() != ")":
            raise ValueError("trying to compile class but could not find symbol ')'")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        self.compile_subroutine_body()

        self._outfile.write("</subroutineDec>\n")

    def compile_parameter_list(self):
        self._outfile.write("<parameterList>\n")

        token_type = self._tokenizer.token_type()
        if token_type != TokenType.SYMBOL:
            token_type = self._tokenizer.token_type()
            if token_type != TokenType.KEYWORD:
                raise ValueError(
                    "trying to compile parameter list but could not find a keyword"
                )
            if self._tokenizer.keyword() not in [
                KeyWord.INT,
                KeyWord.BOOLEAN,
                KeyWord.CHAR,
            ]:
                raise ValueError(
                    f"type for parameter list should be one of [int, boolean, char]"
                )
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

            token_type = self._tokenizer.token_type()
            if token_type != TokenType.IDENTIFIER:
                raise ValueError(
                    "trying to compile a var dec but could not find an identifier"
                )
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

        while not (
            self._tokenizer.token_type() == TokenType.SYMBOL
            and self._tokenizer.symbol() == ")"
        ):
            token_type = self._tokenizer.token_type()
            if token_type != TokenType.SYMBOL or self._tokenizer.symbol() != ",":
                raise ValueError(
                    "trying to compile parameter list but could not find symbol ','"
                )
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

            token_type = self._tokenizer.token_type()
            if token_type != TokenType.KEYWORD:
                raise ValueError(
                    "trying to compile parameter list but could not find a keyword"
                )
            if self._tokenizer.keyword() not in [
                KeyWord.INT,
                KeyWord.BOOLEAN,
                KeyWord.CHAR,
            ]:
                raise ValueError(
                    f"type for parameter list should be one of [int, boolean, char]"
                )
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

            token_type = self._tokenizer.token_type()
            if token_type != TokenType.IDENTIFIER:
                raise ValueError(
                    "trying to compile a var dec but could not find an identifier"
                )
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

        self._outfile.write("</parameterList>\n")

    def compile_subroutine_body(self):
        self._outfile.write("<subroutineBody>\n")

        token_type = self._tokenizer.token_type()
        if token_type != TokenType.SYMBOL:
            raise ValueError("trying to compile class but could not find symbol '{'")
        if self._tokenizer.symbol() != "{":
            raise ValueError("trying to compile class but could not find symbol '{'")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        while (
            self._tokenizer.token_type() == TokenType.KEYWORD
            and self._tokenizer.keyword() == KeyWord.VAR
        ):
            self.compile_var_dec()

        self.compile_statements()

        token_type = self._tokenizer.token_type()
        if token_type != TokenType.SYMBOL:
            raise ValueError("trying to compile class but could not find symbol '}'")
        if self._tokenizer.symbol() != "}":
            raise ValueError("trying to compile class but could not find symbol '}'")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        self._outfile.write("</subroutineBody>\n")

    def compile_var_dec(self):
        self._outfile.write("<varDec>\n")

        token_type = self._tokenizer.token_type()
        if token_type != TokenType.KEYWORD:
            raise ValueError("trying to compile var dec but could not find keyword var")
        if self._tokenizer.keyword() != KeyWord.VAR:
            raise ValueError("trying to compile var dec but could not find keywrod var")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        token_type = self._tokenizer.token_type()
        if token_type == TokenType.KEYWORD:
            if self._tokenizer.keyword() not in [
                KeyWord.INT,
                KeyWord.BOOLEAN,
                KeyWord.CHAR,
            ]:
                raise ValueError(
                    f"type for var dec should be one of [int, boolean, char]"
                )
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()
        elif token_type == TokenType.IDENTIFIER:
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

        token_type = self._tokenizer.token_type()
        if token_type != TokenType.IDENTIFIER:
            raise ValueError(
                "trying to compile a var dec but could not find an identifier"
            )
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        while not (
            self._tokenizer.token_type() == TokenType.SYMBOL
            and self._tokenizer.symbol() == ";"
        ):
            token_type = self._tokenizer.token_type()
            if token_type != TokenType.SYMBOL or self._tokenizer.symbol() != ",":
                raise ValueError(
                    "trying to compile var dec but could not find symbol ','"
                )
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

            token_type = self._tokenizer.token_type()
            if token_type != TokenType.IDENTIFIER:
                raise ValueError(
                    "trying to compile a var dec but could not find an identifier"
                )
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

        token_type = self._tokenizer.token_type()
        if token_type != TokenType.SYMBOL:
            raise ValueError("trying to compile class but could not find symbol ';'")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        self._outfile.write("</varDec>\n")

    def compile_statements(self):
        self._outfile.write("<statements>\n")

        while self._tokenizer.token_type() == TokenType.KEYWORD:
            keyword = self._tokenizer.keyword()
            if keyword not in [
                KeyWord.LET,
                KeyWord.IF,
                KeyWord.WHILE,
                KeyWord.DO,
                KeyWord.RETURN,
            ]:
                raise ValueError("Could not find statement keyword")
            if keyword == KeyWord.LET:
                self.compile_let()
            if keyword == KeyWord.IF:
                self.compile_if()
            if keyword == KeyWord.WHILE:
                self.compile_while()
            if keyword == KeyWord.DO:
                self.compile_do()
            if keyword == KeyWord.RETURN:
                self.compile_return()
        self._outfile.write("</statements>\n")

    def compile_let(self):
        self._outfile.write("<letStatement>\n")
        keyword = self._tokenizer.keyword()
        if keyword != KeyWord.LET:
            raise ValueError("Keyword is not let")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        token_type = self._tokenizer.token_type()
        if token_type != TokenType.IDENTIFIER:
            raise ValueError(
                "trying to compile a let statement but could not find an identifier"
            )
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        token_type = self._tokenizer.token_type()
        if not (token_type == TokenType.SYMBOL and self._tokenizer.symbol() == "="):
            if self._tokenizer.symbol() != "[":
                raise ValueError("symbol [ not found")
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

            self.compile_expression()

            if self._tokenizer.symbol() != "]":
                raise ValueError("symbol ] not found")
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

        if self._tokenizer.symbol() != "=":
            raise ValueError("symbol = not found")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        self.compile_expression()

        token_type = self._tokenizer.token_type()
        if token_type != TokenType.SYMBOL:
            raise ValueError(
                "trying to compile a let statement but could not find symbold ';'"
            )
        if self._tokenizer.symbol() != ";":
            raise ValueError("symbol ; not found")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        self._outfile.write("</letStatement>\n")

    def compile_if(self):
        self._outfile.write("<ifStatement>\n")

        keyword = self._tokenizer.keyword()
        if keyword != KeyWord.IF:
            raise ValueError("Keyword is not if")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        if self._tokenizer.symbol() != "(":
            raise ValueError("symbol ( not found")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        self.compile_expression()

        if self._tokenizer.symbol() != ")":
            raise ValueError("symbol ) not found")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        if self._tokenizer.symbol() != "{":
            raise ValueError("symbol { not found")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        self.compile_statements()

        if self._tokenizer.symbol() != "}":
            raise ValueError("symbol } not found")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        token_type = self._tokenizer.token_type()
        keyword = self._tokenizer.keyword()
        if token_type == TokenType.KEYWORD and keyword == KeyWord.ELSE:
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

            if self._tokenizer.symbol() != "{":
                raise ValueError("symbol { not found")
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

            self.compile_statements()

            if self._tokenizer.symbol() != "}":
                raise ValueError("symbol } not found")
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

        self._outfile.write("</ifStatement>\n")

    def compile_while(self):
        self._outfile.write("<whileStatement>\n")

        keyword = self._tokenizer.keyword()
        if keyword != KeyWord.WHILE:
            raise ValueError("Keyword is not while")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        if self._tokenizer.symbol() != "(":
            raise ValueError("symbol ( not found")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        self.compile_expression()

        if self._tokenizer.symbol() != ")":
            raise ValueError("symbol ) not found")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        if self._tokenizer.symbol() != "{":
            raise ValueError("symbol { not found")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        self.compile_statements()

        if self._tokenizer.symbol() != "}":
            raise ValueError("symbol } not found")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        self._outfile.write("</whileStatement>\n")

    def compile_do(self):
        self._outfile.write("<doStatement>\n")

        keyword = self._tokenizer.keyword()
        if keyword != KeyWord.DO:
            raise ValueError("Keyword is not do")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        self.compile_subroutine_call()

        if self._tokenizer.symbol() != ";":
            raise ValueError("symbol ; not found")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        self._outfile.write("</doStatement>\n")

    def compile_return(self):
        self._outfile.write("<returnStatement>\n")

        keyword = self._tokenizer.keyword()
        if keyword != KeyWord.RETURN:
            raise ValueError("Keyword is not return")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        if self._tokenizer.symbol() != ";":
            self.compile_expression()

        if self._tokenizer.symbol() != ";":
            raise ValueError("symbol ; not found")
        self._tokenizer.write_token(self._outfile)
        self._tokenizer.advance()

        self._outfile.write("</returnStatement>\n")

    def compile_subroutine_call(self, term=False):
        if not term:
            token_type = self._tokenizer.token_type()
            if token_type != TokenType.IDENTIFIER:
                raise ValueError(
                    "trying to compile a subroutine call but could not find an identifier"
                )
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

        token_type = self._tokenizer.token_type()

        if self._tokenizer.symbol() == ".":
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

            token_type = self._tokenizer.token_type()
            if token_type != TokenType.IDENTIFIER:
                raise ValueError(
                    "trying to compile a subroutine call but could not find an identifier"
                )
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

        if self._tokenizer.symbol() == "(":
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

            self.compile_expression_list()

            if self._tokenizer.symbol() != ")":
                raise ValueError("symbol ) not found")
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()
        else:
            raise ValueError(
                "trying to compile a subroutine call but could not find '(' symbol."
            )

    def compile_expression(self):
        self._outfile.write("<expression>\n")

        self.compile_term()

        while self._tokenizer.symbol() in ["+", "-", "*", "/", "&", "|", "<", ">", "="]:
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

            self.compile_term()

        self._outfile.write("</expression>\n")

    def compile_term(self):
        self._outfile.write("<term>\n")
        token_type = self._tokenizer.token_type()
        if token_type == TokenType.SYMBOL:
            symbol = self._tokenizer.symbol()
            if symbol in ["-", "~"]:
                self._tokenizer.write_token(self._outfile)
                self._tokenizer.advance()
                self.compile_term()
            if symbol == "(":
                self._tokenizer.write_token(self._outfile)
                self._tokenizer.advance()

                self.compile_expression()

                self._tokenizer.write_token(self._outfile)
                self._tokenizer.advance()

        if token_type == TokenType.IDENTIFIER:
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

            token_type = self._tokenizer.token_type()
            if token_type == TokenType.SYMBOL:
                symbol = self._tokenizer.symbol()
                if symbol == "[":
                    self._tokenizer.write_token(self._outfile)
                    self._tokenizer.advance()

                    self.compile_expression()

                    self._tokenizer.write_token(self._outfile)
                    self._tokenizer.advance()

                if symbol in ["(", "."]:
                    self.compile_subroutine_call(term=True)

        if token_type in [TokenType.INT_CONST, TokenType.STRING_CONST]:
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

        if token_type == TokenType.KEYWORD:
            keyword = self._tokenizer.keyword()
            if keyword in [KeyWord.TRUE, KeyWord.FALSE, KeyWord.NULL, KeyWord.THIS]:
                self._tokenizer.write_token(self._outfile)
                self._tokenizer.advance()

        self._outfile.write("</term>\n")

    def compile_expression_list(self):
        self._outfile.write("<expressionList>\n")

        if self._tokenizer.symbol() == ")":
            self._outfile.write("</expressionList>\n")
            return
        self.compile_expression()

        while self._tokenizer.symbol() != ")":
            token_type = self._tokenizer.token_type()
            if token_type != TokenType.SYMBOL or self._tokenizer.symbol() != ",":
                raise ValueError(
                    "trying to compile expression list but could not find symbol ','"
                )
            self._tokenizer.write_token(self._outfile)
            self._tokenizer.advance()

            self.compile_expression()

        self._outfile.write("</expressionList>\n")


def compile(args):
    source_path = pathlib.Path(args.source)
    sources = list(source_path.iterdir()) if source_path.is_dir() else [source_path]

    for source in sources:
        if source.suffix != ".jack":
            continue
        token_xml = source.with_name(source.stem + "T-new").with_suffix(".xml")
        print(f"Token xml -> {token_xml}")
        with JackTokenizer(source) as tokenizer, open(token_xml, "w") as token_xml_file:
            token_xml_file.write("<tokens>\n")
            while tokenizer.has_more_tokens():
                tokenizer.advance()
                tokenizer.write_token(token_xml_file)
            token_xml_file.write("</tokens>\n")

        compile_xml = source.with_name(source.stem + "-new").with_suffix(".xml")
        with JackTokenizer(source) as tokenizer, open(
            compile_xml, "w"
        ) as compile_xml_file:
            tokenizer.advance()
            engine = CompilationEngine(tokenizer=tokenizer, outfile=compile_xml_file)
            engine.compile()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=str, default="project10/Square/Main.jack")

    args = parser.parse_args()

    compile(args)


if __name__ == "__main__":
    main()
