# ===================================================================================================
# Dependencies
# ===================================================================================================
import psycopg2
from hashlib import md5

# ===================================================================================================
# Constants
# ===================================================================================================
ORDER_STATE_APPLIED = 1
ORDER_STATE_APPROVED = 2
ORDER_STATE_ESTABLISHED = 3
ORDER_STATE_ON_ROAD = 4
ORDER_STATE_FINISHED = 5
ORDER_STATE_OFF_SALE = 6

ORDER_STATE_MAP = {
    ORDER_STATE_APPLIED: '待同意',
    ORDER_STATE_APPROVED: '待补充信息',
    ORDER_STATE_ESTABLISHED: '待发货',
    ORDER_STATE_ON_ROAD: '待收货',
    ORDER_STATE_FINISHED: '已完成',
    ORDER_STATE_OFF_SALE: '被买走',
}

ORDER_KEYS = {
    'ORDER_STATE_APPLIED': ORDER_STATE_APPLIED,
    'ORDER_STATE_APPROVED': ORDER_STATE_APPROVED,
    'ORDER_STATE_ESTABLISHED': ORDER_STATE_ESTABLISHED,
    'ORDER_STATE_ON_ROAD': ORDER_STATE_ON_ROAD,
    'ORDER_STATE_FINISHED': ORDER_STATE_FINISHED,
    'ORDER_STATE_OFF_SALE': ORDER_STATE_OFF_SALE,
}

ORDER_STATE_COLOR_MAP = {
    ORDER_STATE_APPLIED: 'bg-info',
    ORDER_STATE_APPROVED: 'bg-primary',
    ORDER_STATE_ESTABLISHED: 'bg-danger',
    ORDER_STATE_ON_ROAD: 'bg-warning',
    ORDER_STATE_FINISHED: 'bg-success',
    ORDER_STATE_OFF_SALE: 'bg-secondary',
}


# ===================================================================================================
# Additional functions
# ===================================================================================================
def get_md5(password):
    """
    功能：获取字符串的md5值
    :param password:
    :return: md5值
    """
    return md5(password.encode('utf-8')).hexdigest()


def get_db_conn():
    """
    功能：获取数据库连接
    注意：替换为自己的数据库信息
    :return: psycopg2.connect
    """
    return psycopg2.connect(database='TradingPlatform',
                            user='postgres',
                            password='20021202xiaozx',
                            host='127.0.0.1',
                            port=5432)


# =========================================== 大作业分数组成 ===========================================
# 数据库设计 (15分)：ERD (15分)
# 功能实现 (70分)：建表(5分), 用户接口 (9分)，商品接口 (17分)，订单接口 (25分)，评论接口 (7分)，收货地址接口 (7分)。
# 优化 (5分)：接口的鲁棒性，异常输入处理，界面美化，附加功能等。
# 文档 (10分)：比如系统流程图，功能实现情况、实现方式和正确运行截图，任何关于稳定性和优化的工作，总结、感悟、建议等。
# ===================================================================================================


# ======================= 用户接口 (2 + 2 + 2 + 3 = 9分) ======================= #

def check_username_used(username):
    """
    功能：检测用户名是否已经被注册。

    :param username: 要检测的用户名
    :return: 如果用户名已被注册，返回True；否则返回False。
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    query = 'select * from "User" where username = %s'
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    conn.close()
    if user is not None:
        return True
    else:
        return False


def create_user(username, password):
    """
    功能：在数据库中创建用户，用于实现注册功能。

    :param username: 用户名称
    :param password: 用户明文密码，建议存储时使用md5加密
    :return: 如果创建成功，返回True；否则返回False。
    """
    password = get_md5(password)
    success = True
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        query = 'insert into "User" (username, password) values (%s, %s)'
        cursor.execute(query, (username, password))
        conn.commit()
    except psycopg2.Error as err:
        success = False
        print(err)
    else:
        conn.close()
    return success


def login(username, password):
    """
    功能：登录用户，并返回用户的id。
    分值：2分
    :param username: 用户名称
    :param password: 用户明文密码
    :return: 如果登录成功，返回用户id；否则返回None
    """
    password = get_md5(password)
    conn = get_db_conn()
    cursor = conn.cursor()
    query = 'select id from "User" where username = %s and password = %s'
    cursor.execute(query, (username, password))
    user = cursor.fetchone()
    user_id = user[0] if user is not None else None
    conn.close()
    return user_id


def get_user_info(user_id):
    """
    功能：获取用户信息摘要，用于商品详情页中显示卖家的信息。
    分值：3分
    :param user_id: 要获取的用户id
    :return: 如果获取用户信息失败，返回None；否则返回包含如下字段的dict：
        username: 字符串，该用户的名称
        sale_count: 数字，该用户卖出的商品数量（即完成的订单数）
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    query = 'select username from "User" where id = %s'
    cursor.execute(query, (user_id,))
    user = cursor.fetchone()
    username = user[0] if user is not None else None
    query = 'select count(*) from "Order" where user_id = %s and state = %s'
    cursor.execute(query, (user_id, ORDER_STATE_FINISHED))
    sale_count = cursor.fetchone()[0]
    conn.close()
    if username is None:
        return None
    else:
        return {
            'username': username,
            'sale_count': sale_count
        }


