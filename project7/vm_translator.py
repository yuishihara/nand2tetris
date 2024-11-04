import pathlib

import argparse

from enum import Enum


class CommandType(Enum):
    C_ARITHMETIC = 1
    C_PUSH = 2
    C_POP = 3
    C_LABEL = 4
    C_GOTO = 5
    C_IF = 6
    C_FUNCTION = 7
    C_RETURN = 8
    C_CALL = 9


class Parser:
    ARITHMETIC_COMMANDS = [
        "add",
        "sub",
        "neg",
        "eq",
        "gt",
        "lt",
        "and",
        "or",
        "not",
    ]

    def __init__(self, vm_file):
        self._vm_file = vm_file
        self._current_command = None
        self._next_command = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __repr__(self):
        if self.command_type() == CommandType.C_ARITHMETIC:
            return f"ARITHMETIC command: {self.arg1()}"
        if self.command_type() == CommandType.C_PUSH:
            return f"PUSH arg1: {self.arg1()} arg2: {self.arg2()}"
        if self.command_type() == CommandType.C_POP:
            return f"POP arg1: {self.arg1()} arg2: {self.arg2()}"
        return "Unknown command"

    def open(self):
        self._file = open(self._vm_file, "r", encoding="UTF-8")
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
        if self._current_command[0] in Parser.ARITHMETIC_COMMANDS:
            return CommandType.C_ARITHMETIC
        if self._current_command[0] == "pop":
            return CommandType.C_POP
        if self._current_command[0] == "push":
            return CommandType.C_PUSH
        raise ValueError(f"Unknown command: {self._current_command[0]}")

    def arg1(self):
        if len(self._current_command) == 1:
            return self._current_command[0]
        else:
            return self._current_command[1]

    def arg2(self):
        return self._current_command[2]

    def _remove_comment(self, line: str):
        command_index = line.find("//")
        return line[:command_index]

    def _retrieve_next_command(self):
        command = self._file.readline()
        while len(command) != 0:
            command = self._remove_comment(command)
            command = [c for c in command.split(" ") if " " not in c and len(c) != 0]
            if len(command) != 0:
                return command
            else:
                command = self._file.readline()
        return None


