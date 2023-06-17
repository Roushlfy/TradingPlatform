import os
from functools import wraps
from uuid import uuid4

from flask import Flask
from flask import render_template
from flask import request, session, url_for, redirect

import db_api

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Database Concept (2022)'


def upload_file(file):
    if file is None or len(file.filename) == 0:
        return None
    filename = str(uuid4()).replace('-', '') + '_' + file.filename
    file.save(os.path.join('static/images', filename))
    return url_for('static', filename='images/' + filename)


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login') + '?next=' + request.url)
        return func(*args, **kwargs)

    return wrapper


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    success = request.args.get('success', None)
    if session.get('logged_in'):
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        user_id = db_api.login(username, password)
        if user_id is None:
            error = '用户名或密码错误！'
        else:
            session['logged_in'] = True
            session['username'] = username
            session['user_id'] = user_id
            return redirect(url_for('index'))
    return render_template('login.html', error=error, success=success)


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        if db_api.check_username_used(username):
            error = '该用户已被注册！'
        else:
            password = request.form.get('password', '')
            if db_api.create_user(username, password):
                return redirect(url_for('login') + '?success=注册成功！请登录。')
            else:
                error = '注册失败！'
    return render_template('signup.html', error=error)


@app.route('/', methods=['GET'])
@login_required
def index():
    key = request.args.get('key', '')
    exempt_postage = request.args.get('exempt_postage', 'all')
    state = request.args.get('state', 'all')
    price = request.args.get('price', 'asc')
    goods_list = db_api.get_goods_list(key, exempt_postage, state, price)
    return render_template('index.html', goods_list=goods_list, key=key, exempt_postage=exempt_postage, state=state,
                           price=price)


@app.route('/manage_goods', methods=['GET'])
@login_required
def manage_goods():
    error = request.args.get('error')
    success = request.args.get('success')
    user_id = session.get('user_id')
    goods_list = db_api.get_goods_list_of_user(user_id)
    return render_template('manage_goods.html', success=success, error=error, goods_list=goods_list)


@app.route('/add_goods', methods=['POST'])
@login_required
def add_goods():
    name = request.form.get('name', '')
    description = request.form.get('description', '')
    img = upload_file(request.files.get('img', None))
    if img is None:
        img = url_for('static', filename='images/cart.jpeg')
    price = request.form.get('price', '')
    exempt_postage = request.form.get('exempt_postage', '') == 'on'
    owner = session.get('user_id')
    if db_api.create_goods(owner, name, description, img, price, exempt_postage):
        return redirect(url_for('manage_goods') + '?success=添加商品成功！')
    return redirect(url_for('manage_goods') + '?error=添加商品失败！参数不正确。')


@app.route('/update_goods', methods=['POST'])
@login_required
def update_goods():
    name = request.form.get('name', '')
    description = request.form.get('description', '')
    img = upload_file(request.files.get('img', None))
    goods_id = request.form.get('id', '')
    price = request.form.get('price', '')
    exempt_postage = request.form.get('exempt_postage', '')
    exempt_postage = exempt_postage == 'on' or exempt_postage == 'true'
    owner = session.get('user_id')
    if db_api.update_goods(owner, goods_id, name, description, img, price, exempt_postage):
        return redirect(url_for('manage_goods') + '?success=修改商品信息成功！')
    return redirect(url_for('manage_goods') + '?error=修改商品信息失败！参数不正确。')


@app.route('/delete_goods', methods=['GET'])
@login_required
def delete_goods():
    goods_id = request.args.get('id', '')
    owner = session.get('user_id')
    if db_api.delete_goods(owner, goods_id):
        return redirect(url_for('manage_goods') + '?success=删除商品成功！')
    return redirect(url_for('manage_goods') + '?error=删除失败！没有权限。')


@app.route('/goods_detail', methods=['GET'])
@login_required
def goods_detail():
    error = request.args.get('error')
    success = request.args.get('success')
    goods_id = request.args.get('id')
    if goods_id == '':
        goods_id = None
    goods = db_api.get_goods_detail(goods_id)
    if goods is None:
        error = '错误！非法请求！该商品不存在！'
        owner = None
        comments = None
        order = None
        comment_order = 'asc'
    else:
        owner = db_api.get_user_info(goods['owner'])
        comment_order = request.args.get('comment_order', 'asc')
        comments = db_api.get_comments(goods_id, comment_order)
        order = db_api.get_order_by_user_and_goods(session.get('user_id'), goods_id)
    return render_template('goods_detail.html', error=error, success=success, goods=goods, owner=owner,
                           comments=comments, order=order, comment_order=comment_order)


@app.route('/apply_order', methods=['GET'])
@login_required
def apply_order():
    goods_id = request.args.get('id')
    user_id = session.get('user_id')
    if db_api.apply_order(user_id, goods_id):
        return redirect(url_for('goods_detail') + f'?id={goods_id}&success=申请成功！')
    return redirect(url_for('goods_detail') + f'?id={goods_id}&error=申请失败！不能重复申请！')