# ======================= 商品接口 (2 + 2 + 5 + 3 + 2 + 3 = 17分) ======================= #
def create_goods(owner, name, description, img, price, exempt_postage):
    """
    功能：发布二手商品。
    分值：2分
    :param owner: 商品发布者id
    :param name: 商品的名称
    :param description: 商品的描述
    :param img: 商品图片链接
    :param price: 商品的价格
    :param exempt_postage: 商品是否包邮，布尔值，True表示包邮，False表示不包邮
    :return: 如果创建成功，返回True；否则返回False。
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    query = 'insert into "Goods" (owner, name, description, img, price, exempt_postage) values (%s, %s, %s, %s, %s, %s)'
    cursor.execute(query, (owner, name, description, img, price, exempt_postage))
    if cursor.rowcount == 0:
        conn.close()
        return False
    else:
        conn.commit()
        conn.close()
        return True


def update_goods(owner, goods_id, name, description, img, price, exempt_postage):
    """
    功能：更新商品信息。
    分值：2分
    :param owner: 商品发布者id
    :param goods_id: 商品的id
    :param name: 商品的名称
    :param description: 商品的描述
    :param img: 商品图片链接。注意！如果未上传新的商品图片，此字段为None，此时无需更新该商品的img字段！
    :param price: 商品的价格
    :param exempt_postage: 商品是否包邮，布尔值，True表示包邮，False表示不包邮
    :return: 如果更新成功，返回True；否则返回False。
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    if img is None:
        query = 'update "Goods" set name = %s, description = %s, price = %s, exempt_postage = %s where id = %s and ' \
                'owner = %s'
        cursor.execute(query, (name, description, price, exempt_postage, goods_id, owner))

    else:
        query = 'update "Goods" set name = %s, description = %s, img = %s, price = %s, exempt_postage = %s where id = ' \
                '%s and owner = %s'
        cursor.execute(query, (name, description, img, price, exempt_postage, goods_id, owner))
    if cursor.rowcount == 0:
        conn.close()
        return False
    else:
        conn.commit()
        conn.close()
        return True


