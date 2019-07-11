import flask_whooshalchemy
from blinker import Namespace
from my_app import es
from my_app import db, app


catalog_signals = Namespace()
product_created = catalog_signals.signal('product-created')
category_created = catalog_signals.signal('category-created')


class Product(db.Model):
    __searchable__ = ['name', 'company']

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    price = db.Column(db.Float)
    company = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship(
        'Category', backref=db.backref('products', lazy='dynamic')
    )

    def __init__(self, name, price, category, company=''):
        self.name = name
        self.price = price
        self.category = category
        self.company = company

    def __repr__(self):
        return '<Product %d>' % self.id


def add_product_index_to_es(sender, product):
    es.index(index='catalog', body={
        'name': product.name,
        'category': product.category.name
    }, id=product.id)
    es.indices.refresh(index='catalog')

product_created.connect(add_product_index_to_es, app)


class Category(db.Model):
    __searchable__ = ['name']

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Category %d>' % self.id


def add_category_index_to_es(sender, category):
    es.index(index='catalog', body={
        'name': category.name,
    }, id=category.id)
    es.indices.refresh('catalog')

category_created.connect(add_category_index_to_es, app)
