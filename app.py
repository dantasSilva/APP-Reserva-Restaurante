from flask import Flask, render_template, request, redirect, url_for  # Importa funcionalidades do Flask
from flask_sqlalchemy import SQLAlchemy  # Importa o ORM para interagir com o banco de dados
from datetime import datetime, date  # Para manipulação de datas e horas

app = Flask(__name__)  # Inicializa a aplicação Flask
# Configurações do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o objeto de banco de dados com as configurações acima
db = SQLAlchemy(app)

# Modelo de dados para a tabela de reservas
class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # ID único da reserva
    nome_responsavel = db.Column(db.String(100), nullable=False)  # Nome do responsável
    data = db.Column(db.Date, nullable=False)  # Data da reserva
    hora = db.Column(db.Time, nullable=False)  # Hora da reserva
    numero_mesa = db.Column(db.Integer, nullable=False)  # Número da mesa
    qtd_pessoas = db.Column(db.Integer, nullable=False)  # Quantidade de pessoas
    status = db.Column(db.String(20), nullable=False, default='reservada')  # Status da reserva
    garcom_confirmador = db.Column(db.String(100))  # Nome do garçom que confirmou (opcional)

# Cria as tabelas no banco de dados
with app.app_context():
    db.create_all()

# Rota da página inicial
@app.route('/')
def index():
    return render_template('index.html')

# Rota para a interface do atendente
@app.route('/atendente')
def atendente():
    reservas = Reserva.query.filter_by(status='reservada').all()  # Busca todas as reservas com status "reservada"
    mensagem = request.args.get('mensagem')
    tipo = request.args.get('tipo', 'sucesso')
    return render_template('atendente.html', reservas=reservas, mensagem=mensagem, tipo=tipo)

# Rota para criação de nova reserva
@app.route('/atendente/criar', methods=['POST'])
def criar_reserva():
    data_formulario = request.form
    data_reserva = datetime.strptime(data_formulario['data'], '%Y-%m-%d').date()
    hora_reserva = datetime.strptime(data_formulario['hora'], '%H:%M').time()

    #Verificação de data passada
    if data_reserva < date.today():
        mensagem_erro = 'Erro: Não é possível criar uma reserva em uma data passada.'
        return redirect(url_for('atendente', mensagem=mensagem_erro, tipo='erro'))

    #Validação de hora passada (APENAS se a data for hoje)
    if data_reserva == date.today() and hora_reserva < datetime.now().time():
        mensagem_erro = 'Erro: Não é possível criar uma reserva para um horário que já passou hoje.'
        return redirect(url_for('atendente', mensagem=mensagem_erro, tipo='erro'))

    # Verifica se já existe uma reserva para a mesma mesa, data e hora
    reserva_existente = Reserva.query.filter(
        Reserva.data == data_reserva,
        Reserva.hora == hora_reserva,
        Reserva.numero_mesa == data_formulario['numero_mesa'],
        Reserva.status.in_(['reservada', 'confirmada'])
    ).first()

    # Se existir, redireciona com mensagem de erro
    if reserva_existente:
        return redirect(url_for('atendente', mensagem='Erro: Mesa já reservada para essa data e hora.', tipo='erro'))

    # Cria nova reserva
    nova = Reserva(
        nome_responsavel=data_formulario['nome_responsavel'],
        data=data_reserva,
        hora=hora_reserva,
        numero_mesa=data_formulario['numero_mesa'],
        qtd_pessoas=data_formulario['qtd_pessoas'],
        status='reservada'
    )
    db.session.add(nova)
    db.session.commit()
    return redirect(url_for('atendente', mensagem='Reserva criada com sucesso!', tipo='sucesso'))

