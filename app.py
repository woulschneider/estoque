from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///estoque.db'
app.secret_key = 'supersecretkey'  # Chave secreta para Flask-Flash
db = SQLAlchemy(app)

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_sugerido = db.Column(db.Float, nullable=False)

class Venda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    data_venda = db.Column(db.DateTime, default=datetime.utcnow)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_venda = db.Column(db.Float, nullable=False)
    produto = db.relationship('Produto', backref=db.backref('vendas', lazy=True))

@app.route('/')
def index():
    produtos = Produto.query.all()
    return render_template('index.html', produtos=produtos)

@app.route('/add_produto', methods=['POST'])
def add_produto():
    nome = request.form['nome']
    quantidade = request.form['quantidade']
    preco_sugerido = request.form['preco_sugerido']
    novo_produto = Produto(nome=nome, quantidade=quantidade, preco_sugerido=preco_sugerido)
    try:
        db.session.add(novo_produto)
        db.session.commit()
        flash('Produto adicionado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao adicionar produto: {e}', 'danger')
    return redirect(url_for('index'))

@app.route('/add_venda', methods=['POST'])
def add_venda():
    produto_id = request.form['produto_id']
    quantidade = request.form['quantidade']
    valor_venda = request.form['valor_venda']
    produto = db.session.get(Produto, produto_id)
    if produto and produto.quantidade >= int(quantidade):
        try:
            nova_venda = Venda(produto_id=produto_id, quantidade=quantidade, valor_venda=valor_venda)
            produto.quantidade -= int(quantidade)
            db.session.add(nova_venda)
            db.session.commit()
            flash('Venda registrada com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar venda: {e}', 'danger')
    else:
        flash('Quantidade insuficiente ou produto não encontrado', 'danger')
    return redirect(url_for('index'))

@app.route('/edit_produto/<int:id>', methods=['GET', 'POST'])
def edit_produto(id):
    produto = db.session.get(Produto, id)
    if request.method == 'POST':
        produto.nome = request.form['nome']
        produto.quantidade = request.form['quantidade']
        produto.preco_sugerido = request.form['preco_sugerido']
        try:
            db.session.commit()
            flash('Produto atualizado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar produto: {e}', 'danger')
        return redirect(url_for('index'))
    return render_template('edit.html', produto=produto)

@app.route('/balanco')
def balanco():
    vendas = Venda.query.options(joinedload(Venda.produto)).all()
    total_vendas = sum(venda.valor_venda * venda.quantidade for venda in vendas)
    return render_template('balanco.html', vendas=vendas, total_vendas=total_vendas)

if __name__ == '__main__':
    app.run(debug=True)
