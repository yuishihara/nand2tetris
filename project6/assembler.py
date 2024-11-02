import argparse

import pathlib

from enum import Enum


class SymbolTable:
    def __init__(self):
        self._table = {
            "SP": 0,
            "LCL": 1,
            "ARG": 2,
            "THIS": 3,
            "THAT": 4,
        }
        self._table.update({f"R{i}": i for i in range(16)})
        self._table["SCREEN"] = 16384
        self._table["KBD"] = 24576

    def add_entry(self, symbol, address):
        self._table[symbol] = address

    def contains(self, symbol):
        return symbol in self._table

    def get_address(self, symbol):
        return self._table[symbol]


class Code:
    def __init__(self):
        pass

    def dest(self, mnemonic):
        code = {
            "M": "001",
            "D": "010",
            "MD": "011",
            "A": "100",
            "AM": "101",
            "AD": "110",
            "AMD": "111",
        }
        return code.get(mnemonic, "000")

    def comp(self, mnemonic):
        code = {
            "0": "0101010",
            "1": "0111111",
            "-1": "0111010",
            "D": "0001100",
            "A": "0110000",
            "!D": "0001101",
            "!A": "0110001",
            "-D": "0001111",
            "-A": "0110011",
            "D+1": "0011111",
            "A+1": "0110111",
            "D-1": "0001110",
            "A-1": "0110010",
            "D+A": "0000010",
            "D-A": "0010011",
            "A-D": "0000111",
            "D&A": "0000000",
            "D|A": "0010101",
            "M": "1110000",
            "!M": "1110001",
            "-M": "1110011",
            "M+1": "1110111",
            "M-1": "1110010",
            "D+M": "1000010",
            "D-M": "1010011",
            "M-D": "1000111",
            "D&M": "1000000",
            "D|M": "1010101",
        }
        return code.get(mnemonic, "1111111")

    def jump(self, mnemonic):
        code = {
            "JGT": "001",
            "JEQ": "010",
            "JGE": "011",
            "JLT": "100",
            "JNE": "101",
            "JLE": "110",
            "JMP": "111",
        }
        return code.get(mnemonic, "000")


class CommandType(Enum):
    A_COMMAND = 1
    C_COMMAND = 2
    L_COMMAND = 3


class Parser:
    def __init__(self, asm_file):
        self._asm_file = asm_file
        self._current_command = None
        self._next_command = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __repr__(self):
        if self.command_type() == CommandType.A_COMMAND:
            return f"A command: {self._current_command} symbol: {self.symbol()}"
        if self.command_type() == CommandType.C_COMMAND:
            return f"C command: {self._current_command} dest: {self.dest()} comp: {self.comp()} jump: {self.jump()}"
        if self.command_type() == CommandType.L_COMMAND:
            return f"L command: {self._current_command} symbol: {self.symbol()}"
        return "Unknown command"

    def open(self):
        self._file = open(self._asm_file, "r", encoding="UTF-8")
        self._next_command = self._retrieve_next_command()

    def close(self):
        if not self._file.closed:
            self._file.close()

    def has_more_commands(self):
        return self._next_command is not None

    def advance(self):
        self._current_command = self._next_command
        self._next_command = self._retrieve_next_command()

    def command_type(self) -> CommandType:
        if self._current_command.startswith("(") and self._current_command.endswith(
            ")"
        ):
            return CommandType.L_COMMAND
        if self._current_command.startswith("@"):
            return CommandType.A_COMMAND
        if ";" in self._current_command or "=" in self._current_command:
            return CommandType.C_COMMAND
        raise ValueError(f"Unknown command: {self._current_command}")

    def symbol(self):
        command_type = self.command_type()
        if command_type == CommandType.A_COMMAND:
            return self._current_command[1:]
        if command_type == CommandType.L_COMMAND:
            return self._current_command[1:-1]
        return None

    def dest(self):
        eq_index = self._current_command.find("=")
        if eq_index == -1:
            return None
        else:
            return self._current_command[:eq_index]

    def comp(self):
        eq_index = self._current_command.find("=") + 1
        sc_index = self._current_command.find(";")
        if sc_index == -1:
            sc_index = len(self._current_command)
        return self._current_command[eq_index:sc_index]

    def jump(self):
        sc_index = self._current_command.find(";")
        if sc_index == -1:
            return None
        else:
            return self._current_command[sc_index + 1 :]

    def _remove_comment(self, line: str):
        command_index = line.find("//")
        return line[:command_index]

    def _remove_white_spaces(self, line: str):
        return line.replace(" ", "")

    def _retrieve_next_command(self):
        command = self._file.readline()
        while len(command) != 0:
            command = self._remove_comment(command)
            command = self._remove_white_spaces(command)
            if len(command) != 0:
                return command
            else:
                command = self._file.readline()
        return None


def assemble(asm_file: pathlib.Path):
    symbol_table = SymbolTable()

    address = 0
    with Parser(asm_file) as parser:
        while parser.has_more_commands():
            parser.advance()
            if parser.command_type() == CommandType.L_COMMAND:
                symbol = parser.symbol()
                symbol_table.add_entry(symbol, address)
            else:
                address += 1
            print(f"{parser}")

    next_ram_address = 16
    code_generator = Code()
    binary_code = None

    code_list = []
    with Parser(asm_file) as parser:
        while parser.has_more_commands():
            parser.advance()
            if parser.command_type() == CommandType.L_COMMAND:
                continue
            elif parser.command_type() == CommandType.A_COMMAND:
                symbol = parser.symbol()
                try:
                    value = int(symbol)
                    binary_code = f"{value:016b}"
                except:
                    if not symbol_table.contains(symbol):
                        ram_address = next_ram_address
                        symbol_table.add_entry(symbol, ram_address)
                        next_ram_address += 1
                    else:
                        ram_address = symbol_table.get_address(symbol)
                    binary_code = f"{ram_address:016b}"
            elif parser.command_type() == CommandType.C_COMMAND:
                dest = code_generator.dest(parser.dest())
                comp = code_generator.comp(parser.comp())
                jump = code_generator.jump(parser.jump())
                binary_code = f"111{comp}{dest}{jump}"
            else:
                raise NotImplementedError("Unknown command type")
            code_list.append(binary_code)
            print(f"code: {binary_code}")

    hack_file = asm_file.with_suffix(".hack")
    with open(hack_file, "w", encoding="UTF-8") as f:
        for code in code_list:
            f.write(code + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--asm", type=str, required=True)
    args = parser.parse_args()

    asm_file = args.asm
    if not asm_file.endswith(".asm"):
        raise ValueError(
            f"Given file is not an asm file: {asm_file}. Asm file should end with '.asm'"
        )

    assemble(pathlib.Path(args.asm))


if __name__ == "__main__":
    main()