def get_goods_list(key=None, exempt_postage=None, state=None, price=None):
    """
    功能：获取商品列表，用于交易大厅的商品展示。
    分值：5分
    :param key: 搜索关键词，用于进行商品名称和商品描述等的搜索。可能为None或为空字符串，此时表示不指定搜索关键词。
    :param exempt_postage: 用于根据是否包邮对商品进行筛选。为None或为all时表示不筛选，为yes时仅选择包邮的商品，为no时仅选择不包邮的商品。
    :param state: 用于根据商品状态对商品进行筛选。为None或为all时表示不筛选，为yes时仅选择可购买的商品，为no时仅选择已售出的商品。
    :param price: 用于按价格对商品进行排序。为None或asc时表示价格升序，为desc时表示价格降序。
    :return: 返回list形式的商品列表，list的每一项为一个以dict表示的商品，每个dict的字段如下：
        id: 商品id
        name: 商品名称
        description: 商品描述
        img: 商品图片链接
        price: 商品价格
        exempt_postage: 是否包邮
        owner: 商品发布者id
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    if state == 'yes':
        order_state = ORDER_STATE_APPLIED
        query = 'select id, name, description, img, price, exempt_postage, owner from "Goods" where (id not in (' \
                'select goods_id from "Order") or id in (select goods_id from "Order" where state = %s))'
        if key is None or key == '':
            cursor.execute(query, (order_state,))
        else:
            q = ' and name like %s or description like %s'
            cursor.execute(query + q, (order_state, key, key))
    elif state == 'no':
        order_state = ORDER_STATE_APPLIED
        query = 'select id, name, description, img, price, exempt_postage, owner from "Goods" where (id in (select ' \
                'goods_id from "Order") and id not in (select goods_id from "Order" where state = %s))'
        if key is None or key == '':
            cursor.execute(query, (order_state,))
        else:
            q = ' and name like %s or description like %s'
            cursor.execute(query + q, (order_state, key, key))
    else:
        query = 'select id, name, description, img, price, exempt_postage, owner from "Goods"'
        if key is None or key == '':
            cursor.execute(query)
        else:
            q = ' where name like %s or description like %s'
            cursor.execute(query + q, (key, key))
    goods_list = []
    for row in cursor.fetchall():
        goods_list.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'img': row[3],
            'price': row[4],
            'exempt_postage': row[5],
            'owner': row[6]
        })
    conn.close()
    if price == 'asc':
        goods_list.sort(key=lambda x: x['price'])
    elif price == 'desc':
        goods_list.sort(key=lambda x: x['price'], reverse=True)
    if exempt_postage == 'yes':
        goods_list = list(filter(lambda x: x['exempt_postage'] is True, goods_list))
    elif exempt_postage == 'no':
        goods_list = list(filter(lambda x: x['exempt_postage'] is False, goods_list))
    return goods_list


def get_goods_list_of_user(user_id):
    """
    功能：获取某个用户发布的商品列表，用于商品管理页面。
    分值：3分
    :param user_id: 要获取商品列表的用户id
    :return: 返回list形式的商品列表，list的每一项为一个以dict表示的商品，每个dict的字段如下：
        id: 商品id
        name: 商品名称
        description: 商品描述
        img: 商品图片链接
        price: 商品价格
        exempt_postage: 是否包邮
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    query = 'select id, name, description, img, price, exempt_postage from "Goods" where owner = %s'
    cursor.execute(query, (user_id,))
    goods_list = []
    for row in cursor.fetchall():
        goods_list.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'img': row[3],
            'price': row[4],
            'exempt_postage': row[5]
        })
    conn.close()
    return goods_list