# Rota para cancelamento de reserva
@app.route('/atendente/cancelar/<int:id>', methods=['POST'])
def cancelar_reserva(id):
    reserva = Reserva.query.get(id)

    # Se não encontrar a reserva, redireciona com erro
    if not reserva:
        return redirect(url_for('atendente', mensagem='Erro: Reserva não encontrada.', tipo='erro'))

    # Se a reserva estiver apenas "reservada", pode cancelar
    if reserva.status == 'reservada':
        db.session.delete(reserva)
        db.session.commit()
        return redirect(url_for('atendente', mensagem='Reserva cancelada com sucesso!', tipo='alerta'))
    else:
        mensagem_erro = f"A reserva não pode ser cancelada, pois seu status atual é '{reserva.status}'."
        return redirect(url_for('atendente', mensagem=mensagem_erro, tipo='erro'))

# Rota para a interface do garçom
@app.route('/garcom')
def garcom():
    reservas = Reserva.query.filter_by(status='reservada').all()  # Apenas reservas pendentes
    mensagem = request.args.get('mensagem')
    tipo = request.args.get('tipo', 'sucesso')
    return render_template('garcom.html', reservas=reservas, mensagem=mensagem, tipo=tipo)

# Rota para confirmar uma reserva (garçom)
@app.route('/garcom/confirmar/<int:id>', methods=['POST'])
def confirmar_reserva(id):
    reserva = Reserva.query.get(id)
    if reserva:
        if reserva.data != date.today():
            return redirect(url_for('garcom', mensagem='Alerta: Só é possível confirmar reservas para o dia de hoje.', tipo='alerta'))
        if reserva.status == 'reservada':
            reserva.status = 'confirmada'
            reserva.garcom_confirmador = request.form['garcom']
            db.session.commit()
            return redirect(url_for('garcom', mensagem='Reserva confirmada com sucesso!', tipo='sucesso'))
        else:
            return redirect(url_for('garcom', mensagem='Erro: A reserva não está mais disponível para confirmação.', tipo='erro'))
    else:
        return redirect(url_for('garcom', mensagem='Erro: Reserva não encontrada.', tipo='erro'))

# Rota da interface do gerente
@app.route('/gerente')
def gerente():
    reservas = None
    mensagem = request.args.get('mensagem')
    tipo = request.args.get('tipo', 'sucesso')
    return render_template('gerente.html', reservas=reservas, mensagem=mensagem, tipo=tipo)

# Rota para gerar relatórios (por período, mesa ou garçom)
@app.route('/gerente/relatorio')
def gerar_relatorio():
    tipo = request.args.get('tipo')
    data_inicial = request.args.get('data_inicial')
    data_final = request.args.get('data_final')
    numero_mesa = request.args.get('numero_mesa')

    if tipo == 'periodo':
        if data_inicial and data_final:
            data_i = datetime.strptime(data_inicial, '%Y-%m-%d').date()
            data_f = datetime.strptime(data_final, '%Y-%m-%d').date()
            reservas = Reserva.query.filter(Reserva.data.between(data_i, data_f)).all()
        else:
            return redirect(url_for('gerente', mensagem='Informe a data inicial e final.', tipo='erro'))

        return render_template('gerente.html', reservas=reservas, tipo_relatorio='periodo')

    elif tipo == 'mesa':
        if numero_mesa:
            reservas = Reserva.query.filter_by(numero_mesa=numero_mesa).all()
        else:
            return redirect(url_for('gerente', mensagem='Informe o número da mesa.', tipo='erro'))

        return render_template('gerente.html', reservas=reservas, tipo_relatorio='mesa')

    elif tipo == 'garcom':
        reservas = Reserva.query.filter_by(status='confirmada').all()
        relatorio_por_garcom = {}
        for r in reservas:
            garcom = r.garcom_confirmador or 'Não informado'
            if garcom not in relatorio_por_garcom:
                relatorio_por_garcom[garcom] = []
            relatorio_por_garcom[garcom].append(r)

        return render_template('gerente.html', relatorio_por_garcom=relatorio_por_garcom, tipo_relatorio='garcom')

    else:
        return redirect(url_for('gerente', mensagem='Tipo de relatório inválido.', tipo='erro'))

# Executa a aplicação se este for o arquivo principal
if __name__ == '__main__':
    app.run(debug=True)