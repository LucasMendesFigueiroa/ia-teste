import struct
import random
import time
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import BinaryIO, Optional, Tuple, List

# Constantes de layout
NAME_LEN = 50
CPF_LEN = 15
DATE_LEN = 11
CARGO_LEN = 30
DEPTO_LEN = 30
RECORD_FORMAT = f"=i{NAME_LEN}s{CPF_LEN}s{DATE_LEN}s{CARGO_LEN}s{DEPTO_LEN}sd"
RECORD_SIZE = struct.calcsize(RECORD_FORMAT)
_struct = struct.Struct(RECORD_FORMAT)

LOG_FILE = "buscas.log"
ARQUIVO_PADRAO = "funcionarios_ord.dat"

@dataclass(slots=True)
class Funcionario:
    """Registro de um funcionário."""
    cod: int
    nome: str
    cpf: str
    data_nascimento: str
    cargo: str
    departamento: str
    salario: float

    def __str__(self) -> str:
        return (
            f"Funcionario de código {self.cod}\n"
            f"Nome: {self.nome}\n"
            f"CPF: {self.cpf}\n"
            f"Data de Nascimento: {self.data_nascimento}\n"
            f"Cargo: {self.cargo}\n"
            f"Departamento: {self.departamento}\n"
            f"Salário: {self.salario:,.2f}"
        )


def funcionario(
    cod: int,
    nome: str,
    cpf: str,
    data_nascimento: str,
    cargo: str,
    departamento: str,
    salario: float,
) -> Funcionario:
    """Facilita a criação de registros."""
    return Funcionario(cod, nome, cpf, data_nascimento, cargo, departamento, salario)


def _encode(text: str, length: int) -> bytes:
    return text.encode("utf-8").ljust(length, b"\x00")[:length]


def salva(func: Funcionario, file_obj: BinaryIO) -> None:
    """Grava um registro na posição atual do arquivo."""
    packed = _struct.pack(
        func.cod,
        _encode(func.nome, NAME_LEN),
        _encode(func.cpf, CPF_LEN),
        _encode(func.data_nascimento, DATE_LEN),
        _encode(func.cargo, CARGO_LEN),
        _encode(func.departamento, DEPTO_LEN),
        func.salario,
    )
    file_obj.write(packed)


