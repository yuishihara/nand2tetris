// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Fill.asm

// Runs an infinite loop that listens to the keyboard input. 
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel. When no key is pressed, 
// the screen should be cleared.

(LOOP)
@SCREEN
D=A
@pixeladdr
M=D

@32
D=A
@column
M=D
@16
D=A
@row
M=D

@CHECK_KEY
0;JMP

(CHECK_KEY)
@KBD
D=M
@CLEAR
D;JEQ
@FILL
0;JMP

(FILL)
// Fill 0xFF
@pixeladdr
A=M
M=-1

@pixeladdr
D=M+1
@pixeladdr
M=D

@NEXT_PIXEL
0;JMP

(CLEAR)
// Fill 0x00
@pixeladdr
A=M
M=0

@pixeladdr
D=M+1
@pixeladdr
M=D

@NEXT_PIXEL
0;JMP

(NEXT_PIXEL)
@column
M=M-1
@column
D=M
@CHECK_KEY
D;JGT

@row
M=M-1
@row
D=M

@LOOP
D;JEQ
@CHECK_KEY
0;JMP

