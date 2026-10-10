#!/usr/bin/env python3
"""
CALCULADORA DE 8 BITS EMULADA A NIVEL DE TRANSISTOR
===================================================

Todo el procesador (PC, registro de instrucción, decodificador, ALU, acumulador, flags,
fase fetch/execute, lógica de saltos y HALT) está construido SOLO con transistores NMOS/PMOS.
Lo único fuera del chip es la memoria de programa (una ROM en Python), igual que en un
computador real donde la memoria es un dispositivo externo conectado por un bus.

Arquitectura (acumulador, 8 bits de datos, 8 bits de dirección, instrucción de 12 bits):

     bus de memoria (12 bits)                       +---------------------------+
   ROM[PC] --------------------> IR (12 FF) ------> | Decodificador de opcode   |
      ^                            | imm[7:0]       +-------------+-------------+
      | PC[7:0]                    v                              | señales de control
   +--+--+  <-- incrementador   +--------+   A     +-----------+   v
   | PC  |  <-- carga de salto  |  MUX   |-------> |  SUMADOR  |--> ACC (8 FF) --+
   +-----+                      | LDI/ALU|  B'     | / RESTADOR|                 |
                                +--------+<--------+  8 bits   |--> FLAGS Z N C V|
                                                   +-----------+       |         |
                                                         ^ acc  <------+---------+

  Ciclo de instrucción (2 pulsos de reloj, controlados por el FF de fase):
     fase 0 = FETCH   : IR <- ROM[PC] ;  PC <- PC + 1
     fase 1 = EXECUTE : ALU/flags/ACC o salto (PC <- imm) o HALT

  Formato de instrucción (12 bits):   [11:8] opcode   [7:0] operando

  Instrucciones:
     NOP, LDI n, ADD n, SUB n, CMP n (resta sin guardar, solo flags),
     JMP a, JZ a, JNZ a, JC a, JNC a, JN a, JV a, HALT

  Flags:  Z cero | N negativo | C acarreo (en SUB: 1 = sin préstamo) | V desbordamiento con signo

Uso:
    python calculadora_8bit.py                   -> bucle de entrada: escribe números (negativo = resta);
                                                    algo que no sea número ('no') termina y da el resultado
    python calculadora_8bit.py "100 - 30 + 5"    -> calcula una expresión
    python calculadora_8bit.py --demo            -> programas de ejemplo (bucles, saltos, flags)
    python calculadora_8bit.py --asm prog.asm    -> ensambla y ejecuta un archivo
    python calculadora_8bit.py --test            -> batería de pruebas
"""
from __future__ import annotations

import random
import re
import sys
import time

# ========================================================================================
# 1. MOTOR DE SIMULACIÓN A NIVEL DE INTERRUPTOR (event-driven, por componentes conexas)
# ========================================================================================
L, H, Z, X = 0, 1, 2, 3          # 0, 1, alta impedancia (flotante), desconocido/conflicto
NMOS, PMOS = 0, 1


