import json
import os
from flask import Blueprint, render_template, session, redirect, url_for, jsonify

from app.dto.dtos import ResultadosDTO
from app.process.utils import verificar_token_valido
from app.globals import api_url
main_bp = Blueprint("main", __name__)  # O nome do Blueprint deve ser "main"

@main_bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# Rota para a página de acesso
@main_bp.route("/acesso", methods=["GET"])
def acesso():
    # Verifica se o usuário já está autenticado
    if "head" in session:
        # Redireciona para o formulário se já estiver logado
        return redirect(url_for("main.form"))
    return render_template("acesso.html")

@main_bp.route("/form", methods=["GET"])
def form():
    if "head" not in session:
        return redirect(url_for("main.acesso"))  # Redireciona para a página de acesso se não estiver autenticado

    head = session["head"]
    usuario = session["usuario"]
    user_id = session.get("user_id")

    # Verifica se o token ainda é válido
    if not verificar_token_valido(api_url, head):
        session.pop("head", None)  # Remove o token inválido da sessão
        return redirect(url_for("main.acesso"))  # Redireciona para a página de acesso


    # Caminho para a pasta do usuário
    user_folder = os.path.join("app/static/data", user_id)

    # Caminho correto para o arquivo de resultados
    resultados_path = os.path.join(user_folder, f"{user_id}_resultados.json")

    # Verifica se o arquivo de resultados existe
    if os.path.exists(resultados_path):
        return redirect(url_for("main.painel"))  # Redireciona para o painel

    # Passa o nome do usuário para o template
    return render_template("form.html", usuario=usuario)


@main_bp.route("/painel", methods=["GET"])
def painel():
    if "head" not in session:
        return redirect(url_for("main.acesso"))  # Redireciona para a página de acesso se não estiver autenticado

    head = session["head"]
    user_id = session.get("user_id")

    # Verifica se o token ainda é válido
    if not verificar_token_valido(api_url, head):
        session.pop("head", None)  # Remove o token inválido da sessão
        return redirect(url_for("main.acesso"))  # Redireciona para a página de acesso


    # Caminho para os resultados salvos
    user_folder = os.path.join("app/static/data", user_id)
    resultados_path = os.path.join(user_folder, f"{user_id}_resultados.json")    # Tenta carregar os resultados do disco
    if os.path.exists(resultados_path):
        try:
            with open(resultados_path, "r") as f:
                resultados_data = json.load(f)
                  # Mapear campos antigos para os novos se necessário (compatibilidade retroativa)
                campos_mapeamento = {
                    'grafico_precipitacao': 'dados_grafico_precipitacao',
                    'grafico_precipitacao_vs_evaporacao': 'dados_grafico_precipitacao_vs_evaporacao',
                    'grafico_balanco_hidrico': 'dados_grafico_balanco_hidrico',
                    'grafico_rai': 'dados_grafico_rai',
                    'grafico_aridez': 'dados_grafico_aridez'
                }
                
                # Atualizar os nomes dos campos se necessário
                for campo_antigo, campo_novo in campos_mapeamento.items():
                    if campo_antigo in resultados_data and campo_novo not in resultados_data:
                        valor = resultados_data.pop(campo_antigo)
                        # Se o valor é uma string (caminho de arquivo), substitui por None para indicar dados indisponíveis
                        if isinstance(valor, str):
                            print(f"Convertendo campo {campo_antigo} de caminho de arquivo para dados estruturados (será substituído por dados de exemplo)")
                            resultados_data[campo_novo] = None  # Será tratado no frontend
                        else:
                            resultados_data[campo_novo] = valor
                
                resultados = ResultadosDTO(**resultados_data)  # Reconstrói o DTO a partir do JSON
        except Exception as e:
            print(f"Erro ao carregar resultados do disco: {e}")
            return render_template("error.html", mensagem="Erro ao carregar os resultados.")
    else:
        return render_template(
            "error.html", 
            mensagem="Nenhum resultado encontrado. Certifique-se de que o processamento foi concluído."
        )

    # Passa os resultados para o template
    return render_template("painel.html", resultados=resultados)
