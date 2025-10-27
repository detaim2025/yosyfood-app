# --- START OF FILE app.py (UPDATED WITH FLEXIBLE CONSUMO MODULE) ---

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, current_user
from datetime import datetime, timedelta  # <--- LÍNEA CORREGIDA
from dotenv import load_dotenv
from sqlalchemy import func
import os

# -----------------------------------------------------
# CONFIGURACIÓN INICIAL
# -----------------------------------------------------
load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "dev_secret_key")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///yosyfood.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "dashboard"

# -----------------------------------------------------
# MODELOS
# -----------------------------------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)

class Inventario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo_barras = db.Column(db.String(50), unique=True, nullable=True)
    nombre = db.Column(db.String(100), nullable=False)
    cantidad = db.Column(db.Float, nullable=False)
    unidad = db.Column(db.String(20), nullable=False)
    minimo = db.Column(db.Float, default=0)
    precio = db.Column(db.Float, default=0)
    casino = db.Column(db.String(20), nullable=False, default="Casino 1")

class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recibo_id = db.Column(db.String(50), nullable=False, index=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    producto_id = db.Column(db.Integer, db.ForeignKey('inventario.id'), nullable=False)
    cantidad = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    pago = db.Column(db.Float, nullable=False)
    cambio = db.Column(db.Float, nullable=False)
    vendedor = db.Column(db.String(100), nullable=False)
    casino = db.Column(db.String(20), nullable=False, default="Casino 1")
    producto = db.relationship('Inventario', backref='ventas')

class Compra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recibo_compra_id = db.Column(db.String(50), nullable=False, index=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    producto_id = db.Column(db.Integer, db.ForeignKey('inventario.id'), nullable=False)
    cantidad = db.Column(db.Float, nullable=False)
    costo_unitario = db.Column(db.Float, nullable=False)
    proveedor = db.Column(db.String(100), nullable=False)
    comprador = db.Column(db.String(100), nullable=False)
    casino = db.Column(db.String(20), nullable=False, default="Casino 1")
    producto = db.relationship('Inventario', backref='compras')

class Inversion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    descripcion = db.Column(db.String(200), nullable=False)
    costo = db.Column(db.Float, nullable=False)
    proveedor = db.Column(db.String(100), nullable=False)
    comprador = db.Column(db.String(100), nullable=False)
    casino = db.Column(db.String(20), nullable=False, default="Casino 1")

class Gasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    descripcion = db.Column(db.String(200), nullable=False)
    costo = db.Column(db.Float, nullable=False)
    proveedor = db.Column(db.String(100), nullable=False)
    comprador = db.Column(db.String(100), nullable=False)
    casino = db.Column(db.String(20), nullable=False, default="Casino 1")

# --- NUEVOS MODELOS PARA CONSUMO DE REFRIGERIOS (SISTEMA FLEXIBLE) ---
class ConsumoRefrigerio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    descripcion = db.Column(db.String(200), nullable=False)
    cantidad_total = db.Column(db.Integer, nullable=False)
    responsable = db.Column(db.String(100), nullable=False)
    casino = db.Column(db.String(20), nullable=False)
    items = db.relationship('ConsumoRefrigerioItem', backref='consumo', cascade="all, delete-orphan")

class ConsumoRefrigerioItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    consumo_id = db.Column(db.Integer, db.ForeignKey('consumo_refrigerio.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('inventario.id'), nullable=False)
    cantidad_consumida = db.Column(db.Float, nullable=False)
    producto = db.relationship('Inventario')

# -----------------------------------------------------
# CARGA DE USUARIO Y CONTEXTO
# -----------------------------------------------------
@login_manager.user_loader
def load_user(user_id): return User.query.get(int(user_id))

@app.context_processor
def inject_current_year(): return {'current_year': datetime.utcnow().year}

# -----------------------------------------------------
# RUTAS (EXISTENTES)
# -----------------------------------------------------
# (Todas tus rutas de dashboard, inventario, ventas, compras, etc. van aquí sin cambios)
# ...
@app.route('/')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', user=current_user, Inventario=Inventario)
@app.route('/inventario')
def inventario_list():
    casino = request.args.get('casino', 'Casino 1')
    items = Inventario.query.filter_by(casino=casino).order_by(Inventario.nombre).all()
    return render_template('inventario_list.html', items=items, casino=casino)
@app.route('/inventario/nuevo', methods=['GET', 'POST'])
def inventario_nuevo():
    if request.method == 'POST':
        item = Inventario(codigo_barras=request.form['codigo_barras'],nombre=request.form['nombre'],cantidad=float(request.form['cantidad']),unidad=request.form['unidad'],minimo=float(request.form.get('minimo', 0)),precio=float(request.form.get('precio', 0)),casino=request.form['casino'])
        db.session.add(item)
        db.session.commit()
        flash('✅ Insumo creado exitosamente.', 'success')
        return redirect(url_for('inventario_list', casino=item.casino))
    return render_template('inventario_form.html', item=None)
@app.route('/inventario/editar/<int:item_id>', methods=['GET', 'POST'])
def inventario_editar(item_id):
    item = Inventario.query.get_or_404(item_id)
    if request.method == 'POST':
        item.codigo_barras = request.form['codigo_barras']; item.nombre = request.form['nombre']; item.cantidad = float(request.form['cantidad']); item.unidad = request.form['unidad']; item.minimo = float(request.form.get('minimo', 0)); item.precio = float(request.form.get('precio', 0)); item.casino = request.form['casino']
        db.session.commit()
        flash('🟣 Insumo actualizado correctamente.', 'info')
        return redirect(url_for('inventario_list', casino=item.casino))
    return render_template('inventario_form.html', item=item)
@app.route('/inventario/eliminar/<int:item_id>', methods=['POST'])
def inventario_eliminar(item_id):
    item = Inventario.query.get_or_404(item_id)
    casino = item.casino
    if item.ventas or item.compras:
        flash('❌ No se puede eliminar un insumo con historial de ventas o compras.', 'danger')
        return redirect(url_for('inventario_list', casino=casino))
    db.session.delete(item)
    db.session.commit()
    flash('⚠️ Insumo eliminado.', 'warning')
    return redirect(url_for('inventario_list', casino=casino))
@app.route('/ventas')
def venta_list():
    from itertools import groupby
    casino = request.args.get('casino', 'Casino 1')
    ventas_query = Venta.query.filter_by(casino=casino).order_by(Venta.fecha.desc(), Venta.recibo_id).all()
    ventas_agrupadas = []
    for key, group in groupby(ventas_query, key=lambda x: x.recibo_id):
        items = list(group); primera_venta = items[0]; total_recibo = sum(item.total for item in items)
        ventas_agrupadas.append({'recibo_id': key,'fecha': primera_venta.fecha,'vendedor': primera_venta.vendedor,'pago': primera_venta.pago,'cambio': primera_venta.cambio,'total_recibo': total_recibo,'productos': items})
    return render_template('ventas_list.html', recibos=ventas_agrupadas, casino=casino)
@app.route('/ventas/registrar')
def venta_registrar():
    casino = request.args.get('casino', 'Casino 1')
    productos = Inventario.query.filter_by(casino=casino).order_by(Inventario.nombre).all()
    return render_template('ventas_form.html', casino=casino, productos=productos)
@app.route('/ventas/registrar_multiple', methods=['POST'])
def venta_registrar_multiple():
    import uuid; from sqlalchemy.exc import IntegrityError
    data = request.get_json(); carrito = data.get('carrito'); pago = float(data.get('pago')); vendedor = data.get('vendedor'); casino = data.get('casino')
    if not all([carrito, pago is not None, vendedor, casino]): return jsonify({'error': 'Faltan datos en la solicitud.'}), 400
    try:
        with db.session.begin_nested():
            total_general = 0; productos_a_actualizar = []
            for item in carrito:
                producto = db.session.get(Inventario, item['id'])
                if not producto or producto.cantidad < float(item['cantidad']): raise ValueError(f"No hay stock para '{item['nombre']}'")
                total_item = producto.precio * float(item['cantidad']); total_general += total_item
                productos_a_actualizar.append({'producto_db': producto, 'cantidad_vendida': float(item['cantidad']),'total_item': total_item})
            cambio = pago - total_general
            if cambio < 0: raise ValueError(f'Pago insuficiente. Faltan ${abs(cambio):.2f}.')
            recibo_id = str(uuid.uuid4())
            for item_info in productos_a_actualizar:
                item_info['producto_db'].cantidad -= item_info['cantidad_vendida']
                nueva_venta = Venta(recibo_id=recibo_id, producto_id=item_info['producto_db'].id, cantidad=item_info['cantidad_vendida'], total=item_info['total_item'], pago=pago, cambio=cambio, vendedor=vendedor, casino=casino)
                db.session.add(nueva_venta)
        db.session.commit()
        return jsonify({'mensaje': f'Venta registrada. Cambio: ${cambio:.2f}', 'cambio': cambio}), 200
    except ValueError as e: db.session.rollback(); return jsonify({'error': str(e)}), 400
    except IntegrityError: db.session.rollback(); return jsonify({'error': 'Error al guardar la venta.'}), 500
@app.route('/compras')
def compra_list():
    from itertools import groupby
    casino = request.args.get('casino', 'Casino 1')
    compras_query = Compra.query.filter_by(casino=casino).order_by(Compra.fecha.desc(), Compra.recibo_compra_id).all()
    compras_agrupadas = []
    for key, group in groupby(compras_query, key=lambda x: x.recibo_compra_id):
        items = list(group); primera_compra = items[0]; total_recibo = sum(item.cantidad * item.costo_unitario for item in items)
        compras_agrupadas.append({'recibo_compra_id': key, 'fecha': primera_compra.fecha, 'proveedor': primera_compra.proveedor, 'comprador': primera_compra.comprador, 'total_recibo': total_recibo, 'productos': items})
    return render_template('compras_list.html', recibos=compras_agrupadas, casino=casino)
@app.route('/compras/registrar')
def compra_registrar():
    casino = request.args.get('casino', 'Casino 1')
    productos = Inventario.query.filter_by(casino=casino).order_by(Inventario.nombre).all()
    return render_template('compras_form.html', casino=casino, productos=productos)
@app.route('/compras/registrar_multiple', methods=['POST'])
def compra_registrar_multiple():
    import uuid; from sqlalchemy.exc import IntegrityError
    data = request.get_json(); carrito = data.get('carrito'); proveedor = data.get('proveedor'); comprador = data.get('comprador'); casino = data.get('casino')
    if not all([carrito, proveedor, comprador, casino]): return jsonify({'error': 'Faltan datos en la solicitud.'}), 400
    try:
        with db.session.begin_nested():
            recibo_id = str(uuid.uuid4())
            for item in carrito:
                producto = db.session.get(Inventario, item['id'])
                if not producto: raise ValueError(f"Producto con ID {item['id']} no encontrado.")
                producto.cantidad += float(item['cantidad'])
                nueva_compra = Compra(recibo_compra_id=recibo_id, producto_id=producto.id, cantidad=float(item['cantidad']), costo_unitario=float(item['costo_unitario']), proveedor=proveedor, comprador=comprador, casino=casino)
                db.session.add(nueva_compra)
        db.session.commit()
        return jsonify({'mensaje': 'Compra registrada y stock actualizado con éxito.'}), 200
    except ValueError as e: db.session.rollback(); return jsonify({'error': str(e)}), 400
    except IntegrityError: db.session.rollback(); return jsonify({'error': 'Error al guardar la compra.'}), 500
# INVERSIONES (CRUD COMPLETO)
# -----------------------------------------------------
@app.route('/inversiones')
def inversion_list():
    casino = request.args.get('casino', 'Casino 1')
    inversiones = Inversion.query.filter_by(casino=casino).order_by(Inversion.fecha.desc()).all()
    return render_template('inversion_list.html', items=inversiones, casino=casino)

@app.route('/inversiones/nueva', methods=['GET', 'POST'])
def inversion_nueva():
    if request.method == 'POST':
        nueva_inversion = Inversion(fecha=datetime.strptime(request.form['fecha'], '%Y-%m-%d'),descripcion=request.form['descripcion'],costo=float(request.form['costo']),proveedor=request.form['proveedor'],comprador=request.form['comprador'],casino=request.form['casino'])
        db.session.add(nueva_inversion)
        db.session.commit()
        flash('✅ Inversión registrada correctamente.', 'success')
        return redirect(url_for('inversion_list', casino=nueva_inversion.casino))
    return render_template('inversion_form.html', item=None, casino=request.args.get('casino', 'Casino 1'))

@app.route('/inversiones/editar/<int:inversion_id>', methods=['GET', 'POST'])
def inversion_editar(inversion_id):
    item = Inversion.query.get_or_404(inversion_id)
    if request.method == 'POST':
        item.fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d')
        item.descripcion = request.form['descripcion']
        item.costo = float(request.form['costo'])
        item.proveedor = request.form['proveedor']
        item.comprador = request.form['comprador']
        item.casino = request.form['casino']
        db.session.commit()
        flash('🟣 Inversión actualizada correctamente.', 'info')
        return redirect(url_for('inversion_list', casino=item.casino))
    return render_template('inversion_form.html', item=item, casino=item.casino)

@app.route('/inversiones/eliminar/<int:inversion_id>', methods=['POST'])
def inversion_eliminar(inversion_id):
    item = Inversion.query.get_or_404(inversion_id)
    casino = item.casino
    db.session.delete(item)
    db.session.commit()
    flash('⚠️ Inversión eliminada.', 'warning')
    return redirect(url_for('inversion_list', casino=casino))

# -----------------------------------------------------
# GASTOS (CRUD COMPLETO)
# -----------------------------------------------------
@app.route('/gastos')
def gasto_list():
    casino = request.args.get('casino', 'Casino 1')
    gastos = Gasto.query.filter_by(casino=casino).order_by(Gasto.fecha.desc()).all()
    return render_template('gasto_list.html', items=gastos, casino=casino)

@app.route('/gastos/nuevo', methods=['GET', 'POST'])
def gasto_nuevo():
    if request.method == 'POST':
        nuevo_gasto = Gasto(fecha=datetime.strptime(request.form['fecha'], '%Y-%m-%d'),descripcion=request.form['descripcion'],costo=float(request.form['costo']),proveedor=request.form['proveedor'],comprador=request.form['comprador'],casino=request.form['casino'])
        db.session.add(nuevo_gasto)
        db.session.commit()
        flash('✅ Gasto registrado correctamente.', 'success')
        return redirect(url_for('gasto_list', casino=nuevo_gasto.casino))
    return render_template('gasto_form.html', item=None, casino=request.args.get('casino', 'Casino 1'))

@app.route('/gastos/editar/<int:gasto_id>', methods=['GET', 'POST'])
def gasto_editar(gasto_id):
    item = Gasto.query.get_or_404(gasto_id)
    if request.method == 'POST':
        item.fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d')
        item.descripcion = request.form['descripcion']
        item.costo = float(request.form['costo'])
        item.proveedor = request.form['proveedor']
        item.comprador = request.form['comprador']
        item.casino = request.form['casino']
        db.session.commit()
        flash('🟣 Gasto actualizado correctamente.', 'info')
        return redirect(url_for('gasto_list', casino=item.casino))
    return render_template('gasto_form.html', item=item, casino=item.casino)

@app.route('/gastos/eliminar/<int:gasto_id>', methods=['POST'])
def gasto_eliminar(gasto_id):
    item = Gasto.query.get_or_404(gasto_id)
    casino = item.casino
    db.session.delete(item)
    db.session.commit()
    flash('⚠️ Gasto eliminado.', 'warning')
    return redirect(url_for('gasto_list', casino=casino))
@app.route('/api/producto/<code>')
def buscar_producto_por_codigo(code):
    casino = request.args.get('casino', 'Casino 1')
    producto = Inventario.query.filter_by(codigo_barras=code, casino=casino).first()
    if producto: return jsonify({'id': producto.id, 'nombre': producto.nombre, 'codigo_barras': producto.codigo_barras, 'precio': producto.precio, 'stock': producto.cantidad, 'unidad': producto.unidad})
    return jsonify({'error': 'Producto no encontrado'}), 404
@app.route('/api/inventario/nuevo', methods=['POST'])
def api_inventario_nuevo():
    data = request.get_json()
    if not data or not data.get('nombre') or not data.get('unidad'): return jsonify({'error': 'Nombre y unidad son requeridos.'}), 400
    item = Inventario(codigo_barras=data.get('codigo_barras'), nombre=data.get('nombre'), cantidad=float(data.get('cantidad', 0)), unidad=data.get('unidad'), minimo=float(data.get('minimo', 0)), precio=float(data.get('precio', 0)), casino=data.get('casino', 'Casino 1'))
    db.session.add(item)
    db.session.commit()
    return jsonify({'id': item.id, 'nombre': item.nombre, 'codigo_barras': item.codigo_barras}), 201

# -----------------------------------------------------
# CONSUMO DE REFRIGERIOS (NUEVAS RUTAS CRUD)
# -----------------------------------------------------

@app.route('/analisis')
def analisis():
    # --- 1. OBTENER FILTROS DE FECHA Y CASINO ---
    casino = request.args.get('casino', 'Casino 1')
    
    # Manejo de fechas: por defecto los últimos 30 días
    fecha_fin_str = request.args.get('fecha_fin', datetime.utcnow().strftime('%Y-%m-%d'))
    fecha_inicio_str = request.args.get('fecha_inicio', (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d'))
    
    # Convertir a objetos datetime para las consultas
    fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
    # Se añade un día a la fecha fin para incluir todo el día en la consulta
    fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d') + timedelta(days=1)

    # --- 2. CONSULTAS A LA BASE DE DATOS ---

    # Ingresos totales por ventas
    total_ingresos = db.session.query(func.sum(Venta.total)).filter(
        Venta.casino == casino,
        Venta.fecha >= fecha_inicio,
        Venta.fecha < fecha_fin
    ).scalar() or 0

    # Costos totales (Compras + Gastos + Inversiones)
    total_compras = db.session.query(func.sum(Compra.cantidad * Compra.costo_unitario)).filter(
        Compra.casino == casino,
        Compra.fecha >= fecha_inicio,
        Compra.fecha < fecha_fin
    ).scalar() or 0
    
    total_gastos = db.session.query(func.sum(Gasto.costo)).filter(
        Gasto.casino == casino,
        Gasto.fecha >= fecha_inicio,
        Gasto.fecha < fecha_fin
    ).scalar() or 0

    total_inversiones = db.session.query(func.sum(Inversion.costo)).filter(
        Inversion.casino == casino,
        Inversion.fecha >= fecha_inicio,
        Inversion.fecha < fecha_fin
    ).scalar() or 0
    
    total_costos = total_compras + total_gastos + total_inversiones

    # Total de refrigerios servidos
    total_refrigerios = db.session.query(func.sum(ConsumoRefrigerio.cantidad_total)).filter(
        ConsumoRefrigerio.casino == casino,
        ConsumoRefrigerio.fecha >= fecha_inicio.date(),
        ConsumoRefrigerio.fecha < fecha_fin.date()
    ).scalar() or 0

    # --- 3. DATOS PARA GRÁFICOS ---
    
    # Gráfico de Ventas Diarias (Barras)
    ventas_por_dia = db.session.query(
        func.date(Venta.fecha).label('dia'),
        func.sum(Venta.total).label('total_dia')
    ).filter(
        Venta.casino == casino,
        Venta.fecha >= fecha_inicio,
        Venta.fecha < fecha_fin
    ).group_by('dia').order_by('dia').all()

    ventas_chart_labels = [v.dia.strftime('%d/%m') for v in ventas_por_dia]
    ventas_chart_data = [float(v.total_dia) for v in ventas_por_dia]

    # Gráfico de Desglose de Costos (Dona)
    costos_chart_labels = ['Compras', 'Gastos', 'Inversiones']
    costos_chart_data = [float(total_compras), float(total_gastos), float(total_inversiones)]

    # --- 4. PREPARAR CONTEXTO PARA LA PLANTILLA ---
    context = {
        'casino': casino,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': (fecha_fin - timedelta(days=1)).strftime('%Y-%m-%d'),
        'total_ingresos': total_ingresos,
        'total_costos': total_costos,
        'ganancia_bruta': total_ingresos - total_costos,
        'total_refrigerios': total_refrigerios,
        'ventas_por_dia': {
            'labels': ventas_chart_labels,
            'data': ventas_chart_data,
        },
        'desglose_costos': {
            'labels': costos_chart_labels,
            'data': costos_chart_data,
        }
    }
    
    return render_template('analisis.html', **context)


@app.route('/consumo')
def consumo_list():
    casino = request.args.get('casino', 'Casino 1')
    consumos = ConsumoRefrigerio.query.filter_by(casino=casino).order_by(ConsumoRefrigerio.fecha.desc()).all()
    return render_template('consumo_list.html', consumos=consumos, casino=casino)

@app.route('/consumo/nuevo', methods=['GET', 'POST'])
def consumo_nuevo():
    casino = request.args.get('casino', 'Casino 1')
    if request.method == 'POST':
        try:
            with db.session.begin_nested():
                nuevo_consumo = ConsumoRefrigerio(
                    fecha=datetime.strptime(request.form['fecha'], '%Y-%m-%d').date(),
                    descripcion=request.form['descripcion'],
                    cantidad_total=int(request.form['cantidad_total']),
                    responsable=request.form['responsable'],
                    casino=request.form['casino']
                )
                db.session.add(nuevo_consumo)

                productos_ids = request.form.getlist('producto_id[]')
                cantidades = request.form.getlist('cantidad[]')
                
                for i, producto_id_str in enumerate(productos_ids):
                    if producto_id_str and cantidades[i]:
                        producto_id = int(producto_id_str)
                        cantidad_consumida = float(cantidades[i]) * nuevo_consumo.cantidad_total
                        
                        producto_inv = db.session.get(Inventario, producto_id)
                        if producto_inv.cantidad < cantidad_consumida:
                            raise ValueError(f"Stock insuficiente para '{producto_inv.nombre}'. Necesitas: {cantidad_consumida}, Disponible: {producto_inv.cantidad}")
                        
                        producto_inv.cantidad -= cantidad_consumida
                        
                        item = ConsumoRefrigerioItem(
                            producto_id=producto_id,
                            cantidad_consumida=cantidad_consumida,
                            consumo=nuevo_consumo
                        )
                        db.session.add(item)
            
            db.session.commit()
            flash('✅ Consumo de refrigerio registrado y stock actualizado.', 'success')
            return redirect(url_for('consumo_list', casino=nuevo_consumo.casino))

        except (ValueError, AttributeError) as e:
            db.session.rollback()
            flash(f'❌ Error: {e}', 'danger')
            return redirect(url_for('consumo_nuevo', casino=casino))
    
    productos = Inventario.query.filter_by(casino=casino).order_by(Inventario.nombre).all()
    return render_template('consumo_form.html', productos=productos, casino=casino, consumo=None)


@app.route('/consumo/editar/<int:consumo_id>', methods=['GET', 'POST'])
def consumo_editar(consumo_id):
    consumo = ConsumoRefrigerio.query.get_or_404(consumo_id)
    casino = consumo.casino
    
    if request.method == 'POST':
        try:
            with db.session.begin_nested():
                # Revertir el descuento de inventario del consumo original
                for item in consumo.items:
                    producto_inv = db.session.get(Inventario, item.producto_id)
                    if producto_inv:
                        producto_inv.cantidad += item.cantidad_consumida

                # Limpiar los items viejos para reemplazarlos
                for item in list(consumo.items):
                    db.session.delete(item)
                
                # Actualizar datos principales
                consumo.fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
                consumo.descripcion = request.form['descripcion']
                consumo.cantidad_total = int(request.form['cantidad_total'])
                consumo.responsable = request.form['responsable']
                consumo.casino = request.form['casino']

                # Procesar los nuevos productos y aplicar el nuevo descuento
                productos_ids = request.form.getlist('producto_id[]')
                cantidades = request.form.getlist('cantidad[]')
                
                for i, producto_id_str in enumerate(productos_ids):
                    if producto_id_str and cantidades[i]:
                        producto_id = int(producto_id_str)
                        cantidad_consumida_nueva = float(cantidades[i]) * consumo.cantidad_total
                        
                        producto_inv = db.session.get(Inventario, producto_id)
                        if producto_inv.cantidad < cantidad_consumida_nueva:
                            raise ValueError(f"Stock insuficiente para '{producto_inv.nombre}'. Disponible: {producto_inv.cantidad} (después de revertir).")
                        
                        producto_inv.cantidad -= cantidad_consumida_nueva
                        
                        item = ConsumoRefrigerioItem(
                            producto_id=producto_id,
                            cantidad_consumida=cantidad_consumida_nueva,
                            consumo_id=consumo.id
                        )
                        db.session.add(item)
            
            db.session.commit()
            flash('🟣 Consumo de refrigerio actualizado correctamente.', 'info')
            return redirect(url_for('consumo_list', casino=consumo.casino))

        except (ValueError, AttributeError) as e:
            db.session.rollback()
            flash(f'❌ Error al actualizar: {e}', 'danger')
            # Es importante no redirigir inmediatamente para poder ver el error si se está depurando
            return redirect(url_for('consumo_editar', consumo_id=consumo_id))

    productos = Inventario.query.filter_by(casino=casino).order_by(Inventario.nombre).all()
    return render_template('consumo_form.html', consumo=consumo, productos=productos, casino=casino)


@app.route('/consumo/eliminar/<int:consumo_id>', methods=['POST'])
def consumo_eliminar(consumo_id):
    consumo = ConsumoRefrigerio.query.get_or_404(consumo_id)
    casino = consumo.casino
    
    with db.session.begin_nested():
        # Devolver los productos al inventario antes de eliminar
        for item in consumo.items:
            producto_inv = db.session.get(Inventario, item.producto_id)
            if producto_inv:
                producto_inv.cantidad += item.cantidad_consumida
        
        db.session.delete(consumo)
    
    db.session.commit()
    flash('⚠️ Registro de consumo eliminado. El stock ha sido restaurado.', 'warning')
    return redirect(url_for('consumo_list', casino=casino))

# -----------------------------------------------------
# EJECUCIÓN LOCAL
# -----------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
# Forzar re-despliegue 2