class Circuit:
    """
    Red de nodos y transistores.
      * NMOS conduce cuando su compuerta = 1;  PMOS conduce cuando su compuerta = 0.
      * Compuerta Z/X => el transistor se considera apagado.
      * Un nodo toma el valor de lo que lo maneja (VDD, GND, entradas externas) a través de
        transistores encendidos. Manejado por 0 y 1 a la vez => X. Sin manejo => conserva su
        carga anterior (así se implementa la memoria de los latches).

    Optimización: la red se parte en "componentes conexas por canal" (grupos de nodos unidos por
    fuente/drenador, sin cruzar rieles ni entradas). Cuando cambia una señal solo se reevalúan los
    grupos cuyas compuertas dependen de ella. Se mantiene un retardo unitario por "generación",
    de modo que el comportamiento temporal (carreras, flip-flops) es determinista.
    """

    def __init__(self) -> None:
        self.value: list[int] = []
        self.names: list[str] = []
        self.fixed: dict[int, int] = {}
        self.transistors: list[tuple[int, int, int, int]] = []
        self._compiled = False
        self._pending: set[int] = set()
        self.evaluations = 0               # estadística: grupos evaluados en total
        self.VDD = self.node("VDD")
        self.GND = self.node("GND")
        self.drive(self.VDD, H)
        self.drive(self.GND, L)

    # ---------------- construcción ----------------
    def node(self, name: str | None = None) -> int:
        i = len(self.value)
        self.value.append(Z)
        self.names.append(name or f"n{i}")
        self._compiled = False
        return i

    def input(self, name: str, v: int = L) -> int:
        n = self.node(name)
        self.drive(n, v)
        return n

    def nmos(self, gate: int, a: int, b: int) -> None:
        self.transistors.append((NMOS, gate, a, b))
        self._compiled = False

    def pmos(self, gate: int, a: int, b: int) -> None:
        self.transistors.append((PMOS, gate, a, b))
        self._compiled = False

    # ---------------- control externo ----------------
    def drive(self, n: int, v: int) -> None:
        if n not in self.fixed:
            self._compiled = False
        self.fixed[n] = v
        if self.value[n] != v:
            self.value[n] = v
            if self._compiled:
                self._pending.update(self._trigger.get(n, ()))

    def preset(self, n: int, v: int) -> None:
        """Estado inicial de un nodo interno (power-on de una celda de memoria)."""
        self.value[n] = v
        if self._compiled and n in self._ccc_of:
            self._pending.add(self._ccc_of[n])

    # ---------------- compilación ----------------
    def _compile(self) -> None:
        supply = set(self.fixed)
        n = len(self.value)
        parent = list(range(n))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for _, _, a, b in self.transistors:
            if a not in supply and b not in supply:
                ra, rb = find(a), find(b)
                if ra != rb:
                    parent[ra] = rb

        root_to_ccc: dict[int, int] = {}
        self._ccc_nodes: list[list[int]] = []
        self._ccc_of: dict[int, int] = {}
        local: dict[int, int] = {}
        for _, _, a, b in self.transistors:
            for t in (a, b):
                if t in supply or t in self._ccc_of:
                    continue
                r = find(t)
                cid = root_to_ccc.get(r)
                if cid is None:
                    cid = len(self._ccc_nodes)
                    root_to_ccc[r] = cid
                    self._ccc_nodes.append([])
                local[t] = len(self._ccc_nodes[cid])
                self._ccc_nodes[cid].append(t)
                self._ccc_of[t] = cid

        self._ccc_trans: list[list[tuple]] = [[] for _ in self._ccc_nodes]
        trigger: dict[int, set[int]] = {}
        for kind, g, a, b in self.transistors:
            if a in supply and b in supply:
                continue
            cid = self._ccc_of[a] if a not in supply else self._ccc_of[b]
            la = local[a] if a not in supply else -1
            lb = local[b] if b not in supply else -1
            self._ccc_trans[cid].append((kind, g, la, lb, a, b))
            trigger.setdefault(g, set()).add(cid)
            for t in (a, b):
                if t in supply:
                    trigger.setdefault(t, set()).add(cid)
        self._trigger = {k: tuple(v) for k, v in trigger.items()}
        self._compiled = True
        self._pending = set(range(len(self._ccc_nodes)))

    # ---------------- simulación ----------------
    def _eval(self, cid: int, val: list[int], out: list[tuple[int, int]]) -> None:
        nodes = self._ccc_nodes[cid]
        m = len(nodes)
        parent = list(range(m))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        ext: list[tuple[int, int]] = []
        for kind, g, la, lb, a, b in self._ccc_trans[cid]:
            gv = val[g]
            if (kind == NMOS and gv == H) or (kind == PMOS and gv == L):
                if la >= 0 and lb >= 0:
                    ra, rb = find(la), find(lb)
                    if ra != rb:
                        parent[ra] = rb
                elif la >= 0:
                    ext.append((la, 1 if val[b] == L else 2))
                else:
                    ext.append((lb, 1 if val[a] == L else 2))
        drivers: dict[int, int] = {}
        for li, bit in ext:
            r = find(li)
            drivers[r] = drivers.get(r, 0) | bit
        stored: dict[int, int] = {}
        for li in range(m):
            v = val[nodes[li]]
            if v == L or v == H:
                r = find(li)
                stored[r] = stored.get(r, 0) | (1 if v == L else 2)
        for li in range(m):
            r = find(li)
            d = drivers.get(r)
            if d is None:
                d = stored.get(r, 0)
                nv = Z if d == 0 else L if d == 1 else H if d == 2 else X
            else:
                nv = L if d == 1 else H if d == 2 else X
            node = nodes[li]
            if nv != val[node]:
                out.append((node, nv))

    def settle(self, max_iter: int = 2000) -> int:
        """Propaga cambios hasta estabilizar. Devuelve el nº de generaciones (retardos de compuerta)."""
        if not self._compiled:
            self._compile()
        val = self.value
        gens = 0
        while self._pending:
            gens += 1
            if gens > max_iter:
                raise RuntimeError("El circuito no converge (oscilación o carrera crítica)")
            cur, self._pending = self._pending, set()
            changes: list[tuple[int, int]] = []
            for cid in cur:
                self._eval(cid, val, changes)
            self.evaluations += len(cur)
            for node, v in changes:
                val[node] = v
            for node, _ in changes:
                self._pending.update(self._trigger.get(node, ()))
        return gens

    # ---------------- lectura / escritura de buses ----------------
    def get(self, n: int) -> int:
        return self.value[n]

    def read_bits(self, bits: list[int]) -> int | None:
        r = 0
        for i, b in enumerate(bits):
            v = self.value[b]
            if v not in (L, H):
                return None
            r |= v << i
        return r

    def drive_bits(self, bits: list[int], x: int) -> None:
        for i, b in enumerate(bits):
            self.drive(b, (x >> i) & 1)

    @property
    def n_transistors(self) -> int:
        return len(self.transistors)


