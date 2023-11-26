import gurobipy as gp
from flask import Flask, request,jsonify
from flask_cors import CORS
import json


app = Flask(__name__)

CORS(app)

@app.route("/upload", methods=["POST"])
def upload_file():
    if request.method == "POST":
        json_data = request.get_json()
        # pega as Variaveis do Json
        numFuncionarios = json_data["numFuncionarios"]
        minFuncionarios = json_data["minFuncionarios"]
        numFolgas = json_data["folgasPreferenciais"]
        folgasProcessadas = process_file_content(numFuncionarios, minFuncionarios, numFolgas)

        return str(folgasProcessadas)

    # If the request does not meet the expected criteria, return an error response
    return "Invalid request"


def process_file_content(numFuncionarios, minFuncionarios, numFolgas):
    H = [1, 4, 11, 14, 18, 19, 25]  # conjunto de feriados e Domingos de Novembro
    NF = 5  # número de folga no mês
    m = 30  # número de dias do mês de Novembro
    n = numFuncionarios  # número de funcionário
    QuantidadeLinhas = n +2
    numeFolga = []
    #Criação da matriz de folgas, lendo o arquivo informado
    QuantidadeLinhas = int(numFolgas.__len__())
    for l in range(QuantidadeLinhas):
        dias_folga = [int(dia)-1 for dia in numFolgas[l]]
        numeFolga.append(dias_folga)
        print(numeFolga[l])
        
    modelo = gp.Model()  # inicializa o modelo

    # VARIÁVEIS DE DESCISÃO
    x = modelo.addVars(
        range(n), range(m), vtype=gp.GRB.BINARY
    )  # cria variável binaria x

    z = modelo.addVar()
    # FUNÇÃO OBJETIVO
    # modelo.setObjective(sum(x[i,j] for i in range(n) for j in numeFolga[i]), sense = gp.GRB.MINIMIZE)
    modelo.setObjective(z, sense=gp.GRB.MINIMIZE)

    # RESTRIÇÕES
    # Cada funcionário deve ter 5 folgas durante o mês, soma dos dias trabalhados
    # de cada funcionário deve ser exatamente igual os dias do mês - 5 folgas de direito
    c0 = modelo.addConstrs(
        sum(x[i,j] for j in numeFolga[i]) <= z
        for i in range(n)
    )


    c1 = modelo.addConstrs(sum(x[i, j] for j in range(m)) == m - NF for i in range(n))

    # A equipe não pode operar com menos de x funcionários (definido contratualmente) em um dia
    c2 = modelo.addConstrs(
        sum(x[i, j] for i in range(n)) >= minFuncionarios for j in range(m)
    )

    # Nenhum funcionário pode trabalhar por 6 dias seguidos sem folga
    c3 = modelo.addConstrs(
        sum(x[i, j] for j in range(k, k + 6)) <= 5
        for k in range(m - 5)
        for i in range(n)
    )

    # Pelo menos uma folga deve ocorrer em um domingo ou feriado
    c4 = modelo.addConstrs(sum(x[i, j] for j in H) == 6 for i in range(n))

    # Pelo menos duas folgas deve ocorrer dentro dos dias escolhidos pelos funcionários
    # c5 = modelo.addConstrs(
    #     sum(x[i,j] for j in numeFolga[i]) >= 2
    #     for i in range (n)
    # )

    # Suprimindo console output
    modelo.setParam("OutputFlag", 0)

    # Resolvendo
    modelo.optimize()

    # verificar status da solução
    status = modelo.Status
    # print("Status = ", status)
    app = Flask(__name__)
    numDias = (len(numeFolga) * 4) - int(modelo.objVal)
    obj = []
    if status == gp.GRB.OPTIMAL:
        print("Valor ótimo = {}".format(modelo.objVal))
        print("Dias atendidos: {}\n".format(numDias))
        print("Escala de Funcionários para o mês de novembro de 2023 (Dias Trabalhados):")
        for i in range(n):
            escala = [j + 1 for j in range(m) if x[i, j].x == 1]
            print(f"Func {i + 1}: {escala}")
        print("\n\nEscala de Funcionários para o mês de novembro de 2023 (Folgas):")
        for i in range(n):
            escala = [j + 1 for j in range(m) if x[i, j].x == 0]
            obj.append({"id": i + 1, "value": escala})
            print(f"Func {i + 1}: {escala}")
        return json.dumps(obj)
    else:
        print("Problema não resolvido")


if __name__ == "__main__":
    app.run(debug=True)