def le(file_obj: BinaryIO) -> Optional[Funcionario]:
    """Lê um registro na posição atual do cursor."""
    raw = file_obj.read(RECORD_SIZE)
    if len(raw) < RECORD_SIZE:
        return None
    cod, nome_b, cpf_b, data_b, cargo_b, depto_b, salario = _struct.unpack(raw)
    return Funcionario(
        cod,
        nome_b.split(b"\x00", 1)[0].decode("utf-8"),
        cpf_b.split(b"\x00", 1)[0].decode("utf-8"),
        data_b.split(b"\x00", 1)[0].decode("utf-8"),
        cargo_b.split(b"\x00", 1)[0].decode("utf-8"),
        depto_b.split(b"\x00", 1)[0].decode("utf-8"),
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
        "Ana",
        "Bruno",
        "Carla",
        "Diego",
        "Elisa",
        "Fabio",
        "Giovana",
        "Heitor",
        "Isabela",
        "Jonas",
    ]
    sobrenomes = [
        "Silva",
        "Santos",
        "Oliveira",
        "Costa",
        "Almeida",
        "Souza",
        "Ferreira",
        "Ribeiro",
        "Carvalho",
        "Barbosa",
    ]
    cargos = [
        "Analista",
        "Gerente",
        "Diretor",
        "Coordenador",
        "Assistente",
    ]
    departamentos = [
        "RH",
        "Financeiro",
        "TI",
        "Marketing",
        "Vendas",
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
        cargo = random.choice(cargos)
        departamento = random.choice(departamentos)
        salva(
            Funcionario(
                prox_codigo + i,
                nome,
                cpf,
                data_nasc,
                cargo,
                departamento,
                salario,
            ),
            file_obj,
        )

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


def busca_por_nome(name_arq: str, nome: str) -> List[Funcionario]:
    """Retorna todos os funcionários que possuem o nome informado."""
    resultados: List[Funcionario] = []
    with open(name_arq, "rb") as arq:
        while (f := le(arq)) is not None:
            if f.nome.lower() == nome.lower():
                resultados.append(f)
    return resultados


def busca_por_cargo(name_arq: str, cargo: str) -> List[Funcionario]:
    """Retorna todos os funcionários com o cargo informado."""
    resultados: List[Funcionario] = []
    with open(name_arq, "rb") as arq:
        while (f := le(arq)) is not None:
            if f.cargo.lower() == cargo.lower():
                resultados.append(f)
    return resultados


def busca_por_departamento(name_arq: str, departamento: str) -> List[Funcionario]:
    """Retorna todos os funcionários que pertencem ao departamento informado."""
    resultados: List[Funcionario] = []
    with open(name_arq, "rb") as arq:
        while (f := le(arq)) is not None:
            if f.departamento.lower() == departamento.lower():
                resultados.append(f)
    return resultados


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
    cargos = [
        "Analista",
        "Gerente",
        "Diretor",
        "Coordenador",
        "Assistente",
    ]
    departamentos = [
        "RH",
        "Financeiro",
        "TI",
        "Marketing",
        "Vendas",
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
            cargo = random.choice(cargos)
            departamento = random.choice(departamentos)
            salva(Funcionario(cod, nome, cpf, data_nasc, cargo, departamento, salario), f)


def imprime_arquivo_paginado(nome_arquivo: str, page_size: int = 20) -> None:
    """Exibe os registros do arquivo utilizando paginação."""
    if page_size <= 0:
        raise ValueError("page_size deve ser maior que zero")

    try:
        with open(nome_arquivo, "rb") as arq:
            registros = []
            while (f := le(arq)) is not None:
                registros.append(f)
    except FileNotFoundError:
        print(f"Arquivo '{nome_arquivo}' não encontrado.")
        return

    total = len(registros)
    if total == 0:
        print("Nenhum registro para exibir.")
        return

    paginas = (total + page_size - 1) // page_size
    while True:
        try:
            escolha = int(
                input(f"Escolha a página para visualizar (1-{paginas}) ou 0 para sair: ")
            )
        except ValueError:
            print("Entrada inválida. Informe um número.")
            continue
        if escolha == 0:
            break
        if escolha < 1 or escolha > paginas:
            print("Página inválida.")
            continue

        inicio = (escolha - 1) * page_size
        fim = min(inicio + page_size, total)
        print(f"Página {escolha} de {paginas} – Total de {total} registros")
        for reg in registros[inicio:fim]:
            imprime(reg)
        print("-" * 40)


def main() -> None:
    arquivo_name = ARQUIVO_PADRAO

    if not os.path.exists(arquivo_name):
        gera_base_ordenada(arquivo_name, 100)

    while True:
        print("\n--- MENU ---")
        print("1 - Buscar por nome")
        print("2 - Buscar por cargo")
        print("3 - Buscar por departamento")
        print("4 - Buscar em todas as buscas")
        print("5 - Imprimir todos os registros com paginação")
        print("6 - Sair do sistema")
        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            nome = input("Nome a buscar: ").strip()
            encontrados = busca_por_nome(arquivo_name, nome)
            if encontrados:
                for f in encontrados:
                    imprime(f)
            else:
                print("Nenhum funcionário encontrado com esse nome.")

        elif opcao == "2":
            cargo = input("Cargo a buscar: ").strip()
            encontrados = busca_por_cargo(arquivo_name, cargo)
            if encontrados:
                for f in encontrados:
                    imprime(f)
            else:
                print("Nenhum funcionário encontrado com esse cargo.")

        elif opcao == "3":
            depto = input("Departamento a buscar: ").strip()
            encontrados = busca_por_departamento(arquivo_name, depto)
            if encontrados:
                for f in encontrados:
                    imprime(f)
            else:
                print("Nenhum funcionário encontrado nesse departamento.")

        elif opcao == "4":
            termo = input("Termo de busca: ").strip()
            print("\n-- Por nome --")
            for f in busca_por_nome(arquivo_name, termo):
                imprime(f)
            print("\n-- Por cargo --")
            for f in busca_por_cargo(arquivo_name, termo):
                imprime(f)
            print("\n-- Por departamento --")
            for f in busca_por_departamento(arquivo_name, termo):
                imprime(f)

        elif opcao == "5":
            imprime_arquivo_paginado(arquivo_name, 20)

        elif opcao == "6":
            print("Saindo do sistema.")
            break

        else:
            print("Opção inválida.")


if __name__ == "__main__":
    main()