# ========================================================================================
# 2. COMPUERTAS CMOS (solo transistores)
# ========================================================================================
def inv(c: Circuit, a: int, out: int | None = None) -> int:
    out = c.node() if out is None else out
    c.pmos(a, c.VDD, out)
    c.nmos(a, out, c.GND)
    return out


def nand(c: Circuit, *ins: int, out: int | None = None) -> int:
    """PMOS en paralelo (VDD->out) y NMOS en serie (out->GND)."""
    out = c.node() if out is None else out
    prev = out
    for k, x in enumerate(ins):
        c.pmos(x, c.VDD, out)
        nxt = c.GND if k == len(ins) - 1 else c.node()
        c.nmos(x, prev, nxt)
        prev = nxt
    return out


def nor(c: Circuit, *ins: int, out: int | None = None) -> int:
    """NMOS en paralelo (out->GND) y PMOS en serie (VDD->out)."""
    out = c.node() if out is None else out
    prev = c.VDD
    for k, x in enumerate(ins):
        c.nmos(x, out, c.GND)
        nxt = out if k == len(ins) - 1 else c.node()
        c.pmos(x, prev, nxt)
        prev = nxt
    return out


def and_(c: Circuit, *ins: int) -> int:
    return inv(c, nand(c, *ins))


def or_(c: Circuit, *ins: int) -> int:
    return inv(c, nor(c, *ins))


def xor(c: Circuit, a: int, b: int) -> int:
    t = nand(c, a, b)
    return nand(c, nand(c, a, t), nand(c, b, t))


def mux2(c: Circuit, sel: int, a0: int, a1: int, nsel: int | None = None) -> int:
    """sel=0 -> a0 ; sel=1 -> a1."""
    nsel = inv(c, sel) if nsel is None else nsel
    return nand(c, nand(c, a0, nsel), nand(c, a1, sel))


# ========================================================================================
# 3. ARITMÉTICA
# ========================================================================================
def full_adder(c: Circuit, a: int, b: int, cin: int) -> tuple[int, int]:
    p = xor(c, a, b)
    s = xor(c, p, cin)
    cout = nand(c, nand(c, a, b), nand(c, p, cin))
    return s, cout


def ripple_adder(c: Circuit, a: list[int], b: list[int], cin: int) -> tuple[list[int], int, int]:
    """Devuelve (suma, acarreo_de_salida, acarreo_hacia_el_bit_MSB) -> este último sirve para V."""
    s, carry = [], cin
    carry_into_msb = cin
    for i, (ai, bi) in enumerate(zip(a, b)):
        if i == len(a) - 1:
            carry_into_msb = carry
        si, carry = full_adder(c, ai, bi, carry)
        s.append(si)
    return s, carry, carry_into_msb


def incrementer(c: Circuit, a: list[int]) -> list[int]:
    """a + 1 con cadena de medios sumadores (para el contador de programa)."""
    out = [inv(c, a[0])]
    carry = a[0]
    for i in range(1, len(a)):
        out.append(xor(c, a[i], carry))
        if i < len(a) - 1:
            carry = and_(c, a[i], carry)
    return out


# ========================================================================================
# 4. MEMORIA: LATCH, FLIP-FLOP, REGISTRO
# ========================================================================================
def d_latch(c: Circuit, d: int, nd: int, en: int, init: int, q: int | None = None) -> tuple[int, int]:
    """Latch D con NAND cruzadas; transparente cuando en=1."""
    s = nand(c, d, en)
    r = nand(c, nd, en)
    q = c.node() if q is None else q
    qn = c.node()
    nand(c, s, qn, out=q)
    nand(c, r, q, out=qn)
    c.preset(q, init)
    c.preset(qn, 1 - init)
    return q, qn


class DFF:
    """Flip-flop D maestro-esclavo (flanco de subida). q puede pasarse ya creado (realimentación)."""

    def __init__(self, c: Circuit, d: int, clk: int, init: int = 0, q: int | None = None) -> None:
        nclk = inv(c, clk)           # el retardo de este inversor evita que maestro y esclavo se solapen
        nd = inv(c, d)
        qm, qmn = d_latch(c, d, nd, nclk, init)
        self.q, self.qn = d_latch(c, qm, qmn, clk, init, q=q)


