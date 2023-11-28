import gurobipy as gp
from flask import Flask, request,jsonify
from flask_cors import CORS
import math
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
        tipo = json_data["tipo"]
        folgasProcessadas = process_file_content(numFuncionarios, minFuncionarios, numFolgas, tipo)

        return str(folgasProcessadas)

    # If the request does not meet the expected criteria, return an error response
    return "Invalid request"


def process_file_content(numFuncionarios, minFuncionarios, numFolgas, tipo):
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
        
    modelo = gp.Model()  # inicializa o modelo

    # VARIÁVEIS DE DESCISÃO
    x = modelo.addVars(
        range(n), range(m), vtype=gp.GRB.BINARY
    )  # cria variável binaria x
    z = modelo.addVar() # cria variável z (makespan)
    
    # FUNÇÃO OBJETIVO
    # modelo.setObjective(sum(x[i,j] for i in range(n) for j in numeFolga[i]), sense = gp.GRB.MINIMIZE)
    if(tipo == "B"):
        modelo.setObjective(z, sense = gp.GRB.MINIMIZE)
    else:
        modelo.setObjective(sum(x[i,j] for i in range(n) for j in numeFolga[i]), sense = gp.GRB.MINIMIZE)
        
    numRestricoesManuais = 0
    # RESTRIÇÕES
    # Cada funcionário deve ter 5 folgas durante o mês, soma dos dias trabalhados
    # de cada funcionário deve ser exatamente igual os dias do mês - 5 folgas de direito


    # RESTRIÇÕES
    if(tipo == "B"):
        c0 = modelo.addConstrs(sum(x[i,j] for j in numeFolga[i]) <= z for i in range (n))
        numRestricoesManuais += 1
    
    #Cada funcionário deve ter 5 folgas durante o mês, soma dos dias trabalhados
    #de cada funcionário deve ser exatamente igual os dias do mês - 5 folgas de direito
    c1 = modelo.addConstrs(
        sum(x[i,j] for j in range (m)) == m-NF
        for i in range (n)
    )
    numRestricoesManuais += 1

    #A equipe não pode operar com menos de x funcionários (definido contratualmente) em um dia
    c2 = modelo.addConstrs(
        sum(x[i,j] for i in range (n)) >= minFuncionarios 
        for j in range (m)   
    )
    numRestricoesManuais += 1

    #Nenhum funcionário pode trabalhar por 6 dias seguidos sem folga
    c3 = modelo.addConstrs(
        sum(x[i, j] for j in range(k, k + 6)) <= NF
        for k in range(m - 5)
        for i in range(n)
    )
    numRestricoesManuais += 1

    #Pelo menos uma folga deve ocorrer em um domingo ou feriado
    c4 = modelo.addConstrs(
        sum(x[i,j] for j in H) == NF+1
        for i in range (n)
    )
    numRestricoesManuais += 1
    
    

    # Suprimindo console output
    modelo.setParam("OutputFlag", 0)

    # Resolvendo
    modelo.optimize()

    # verificar status da solução
    status = modelo.Status
    # print("Status = ", status)
    app = Flask(__name__)
    diasTotais = len(numeFolga) * 4
    numDias = sum(x[i,j].x for i in range (n) for j in numeFolga[i])
    numeFolgasEscolhidas = []
    for i in range(n):
        numeFolgasEscolhidas.append({"id": i + 1, "value": numeFolga[i]})
    obj = []
    if status == gp.GRB.OPTIMAL:
        obj.append({"ValorOtimo":  math.ceil(modelo.objVal)})
        obj.append({"DiasAtendidos": math.ceil(numDias)})
        obj.append({"DiasNaoAtendidos": math.ceil(numDias)})
        obj.append({"QuantidadeRestricoes": numRestricoesManuais})
        folgasPreferidas = []
        # Escala de funcionários para o mês de novembro de 2023
        for i in range(n):
            escala = [j + 1 for j in range(m) if x[i, j].x == 1]
        for i in range(n):
            escala = [j + 1 for j in range(m) if x[i, j].x == 0]
            for i in range(escala.__len__()):
                escala[i] = escala[i] - 1
            folgasPreferidas.append({"id": i + 1, "value": escala})
        obj.append({"DiasCalculados": folgasPreferidas})
        obj.append({"DiasEscolhidos": numeFolgasEscolhidas})
        return json.dumps(obj)
    else:
        return "Problema não resolvido"


if __name__ == "__main__":
    app.run(debug=True)