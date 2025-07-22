from flask import Flask, render_template, request, redirect, session, url_for
import pymssql
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'chave-padrao-fraca')

def conectar_banco():
    try:
        conn_str = os.getenv('DATABASE_URL')
        server, user, password, database = conn_str.split(';')
        conexao = pymssql.connect(
            server=server,
            user=user,
            password=password,
            database=database
        )   
        return conexao
    except Exception as e:
        print("Erro ao conectar:", e)
        return None

@app.route('/', methods=['GET', 'POST'])
def login():
    mensagem = ''
    if request.method == 'POST':
        id_ajudante = request.form['id_ajudante']
        senha = request.form['senha']

        conexao = conectar_banco()
        if conexao:
            cursor = conexao.cursor(as_dict=True)
            cursor.execute("SELECT * FROM Ajudantes WHERE ID = %s AND Senha = %s", (id_ajudante, senha))
            ajudante = cursor.fetchone()
            cursor.close()
            conexao.close()

            if ajudante:
                session['id_ajudante'] = id_ajudante

                # Verifica se o ID é de supervisor
                if id_ajudante.upper() in ['123']:
                    return redirect(url_for('painel_coordenador'))
                else:
                    return redirect(url_for('painel'))

            else:
                mensagem = 'ID ou Senha incorretos.'

    return render_template('login.html', mensagem=mensagem)

@app.route('/painel')
def painel():
    if 'id_ajudante' not in session:
        return redirect(url_for('login'))

    id_ajudante = session['id_ajudante']
    mes_selecionado = request.args.get('mes', '')

    conexao = conectar_banco()
    dados_formatados = []
    media_valor = 0
    media_meta = 0

    def calcula_media(lista):
        if lista:
            return round(sum(lista) / len(lista), 2)
        return 0

    if conexao:
        cursor = conexao.cursor(as_dict=True)
        try:
            query = """
                    SELECT 
                        CONVERT(varchar, Data, 23) AS DataISO,
                        ID,
                        Nome,
                        Valor,
                        Meta
                    FROM Palete
                    WHERE ID = %s
            """

            params = [id_ajudante]

            if mes_selecionado:
                query += " AND FORMAT(Data, 'yyyy-MM') = %s"
                params.append(mes_selecionado)

            query += " ORDER BY Data ASC"

            cursor.execute(query, tuple(params))
            resultados = cursor.fetchall()

            valores = []
            metas = []

            for linha in resultados:
                data = linha['DataISO']
                if data:
                    partes = data.split('-')
                    data_formatada = f"{partes[2]}/{partes[1]}/{partes[0]}"
                else:
                    data_formatada = "-"

                valor = linha['Valor']
                meta = linha['Meta']

                if valor is not None:
                    valores.append(valor)
                if meta is not None:
                    metas.append(meta)

                dados_formatados.append({
                    'data': data_formatada,
                    'id': linha['ID'],
                    'nome': linha['Nome'],
                    'valor': valor,
                    'meta': meta
                })

            media_valor = calcula_media(valores)
            media_meta = calcula_media(metas)

        except Exception as e:
            print("Erro ao consultar o banco:", e)
        finally:
            cursor.close()
            conexao.close()

    return render_template('painel.html',
                           dados=dados_formatados,
                           mes_selecionado=mes_selecionado,
                           media_valor=media_valor,
                           media_meta=media_meta)

@app.route('/painel_coordenador')
def painel_coordenador():
    if 'id_ajudante' not in session:
        return redirect(url_for('login'))

    mes_selecionado = request.args.get('mes', '')
    ajudante_selecionado = request.args.get('ajudante', '')

    conexao = conectar_banco()
    dados_formatados = []
    media_valor = 0
    media_meta = 0
    lista_ajudantes = []

    def calcula_media(lista):
        if lista:
            return round(sum(lista) / len(lista), 2)
        return 0

    if conexao:
        cursor = conexao.cursor(as_dict=True)
        try:
            # Carrega lista de ajudantes para o dropdown
            cursor.execute("SELECT DISTINCT Nome FROM Ajudantes WHERE Nome <> 'Coordenador João' ORDER BY Nome ASC")
            lista_ajudantes = [row['Nome'] for row in cursor.fetchall()]

            # Carrega dados da tabela Palete
            query = """
                SELECT 
                    CONVERT(varchar, Data, 23) AS DataISO,
                    ID,
                    Nome,
                    Valor,
                    Meta
                FROM Palete
                WHERE 1=1
            """
            params = []

            if ajudante_selecionado:
                query = """
                    SELECT 
                        CONVERT(varchar, Data, 23) AS DataISO,
                        ID,
                        Nome,
                        Valor,
                        Meta
                    FROM Palete
                    WHERE Nome = %s
                """
                params = [ajudante_selecionado]

            if mes_selecionado:
                query += " AND FORMAT(Data, 'yyyy-MM') = %s"
                params.append(mes_selecionado)

            query += " ORDER BY Data ASC"

            cursor.execute(query, tuple(params))
            resultados = cursor.fetchall()

            valores = []
            metas = []

            for linha in resultados:
                data = linha['DataISO']
                if data:
                    partes = data.split('-')
                    data_formatada = f"{partes[2]}/{partes[1]}/{partes[0]}"
                else:
                    data_formatada = "-"

                valor = linha['Valor']
                meta = linha['Meta']

                if valor is not None:
                    valores.append(valor)
                if meta is not None:
                    metas.append(meta)

                dados_formatados.append({
                    'data': data_formatada,
                    'id': linha['ID'],
                    'nome': linha['Nome'],
                    'valor': valor,
                    'meta': meta
                })

            media_valor = calcula_media(valores)
            media_meta = calcula_media(metas)

        except Exception as e:
            print("Erro ao consultar o banco (coordenador):", e)
        finally:
            cursor.close()
            conexao.close()

    return render_template('painel_coordenador.html',
                           dados=dados_formatados,
                           mes_selecionado=mes_selecionado,
                           ajudante_selecionado=ajudante_selecionado,
                           lista_ajudantes=lista_ajudantes,
                           media_valor=media_valor,
                           media_meta=media_meta)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))