class Register:
    """Registro de N bits con enable opcional y reset síncrono opcional (nrst activo en bajo)."""

    def __init__(self, c: Circuit, d: list[int], clk: int, en: int | None = None,
                 nrst: int | None = None, init: int = 0, q: list[int] | None = None) -> None:
        self.q = q if q is not None else [c.node() for _ in d]
        nen = inv(c, en) if en is not None else None
        for i, di in enumerate(d):
            din = di
            if en is not None:
                din = mux2(c, en, self.q[i], di, nsel=nen)      # si en=0 se realimenta Q (retiene)
            if nrst is not None:
                din = and_(c, din, nrst)
            DFF(c, din, clk, (init >> i) & 1, q=self.q[i])


# ========================================================================================
# 5. JUEGO DE INSTRUCCIONES Y ENSAMBLADOR
# ========================================================================================
OPCODES = {"NOP": 0, "LDI": 1, "ADD": 2, "SUB": 3, "CMP": 4, "JMP": 5, "JZ": 6, "JNZ": 7,
           "JC": 8, "JNC": 9, "JN": 10, "JV": 11, "HALT": 15}
OPNAMES = {v: k for k, v in OPCODES.items()}
NO_OPERAND = {"NOP", "HALT"}


def assemble(src: str) -> list[int]:
    """Ensamblador: etiquetas 'loop:', comentarios ';', números decimales/0x/0b (admite negativos)."""
    items, labels = [], {}
    for raw in src.splitlines():
        line = raw.split(";")[0].strip()
        if not line:
            continue
        if line.endswith(":"):
            labels[line[:-1].strip()] = len(items)
            continue
        items.append(line.replace(",", " ").split())
    rom = []
    for parts in items:
        op = parts[0].upper()
        if op not in OPCODES:
            raise ValueError(f"Instrucción desconocida: {op}")
        arg = 0
        if len(parts) > 1:
            arg = labels[parts[1]] if parts[1] in labels else int(parts[1], 0)
        elif op not in NO_OPERAND:
            raise ValueError(f"{op} requiere un operando")
        rom.append((OPCODES[op] << 8) | (arg & 0xFF))
    return rom


def disassemble(word: int) -> str:
    op, imm = (word >> 8) & 0xF, word & 0xFF
    name = OPNAMES.get(op, f"???{op}")
    return name if name in NO_OPERAND else f"{name} {imm}"


