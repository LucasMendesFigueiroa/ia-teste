import struct
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import BinaryIO, Optional, Tuple

# Constantes de layout
NAME_LEN = 50
CPF_LEN = 15
DATE_LEN = 11
RECORD_FORMAT = f"=i{NAME_LEN}s{CPF_LEN}s{DATE_LEN}sd"
RECORD_SIZE = struct.calcsize(RECORD_FORMAT)
_struct = struct.Struct(RECORD_FORMAT)

LOG_FILE = "buscas.log"

@dataclass(slots=True)
class Funcionario:
    """Registro de um funcionário."""
    cod: int
    nome: str
    cpf: str
    data_nascimento: str
    salario: float

    def __str__(self) -> str:
        return (
            f"Funcionario de código {self.cod}\n"
            f"Nome: {self.nome}\n"
            f"CPF: {self.cpf}\n"
            f"Data de Nascimento: {self.data_nascimento}\n"
            f"Salário: {self.salario:,.2f}"
        )


def funcionario(cod: int, nome: str, cpf: str, data_nascimento: str, salario: float) -> Funcionario:
    """Facilita a criação de registros."""
    return Funcionario(cod, nome, cpf, data_nascimento, salario)


def _encode(text: str, length: int) -> bytes:
    return text.encode("utf-8").ljust(length, b"\x00")[:length]


def salva(func: Funcionario, file_obj: BinaryIO) -> None:
    """Grava um registro na posição atual do arquivo."""
    packed = _struct.pack(
        func.cod,
        _encode(func.nome, NAME_LEN),
        _encode(func.cpf, CPF_LEN),
        _encode(func.data_nascimento, DATE_LEN),
        func.salario,
    )
    file_obj.write(packed)


def le(file_obj: BinaryIO) -> Optional[Funcionario]:
    """Lê um registro na posição atual do cursor."""
    raw = file_obj.read(RECORD_SIZE)
    if len(raw) < RECORD_SIZE:
        return None
    cod, nome_b, cpf_b, data_b, salario = _struct.unpack(raw)
    return Funcionario(
        cod,
        nome_b.split(b"\x00", 1)[0].decode("utf-8"),
        cpf_b.split(b"\x00", 1)[0].decode("utf-8"),
        data_b.split(b"\x00", 1)[0].decode("utf-8"),
        salario,
    )


def imprime(func: Funcionario) -> None:
    print("**********************************************")
    print(func)
    print("**********************************************")


def tamanho() -> int:
    return RECORD_SIZE


def gera_registros_aleatorios(file_obj: BinaryIO) -> None:
    try:
        qtd = int(input("Quantos registros aleatórios deseja gerar? "))
        if qtd <= 0:
            print("Nada a fazer.")
            return
    except ValueError:
        print("Entrada inválida; operação cancelada.")
        return

    file_obj.seek(0, 2)
    total_registros = file_obj.tell() // RECORD_SIZE
    prox_codigo = total_registros + 1

    nomes = [
        "Ana", "Bruno", "Carla", "Diego", "Elisa",
        "Fabio", "Giovana", "Heitor", "Isabela", "Jonas",
    ]
    sobrenomes = [
        "Silva", "Santos", "Oliveira", "Costa", "Almeida",
        "Souza", "Ferreira", "Ribeiro", "Carvalho", "Barbosa",
    ]

    for i in range(qtd):
        nome = f"{random.choice(nomes)} {random.choice(sobrenomes)}"
        cpf = "{:03d}.{:03d}.{:03d}-{:02d}".format(
            random.randint(0, 999),
            random.randint(0, 999),
            random.randint(0, 999),
            random.randint(0, 99),
        )
        delta_dias = random.randint(0, (datetime(2005, 12, 31) - datetime(1960, 1, 1)).days)
        data_nasc = (datetime(1960, 1, 1) + timedelta(days=delta_dias)).strftime("%d/%m/%Y")
        salario = round(random.uniform(500, 10_000), 2)
        salva(Funcionario(prox_codigo + i, nome, cpf, data_nasc, salario), file_obj)

    print(f"{qtd} registro(s) gerado(s) com sucesso!\n")


def busca_sequencial_por_codigo(name_arq: str, codigo: int) -> Tuple[Optional[Funcionario], int, float]:
    with open(name_arq, "rb") as arq:
        comparacoes = 0
        inicio = time.time()
        while (f := le(arq)) is not None:
            comparacoes += 1
            if f.cod == codigo:
                return f, comparacoes, time.time() - inicio
        return None, comparacoes, time.time() - inicio