@app.route('/abandon_order', methods=['GET'])
@login_required
def abandon_order():
    goods_id = request.args.get('id')
    source = request.args.get('from')
    user_id = session.get('user_id')
    if db_api.abandon_order(user_id, goods_id):
        if source:
            return redirect(source + f'?success=操作成功！')
        return redirect(url_for('goods_detail') + f'?id={goods_id}&success=操作成功！')
    if source:
        return redirect(source + f'?error=操作失败！')
    return redirect(url_for('goods_detail') + f'?id={goods_id}&error=操作失败！')


@app.route('/manage_order', methods=['GET'])
@login_required
def manage_order():
    error = request.args.get('error')
    success = request.args.get('success')
    user_id = session.get('user_id')
    orders_from_user = db_api.get_orders_from_user(user_id)
    orders_to_user = db_api.get_orders_to_user(user_id)
    address_list = db_api.get_address_list(user_id)
    return render_template('manage_order.html', error=error, success=success, orders_from_user=orders_from_user,
                           orders_to_user=orders_to_user, state_map=db_api.ORDER_STATE_MAP,
                           state_color_map=db_api.ORDER_STATE_COLOR_MAP, **db_api.ORDER_KEYS, address_list=address_list)


@app.route('/approve_order', methods=['GET'])
@login_required
def approve_order():
    goods_id = request.args.get('goods_id')
    order_id = request.args.get('order_id')
    user_id = session.get('user_id')
    if db_api.approve_order(user_id, goods_id, order_id):
        return redirect(url_for('manage_order') + f'?success=操作成功！')
    return redirect(url_for('manage_order') + f'?error=操作失败！没有权限！')


@app.route('/establish_order/<goods_id>/<order_id>', methods=['GET'])
@login_required
def establish_order(goods_id, order_id):
    user_id = session.get('user_id')
    address_id = request.args.get('address')
    if db_api.establish_order(user_id, goods_id, order_id, address_id):
        return redirect(url_for('manage_order') + f'?success=操作成功！')
    return redirect(url_for('manage_order') + f'?error=操作失败！没有权限！')


@app.route('/deliver_goods', methods=['POST'])
@login_required
def deliver_goods():
    user_id = session.get('user_id')
    code = request.form.get('code')
    goods_id = request.form.get('goods_id')
    order_id = request.form.get('order_id')
    company = request.form.get('company')
    if db_api.deliver_goods(user_id, goods_id, order_id, code, company):
        return redirect(url_for('manage_order') + f'?success=操作成功！')
    return redirect(url_for('manage_order') + f'?error=操作失败！没有权限！')


@app.route('/finish_order/<goods_id>/<order_id>', methods=['GET'])
@login_required
def finish_order(goods_id, order_id):
    user_id = session.get('user_id')
    if db_api.finish_order(user_id, goods_id, order_id):
        return redirect(url_for('manage_order') + f'?success=操作成功！')
    return redirect(url_for('manage_order') + f'?error=操作失败！没有权限！')


@app.route('/add_comment', methods=['POST'])
@login_required
def add_comment():
    goods_id = request.form.get('id', '')
    content = request.form.get('content', '')
    user_id = session.get('user_id')
    if db_api.create_comment(user_id, goods_id, content):
        return redirect(url_for('goods_detail') + f'?id={goods_id}&success=添加评论成功！')
    return redirect(url_for('goods_detail') + f'?id={goods_id}&error=添加评论失败！参数不正确。')


@app.route('/delete_comment', methods=['GET'])
@login_required
def delete_comment():
    comment_id = request.args.get('comment_id', '')
    goods_id = request.args.get('goods_id', '')
    user_id = session.get('user_id')
    if db_api.delete_comment(user_id, goods_id, comment_id):
        return redirect(url_for('goods_detail') + f'?id={goods_id}&success=删除评论成功！')
    return redirect(url_for('goods_detail') + f'?id={goods_id}&error=删除评论失败！没有权限。')


@app.route('/manage_address', methods=['GET'])
@login_required
def manage_address():
    error = request.args.get('error')
    success = request.args.get('success')
    user_id = session.get('user_id')
    address_list = db_api.get_address_list(user_id)
    return render_template('manage_address.html', address_list=address_list, error=error, success=success)


@app.route('/add_address', methods=['POST'])
@login_required
def add_address():
    name = request.form.get('name', '')
    phone = request.form.get('phone', '')
    location = request.form.get('location', '')
    user_id = session.get('user_id')
    if db_api.create_address(user_id, name, phone, location):
        return redirect(url_for('manage_address') + '?success=添加地址成功！')
    return redirect(url_for('manage_address') + '?error=添加地址失败！参数不正确。')


@app.route('/delete_address', methods=['GET'])
@login_required
def delete_address():
    address_id = request.args.get('id', '')
    user_id = session.get('user_id')
    result = db_api.delete_address(user_id, address_id)
    if result is True:
        return redirect(url_for('manage_address') + '?success=删除地址成功！')
    elif isinstance(result, Exception):
        return redirect(url_for('manage_address') + '?error=删除地址失败！当前地址有订单。')
    else:
        return redirect(url_for('manage_address') + '?error=删除地址失败！没有权限。')


if __name__ == '__main__':
    app.debug = True
    app.run(port='8000')