# ========================================================================================
# 6. EL PROCESADOR (todo transistores salvo la ROM)
# ========================================================================================
class Calc8CPU:
    def __init__(self) -> None:
        c = self.c = Circuit()
        self.clk = c.input("clk")
        self.rst = c.input("rst", H)
        self.bus = [c.input(f"mem{i}") for i in range(12)]       # bus de datos de la memoria externa
        nrst = inv(c, self.rst)

        # Nodos de estado creados de antemano (hay realimentación entre ellos)
        self.pc = [c.node(f"pc{i}") for i in range(8)]
        self.acc = [c.node(f"acc{i}") for i in range(8)]
        self.ir = [c.node(f"ir{i}") for i in range(12)]
        self.phase = c.node("phase")
        self.halted = c.node("halted")
        self.fz, self.fn, self.fc, self.fv = (c.node("Z"), c.node("N"), c.node("C"), c.node("V"))

        # --- fase: 0 = fetch, 1 = execute ---
        nhalt = inv(c, self.halted)
        fetch = inv(c, self.phase)
        run_f = and_(c, fetch, nhalt)
        run_e = and_(c, self.phase, nhalt)
        DFF(c, and_(c, inv(c, self.phase), nrst), self.clk, q=self.phase)

        # --- registro de instrucción (captura la ROM durante FETCH) ---
        Register(c, self.bus, self.clk, en=run_f, q=self.ir)
        imm, op = self.ir[0:8], self.ir[8:12]

        # --- decodificador de opcode ---
        nop_ = [inv(c, b) for b in op]

        def dec(code: int) -> int:
            return and_(c, *[op[i] if (code >> i) & 1 else nop_[i] for i in range(4)])

        is_ = {name: dec(code) for name, code in OPCODES.items() if name != "NOP"}

        # --- ALU: ACC + B  o  ACC - B (B' = B xor sub, cin = sub) ---
        sub = or_(c, is_["SUB"], is_["CMP"])
        b_eff = [xor(c, bi, sub) for bi in imm]
        total, cout, c_msb = ripple_adder(c, self.acc, b_eff, sub)
        result = [mux2(c, is_["LDI"], total[i], imm[i]) for i in range(8)]   # LDI deja pasar el inmediato
        zero = nor(c, *result)
        negative = result[7]
        overflow = xor(c, c_msb, cout)

        # --- habilitaciones (solo actúan en la fase EXECUTE y si no hay HALT) ---
        we_acc = and_(c, run_e, or_(c, is_["LDI"], is_["ADD"], is_["SUB"]))
        we_zn = and_(c, run_e, or_(c, is_["LDI"], is_["ADD"], is_["SUB"], is_["CMP"]))
        we_cv = and_(c, run_e, or_(c, is_["ADD"], is_["SUB"], is_["CMP"]))
        Register(c, result, self.clk, en=we_acc, nrst=nrst, q=self.acc)
        Register(c, [zero], self.clk, en=we_zn, nrst=nrst, q=[self.fz])
        Register(c, [negative], self.clk, en=we_zn, nrst=nrst, q=[self.fn])
        Register(c, [cout], self.clk, en=we_cv, nrst=nrst, q=[self.fc])
        Register(c, [overflow], self.clk, en=we_cv, nrst=nrst, q=[self.fv])

        # --- lógica de saltos ---
        cond = or_(c, is_["JMP"],
                   and_(c, is_["JZ"], self.fz), and_(c, is_["JNZ"], inv(c, self.fz)),
                   and_(c, is_["JC"], self.fc), and_(c, is_["JNC"], inv(c, self.fc)),
                   and_(c, is_["JN"], self.fn), and_(c, is_["JV"], self.fv))
        take = and_(c, run_e, cond)

        # --- contador de programa: +1 en FETCH, carga imm en EXECUTE si hay salto ---
        pc_inc = incrementer(c, self.pc)
        pc_next = [mux2(c, take, pc_inc[i], imm[i]) for i in range(8)]
        Register(c, pc_next, self.clk, en=or_(c, run_f, take), nrst=nrst, q=self.pc)

        # --- HALT (queda enclavado hasta el reset) ---
        DFF(c, and_(c, or_(c, self.halted, and_(c, self.phase, is_["HALT"])), nrst), self.clk, q=self.halted)

        # --- estado del sistema ---
        self.rom: list[int] = []
        self.ticks = 0
        self.instructions = 0
        self.trace: list[dict] = []
        self.reset()

    # ---------------- lectura del estado (se lee de los transistores) ----------------
    @property
    def PC(self) -> int | None:
        return self.c.read_bits(self.pc)

    @property
    def ACC(self) -> int | None:
        return self.c.read_bits(self.acc)

    @property
    def IR(self) -> int | None:
        return self.c.read_bits(self.ir)

    @property
    def flags(self) -> dict[str, int]:
        g = self.c.get
        return {"Z": g(self.fz), "N": g(self.fn), "C": g(self.fc), "V": g(self.fv)}

    @property
    def is_halted(self) -> bool:
        return self.c.get(self.halted) == H

    # ---------------- control ----------------
    def load(self, rom: list[int]) -> None:
        if len(rom) > 256:
            raise ValueError("La ROM admite como máximo 256 instrucciones")
        self.rom = list(rom)

    def reset(self) -> None:
        c = self.c
        c.drive(self.rst, H)
        c.drive(self.clk, L)
        c.drive_bits(self.bus, 0)
        c.settle()
        for _ in range(2):
            self._clock_pulse()
        c.drive(self.rst, L)
        c.settle()
        self.ticks = 0
        self.instructions = 0
        self.trace = []

    def _clock_pulse(self) -> None:
        c = self.c
        c.drive(self.clk, H)
        c.settle()
        c.drive(self.clk, L)
        c.settle()

    def tick(self) -> None:
        """Un pulso de reloj completo. La ROM responde con la palabra de la dirección PC actual."""
        pc = self.PC
        word = self.rom[pc] if pc is not None and pc < len(self.rom) else 0
        self.c.drive_bits(self.bus, word)
        self.c.settle()
        self._clock_pulse()
        self.ticks += 1

    def step(self) -> dict | None:
        """Ejecuta una instrucción completa (FETCH + EXECUTE). None si terminó."""
        if self.is_halted:
            return None
        pc0 = self.PC
        if pc0 is None or pc0 >= len(self.rom):
            return None              # se acabó el programa sin HALT
        self.tick()                  # FETCH
        ir = self.IR
        self.tick()                  # EXECUTE
        self.instructions += 1
        entry = {"pc": pc0, "ir": ir, "asm": disassemble(ir), "acc": self.ACC,
                 "next_pc": self.PC, **self.flags}
        self.trace.append(entry)
        return entry

    def run(self, max_instructions: int = 100000) -> None:
        while self.instructions < max_instructions:
            if self.step() is None:
                break


# ========================================================================================
# 7. CALCULADORA (compila una expresión a instrucciones y la ejecuta en los transistores)
# ========================================================================================
TOKEN = re.compile(r"\s*(0x[0-9a-fA-F]+|0b[01]+|\d+|[+\-])")