def delete_goods(owner, goods_id):
    """
    功能：删除商品。
    分值：2分
    :param owner: 商品发布者的id
    :param goods_id: 商品id
    :return: 如果删除成功，返回True；否则返回False
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    query = 'delete from "Goods" where id = %s and owner = %s'
    cursor.execute(query, (goods_id, owner))
    if cursor.rowcount == 0:
        conn.close()
        return False
    else:
        conn.commit()
        conn.close()
        return True


def get_goods_detail(goods_id):
    """
    功能：获取商品详情。
    分值：3分
    :param goods_id: 要获取的商品id
    :return: dict形式的商品信息，字段如下：
        name: 商品名称
        description: 商品描述
        img: 商品图片链接
        price: 商品价格
        exempt_postage: 商品是否包邮
        owner: 商品发布者id
        id: 商品id
        apply_count: 该商品”想要“的人数
        off_sale: 商品是否已售出，True表示已售出，False表示可购买
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    query = 'select name, description, img, price, exempt_postage, owner from "Goods" where id = %s'
    cursor.execute(query, (goods_id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return None
    else:
        query = 'select count(*) from "Order" where goods_id = %s and state = %s'
        cursor.execute(query, (goods_id, ORDER_STATE_OFF_SALE))
        off_sale = cursor.fetchone()
        query = 'select count(*) from "Order" where goods_id = %s and state = %s'
        cursor.execute(query, (goods_id, ORDER_STATE_APPLIED))
        apply = cursor.fetchone()
        conn.close()
        return {
            'name': row[0],
            'description': row[1],
            'img': row[2],
            'price': row[3],
            'exempt_postage': row[4],
            'owner': row[5],
            'id': goods_id,
            'apply_count': apply[0],
            'off_sale': off_sale[0] > 0
        }


# ======================= 订单接口 (2 + 3 + 3 + 2 + 2 + 2 + 2 + 4 + 5 = 25分) ======================= #
def apply_order(customer, goods_id):
    """
    功能：用户点击“想要”，申请购买商品（即创建ORDER_STATE_APPLIED状态的订单）。
    分值：2分
    :param customer: 申请人id
    :param goods_id: 商品id
    :return: 如果申请成功，返回True；否则返回False
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    query = 'insert into "Order" (user_id, goods_id, state) values (%s, %s, %s)'
    cursor.execute(query, (customer, goods_id, ORDER_STATE_APPLIED))
    if cursor.rowcount == 0:
        conn.close()
        return False
    else:
        conn.commit()
        conn.close()
        return True


def abandon_order(customer, goods_id):
    """
    功能：放弃商品的购买申请（即删除订单）。注意！用户放弃购买申请可能使有些商品从“已卖出”状态（即ORDER_STATE_OFF_SALE）重新变成可购买状态，此时可能需对其他申请了该商品的订单进行状态更新！
    分值：3分
    :param customer: 申请人id
    :param goods_id: 商品id
    :return: 如果放弃成功，返回True；否则返回False
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    query_delete = 'delete from "Order" where user_id = %s and goods_id = %s'
    query_update = 'update "Order" set state = %s where goods_id = %s and state = %s'
    cursor.execute(query_delete, (customer, goods_id))
    if cursor.rowcount == 0:
        conn.close()
        return False
    else:
        cursor.execute(query_update, (ORDER_STATE_APPLIED, goods_id, ORDER_STATE_OFF_SALE))
        conn.commit()
        conn.close()
        return True


def approve_order(owner, goods_id, order_id):
    """
    功能：商品发布者同意某个申请人的购买申请，即将订单状态修改为ORDER_STATE_APPROVED。注意！同意某个申请人的购买申请意味着该商品转变为已卖出状态（即ORDER_STATE_OFF_SALE），此时可能需要更新其他申请订单的状态。
    分值：3分
    :param owner: 商品发布者id
    :param goods_id: 商品id
    :param order_id: 订单id
    :return: 如果操作成功，返回True；否则返回False
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    query = 'update "Order" set state = %s where id = %s and goods_id = %s and goods_id in (select id from "Goods" ' \
            'where owner = %s)'
    cursor.execute(query, (ORDER_STATE_APPROVED, order_id, goods_id, owner))
    if cursor.rowcount == 0:
        conn.close()
        return False
    else:
        query_update = 'update "Order" set state = %s where goods_id = %s and id != %s'
        cursor.execute(query_update, (ORDER_STATE_OFF_SALE, goods_id, order_id))
        conn.commit()
        conn.close()
        return True


def establish_order(customer, goods_id, order_id, address_id):
    """
    功能：对于商品发布者同意的申请订单，申请人选择收货地址并“付款”，订单状态变为ORDER_STATE_ESTABLISHED。
    分值：2分
    :param customer: 申请人id
    :param goods_id: 商品id
    :param order_id: 订单id
    :param address_id: 收货地址id
    :return: 如果操作成功，返回True；否则返回False
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    query = 'update "Order" set state = %s, address_id = %s where id = %s and user_id = %s and goods_id = %s and ' \
            'state = %s'
    cursor.execute(query, (ORDER_STATE_ESTABLISHED, address_id, order_id, customer, goods_id, ORDER_STATE_APPROVED))
    if cursor.rowcount == 0:
        conn.close()
        return False
    else:
        conn.commit()
        conn.close()
        return True


def deliver_goods(owner, goods_id, order_id, code, company):
    """
    功能：对于已“付款”和添加收货地址的订单，商品发布者进行商品“发货”，并添加快递信息，订单状态变为ORDER_STATE_ON_ROAD。
    分值：2分
    :param owner: 商品发布者id
    :param goods_id: 商品id
    :param order_id: 订单id
    :param code: 快递单号
    :param company: 快递公司
    :return: 如果操作成功，返回True；否则返回False
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    query = 'update "Order" set state = %s, express_code = %s, express_company = %s where id = %s and goods_id = %s ' \
            'and state = %s'
    cursor.execute(query, (ORDER_STATE_ON_ROAD, code, company, order_id, goods_id, ORDER_STATE_ESTABLISHED))
    if cursor.rowcount == 0:
        conn.close()
        return False
    else:
        conn.commit()
        conn.close()
        return True


def finish_order(customer, goods_id, order_id):
    """
    功能：申请人确认收货，订单状态变为ORDER_STATE_FINISHED。
    分值：2分
    :param customer: 申请人id
    :param goods_id: 商品id
    :param order_id: 订单id
    :return: 如果操作成功，返回True；否则返回False
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    query = 'update "Order" set state = %s where id = %s and user_id = %s and goods_id = %s'
    cursor.execute(query, (ORDER_STATE_FINISHED, order_id, customer, goods_id))
    if cursor.rowcount == 0:
        conn.close()
        return False
    else:
        conn.commit()
        conn.close()
        return True


def get_order_by_user_and_goods(user_id, goods_id):
    """
    功能：根据申请人id和商品id获取订单id，用于商品详情页检测当前用户是否已申请购买改商品。
    分值：2分
    :param user_id: 申请人id
    :param goods_id: 商品id
    :return: 如果未找到相应订单，返回None；否则返回一个dict，字段如下：
        id: 订单id
        state: 订单的状态
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    query = 'select id, state from "Order" where user_id = %s and goods_id = %s'
    cursor.execute(query, (user_id, goods_id))
    result = cursor.fetchone()
    conn.close()
    if result is None:
        return None
    else:
        return {
            'id': result[0],
            'state': result[1]
        }


def get_orders_from_user(user_id):
    """
    功能：获取某用户发起的订单列表。
    分值：4分
    :param user_id: 要获取的用户id
    :return: 返回list形式的订单列表，list的每一项为一个以dict表示的订单，每个dict的字段如下：
        id: 订单id
        goods_id: 订单关联的商品id
        name: 订单关联的商品名称
        state: 订单状态
        price: 订单关联的商品价格
        exempt_postage: 订单关联的商品是否包邮
        express_code: 订单的快递单号，可以为空
        express_company: 订单的快递公司，可以为空
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    query = 'select "Order".id, goods_id, name, state, price, exempt_postage, express_code, express_company from ' \
            '"Order" join "Goods" on "Order".goods_id = "Goods".id where user_id = %s'
    cursor.execute(query, (user_id,))
    result = cursor.fetchall()
    conn.close()
    if result is None:
        return None
    else:
        return [{
            'id': result[0],
            'goods_id': result[1],
            'name': result[2],
            'state': result[3],
            'price': result[4],
            'exempt_postage': result[5],
            'express_code': result[6],
            'express_company': result[7]
        } for result in result]


def get_orders_to_user(user_id):
    """
    功能：获取某用户收到的订单列表。
    分值：5分
    :param user_id: 要获取的用户id
    :return: 返回list形式的订单列表，list的每一项为一个以dict表示的订单，每个dict的字段如下：
        id: 订单id
        user_id: 订单申请人id
        goods_id: 订单关联的商品id
        name: 订单关联的商品名称
        state: 订单状态
        price: 订单关联的商品价格
        exempt_postage: 订单关联的商品是否包邮
        username: 订单申请人用户名
        address_name: 订单关联的收件人姓名
        address_phone: 订单关联的收件人手机号
        address_location: 订单关联的收件人地址
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    query = 'select "Order".id, "Order".user_id, "Order".goods_id, "Goods".name, "Order".state, "Goods".price, ' \
            '"Goods".exempt_postage, "User".username, "Address".name, "Address".phone, "Address".location from ' \
            '"Order" left outer join "Goods" on "Order".goods_id = "Goods".id left outer join "User" on ' \
            '"Order".user_id = "User".id left outer join "Address" on "Order".address_id = "Address".id where ' \
            '"Goods".owner= %s;'
    cursor.execute(query, (user_id,))
    result = cursor.fetchall()
    conn.close()
    if result is None:
        return None
    else:
        return [{
            'id': result[0],
            'user_id': result[1],
            'goods_id': result[2],
            'name': result[3],
            'state': result[4],
            'price': result[5],
            'exempt_postage': result[6],
            'username': result[7],
            'address_name': result[8],
            'address_phone': result[9],
            'address_location': result[10]
        } for result in result]


# ======================= 评论接口 (2 + 3 + 2 = 7分) ======================= #

def create_comment(user_id, goods_id, content):
    """
    功能：添加评论，用于商品详情页当前用户对商品的评论。
    分值：2分
    :param user_id: 发表评论的用户id
    :param goods_id: 评论关联的商品id
    :param content: 评论内容
    :return: 如果评论添加成功，返回True，否则返回False
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    query = 'insert into "Comment" (user_id, goods_id, content, create_at) values (%s, %s, %s, current_timestamp)'
    cursor.execute(query, (user_id, goods_id, content))
    if cursor.rowcount == 1:
        conn.commit()
        conn.close()
        return True
    else:
        conn.rollback()
        conn.close()
        return False


def get_comments(goods_id, order='asc'):
    """
    功能：获取某商品的评论列表。
    分值：3分
    :param goods_id: 要获取评论的商品id
    :param order: 评论的排序方式，asc表示时间升序，desc表示时间降序
    :return: 返回list形式的评论列表，list的每一项为一个以dict表示的评论，每个dict的字段如下：
        id: 评论id
        user_id: 评论发表人id
        username: 评论发表人用户名
        content: 评论内容
        create_at: 字符串形式的评论发布时间，请在后台完成时间的格式化
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    query = 'select "Comment".id, user_id, username, content, "Comment".create_at from "Comment" join "User" on ' \
            '"Comment".user_id = "User".id where goods_id = %s order by create_at ' + order
    cursor.execute(query, (goods_id,))
    result = cursor.fetchall()
    conn.close()
    if result is None:
        return None
    else:
        return [{
            'id': result[0],
            'user_id': result[1],
            'username': result[2],
            'content': result[3],
            'create_at': result[4].strftime('%Y-%m-%d %H:%M:%S')
        } for result in result]


def delete_comment(user_id, goods_id, comment_id):
    """
    功能：删除评论，只能删除自己发布的评论。
    分值：2分
    :param user_id: 进行删除操作的用户id
    :param goods_id: 评论关联的商品id
    :param comment_id: 评论id
    :return: 如果删除成功，返回True；否则返回False
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    query = 'delete from "Comment" where id = %s and user_id = %s and goods_id = %s'
    cursor.execute(query, (comment_id, user_id, goods_id))
    if cursor.rowcount == 1:
        conn.commit()
        conn.close()
        return True
    else:
        conn.rollback()
        conn.close()
        return False


# ======================= 收货地址接口 (2 + 3 + 2 = 7分) ======================= #

def create_address(user_id, name, phone, location):
    """
    功能：添加收货地址。
    分值：2分
    :param user_id: 收货地址关联的用户id
    :param name: 收件人姓名
    :param phone: 收件人手机号
    :param location: 收件人地址
    :return: 如果添加成功，返回True；否则返回False
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    query = 'insert into "Address" (user_id, name, phone, location) values (%s, %s, %s, %s)'
    cursor.execute(query, (user_id, name, phone, location))
    if cursor.rowcount == 1:
        conn.commit()
        conn.close()
        return True
    else:
        conn.rollback()
        conn.close()
        return False


def get_address_list(user_id):
    """
    功能：获取某用户的收货地址列表
    分值：3分
    :param user_id: 要获取收货地址的用户id
    :return: 返回list形式的评论列表，list的每一项为一个以dict表示的评论，每个dict的字段如下：
        id: 收货地址id
        name: 收件人姓名
        phone: 收件人手机号
        location: 收件人地址
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    query = 'select id, name, phone, location from "Address" where user_id = %s'
    cursor.execute(query, (user_id,))
    result = cursor.fetchall()
    conn.close()
    if result is None:
        return None
    else:
        return [{
            'id': result[0],
            'name': result[1],
            'phone': result[2],
            'location': result[3]
        } for result in result]


def delete_address(user_id, address_id):
    """
    分值：2分
    功能：删除收货地址，只能删除自己的收货地址。
    :param user_id: 进行删除操作的用户id
    :param address_id: 收货地址id
    :return: 如果删除成功，返回True；否则返回False
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    query = 'delete from "Address" where id = %s and user_id = %s'
    try:
        cursor.execute(query, (address_id, user_id))
    except Exception as e:
        print(e)
        conn.rollback()
        conn.close()
        return e
    if cursor.rowcount == 1:
        conn.commit()
        conn.close()
        return True
    else:
        conn.rollback()
        conn.close()
        return False