def busca_binaria_por_codigo(name_arq: str, codigo: int) -> Tuple[Optional[Funcionario], int, float]:
    with open(name_arq, "rb") as arq:
        arq.seek(0, 2)
        total = arq.tell() // RECORD_SIZE
        ini, fim = 0, total - 1
        comparacoes = 0
        inicio = time.time()
        while ini <= fim:
            meio = (ini + fim) // 2
            arq.seek(meio * RECORD_SIZE)
            f = le(arq)
            comparacoes += 1
            if f and f.cod == codigo:
                return f, comparacoes, time.time() - inicio
            if f and f.cod < codigo:
                ini = meio + 1
            else:
                fim = meio - 1
        return None, comparacoes, time.time() - inicio


def registra_busca(tipo: str, codigo: int, comparacoes: int, tempo: float, log_file: str = LOG_FILE) -> None:
    """Registra o resultado de uma busca no arquivo de log."""
    momento = datetime.now().isoformat(sep=" ", timespec="seconds")
    with open(log_file, "a", encoding="utf-8") as log:
        log.write(
            f"{momento} | {tipo} | codigo={codigo} | comp={comparacoes} | tempo={tempo:.6f}s\n"
        )


def gera_base_ordenada(nome_arquivo: str, qtd: int) -> None:
    nomes = [
        "Ana", "Bruno", "Carla", "Diego", "Elisa",
        "Fabio", "Giovana", "Heitor", "Isabela", "Jonas",
    ]
    sobrenomes = [
        "Silva", "Santos", "Oliveira", "Costa", "Almeida",
        "Souza", "Ferreira", "Ribeiro", "Carvalho", "Barbosa",
    ]
    with open(nome_arquivo, "wb") as f:
        for cod in range(1, qtd + 1):
            nome = f"{random.choice(nomes)} {random.choice(sobrenomes)}"
            cpf = "{:03d}.{:03d}.{:03d}-{:02d}".format(
                random.randint(0, 999),
                random.randint(0, 999),
                random.randint(0, 999),
                random.randint(0, 99),
            )
            delta = random.randint(0, (datetime(2005, 12, 31) - datetime(1960, 1, 1)).days)
            data_nasc = (datetime(1960, 1, 1) + timedelta(days=delta)).strftime("%d/%m/%Y")
            salario = round(random.uniform(500, 10_000), 2)
            salva(Funcionario(cod, nome, cpf, data_nasc, salario), f)


def imprime_arquivo_inteiro(nome_arquivo: str, page_size: int = 20) -> None:
    """Imprime todos os registros do arquivo de forma paginada."""
    if page_size <= 0:
        raise ValueError("page_size deve ser maior que zero")

    try:
        with open(nome_arquivo, "rb") as arq:
            pos = 0
            while (f := le(arq)) is not None:
                print(f"\nRegistro #{pos}")
                imprime(f)
                pos += 1
                if pos % page_size == 0:
                    resp = input("Pressione Enter para continuar ou 'q' para sair: ")
                    if resp.lower().startswith("q"):
                        break
    except FileNotFoundError:
        print(f"Arquivo '{nome_arquivo}' não encontrado.")


def main() -> None:
    arquivo_name = "funcionarios_ord.dat"
    # gera_base_ordenada(arquivo_name, 5000)
    codigo_procura = 4000
    print(f"\n► Sequencial procurando {codigo_procura}")
    func, comp, tempo = busca_sequencial_por_codigo(arquivo_name, codigo_procura)
    print(f"Comparações: {comp}  •  Tempo: {tempo:.6f} s")
    registra_busca("sequencial", codigo_procura, comp, tempo)
    if func:
        imprime(func)
    else:
        print("Funcionário não encontrado (sequencial).")

    print(f"\n► Binária procurando {codigo_procura}")
    func, comp, tempo2 = busca_binaria_por_codigo(arquivo_name, codigo_procura)
    print(f"Comparações: {comp}  •  Tempo: {tempo2:.6f} s")
    registra_busca("binaria", codigo_procura, comp, tempo2)
    if func:
        imprime(func)
    else:
        print("Funcionário não encontrado (binária).")


if __name__ == "__main__":
    main()