def parse_expression(expr: str) -> list[tuple[str, int]]:
    """'100 - 30 + 5' -> [('+',100), ('-',30), ('+',5)]  (admite negativos y 0x/0b)."""
    pos, toks = 0, []
    expr = expr.strip()
    while pos < len(expr):
        m = TOKEN.match(expr, pos)
        if not m:
            raise ValueError(f"Carácter no válido cerca de: {expr[pos:pos + 5]!r}")
        toks.append(m.group(1))
        pos = m.end()
    terms, sign, expect_num = [], "+", True
    for t in toks:
        if t in "+-" and len(t) == 1:
            if expect_num:
                sign = "-" if (sign == "+") == (t == "-") else "+"   # signos consecutivos
            else:
                sign, expect_num = t, True
        else:
            if not expect_num:
                raise ValueError("Falta un operador entre números")
            terms.append((sign, int(t, 0)))
            sign, expect_num = "+", False
    if not terms or expect_num:
        raise ValueError("Expresión incompleta")
    return terms


def expression_to_asm(terms: list[tuple[str, int]]) -> str:
    lines = []
    for i, (sign, v) in enumerate(terms):
        if not -255 <= v <= 255:
            raise ValueError(f"{v} no cabe en 8 bits (rango -255..255)")
        if i == 0:
            lines.append(f"LDI {(v if sign == '+' else -v) & 0xFF}")
        else:
            lines.append(f"{'ADD' if sign == '+' else 'SUB'} {v & 0xFF}")
    lines.append("HALT")
    return "\n".join(lines)


def to_signed(x: int) -> int:
    return x - 256 if x & 0x80 else x


def calculate(expr: str, cpu: Calc8CPU | None = None) -> dict:
    terms = parse_expression(expr)
    asm = expression_to_asm(terms)
    cpu = cpu or Calc8CPU()
    cpu.reset()
    cpu.load(assemble(asm))
    cpu.run()
    acc = cpu.ACC
    return {"expr": expr, "asm": asm, "acc": acc, "signed": to_signed(acc), "flags": cpu.flags,
            "trace": cpu.trace, "ticks": cpu.ticks, "instructions": cpu.instructions, "cpu": cpu}


def reference(terms: list[tuple[str, int]]) -> int:
    """Modelo de referencia en Python puro (solo para verificar el emulador)."""
    total = 0
    for sign, v in terms:
        total += v if sign == "+" else -v
    return total & 0xFF


def format_result(r: dict, verbose: bool = True) -> str:
    f, acc = r["flags"], r["acc"]
    out = []
    if verbose:
        out.append("  PC  Instrucción   ACC   Z N C V   próximo PC")
        for t in r["trace"]:
            out.append(f"  {t['pc']:02d}  {t['asm']:<12} {t['acc']:>4}   {t['Z']} {t['N']} {t['C']} {t['V']}   "
                       f"{t['next_pc']:>6}")
    out.append(f"  Resultado: {acc} (sin signo) | {to_signed(acc)} (con signo) | 0x{acc:02X} | 0b{acc:08b}")
    out.append(f"  Flags: Z={f['Z']} N={f['N']} C={f['C']} V={f['V']}")
    notes = []
    if f["V"]:
        notes.append("V=1: desbordamiento con signo (el resultado con signo no es válido)")
    terms = parse_expression(r["expr"])
    if len(terms) > 1:                      # C y V solo reflejan la ÚLTIMA suma/resta
        last = terms[-1][0]
        if last == "-" and f["C"] == 0:
            notes.append("C=0 en la última resta: hubo préstamo (resultado sin signo negativo)")
        if last == "+" and f["C"] == 1:
            notes.append("C=1 en la última suma: se superó 255")
    for n in notes:
        out.append("  Aviso: " + n)
    out.append(f"  {r['instructions']} instrucciones, {r['ticks']} pulsos de reloj, "
               f"{r['cpu'].c.n_transistors} transistores")
    return "\n".join(out)


# ========================================================================================
# 8. DEMOS, PRUEBAS Y CLI
# ========================================================================================
DEMOS = {
    "Cuenta regresiva 5 -> 0 (PC + flag Z + JNZ)": """
        LDI 5
    loop:
        SUB 1
        JNZ loop
        HALT
    """,
    "Desbordamiento con signo: 100 + 100 (flag V)": """
        LDI 100
        ADD 100
        JV overflow
        HALT
    overflow:
        LDI 255        ; marca: se detectó overflow
        HALT
    """,
    "Resultado negativo: 5 - 10 (flags N y C)": """
        LDI 5
        SUB 10
        JN negativo
        HALT
    negativo:
        LDI 1
        HALT
    """,
    "Multiplicación 6 x 4 por sumas repetidas (usa CMP/JZ)": """
        ; ACC acumula; no hay segundo registro, así que se desenrolla el bucle
        LDI 0
        ADD 6
        ADD 6
        ADD 6
        ADD 6
        CMP 24         ; ¿es 24?  (Z=1 si sí)
        JZ ok
        LDI 0
        HALT
    ok:
        LDI 24
        HALT
    """,
}


