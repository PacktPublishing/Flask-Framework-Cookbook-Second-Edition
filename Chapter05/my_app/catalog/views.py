import os
from functools import wraps
from werkzeug import secure_filename
from flask import request, Blueprint, render_template, jsonify, flash, \
    redirect, url_for
from my_app import db, app, ALLOWED_EXTENSIONS
from my_app.catalog.models import Product, Category, ProductForm, CategoryForm
from sqlalchemy.orm.util import join

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


def allowed_file(filename):
    return '.' in filename and \
            filename.lower().rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


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
    form = ProductForm()

    if form.validate_on_submit():
        name = form.name.data
        price = form.price.data
        category = Category.query.get_or_404(
            form.category.data
        )
        image = form.image.data
        if allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        product = Product(name, price, category, filename)
        db.session.add(product)
        db.session.commit()
        flash('The product %s has been created' % name, 'success')
        return redirect(url_for('catalog.product', id=product.id))

    if form.errors:
        flash(form.errors, 'danger')

    return render_template('product-create.html', form=form)


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


@catalog.route('/category-create', methods=['GET', 'POST'])
def create_category():
    form = CategoryForm()

    if form.validate_on_submit():
        name = form.name.data
        category = Category(name)
        db.session.add(category)
        db.session.commit()
        flash(
            'The category %s has been created' % name, 'success'
        )
        return redirect(
            url_for('catalog.category', id=category.id)
        )

    if form.errors:
        flash(form.errors, 'danger')

    return render_template('category-create.html', form=form)


@catalog.route('/category/<id>')
def category(id):
    category = Category.query.get_or_404(id)
    return render_template('category.html', category=category)


@catalog.route('/categories')
def categories():
    categories = Category.query.all()
    return render_template('categories.html', categories=categories)