class CodeWriter:
    def __init__(self, asm_file):
        self._asm_file = asm_file
        self._vm_file = None
        self._label_count = 0

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def open(self):
        self._file = open(self._asm_file, "w", encoding="UTF-8")

    def close(self):
        if not self._file.closed:
            self._file.close()

    def set_file_name(self, file_name):
        self._vm_file = file_name

    def write_arithmetic(self, command):
        if command == "add":
            self._write_add()
        elif command == "sub":
            self._write_sub()
        elif command == "neg":
            self._write_neg()
        elif command == "eq":
            self._write_eq()
        elif command == "lt":
            self._write_lt()
        elif command == "gt":
            self._write_gt()
        elif command == "and":
            self._write_and()
        elif command == "or":
            self._write_or()
        elif command == "not":
            self._write_not()
        else:
            raise NotImplementedError

    def write_push_pop(self, command, segment, index):
        if command == CommandType.C_POP:
            self._pop_data_from_stack(segment, index)
        elif command == CommandType.C_PUSH:
            self._push_data_to_stack(segment, index)
        else:
            raise NotImplementedError

    def _write_add(self):
        self._pop_stack_to_D()
        self._pop_stack_to_A()
        self._file.write(f"D=D+A" + "\n")
        self._push_D_to_stack()

    def _write_sub(self):
        self._pop_stack_to_D()
        self._pop_stack_to_A()
        self._file.write(f"D=A-D" + "\n")
        self._push_D_to_stack()

    def _write_neg(self):
        self._pop_stack_to_D()
        self._file.write(f"D=-D" + "\n")
        self._push_D_to_stack()

    def _write_eq(self):
        self._write_jump("JEQ")

    def _write_gt(self):
        self._write_jump("JGT")

    def _write_lt(self):
        self._write_jump("JLT")

    def _write_and(self):
        self._pop_stack_to_D()
        self._pop_stack_to_A()
        self._file.write(f"D=D&A" + "\n")
        self._push_D_to_stack()

    def _write_or(self):
        self._pop_stack_to_D()
        self._pop_stack_to_A()
        self._file.write(f"D=D|A" + "\n")
        self._push_D_to_stack()

    def _write_not(self):
        self._pop_stack_to_D()
        self._file.write(f"D=!D" + "\n")
        self._push_D_to_stack()

    def _write_jump(self, condition):
        self._pop_stack_to_D()
        self._pop_stack_to_A()
        self._file.write(f"D=A-D" + "\n")

        self._file.write(f"@JMP_LABEL{self._label_count}" + "\n")
        self._file.write(f"D;{condition}" + "\n")

        self._file.write(f"D=0" + "\n")
        self._push_D_to_stack()
        self._file.write(f"@JMP_END{self._label_count}" + "\n")
        self._file.write(f"0;JMP" + "\n")

        self._file.write(f"(JMP_LABEL{self._label_count})" + "\n")
        self._file.write(f"D=-1" + "\n")
        self._push_D_to_stack()
        self._file.write(f"(JMP_END{self._label_count})" + "\n")

        self._label_count += 1

    def _pop_stack_to_A(self):
        self._decrement_stack_pointer()

        # pop from stack
        self._file.write(f"@SP" + "\n")
        self._file.write(f"A=M" + "\n")
        self._file.write(f"A=M" + "\n")

    def _pop_stack_to_D(self):
        self._decrement_stack_pointer()

        # pop from stack
        self._file.write(f"@SP" + "\n")
        self._file.write(f"A=M" + "\n")
        self._file.write(f"D=M" + "\n")

    def _pop_data_from_stack(self, segment, index):
        self._set_address_to_D(segment, index)
        self._file.write(f"@R13" + "\n")
        self._file.write(f"M=D" + "\n")
        
        self._pop_stack_to_D()
        self._file.write(f"@R13" + "\n")
        self._file.write(f"A=M" + "\n")
        self._file.write(f"M=D" + "\n")


    def _push_data_to_stack(self, segment, index):
        self._set_data_to_D(segment, index)
        self._push_D_to_stack()

    def _push_D_to_stack(self):
        # push to stack
        self._file.write(f"@SP" + "\n")
        self._file.write(f"A=M" + "\n")
        self._file.write(f"M=D" + "\n")

        self._increment_stack_pointer()

    def _decrement_stack_pointer(self):
        self._file.write(f"@SP" + "\n")
        self._file.write(f"M=M-1" + "\n")

    def _increment_stack_pointer(self):
        # increment stack pointer
        self._file.write(f"@SP" + "\n")
        self._file.write(f"M=M+1" + "\n")

    def _set_data_to_D(self, segment, index):
        if segment == "constant":
            self._file.write(f"@{index}" + "\n")
            self._file.write(f"D=A" + "\n")
        elif segment == "static":
            self._file.write(f"@{self._vm_file}.{index}" + "\n")
            self._file.write(f"D=M" + "\n")
        elif segment == "pointer" or segment == "temp":
            address = self._retrieve_segment_address(segment)
            self._file.write(f"@{address}" + "\n")
            self._file.write(f"D=A" + "\n")
            self._file.write(f"@{index}" + "\n")
            self._file.write(f"A=A+D" + "\n")
            self._file.write(f"D=M" + "\n")
        else:
            address = self._retrieve_segment_address(segment)
            self._file.write(f"@{address}" + "\n")
            self._file.write(f"D=M" + "\n")
            self._file.write(f"@{index}" + "\n")
            self._file.write(f"A=A+D" + "\n")
            self._file.write(f"D=M" + "\n")

    def _set_address_to_D(self, segment, index):
        if segment == "constant":
            raise NotImplementedError
        elif segment == "static":
            self._file.write(f"@{self._vm_file}.{index}" + "\n")
            self._file.write(f"D=A" + "\n")
        elif segment == "pointer" or segment == "temp":
            address = self._retrieve_segment_address(segment)
            self._file.write(f"@{address}" + "\n")
            self._file.write(f"D=A" + "\n")
            self._file.write(f"@{index}" + "\n")
            self._file.write(f"D=A+D" + "\n")
        else:
            address = self._retrieve_segment_address(segment)
            self._file.write(f"@{address}" + "\n")
            self._file.write(f"D=M" + "\n")
            self._file.write(f"@{index}" + "\n")
            self._file.write(f"D=A+D" + "\n")

    def _retrieve_segment_address(self, segment):
        if segment == "local":
            return "LCL"
        if segment == "argument":
            return "ARG"
        if segment == "this":
            return "THIS"
        if segment == "that":
            return "THAT"
        if segment == "pointer":
            return "R3"
        if segment == "temp":
            return "R5"
        raise NotImplementedError(f"unknown segment: {segment}")


def translate(vm_file: pathlib.Path):
    with Parser(vm_file) as parser, CodeWriter(vm_file.with_suffix(".asm")) as writer:
        writer.set_file_name(vm_file.name)
        while parser.has_more_commands():
            parser.advance()
            print(f"command: {parser}")
            if parser.command_type() == CommandType.C_ARITHMETIC:
                writer.write_arithmetic(parser.arg1())
            if parser.command_type() == CommandType.C_PUSH:
                writer.write_push_pop(
                    parser.command_type(), parser.arg1(), parser.arg2()
                )
            if parser.command_type() == CommandType.C_POP:
                writer.write_push_pop(
                    parser.command_type(), parser.arg1(), parser.arg2()
                )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vm", type=str, required=True)
    args = parser.parse_args()

    vm_file = args.vm
    if not vm_file.endswith(".vm"):
        raise ValueError(
            f"Given file is not an vm file: {vm_file}. vm file should end with '.vm'"
        )

    translate(pathlib.Path(args.vm))


if __name__ == "__main__":
    main()