def demo() -> None:
    for title, src in DEMOS.items():
        cpu = Calc8CPU()
        cpu.load(assemble(src))
        cpu.run()
        print(f"\n=== {title} ===")
        print("  PC  Instrucción   ACC   Z N C V   próximo PC")
        for t in cpu.trace:
            print(f"  {t['pc']:02d}  {t['asm']:<12} {t['acc']:>4}   {t['Z']} {t['N']} {t['C']} {t['V']}   "
                  f"{t['next_pc']:>6}")
        print(f"  Final: ACC={cpu.ACC} flags={cpu.flags}  ({cpu.instructions} instr, {cpu.ticks} ticks)")


def ref_flags(a: int, b: int, sub: bool) -> dict:
    """Flags esperados para a±b en 8 bits (modelo de referencia)."""
    if sub:
        r, c = (a - b) & 0xFF, int(a >= b)
        v = int(((a ^ b) & (a ^ r) & 0x80) != 0)
    else:
        r, c = (a + b) & 0xFF, int(a + b > 255)
        v = int((~(a ^ b) & (a ^ r) & 0x80) != 0)
    return {"Z": int(r == 0), "N": r >> 7, "C": c, "V": v}


def run_tests() -> None:
    t0 = time.time()
    cpu = Calc8CPU()
    print(f"Procesador construido: {cpu.c.n_transistors} transistores\n")

    print("[1] Expresiones aleatorias contra modelo de referencia ...")
    rnd = random.Random(2026)
    for k in range(300):
        n_terms = rnd.randint(1, 5)
        parts = [str(rnd.randint(0, 255))]
        for _ in range(n_terms - 1):
            parts += [rnd.choice("+-"), str(rnd.randint(0, 255))]
        expr = " ".join(parts)
        r = calculate(expr, cpu)
        assert r["acc"] == reference(parse_expression(expr)), (expr, r["acc"])
    print("    300 expresiones OK")

    print("[2] Flags Z N C V (suma y resta) contra modelo de referencia ...")
    cases = [(a, b) for a in (0, 1, 127, 128, 200, 255) for b in (0, 1, 127, 128, 200, 255)]
    cases += [(rnd.randint(0, 255), rnd.randint(0, 255)) for _ in range(150)]
    for a, b in cases:
        for sub in (False, True):
            cpu.reset()
            cpu.load(assemble(f"LDI {a}\n{'SUB' if sub else 'ADD'} {b}\nHALT"))
            cpu.run()
            assert cpu.flags == ref_flags(a, b, sub), (a, b, sub, cpu.flags, ref_flags(a, b, sub))
    print(f"    {len(cases) * 2} operaciones OK")

    print("[3] CMP no modifica ACC y sí las flags ...")
    cpu.reset(); cpu.load(assemble("LDI 7\nCMP 7\nHALT")); cpu.run()
    assert cpu.ACC == 7 and cpu.flags["Z"] == 1 and cpu.flags["C"] == 1
    print("    OK")

    print("[4] Contador de programa: saltos condicionales ...")
    cpu.reset(); cpu.load(assemble(DEMOS["Cuenta regresiva 5 -> 0 (PC + flag Z + JNZ)"])); cpu.run()
    assert cpu.ACC == 0 and cpu.instructions == 1 + 5 * 2 + 1
    cpu.reset(); cpu.load(assemble(DEMOS["Desbordamiento con signo: 100 + 100 (flag V)"])); cpu.run()
    assert cpu.ACC == 255
    cpu.reset(); cpu.load(assemble(DEMOS["Resultado negativo: 5 - 10 (flags N y C)"])); cpu.run()
    assert cpu.ACC == 1
    cpu.reset(); cpu.load(assemble("JMP fin\nLDI 99\nfin:\nLDI 3\nHALT")); cpu.run()
    assert cpu.ACC == 3
    print("    OK")

    print("[5] HALT congela el procesador y RESET lo reinicia ...")
    cpu.reset(); cpu.load(assemble("LDI 9\nHALT\nLDI 1")); cpu.run()
    assert cpu.is_halted and cpu.ACC == 9
    pc_frozen = cpu.PC
    for _ in range(4):
        cpu.tick()
    assert cpu.ACC == 9 and cpu.PC == pc_frozen
    cpu.reset()
    assert cpu.ACC == 0 and cpu.PC == 0 and not cpu.is_halted
    print("    OK")

    print("[6] Bucle interactivo (entradas simuladas) ...")
    def scripted(inputs):
        it = iter(inputs)
        return lambda _="": next(it)
    quiet = lambda *_: None
    r = interactive_session(cpu, scripted(["100", "-30", "5", "no"]), quiet)
    assert r["acc"] == 75 and r["instructions"] == 4 and cpu.PC == 4 and cpu.is_halted
    r = interactive_session(cpu, scripted(["5", "-8", "q"]), quiet)         # 5 - 8 = -3
    assert r["acc"] == 253 and r["signed"] == -3 and r["flags"]["N"] == 1 and r["flags"]["C"] == 0
    r = interactive_session(cpu, scripted(["300", "08", "0x10", "-0b11", "fin"]), quiet)   # 300 se rechaza
    assert r["acc"] == 8 + 16 - 3
    assert interactive_session(cpu, scripted(["no"]), quiet) is None
    for _ in range(40):
        nums = [rnd.randint(-255, 255) for _ in range(rnd.randint(1, 8))]
        r = interactive_session(cpu, scripted([str(n) for n in nums] + ["stop"]), quiet)
        assert r["acc"] == sum(nums) & 0xFF, nums
    print("    OK")

    print(f"\nTodas las pruebas pasaron en {time.time() - t0:.1f} s")


