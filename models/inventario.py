rom app import db


class Inventario(db.Model):
id = db.Column(db.Integer, primary_key=True)
nombre = db.Column(db.String(120), nullable=False)
cantidad = db.Column(db.Float, nullable=False, default=0)
unidad = db.Column(db.String(20), nullable=False)
minimo = db.Column(db.Float, default=0)


def __repr__(self):
return f'<Inventario {self.nombre}: {self.cantidad}{self.unidad}>'