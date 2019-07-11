import json
from threading import Thread
from functools import wraps
from flask import request, Blueprint, render_template, jsonify, flash, \
    redirect, url_for
from my_app import db, app, es, cache, mail, celery
from my_app.catalog.models import Product, Category, product_created, \
    category_created
from sqlalchemy.orm.util import join
from flask_mail import Message

catalog = Blueprint('catalog', __name__)


def template_or_json(template=None):
    """"Return a dict from your view and this will either
    pass it to a template or render json. Use like:

    @template_or_json('template.html')
    """
    def decorated(f):
        @wraps(f)
        def decorated_fn(*args, **kwargs):
            ctx = f(*args, **kwargs)
            if request.is_xhr or not template:
                return jsonify(ctx)
            else:
                return render_template(template, **ctx)
        return decorated_fn
    return decorated


@celery.task()
def send_mail(category_id, category_name):
    with app.app_context():
        category = Category(category_name)
        category.id = category_id
        message = Message(
            "New category added",
            recipients=['some-receiver@domain.com']
        )
        message.body = render_template(
            "category-create-email-text.html",
            category=category
        )
        message.html = render_template(
            "category-create-email-html.html",
            category=category
        )
        mail.send(message)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@catalog.route('/')
@catalog.route('/home')
@template_or_json('home.html')
def home():
    products = Product.query.all()
    return {'count': len(products)}


@catalog.route('/product/<id>')
@cache.memoize(120)
def product(id):
    product = Product.query.get_or_404(id)
    return render_template('product.html', product=product)


@catalog.route('/products')
@catalog.route('/products/<int:page>')
def products(page=1):
    products = Product.query.paginate(page, 10)
    return render_template('products.html', products=products)


@catalog.route('/product-create', methods=['GET', 'POST'])
def create_product():
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        company = request.form.get('company')
        categ_name = request.form.get('category')
        category = Category.query.filter_by(name=categ_name).first()
        if not category:
            category = Category(categ_name)
        product = Product(name, price, category, company)
        db.session.add(product)
        db.session.commit()
        product_created.send(app, product=product)
        #product.add_index_to_es()
        flash('The product %s has been created' % name, 'success')
        return redirect(url_for('catalog.product', id=product.id))
    return render_template('product-create.html')


@catalog.route('/product-search')
@catalog.route('/product-search/<int:page>')
def product_search(page=1):
    name = request.args.get('name')
    price = request.args.get('price')
    company = request.args.get('company')
    category = request.args.get('category')
    products = Product.query
    if name:
        products = products.filter(Product.name.like('%' + name + '%'))
    if price:
        products = products.filter(Product.price == price)
    if company:
        products = products.filter(Product.company.like('%' + company + '%'))
    if category:
        products = products.select_from(join(Product, Category)).filter(
            Category.name.like('%' + category + '%')
        )
    return render_template(
        'products.html', products=products.paginate(page, 10)
    )


@catalog.route('/product-search-whoosh')
@catalog.route('/product-search-whoosh/<int:page>')
def product_search_whoosh(page=1):
    q = request.args.get('q')
    products = Product.query.whoosh_search(q)
    return render_template(
        'products.html', products=products.paginate(page, 10)
    )


@catalog.route('/product-search-es')
@catalog.route('/product-search-es/<int:page>')
def product_search_es(page=1):
    q = request.args.get('q')
    products = es.search(index="catalog", body={
        "query": {
            "query_string": {
                "query": q
            }
        }
    })
    return json.dumps(products)


@catalog.route('/category-create', methods=['POST',])
def create_category():
    name = request.form.get('name')
    category = Category(name)
    db.session.add(category)
    db.session.commit()
    category_created.send(app, category=category)
    #category.add_index_to_es()
    #mail.send(message)
    send_mail.apply_async(args=[category.id, category.name])
    return render_template('category.html', category=category)


@catalog.route('/category/<id>')
def category(id):
    category = Category.query.get_or_404(id)
    return render_template('category.html', category=category)


@catalog.route('/categories')
@cache.cached(timeout=120)
def categories():
    categories = Category.query.all()
    return render_template('categories.html', categories=categories)