def parse_number(raw: str) -> int | None:
    """Devuelve el entero (acepta 0x.., 0b.., -8, +5, 08) o None si no es un número."""
    raw = raw.strip()
    for base in (0, 10):
        try:
            return int(raw, base)
        except ValueError:
            continue
    return None


def interactive_session(cpu: Calc8CPU | None = None, read=input, write=print) -> dict | None:
    """
    Bucle de entrada: cada número se ejecuta de inmediato en el procesador.
      - el primer número  -> LDI n          (carga el valor inicial)
      - número positivo   -> ADD n
      - número negativo   -> SUB |n|        (escribir -8 resta 8 al total actual)
      - cualquier cosa que no sea un número ('no', 'q', Enter...) cierra el bucle y da el resultado.
    La ROM crece una instrucción por entrada; el PC (en transistores) simplemente avanza.
    """
    cpu = cpu or Calc8CPU()
    cpu.reset()
    cpu.load([])
    entries: list[int] = []
    write("Calculadora de 8 bits sobre %d transistores emulados." % cpu.c.n_transistors)
    write("Escribe números (positivo suma, negativo resta). Cualquier otra cosa termina y muestra el resultado.\n")
    while True:
        if len(cpu.rom) >= 255:      # 8 bits de PC: queda 1 palabra para el HALT
            write("  Memoria de programa llena (255 operaciones): se cierra el bucle.")
            break
        try:
            raw = read("  número> ")
        except (EOFError, KeyboardInterrupt):
            write("")
            break
        v = parse_number(raw)
        if v is None:
            break
        if not -255 <= v <= 255:
            write("  %d no cabe en 8 bits (rango -255..255); inténtalo de nuevo." % v)
            continue
        if not entries:
            word = (OPCODES["LDI"] << 8) | (v & 0xFF)
        elif v >= 0:
            word = (OPCODES["ADD"] << 8) | v
        else:
            word = (OPCODES["SUB"] << 8) | (-v)
        cpu.rom.append(word)
        entries.append(v)
        t = cpu.step()
        write("     PC=%02d  %-9s total=%3d (con signo %4d)   Z=%d N=%d C=%d V=%d"
              % (t["pc"], t["asm"], t["acc"], to_signed(t["acc"]), t["Z"], t["N"], t["C"], t["V"]))

    if not entries:
        write("\n  No se ingresaron números.")
        return None
    cpu.rom.append(OPCODES["HALT"] << 8)
    cpu.step()                       # el procesador ejecuta HALT y se detiene
    expr = "".join((str(v) if i == 0 else (" + " if v >= 0 else " - ") + str(abs(v)))
                   for i, v in enumerate(entries))
    result = {"expr": expr, "asm": "\n".join(disassemble(w) for w in cpu.rom), "acc": cpu.ACC,
              "signed": to_signed(cpu.ACC), "flags": cpu.flags, "trace": cpu.trace,
              "ticks": cpu.ticks, "instructions": cpu.instructions, "cpu": cpu}
    write("\n  Operación: " + expr)
    write(format_result(result, verbose=False))
    return result


def main(argv: list[str]) -> None:
    if len(argv) > 1 and argv[1] == "--test":
        run_tests()
    elif len(argv) > 1 and argv[1] == "--demo":
        demo()
    elif len(argv) > 2 and argv[1] == "--asm":
        cpu = Calc8CPU()
        cpu.load(assemble(open(argv[2]).read()))
        cpu.run()
        for t in cpu.trace:
            print(f"{t['pc']:02d}  {t['asm']:<12} ACC={t['acc']:<3} Z={t['Z']} N={t['N']} C={t['C']} V={t['V']}")
        print(f"Final: ACC={cpu.ACC} flags={cpu.flags}")
    elif len(argv) > 1:
        print(format_result(calculate(" ".join(argv[1:]))))
    else:
        interactive_session()


if __name__ == "__main__":
    main(sys.argv)
